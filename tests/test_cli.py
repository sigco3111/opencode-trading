"""Tests for the CLI (v0.2.0 + v0.3.0 attach)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_cli(
    *args: str,
    workspace: Path | None = None,
    target: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "opencode_trading", *args]
    if workspace is not None:
        cmd.extend(["--workspace", str(workspace)])
    if target is not None:
        cmd.extend(["--target", str(target)])
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent / "src",
    )


def test_cli_version() -> None:
    """`python -m opencode_trading --version` prints version and exits 0."""
    result = _run_cli("--version")
    assert result.returncode == 0
    assert "opencode-trading" in result.stdout


def test_cli_help() -> None:
    result = _run_cli("--help")
    assert result.returncode == 0
    assert "TradingCodex" in result.stdout
    assert "convert" in result.stdout
    assert "attach" in result.stdout


def test_cli_convert_dry_run(sample_tcx_workspace: Path) -> None:
    """`--dry-run` prints plan without writing files."""
    result = _run_cli(
        "convert", "--dry-run", "--out", str(sample_tcx_workspace / "should-not-exist"),
        workspace=sample_tcx_workspace,
    )
    assert result.returncode == 0, result.stderr
    assert "agents:    10" in result.stdout
    assert "dry-run" in result.stdout
    # Confirm no files were written
    assert not (sample_tcx_workspace / "should-not-exist").exists()


def test_cli_convert_writes_files(sample_tcx_workspace: Path, tmp_path: Path) -> None:
    """Real `convert --out` writes agents.json, mcp.json, hooks.json, skills/."""
    out = tmp_path / "opencode-out"
    result = _run_cli(
        "convert", "--out", str(out),
        workspace=sample_tcx_workspace,
    )
    assert result.returncode == 0, result.stderr
    assert (out / "agents.json").exists()
    assert (out / "mcp.json").exists()
    assert (out / "hooks.json").exists()
    assert (out / "skills").is_dir()
    # agents.json is valid JSON with the 10 agents
    data = json.loads((out / "agents.json").read_text())
    assert len(data) == 10
    assert "head-manager" in data


def test_cli_convert_default_out(sample_tcx_workspace: Path) -> None:
    """When --out is omitted, files go to <workspace>/.opencode/."""
    result = _run_cli("convert", workspace=sample_tcx_workspace)
    assert result.returncode == 0, result.stderr
    default_out = sample_tcx_workspace / ".opencode"
    assert (default_out / "agents.json").exists()
    # Cleanup
    import shutil

    shutil.rmtree(default_out)


def test_cli_convert_missing_workspace(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    result = _run_cli("convert", workspace=missing)
    assert result.returncode == 2
    assert "does not exist" in result.stderr


def test_cli_convert_non_tcx_workspace(tmp_path: Path) -> None:
    plain = tmp_path / "plain-dir"
    plain.mkdir()
    result = _run_cli("convert", workspace=plain)
    assert result.returncode == 2
    assert ".codex" in result.stderr


def test_cli_attach_writes_opencode_artifacts(tmp_path: Path) -> None:
    target = tmp_path / "new-ws"
    result = _run_cli("attach", target=target)
    assert result.returncode == 0, result.stderr
    assert (target / ".opencode" / "agents.json").exists()
    assert (target / ".opencode" / "mcp.json").exists()
    assert (target / ".opencode" / "hooks.json").exists()
    assert (target / ".opencode" / "skills").is_dir()
    data = json.loads((target / ".opencode" / "agents.json").read_text())
    assert len(data) == 10
    assert "head-manager" in data


def test_cli_attach_dry_run(tmp_path: Path) -> None:
    target = tmp_path / "dry-ws"
    result = _run_cli("attach", "--dry-run", target=target)
    assert result.returncode == 0, result.stderr
    assert "dry-run" in result.stdout
    assert "agents:" in result.stdout
    assert not target.exists()


def test_cli_attach_overwrite_existing_opencode(tmp_path: Path) -> None:
    target = tmp_path / "ws"
    target.mkdir()
    (target / ".opencode").mkdir()
    (target / ".opencode" / "stale.txt").write_text("stale")

    result = _run_cli("attach", "--overwrite", target=target)
    assert result.returncode == 0, result.stderr
    assert not (target / ".opencode" / "stale.txt").exists()
    assert (target / ".opencode" / "agents.json").exists()


def test_cli_attach_package_spec(tmp_path: Path) -> None:
    target = tmp_path / "pinned-ws"
    result = _run_cli(
        "attach",
        "--package-spec", "git+https://example.com/tcx@v1",
        target=target,
    )
    assert result.returncode == 0, result.stderr
    mcp = json.loads((target / ".opencode" / "mcp.json").read_text())
    args = mcp["tradingcodex"]["command"]
    assert "git+https://example.com/tcx@v1" in args


def test_cli_attach_target_required(tmp_path: Path) -> None:
    result = _run_cli("attach")
    assert result.returncode == 2


def test_cli_attach_existing_opencode_no_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "ws"
    target.mkdir()
    (target / ".opencode").mkdir()
    (target / ".opencode" / "stale.txt").write_text("stale")

    result = _run_cli("attach", target=target)
    assert result.returncode == 2


def test_cli_attach_help_mentions_flags() -> None:
    result = _run_cli("attach", "--help")
    assert result.returncode == 0
    for flag in ("--target", "--package-spec", "--overwrite", "--dry-run"):
        assert flag in result.stdout, f"missing flag: {flag}"


def test_cli_attach_creates_target_dir(tmp_path: Path) -> None:
    target = tmp_path / "fresh" / "nested"
    assert not target.exists()
    result = _run_cli("attach", target=target)
    assert result.returncode == 0, result.stderr
    assert target.exists()
    assert (target / ".opencode" / "agents.json").exists()
