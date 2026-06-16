"""Main orchestrator: convert a TradingCodex workspace to OpenCode.

Implementation note (for other-PC worker)
----------------------------------------
This is the **only** function most users will call. It runs all 4
sub-converters in order, bundles results into an OpenCodeWorkspace, and
returns it. The caller (CLI) handles writing to disk.

Public entry point
------------------
    >>> from opencode_trading import convert_workspace
    >>> workspace = convert_workspace(Path("~/my-tcx-workspace"))
    >>> workspace.to_opencode_json_blocks()
    {'agent': {...}, 'mcp': {...}, 'hooks': [...]}

TradingCodex workspace structure (v0.2.1)
------------------------------------------
A `tcx attach`-generated workspace contains:
- ``.codex/agents/*.toml``        — 1+9 role definitions
- ``.codex/prompts/*``            — slash commands (e.g. ``$orchestrate-workflow``)
- ``.codex/hooks/*.py``           — UserPromptSubmit / etc.
- ``.tradingcodex/workflows/*.yaml`` — workflow definitions
- ``.tradingcodex/policies/*.yaml``  — policy exports
- ``.agents/skills/*/SKILL.md``   — strategy + repo skills
- ``tcx``                         — generated wrapper script

The conversion reads all of the above and emits OpenCode equivalents
into a single OpenCodeWorkspace bundle.
"""
from __future__ import annotations

from pathlib import Path

from opencode_trading.exceptions import MissingWorkspaceError
from opencode_trading.models import OpenCodeWorkspace

# Stubs (v0.1.0) — full implementation lands in v0.2.0
from opencode_trading.converters.commands import convert_orchestrate_workflow
from opencode_trading.converters.hooks import convert_user_prompt_submit
from opencode_trading.converters.mcp import register_tradingcodex_mcp
from opencode_trading.converters.workflows import convert_workflow_files


def convert_workspace(
    workspace: Path | str,
    *,
    to: str = "opencode",
) -> OpenCodeWorkspace:
    """Convert a TradingCodex workspace to OpenCode format.

    Parameters
    ----------
    workspace : Path | str
        Path to the TradingCodex-generated workspace (the one created by
        ``tcx attach <dir>``). Must contain ``.codex/`` and ``.tradingcodex/``.
    to : str
        Target format. Only ``"opencode"`` is supported in v0.1.0.

    Returns
    -------
    OpenCodeWorkspace
        Bundle of all generated agents, skills, hooks, and MCP servers.

    Raises
    ------
    MissingWorkspaceError
        If ``workspace`` doesn't exist or isn't a TradingCodex workspace.
    """
    if to != "opencode":
        raise ValueError(f"unsupported target format: {to!r} (only 'opencode' in v0.1.0)")

    workspace_path = Path(workspace).expanduser().resolve()
    if not workspace_path.exists() or not workspace_path.is_dir():
        raise MissingWorkspaceError(f"not a directory: {workspace_path}")

    codex_dir = workspace_path / ".codex"
    if not codex_dir.exists():
        raise MissingWorkspaceError(
            f"not a TradingCodex workspace (no .codex/ in {workspace_path})"
        )

    # v0.1.0: return an empty workspace; v0.2.0 wires the 4 sub-converters
    # and discovers .codex/agents/*.toml, .codex/prompts/*, .codex/hooks/*,
    # .tradingcodex/workflows/*.yaml.
    #
    # Plan for v0.2.0 (in order):
    # 1. Discover .codex/agents/*.toml → OpenCodeAgent tuple
    # 2. Discover .agents/skills/*/SKILL.md → OpenCodeSkill tuple
    # 3. hooks = (convert_user_prompt_submit(workspace_path),)
    # 4. mcp_servers = (register_tradingcodex_mcp(),)
    # 5. workflow skills from convert_workflow_files(workspace_path)
    _ = (convert_orchestrate_workflow, convert_user_prompt_submit,
         register_tradingcodex_mcp, convert_workflow_files)  # silence unused

    return OpenCodeWorkspace()
