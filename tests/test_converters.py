"""Smoke tests for sub-converters (v0.1.0 stub)."""
from __future__ import annotations

from pathlib import Path

from opencode_trading.converters.commands import convert_orchestrate_workflow
from opencode_trading.converters.hooks import convert_user_prompt_submit
from opencode_trading.converters.mcp import register_tradingcodex_mcp
from opencode_trading.converters.workflows import convert_workflow_files


def test_hooks_stub_returns_empty(tmp_tcx_workspace: Path) -> None:
    assert convert_user_prompt_submit(tmp_tcx_workspace) == ()


def test_commands_stub_returns_skill(tmp_tcx_workspace: Path) -> None:
    skill = convert_orchestrate_workflow(tmp_tcx_workspace)
    assert skill.name == "orchestrate-workflow"
    assert "v0.1.0 stub" in skill.body


def test_mcp_stub_returns_stdio() -> None:
    mcp = register_tradingcodex_mcp()
    assert mcp.name == "tradingcodex"
    assert mcp.transport == "stdio"
    assert "tcx" in mcp.command


def test_workflows_stub_returns_empty(tmp_tcx_workspace: Path) -> None:
    assert convert_workflow_files(tmp_tcx_workspace) == ()


# Note: fixtures come from tests/conftest.py (tmp_tcx_workspace)
# pytest auto-discovers them.
