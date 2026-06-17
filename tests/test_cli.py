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
        "convert",
        "--dry-run",
        "--out",
        str(sample_tcx_workspace / "should-not-exist"),
        workspace=sample_tcx_workspace,
    )
    assert result.returncode == 0, result.stderr
    assert "agents:    10" in result.stdout
    assert "dry-run" in result.stdout
    # Confirm no files were written
    assert not (sample_tcx_workspace / "should-not-exist").exists()


def test_cli_convert_writes_files(sample_tcx_workspace: Path, tmp_path: Path) -> None:
    """Real `convert --out` writes agents.json, mcp.json, hooks.json under <out>/.opencode/."""
    out = tmp_path / "opencode-out"
    result = _run_cli(
        "convert",
        "--out",
        str(out),
        workspace=sample_tcx_workspace,
    )
    assert result.returncode == 0, result.stderr
    opencode_dir = out / ".opencode"
    assert (opencode_dir / "agents.json").exists()
    assert (opencode_dir / "mcp.json").exists()
    assert (opencode_dir / "hooks.json").exists()
    assert (opencode_dir / "skills").is_dir()
    data = json.loads((opencode_dir / "agents.json").read_text())
    assert len(data) == 10
    assert "head-manager" in data


def test_cli_convert_out_then_verify_round_trip(sample_tcx_workspace: Path, tmp_path: Path) -> None:
    """`convert --out <dir>` followed by `verify <dir>` composes cleanly (v1.0.0 fix)."""
    out = tmp_path / "oc-rt"
    convert = _run_cli("convert", "--out", str(out), workspace=sample_tcx_workspace)
    assert convert.returncode == 0, convert.stderr
    verify = _run_cli("verify", str(out))
    assert verify.returncode == 0, verify.stderr
    assert "PASS" in verify.stdout


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
        "--package-spec",
        "git+https://example.com/tcx@v1",
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


def test_cli_help_lists_all_subcommands() -> None:
    result = _run_cli("--help")
    assert result.returncode == 0
    for sub in ("convert", "attach", "verify"):
        assert sub in result.stdout, f"missing subcommand: {sub}"


def test_cli_attach_help_includes_with_tcx() -> None:
    result = _run_cli("attach", "--help")
    assert result.returncode == 0
    assert "--with-tcx" in result.stdout


def test_cli_attach_with_tcx_writes_all_dirs(tmp_path: Path) -> None:
    target = tmp_path / "ws"
    result = _run_cli("attach", "--with-tcx", target=target)
    assert result.returncode == 0, result.stderr
    assert (target / ".opencode" / "agents.json").exists()
    assert (target / ".codex" / "agents").is_dir()
    assert (target / ".codex" / "hooks.json").is_file()
    assert (target / ".tradingcodex" / "mainagent" / "head-manager.yaml").is_file()
    assert (target / ".tradingcodex" / "config.yaml").is_file()
    assert (target / ".agents" / "skills").is_dir()


def test_cli_attach_with_tcx_dry_run(tmp_path: Path) -> None:
    target = tmp_path / "ws"
    result = _run_cli("attach", "--with-tcx", "--dry-run", target=target)
    assert result.returncode == 0
    assert not (target / ".codex").exists()
    assert not (target / ".tradingcodex").exists()
    assert not (target / ".agents").exists()
    assert not (target / ".opencode").exists()


def test_cli_attach_with_tcx_existing_tcx_no_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "ws"
    (target / ".tradingcodex").mkdir(parents=True)
    (target / ".tradingcodex" / "config.yaml").write_text("stale")
    result = _run_cli("attach", "--with-tcx", target=target)
    assert result.returncode == 2
    assert ".tradingcodex" in result.stderr or "overwrite" in result.stderr.lower()


def test_cli_attach_with_tcx_overwrite_replaces(tmp_path: Path) -> None:
    target = tmp_path / "ws"
    (target / ".tradingcodex" / "config.yaml").parent.mkdir(parents=True)
    (target / ".tradingcodex" / "config.yaml").write_text("stale")
    result = _run_cli("attach", "--with-tcx", "--overwrite", target=target)
    assert result.returncode == 0, result.stderr
    assert "stale" not in (target / ".tradingcodex" / "config.yaml").read_text()


def test_cli_verify_happy(tmp_path: Path) -> None:
    target = tmp_path / "ws"
    result = _run_cli("attach", target=target)
    assert result.returncode == 0, result.stderr
    result = _run_cli("verify", str(target))
    assert result.returncode == 0, result.stderr
    assert "PASS" in result.stdout


def test_cli_verify_missing_dir(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    result = _run_cli("verify", str(empty))
    assert result.returncode == 1
    assert "FAIL" in result.stdout


def test_cli_verify_nonexistent_path(tmp_path: Path) -> None:
    result = _run_cli("verify", str(tmp_path / "does-not-exist"))
    assert result.returncode == 2
    assert "does not exist" in result.stderr


def test_cli_verify_with_workspace_source(sample_tcx_workspace: Path, tmp_path: Path) -> None:
    """S4: --workspace <tcx_src> round-trip via convert (true equivalence).

    Copies the fixture so convert doesn't pollute the original; convert
    writes to ``<src>/.opencode/``; verify then checks round-trip with the
    same src as the --workspace argument.
    """
    import shutil

    tcx_copy = tmp_path / "tcx-src"
    shutil.copytree(sample_tcx_workspace, tcx_copy)
    convert = _run_cli("convert", workspace=tcx_copy)
    assert convert.returncode == 0, convert.stderr
    result = _run_cli("verify", str(tcx_copy), workspace=tcx_copy)
    assert result.returncode == 0, result.stderr
    assert "PASS" in result.stdout


def test_cli_verify_help_mentions_flags() -> None:
    result = _run_cli("verify", "--help")
    assert result.returncode == 0
    for flag in ("--workspace", "--strict"):
        assert flag in result.stdout, f"missing flag: {flag}"
