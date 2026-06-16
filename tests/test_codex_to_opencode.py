"""Tests for the conversion orchestrator (v0.2.0).

Covers the full ``convert_workspace()`` pipeline: 5 sub-converters in series
producing a complete OpenCodeWorkspace bundle.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from opencode_trading.converters.codex_to_opencode import convert_workspace
from opencode_trading.exceptions import MissingWorkspaceError


def test_convert_workspace_produces_ten_agents(sample_tcx_workspace: Path) -> None:
    """Real sample workspace yields 1 primary + 9 subagents = 10 agents."""
    ws = convert_workspace(sample_tcx_workspace)
    assert len(ws.agents) == 10
    assert any(a.name == "head-manager" and a.kind == "primary" for a in ws.agents)
    subagents = [a for a in ws.agents if a.kind == "subagent"]
    assert len(subagents) == 9


def test_convert_workspace_includes_skills_hooks_mcp(sample_tcx_workspace: Path) -> None:
    """The bundle contains orchestrator + role + workflow + head-manager skills,
    10+ hooks (one per event in hooks.json), and 1 MCP server."""
    ws = convert_workspace(sample_tcx_workspace)
    # Skills: head-manager + 6 orchestrator + 5 role + 3 workflow = 15
    assert len(ws.skills) >= 10
    # Hooks: hooks.json has 8 events but some have multiple matchers
    assert len(ws.hooks) >= 8
    # MCP: exactly 1 tradingcodex server
    assert len(ws.mcp_servers) == 1
    assert ws.mcp_servers[0].name == "tradingcodex"


def test_convert_workspace_rejects_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    with pytest.raises(MissingWorkspaceError):
        convert_workspace(missing)


def test_convert_workspace_rejects_non_tcx_directory(tmp_path: Path) -> None:
    plain = tmp_path / "plain-dir"
    plain.mkdir()
    with pytest.raises(MissingWorkspaceError, match="no .codex/"):
        convert_workspace(plain)


def test_convert_workspace_rejects_unsupported_target(sample_tcx_workspace: Path) -> None:
    with pytest.raises(ValueError, match="unsupported target format"):
        convert_workspace(sample_tcx_workspace, to="vscode")  # type: ignore[arg-type]


def test_convert_workspace_accepts_string_path(sample_tcx_workspace: Path) -> None:
    ws = convert_workspace(str(sample_tcx_workspace))
    assert len(ws.agents) == 10
