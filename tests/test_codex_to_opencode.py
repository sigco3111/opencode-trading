"""Smoke tests for the conversion orchestrator (v0.1.0 stub)."""
from __future__ import annotations

from pathlib import Path

import pytest

from opencode_trading.converters.codex_to_opencode import convert_workspace
from opencode_trading.exceptions import MissingWorkspaceError


def test_convert_workspace_stub_returns_empty(tmp_tcx_workspace: Path) -> None:
    """v0.1.0 stub: returns an empty OpenCodeWorkspace."""
    ws = convert_workspace(tmp_tcx_workspace)
    assert ws.agents == ()
    assert ws.skills == ()
    assert ws.hooks == ()
    assert ws.mcp_servers == ()


def test_convert_workspace_rejects_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    with pytest.raises(MissingWorkspaceError):
        convert_workspace(missing)


def test_convert_workspace_rejects_non_tcx_directory(tmp_path: Path) -> None:
    plain = tmp_path / "plain-dir"
    plain.mkdir()
    with pytest.raises(MissingWorkspaceError, match="no .codex/"):
        convert_workspace(plain)


def test_convert_workspace_rejects_unsupported_target(tmp_tcx_workspace: Path) -> None:
    with pytest.raises(ValueError, match="unsupported target format"):
        convert_workspace(tmp_tcx_workspace, to="vscode")  # type: ignore[arg-type]


def test_convert_workspace_accepts_string_path(tmp_tcx_workspace: Path) -> None:
    ws = convert_workspace(str(tmp_tcx_workspace))
    assert isinstance(ws, type(ws))
