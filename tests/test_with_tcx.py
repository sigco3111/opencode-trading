"""Tests for :mod:`opencode_trading.attach` ``with_tcx`` flag (v0.4.0).

When ``with_tcx=True``, ``attach_workspace()`` writes the bundled TCX v0.2.0
template files into a sibling ``.codex/``/``.tradingcodex/``/``.agents/`` tree
alongside the OpenCode bundle, so the user gets a complete, dual-use
workspace in a single command.
"""

from __future__ import annotations

from pathlib import Path


def test_attach_workspace_default_returns_none_tcx_root(tmp_path: Path) -> None:
    """Default behavior: with_tcx=False → returns (ws, None)."""
    from opencode_trading.attach import attach_workspace

    result = attach_workspace(target=tmp_path, package_spec="tradingcodex")
    # New return type is tuple; the old single-return is the first element
    assert isinstance(result, tuple)
    ws, tcx_root = result
    assert tcx_root is None
    assert ws.agents  # still populated


def test_attach_workspace_with_tcx_writes_all_three_dirs(tmp_path: Path) -> None:
    """S1 happy: with_tcx=True → .codex/.tradingcodex/.agents written eagerly
    by ``_write_tcx_files``; ``.opencode/`` written by the caller via
    ``ws.write()`` (TCX side-effects happen in-memory at attach time, not
    on disk until the CLI writes).
    """
    from opencode_trading.attach import attach_workspace

    ws, tcx_root = attach_workspace(
        target=tmp_path, package_spec="tradingcodex", with_tcx=True
    )
    assert isinstance(tcx_root, Path)
    assert (tmp_path / ".codex" / "agents").is_dir()
    assert (tmp_path / ".codex" / "hooks.json").is_file()
    assert (tmp_path / ".codex" / "prompts" / "base_instructions" / "head-manager.md").is_file()
    assert (tmp_path / ".tradingcodex" / "mainagent" / "head-manager.yaml").is_file()
    assert (tmp_path / ".tradingcodex" / "mainagent" / "subagent-registry.yaml").is_file()
    assert (tmp_path / ".tradingcodex" / "config.yaml").is_file()
    assert (tmp_path / ".tradingcodex" / "workflows").is_dir()
    assert (tmp_path / ".tradingcodex" / "subagents" / "skills").is_dir()
    assert (tmp_path / ".agents" / "skills").is_dir()
    ws.write(tmp_path / ".opencode", overwrite=True)
    assert (tmp_path / ".opencode" / "agents.json").exists()


def test_attach_with_tcx_bytes_match_bundled(tmp_path: Path) -> None:
    """S1 invariant: every written file's bytes must match the bundled source."""
    from opencode_trading.attach import _BUNDLED_DIR, attach_workspace

    _ws, _ = attach_workspace(
        target=tmp_path, package_spec="tradingcodex", with_tcx=True
    )
    pairs = [
        (tmp_path / ".codex" / "hooks.json", _BUNDLED_DIR / "hooks.json"),
        (
            tmp_path / ".tradingcodex" / "config.yaml",
            _BUNDLED_DIR / "tradingcodex" / "config.yaml",
        ),
        (
            tmp_path / ".tradingcodex" / "mainagent" / "head-manager.yaml",
            _BUNDLED_DIR / "mainagent" / "head-manager.yaml",
        ),
        (
            tmp_path / ".tradingcodex" / "mainagent" / "subagent-registry.yaml",
            _BUNDLED_DIR / "mainagent" / "subagent-registry.yaml",
        ),
        (
            tmp_path / ".codex" / "prompts" / "base_instructions" / "head-manager.md",
            _BUNDLED_DIR / "prompts" / "head-manager.md",
        ),
    ]
    for dest, src in pairs:
        assert dest.read_bytes() == src.read_bytes(), f"byte mismatch: {dest}"


def test_attach_with_tcx_role_skills_copied(tmp_path: Path) -> None:
    """S1 invariant: role-skills and orchestrator skills mirror under .tradingcodex and .agents."""
    from opencode_trading.attach import _BUNDLED_DIR, attach_workspace

    _ws, _ = attach_workspace(
        target=tmp_path, package_spec="tradingcodex", with_tcx=True
    )
    # Each role-skill under _BUNDLED_DIR/role-skills/<role>/<skill>/SKILL.md
    # must be present under .tradingcodex/subagents/skills/<role>/<skill>/SKILL.md
    for role_skill in (_BUNDLED_DIR / "role-skills").rglob("SKILL.md"):
        rel = role_skill.relative_to(_BUNDLED_DIR / "role-skills")
        dest = tmp_path / ".tradingcodex" / "subagents" / "skills" / rel
        assert dest.is_file(), f"missing: {dest}"
        assert dest.read_bytes() == role_skill.read_bytes()
    # Each orchestrator skill must be under .agents/skills/<skill>/SKILL.md
    for orch_skill in (_BUNDLED_DIR / "orchestrator").rglob("SKILL.md"):
        rel = orch_skill.relative_to(_BUNDLED_DIR / "orchestrator")
        dest = tmp_path / ".agents" / "skills" / rel
        assert dest.is_file(), f"missing: {dest}"
        assert dest.read_bytes() == orch_skill.read_bytes()


def test_attach_with_tcx_refuses_to_overwrite_without_flag(tmp_path: Path) -> None:
    """S3: existing TCX files + no overwrite → FileExistsError."""
    import pytest

    from opencode_trading.attach import attach_workspace

    (tmp_path / ".codex" / "agents").mkdir(parents=True)
    (tmp_path / ".codex" / "agents" / "fundamental-analyst.toml").write_text("stale")
    with pytest.raises(FileExistsError):
        attach_workspace(target=tmp_path, package_spec="tradingcodex", with_tcx=True)


# ---------------------------------------------------------------------------
# Edge cases: nested paths and long target names (v1.0.0 hardening)
# ---------------------------------------------------------------------------


def test_attach_with_tcx_nested_target_path(tmp_path: Path) -> None:
    """Edge: --target points to a non-existent deeply-nested path → created cleanly."""
    from opencode_trading.attach import attach_workspace

    deep = tmp_path / "a" / "b" / "c" / "d" / "trading-ws"
    assert not deep.exists()

    ws, tcx_root = attach_workspace(
        target=deep, package_spec="tradingcodex", with_tcx=True
    )
    ws.write(deep / ".opencode", overwrite=True)

    assert deep.is_dir()
    assert (deep / ".codex" / "agents").is_dir()
    assert (deep / ".opencode" / "agents.json").is_file()
    assert isinstance(tcx_root, Path)


def test_attach_with_tcx_long_target_path(tmp_path: Path) -> None:
    """Edge: --target has a 200-char basename → no path-length regression."""
    from opencode_trading.attach import attach_workspace

    long_name = "a" * 200
    target = tmp_path / long_name

    ws, tcx_root = attach_workspace(
        target=target, package_spec="tradingcodex", with_tcx=True
    )
    ws.write(target / ".opencode", overwrite=True)

    assert (target / ".codex" / "hooks.json").is_file()
    assert (target / ".tradingcodex" / "config.yaml").is_file()
    assert (target / ".agents" / "skills").is_dir()
    assert (target / ".opencode" / "agents.json").is_file()
    assert isinstance(tcx_root, Path)


def test_attach_with_tcx_idempotent_byte_match(tmp_path: Path) -> None:
    """Edge: second run produces byte-identical TCX files (no drift)."""
    from opencode_trading.attach import attach_workspace

    target = tmp_path / "ws"
    ws1, _ = attach_workspace(
        target=target, package_spec="tradingcodex", with_tcx=True
    )
    ws1.write(target / ".opencode", overwrite=True)

    first_hooks = (target / ".codex" / "hooks.json").read_bytes()
    first_config = (target / ".tradingcodex" / "config.yaml").read_bytes()
    first_registry = (
        target / ".tradingcodex" / "mainagent" / "subagent-registry.yaml"
    ).read_bytes()
    first_agents_json = (target / ".opencode" / "agents.json").read_bytes()

    import shutil

    if (target / ".codex").exists():
        shutil.rmtree(target / ".codex")
    if (target / ".tradingcodex").exists():
        shutil.rmtree(target / ".tradingcodex")
    if (target / ".agents").exists():
        shutil.rmtree(target / ".agents")
    if (target / ".opencode").exists():
        shutil.rmtree(target / ".opencode")

    ws2, _ = attach_workspace(
        target=target, package_spec="tradingcodex", with_tcx=True
    )
    ws2.write(target / ".opencode", overwrite=True)

    assert (target / ".codex" / "hooks.json").read_bytes() == first_hooks
    assert (target / ".tradingcodex" / "config.yaml").read_bytes() == first_config
    assert (
        target / ".tradingcodex" / "mainagent" / "subagent-registry.yaml"
    ).read_bytes() == first_registry
    assert (target / ".opencode" / "agents.json").read_bytes() == first_agents_json
