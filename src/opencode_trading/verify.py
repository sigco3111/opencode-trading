"""opencode_trading.verify — Validate an OpenCode workspace artifact directory.

The :func:`verify_workspace` function reads a workspace's ``.opencode/``
artifacts (the JSON files and ``skills/<name>/SKILL.md`` trees emitted by
:meth:`opencode_trading.models.OpenCodeWorkspace.write`) and returns a
:class:`VerifyResult` describing whether the workspace is structurally
valid and (optionally) equivalent to a TradingCodex source workspace.

Validation rules
----------------
1. ``<path>/.opencode/`` must exist. Missing → error, no raise.
2. ``agents.json``, ``mcp.json``, ``hooks.json`` must exist and parse
   as JSON. Missing or invalid → error.
3. Each entry in ``hooks.json`` must declare an ``event`` in the
   :data:`opencode_trading.models.HookEvent` literal. Invalid → error.
4. Every ``skills/<dir>/SKILL.md`` file's frontmatter ``name`` must
   match its directory name. Mismatch → error naming both.
5. If a ``source`` TCX workspace is provided, the bundled TCX→OpenCode
   conversion is run and the resulting agent / skill / hook names and
   hook signatures are compared to the on-disk artifacts. Mismatches →
   error. (We do NOT compare full prompt text — only NAMES + hook
   SIGNATURES — to keep the verifier robust to prompt copy-edit drift
   in either direction.)

Implementation note
-------------------
This module deliberately avoids importing from
:mod:`opencode_trading.cli` (circular) or
:mod:`opencode_trading.attach` (which is the **producer**, not a
validator). For the round-trip comparison we call the lower-level
:func:`opencode_trading.convert_workspace` so the verifier stays
independent of the attach path.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, get_args

from opencode_trading._frontmatter import parse_frontmatter
from opencode_trading.models import HookEvent

_VALID_HOOK_EVENTS: frozenset[str] = frozenset(get_args(HookEvent))


@dataclass(frozen=True)
class VerifyResult:
    """Outcome of :func:`verify_workspace`.

    Attributes
    ----------
    passed : bool
        True if and only if ``errors`` is empty.
    errors : tuple[str, ...]
        Hard validation failures. Empty tuple means a clean run.
    warnings : tuple[str, ...]
        Soft issues that did not fail validation (reserved for future
        use; always empty in v0.4.0).
    summary : dict[str, int]
        Resource counts read from the on-disk artifacts. Keys:
        ``agents``, ``skills``, ``hooks``, ``mcp_servers``.
    """

    passed: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    summary: dict[str, int] = field(default_factory=dict)


def verify_workspace(path: Path, *, source: Path | None = None) -> VerifyResult:
    """Validate the OpenCode workspace at ``<path>/.opencode/``.

    Parameters
    ----------
    path : Path
        Workspace root (parent of ``.opencode/``).
    source : Path | None
        Optional TradingCodex source workspace to round-trip against.
        When provided, the verifier runs :func:`convert_workspace` on
        it and compares the resulting agent/skill/hook NAMES and hook
        SIGNATURES against the on-disk artifacts.

    Returns
    -------
    VerifyResult
        Frozen result with ``passed`` and accumulated ``errors``.
        This function never raises — every failure mode becomes an
        entry in ``errors`` (or, in the case of a missing
        ``.opencode/`` directory, a single short error string).
    """
    root = Path(path)
    opencode_dir = root / ".opencode"
    errors: list[str] = []
    summary: dict[str, int] = {
        "agents": 0,
        "skills": 0,
        "hooks": 0,
        "mcp_servers": 0,
    }

    if not opencode_dir.is_dir():
        return VerifyResult(
            passed=False,
            errors=(f"missing {opencode_dir}/",),
            summary={},
        )

    agents = _read_json(opencode_dir / "agents.json", errors, "agents.json")
    mcp = _read_json(opencode_dir / "mcp.json", errors, "mcp.json")
    hooks = _read_json(opencode_dir / "hooks.json", errors, "hooks.json")

    if agents is not None:
        summary["agents"] = len(agents)
    if mcp is not None:
        summary["mcp_servers"] = len(mcp)
    if hooks is not None:
        summary["hooks"] = len(hooks)
        _validate_hook_events(hooks, errors)

    skill_names = _collect_skill_names(opencode_dir, errors)
    summary["skills"] = len(skill_names)

    if source is not None:
        _compare_against_source(source, opencode_dir, errors)

    return VerifyResult(
        passed=len(errors) == 0,
        errors=tuple(errors),
        summary=summary,
    )


def _read_json(path: Path, errors: list[str], label: str) -> dict[str, Any] | list[Any] | None:
    """Read a JSON file or record an error. Returns None on failure."""
    if not path.is_file():
        errors.append(f"missing {label}")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {label}: {exc.msg}")
        return None
    if not isinstance(data, (dict, list)):
        errors.append(f"invalid JSON in {label}: expected object or array")
        return None
    return data


def _validate_hook_events(hooks: dict[str, Any] | list[Any], errors: list[str]) -> None:
    """Record an error for every hook entry whose ``event`` is invalid."""
    entries = hooks if isinstance(hooks, list) else list(hooks.values())
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        event = entry.get("event")
        if not isinstance(event, str) or event not in _VALID_HOOK_EVENTS:
            errors.append(f"invalid hook event: {event!r}")


def _collect_skill_names(opencode_dir: Path, errors: list[str]) -> set[str]:
    """Walk ``skills/*/SKILL.md`` and return the set of valid skill names.

    A skill is "valid" if its directory name matches its frontmatter
    ``name``. Mismatches and malformed frontmatter are recorded in
    ``errors``; the mismatched name is still included in the returned
    set so summary counts reflect the on-disk state.
    """
    skills_dir = opencode_dir / "skills"
    names: set[str] = set()
    if not skills_dir.is_dir():
        return names

    for skill_md in sorted(skills_dir.rglob("SKILL.md")):
        dir_name = skill_md.parent.name
        try:
            fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        except ValueError as exc:
            errors.append(f"invalid frontmatter in {skill_md}: {exc}")
            continue
        if fm.name != dir_name:
            errors.append(f"skill frontmatter mismatch: dir {dir_name!r} vs fm.name {fm.name!r}")
        names.add(dir_name)
    return names


def _compare_against_source(source: Path, opencode_dir: Path, errors: list[str]) -> None:
    """Compare on-disk artifacts against ``convert_workspace(source)``."""
    from opencode_trading.converters.codex_to_opencode import convert_workspace

    try:
        tcx_ws = convert_workspace(source, to="opencode")
    except Exception as exc:  # convert_workspace may raise on bad source
        errors.append(f"failed to convert source {source}: {exc}")
        return

    expected_agents = {a.name for a in tcx_ws.agents}
    actual_agents = _read_agents_names(opencode_dir, errors)
    missing_in_actual = expected_agents - actual_agents
    missing_in_expected = actual_agents - expected_agents
    for name in sorted(missing_in_actual):
        errors.append(f"agent {name!r} missing from workspace (present in source)")
    for name in sorted(missing_in_expected):
        errors.append(f"agent {name!r} present in workspace but absent from source")

    expected_skills = {s.name for s in tcx_ws.skills}
    actual_skills = _read_skill_names(opencode_dir, errors)
    missing_in_actual = expected_skills - actual_skills
    missing_in_expected = actual_skills - expected_skills
    for name in sorted(missing_in_actual):
        errors.append(f"skill {name!r} missing from workspace (present in source)")
    for name in sorted(missing_in_expected):
        errors.append(f"skill {name!r} present in workspace but absent from source")

    expected_hook_sigs = {_hook_signature(h) for h in tcx_ws.hooks}
    actual_hooks = _read_hooks(opencode_dir, errors)
    actual_hook_sigs = {_hook_signature(h) for h in actual_hooks}
    missing_hooks_in_actual = expected_hook_sigs - actual_hook_sigs
    missing_hooks_in_expected = actual_hook_sigs - expected_hook_sigs
    for sig in sorted(missing_hooks_in_actual):
        errors.append(f"hook {sig!r} missing from workspace (present in source)")
    for sig in sorted(missing_hooks_in_expected):
        errors.append(f"hook {sig!r} present in workspace but absent from source")


def _hook_signature(
    h: Any,
) -> tuple[str, tuple[str, ...], tuple[tuple[str, str], ...], bool]:
    """Return a comparable tuple of a hook's identifying fields.

    Accepts either an :class:`OpenCodeHook` dataclass or the dict form
    written to ``hooks.json`` (``{event, command, env, blocking}``).
    """
    if isinstance(h, dict):
        event = h.get("event")
        command = h.get("command") or ()
        env = h.get("env") or {}
        blocking = h.get("blocking", True)
    else:
        event = getattr(h, "event", None)
        command = getattr(h, "command", ()) or ()
        env = getattr(h, "env", None) or {}
        blocking = getattr(h, "blocking", True)
    env_items = tuple(sorted(env.items()))
    return (str(event), tuple(command), env_items, bool(blocking))


def _read_agents_names(opencode_dir: Path, errors: list[str]) -> set[str]:
    """Read agent names from ``agents.json`` (returns empty set on failure)."""
    path = opencode_dir / "agents.json"
    if not path.is_file():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    if not isinstance(data, dict):
        return set()
    return {str(k) for k in data.keys()}


def _read_skill_names(opencode_dir: Path, errors: list[str]) -> set[str]:
    """Read skill names from ``skills/*/`` directory names.

    We use directory names (not frontmatter names) so a workspace with
    only valid frontmatter matches the on-disk layout exactly.
    """
    skills_dir = opencode_dir / "skills"
    if not skills_dir.is_dir():
        return set()
    return {p.parent.name for p in skills_dir.rglob("SKILL.md") if p.parent.is_dir()}


def _read_hooks(opencode_dir: Path, errors: list[str]) -> list[Any]:
    """Read hook entries from ``hooks.json`` (returns empty list on failure)."""
    path = opencode_dir / "hooks.json"
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return list(data.values())
    return []
