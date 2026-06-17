"""Command-line interface for opencode-trading.

Implementation note (for other-PC worker)
----------------------------------------
The CLI is intentionally thin — it parses args, validates the workspace,
calls the conversion functions in :mod:`opencode_trading.converters`, and
prints results. No business logic here.

Subcommand structure
--------------------
- ``opencode-trading convert --workspace <dir> [--to opencode] [--dry-run] [--out <dir>]`` (v0.2.0+)
- ``opencode-trading attach --target <dir> [--package-spec <pkg>] [--overwrite] [--dry-run]``
  (v0.3.0+)

Argparse pitfall (from python-oss-bootstrap kakao-summary lesson)
----------------------------------------------------------------
``argparse`` positional args with ``nargs="?"`` collide with subparsers when
the positional value contains spaces or special chars (e.g. workspace paths
with brackets, parentheses, or "x" between names). The safe pattern: pass
the workspace as a required ``--workspace`` option, not a positional.
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from opencode_trading import __version__


def main(argv: list[str] | None = None) -> int:
    """CLI entry point registered as the ``opencode-trading`` console script."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"opencode-trading {__version__}")
        return 0

    if args.command is None:
        parser.print_help()
        return 0

    # Dispatch to subcommand handler
    handler = _HANDLERS.get(args.command)
    if handler is None:
        parser.error(f"unknown command: {args.command}")
        return 2  # unreachable, parser.error exits
    return handler(args)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="opencode-trading",
        description="Convert a TradingCodex (Codex-native) workspace into an "
        "OpenCode-compatible workspace.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="print version and exit",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # `convert` subcommand — v0.2.0+ implements the actual logic
    convert = sub.add_parser(
        "convert",
        help="convert a TradingCodex workspace to OpenCode format",
    )
    convert.add_argument(
        "--workspace",
        type=Path,
        required=True,
        help="path to the TradingCodex workspace (the one created by `tcx attach`)",
    )
    convert.add_argument(
        "--to",
        choices=["opencode"],
        default="opencode",
        help="target format (only 'opencode' supported in v0.1.0)",
    )
    convert.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output directory for generated OpenCode artifacts "
        "(default: <workspace>/.opencode/)",
    )
    convert.add_argument(
        "--dry-run",
        action="store_true",
        help="print what would be written without touching the filesystem",
    )
    convert.set_defaults(handler=_cmd_convert)

    # `attach` subcommand — v0.3.0+ scaffolds a fresh OpenCode workspace
    # from bundled TradingCodex v0.2.0 templates (no TCX install needed).
    attach = sub.add_parser(
        "attach",
        help="scaffold a fresh OpenCode workspace from bundled TCX templates",
    )
    attach.add_argument(
        "--target",
        type=Path,
        required=True,
        help="target directory for the new OpenCode workspace "
        "(artifacts written under <target>/.opencode/)",
    )
    attach.add_argument(
        "--package-spec",
        type=str,
        default="tradingcodex",
        help="value for the TradingCodex MCP --from arg "
        "(default: 'tradingcodex'; use a git+https URL to pin a version)",
    )
    attach.add_argument(
        "--overwrite",
        action="store_true",
        help="overwrite existing files in <target>/.opencode/ if they exist",
    )
    attach.add_argument(
        "--dry-run",
        action="store_true",
        help="print the plan without writing any files",
    )
    attach.set_defaults(handler=_cmd_attach)

    return parser


def _cmd_convert(args: argparse.Namespace) -> int:
    """Handler for `opencode-trading convert`."""
    workspace: Path = args.workspace
    if not workspace.exists():
        print(f"error: workspace does not exist: {workspace}", file=sys.stderr)
        return 2
    if not workspace.is_dir():
        print(f"error: workspace is not a directory: {workspace}", file=sys.stderr)
        return 2

    out_dir = args.out or (workspace / ".opencode")

    from opencode_trading import convert_workspace
    from opencode_trading.exceptions import MissingWorkspaceError

    try:
        ws = convert_workspace(workspace, to=args.to)
    except MissingWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"opencode-trading {__version__} — convert")
    print(f"  workspace: {workspace}")
    print(f"  target:    {args.to}")
    print(f"  out dir:   {out_dir}")
    print(f"  agents:    {len(ws.agents)}")
    print(f"  skills:    {len(ws.skills)}")
    print(f"  hooks:     {len(ws.hooks)}")
    print(f"  mcp:       {len(ws.mcp_servers)}")

    if args.dry_run:
        print()
        print("dry-run: no files written.")
        return 0

    try:
        written = ws.write(out_dir, overwrite=True)
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print()
    print(f"wrote {len(written)} files to {out_dir}/")
    return 0


def _cmd_attach(args: argparse.Namespace) -> int:
    """Handler for ``opencode-trading attach``.

    Builds a fresh OpenCode workspace from the bundled TCX v0.2.0 templates
    and writes it under ``<target>/.opencode/``.
    """
    target: Path = args.target
    package_spec: str = args.package_spec
    overwrite: bool = args.overwrite
    dry_run: bool = args.dry_run

    from opencode_trading.attach import attach_workspace

    try:
        ws = attach_workspace(target=target, package_spec=package_spec)
    except Exception as exc:
        print(f"error: failed to build workspace: {exc}", file=sys.stderr)
        return 2

    opencode_dir = target / ".opencode"

    print(f"opencode-trading {__version__} — attach")
    print(f"  target:      {target}")
    print(f"  out dir:     {opencode_dir}")
    print(f"  package:     {package_spec}")
    print(f"  agents:      {len(ws.agents)}")
    print(f"  skills:      {len(ws.skills)}")
    print(f"  hooks:       {len(ws.hooks)}")
    print(f"  mcp:         {len(ws.mcp_servers)}")

    if dry_run:
        print()
        print("dry-run: no files written.")
        return 0

    if target.exists() and not overwrite:
        existing = list(opencode_dir.glob("*")) if opencode_dir.exists() else []
        if existing:
            print(
                f"error: {opencode_dir}/ already has {len(existing)} files. "
                "Pass --overwrite to replace them.",
                file=sys.stderr,
            )
            return 2

    if overwrite and opencode_dir.exists():
        import shutil

        shutil.rmtree(opencode_dir)

    try:
        ws.write(opencode_dir, overwrite=overwrite)
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print()
    print(f"wrote OpenCode workspace to {opencode_dir}/")
    print(f"open it with: opencode {target}")
    return 0


_HANDLERS: dict[str, Callable[[argparse.Namespace], int]] = {
    "convert": _cmd_convert,
    "attach": _cmd_attach,
}


if __name__ == "__main__":
    sys.exit(main())
