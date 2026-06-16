"""Smoke tests for the CLI (v0.1.0)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_cli_version() -> None:
    """`python -m opencode_trading --version` prints version and exits 0."""
    result = subprocess.run(
        [sys.executable, "-m", "opencode_trading", "--version"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent / "src",
    )
    assert result.returncode == 0
    assert "opencode-trading 0.1.0" in result.stdout


def test_cli_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "opencode_trading", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent / "src",
    )
    assert result.returncode == 0
    assert "TradingCodex" in result.stdout
    assert "convert" in result.stdout


def test_cli_convert_dry_run(tmp_tcx_workspace: Path) -> None:
    result = subprocess.run(
        [
            sys.executable, "-m", "opencode_trading", "convert",
            "--workspace", str(tmp_tcx_workspace),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent / "src",
    )
    assert result.returncode == 0
    assert "dry-run" in result.stdout
    assert "v0.1.0 stub" in result.stdout


def test_cli_convert_missing_workspace(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    result = subprocess.run(
        [
            sys.executable, "-m", "opencode_trading", "convert",
            "--workspace", str(missing),
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent / "src",
    )
    assert result.returncode == 2
    assert "does not exist" in result.stderr
