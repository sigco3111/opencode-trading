"""Convert TradingCodex workflow YAML files to OpenCode workflow skills.

Implementation note (for other-PC worker)
----------------------------------------
TradingCodex stores workflows as ``.tradingcodex/workflows/<name>.yaml``
with a schema describing steps, role assignments, and approval gates.
OpenCode has no direct workflow concept — workflows become **skills** that
orchestrate the right MCP tool calls.

For v0.2.0: each workflow YAML becomes a single OpenCode skill whose
body is a markdown instruction sequence telling the agent which
TradingCodex MCP tool to call when. v0.1.0 returns an empty tuple.
"""
from __future__ import annotations

from pathlib import Path

from opencode_trading.models import OpenCodeSkill


def convert_workflow_files(workspace: Path) -> tuple[OpenCodeSkill, ...]:
    """Discover ``.tradingcodex/workflows/*.yaml`` and convert each.

    Returns
    -------
    tuple[OpenCodeSkill, ...]
        One OpenCodeSkill per discovered workflow YAML. Empty in v0.1.0.
    """
    # v0.1.0: stub — v0.2.0 walks .tradingcodex/workflows/*.yaml, parses
    # each with PyYAML (optional dep), and emits a skill per workflow.
    _ = workspace
    return ()
