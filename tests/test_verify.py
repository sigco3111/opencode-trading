"""Tests for :mod:`opencode_trading.verify` (v0.4.0).

The verify module validates an OpenCode workspace artifact directory
(``<path>/.opencode/``) and optionally round-trips it against a
TradingCodex source. Public API surface:

- :class:`VerifyResult` — frozen dataclass with ``passed``, ``errors``,
  ``warnings``, and ``summary`` fields.
- :func:`verify_workspace` — read the workspace, return a ``VerifyResult``.

These tests cover the contract S1–S5 scenarios (happy path, missing
file, invalid hook event, round-trip equivalence, frontmatter
mismatch) plus a structural test for ``VerifyResult`` immutability.
"""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# VerifyResult shape
# ---------------------------------------------------------------------------


def test_verify_result_is_frozen_dataclass() -> None:
    """VerifyResult must be immutable."""
    from opencode_trading.verify import VerifyResult

    r = VerifyResult(passed=True, errors=(), warnings=(), summary={})
    assert r.passed is True
    with pytest.raises(FrozenInstanceError):
        r.passed = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# S1: happy path
# ---------------------------------------------------------------------------


def test_verify_workspace_s1_happy(tmp_path: Path) -> None:
    """S1: valid attach_workspace output → passed=True, no errors."""
    from opencode_trading.attach import attach_workspace
    from opencode_trading.verify import verify_workspace

    target = tmp_path / "ws"
    ws, _ = attach_workspace(target=target)
    ws.write(target / ".opencode", overwrite=True)

    result = verify_workspace(target)

    assert result.passed is True
    assert result.errors == ()
    assert result.summary.get("agents", 0) >= 10
    assert result.summary.get("skills", 0) >= 12
    assert result.summary.get("hooks", 0) >= 8
    assert result.summary.get("mcp_servers", 0) == 1


# ---------------------------------------------------------------------------
# S2: missing file
# ---------------------------------------------------------------------------


def test_verify_workspace_s2_missing_file(tmp_path: Path) -> None:
    """S2: agents.json deleted → passed=False, error names the file."""
    from opencode_trading.attach import attach_workspace
    from opencode_trading.verify import verify_workspace

    target = tmp_path / "ws"
    ws, _ = attach_workspace(target=target)
    ws.write(target / ".opencode", overwrite=True)
    (target / ".opencode" / "agents.json").unlink()

    result = verify_workspace(target)

    assert result.passed is False
    assert any("agents.json" in e for e in result.errors)


# ---------------------------------------------------------------------------
# S3: invalid hook event
# ---------------------------------------------------------------------------


def test_verify_workspace_s3_invalid_hook_event(tmp_path: Path) -> None:
    """S3: invalid event in hooks.json → passed=False, error names the bad event."""
    from opencode_trading.attach import attach_workspace
    from opencode_trading.verify import verify_workspace

    target = tmp_path / "ws"
    ws, _ = attach_workspace(target=target)
    ws.write(target / ".opencode", overwrite=True)
    hooks_path = target / ".opencode" / "hooks.json"
    data = json.loads(hooks_path.read_text())
    data.append({"event": "NotARealEvent", "command": ["x"], "env": {}, "blocking": True})
    hooks_path.write_text(json.dumps(data))

    result = verify_workspace(target)

    assert result.passed is False
    assert any("NotARealEvent" in e for e in result.errors)


# ---------------------------------------------------------------------------
# S4: round-trip equivalence
# ---------------------------------------------------------------------------


def test_verify_workspace_s4_round_trip(tmp_path: Path, sample_tcx_workspace: Path) -> None:
    """S4: --workspace <tcx_src> → round-trip TCX↔OpenCode equivalence.

    Uses convert_workspace(source) so the OpenCodeWorkspace is generated
    from the same source the verify compares against — guarantees round-trip
    equivalence. (attach_workspace uses bundled templates which are a
    different state, so S4 specifically tests convert+verify path.)
    """
    from opencode_trading.converters.codex_to_opencode import convert_workspace
    from opencode_trading.verify import verify_workspace

    target = tmp_path / "ws"
    ws = convert_workspace(sample_tcx_workspace, to="opencode")
    ws.write(target / ".opencode", overwrite=True)

    result = verify_workspace(target, source=sample_tcx_workspace)

    assert result.passed is True, f"errors: {result.errors}"


# ---------------------------------------------------------------------------
# S5: frontmatter / dir name mismatch
# ---------------------------------------------------------------------------


def test_verify_workspace_s5_frontmatter_mismatch(tmp_path: Path) -> None:
    """S5: skill dir name 'review-risk' but fm.name='totally-different' → passed=False."""
    from opencode_trading.attach import attach_workspace
    from opencode_trading.verify import verify_workspace

    target = tmp_path / "ws"
    ws, _ = attach_workspace(target=target)
    ws.write(target / ".opencode", overwrite=True)
    skill_dir = target / ".opencode" / "skills" / "review-risk"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        '---\nname: totally-different\ndescription: "x"\n---\n\nbody\n'
    )

    result = verify_workspace(target)

    assert result.passed is False
    assert any("review-risk" in e and "totally-different" in e for e in result.errors)


# ---------------------------------------------------------------------------
# Edge cases: empty / malformed inputs (v1.0.0 hardening)
# ---------------------------------------------------------------------------


def test_verify_workspace_empty_hooks_list_passes(tmp_path: Path) -> None:
    """Edge: hooks.json is a valid empty list → still passes (zero hooks)."""
    from opencode_trading.attach import attach_workspace
    from opencode_trading.verify import verify_workspace

    target = tmp_path / "ws"
    ws, _ = attach_workspace(target=target)
    ws.write(target / ".opencode", overwrite=True)
    (target / ".opencode" / "hooks.json").write_text("[]")

    result = verify_workspace(target)

    assert result.passed is True
    assert result.summary.get("hooks", -1) == 0
    assert result.errors == ()


def test_verify_workspace_malformed_hooks_json(tmp_path: Path) -> None:
    """Edge: hooks.json is invalid JSON → passed=False, error names 'invalid JSON'."""
    from opencode_trading.attach import attach_workspace
    from opencode_trading.verify import verify_workspace

    target = tmp_path / "ws"
    ws, _ = attach_workspace(target=target)
    ws.write(target / ".opencode", overwrite=True)
    (target / ".opencode" / "hooks.json").write_text("{not valid json")

    result = verify_workspace(target)

    assert result.passed is False
    assert any("invalid JSON" in e and "hooks.json" in e for e in result.errors)


def test_verify_workspace_malformed_agents_json(tmp_path: Path) -> None:
    """Edge: agents.json is a JSON scalar (not object/array) → passed=False."""
    from opencode_trading.attach import attach_workspace
    from opencode_trading.verify import verify_workspace

    target = tmp_path / "ws"
    ws, _ = attach_workspace(target=target)
    ws.write(target / ".opencode", overwrite=True)
    (target / ".opencode" / "agents.json").write_text("42")

    result = verify_workspace(target)

    assert result.passed is False
    assert any("agents.json" in e for e in result.errors)


def test_verify_workspace_agent_with_empty_skills_passes(tmp_path: Path) -> None:
    """Edge: agent entry has empty skills list → still passes (degenerate but legal)."""
    from opencode_trading.attach import attach_workspace
    from opencode_trading.verify import verify_workspace

    target = tmp_path / "ws"
    ws, _ = attach_workspace(target=target)
    ws.write(target / ".opencode", overwrite=True)
    agents_path = target / ".opencode" / "agents.json"
    data = json.loads(agents_path.read_text())
    first_key = next(iter(data))
    data[first_key]["skills"] = []
    agents_path.write_text(json.dumps(data))

    result = verify_workspace(target)

    assert result.passed is True, f"unexpected errors: {result.errors}"
