"""Converters: TradingCodex (Codex-native) → OpenCode.

Implementation note (for other-PC worker)
----------------------------------------
Each submodule handles one conversion concern. The orchestrator
:func:`convert_workspace` (in ``codex_to_opencode.py``) calls all of them
in order and bundles the results into an :class:`OpenCodeWorkspace`.

The 5 conversion responsibilities
---------------------------------
1. ``codex_to_opencode.convert_workspace`` — orchestrator
2. ``hooks.convert_user_prompt_submit``       — Codex hooks → OpenCode hooks
3. ``commands.convert_orchestrate_workflow``  — $orchestrate-workflow → OpenCode cmd
4. ``mcp.register_tradingcodex_mcp``          — TradingCodex MCP server block
5. ``workflows.convert_workflow_files``       — workflow.yaml → OpenCode workflow

Trade-off: TOML parsing
-----------------------
TradingCodex uses TOML for `.codex/agents/*.toml`. Python 3.11+ ships
``tomllib`` in stdlib (read-only). DO NOT add ``tomli`` as a dependency —
use ``tomllib.load()``. For writing TOML (rare in this adapter) use
``tomli_w`` as an optional extra.

Trade-off: pyproject vs uv
--------------------------
This project uses setuptools (per sigco3111 OSS series standard). If the
user later wants to switch to uv/hatch/poetry, the package layout
(src/ layout, pyproject.toml) is portable — just swap the build-backend.
"""
from __future__ import annotations

from opencode_trading.converters.codex_to_opencode import convert_workspace
from opencode_trading.converters.commands import convert_orchestrate_workflow
from opencode_trading.converters.hooks import convert_user_prompt_submit
from opencode_trading.converters.mcp import register_tradingcodex_mcp
from opencode_trading.converters.workflows import convert_workflow_files

__all__ = [
    "convert_workspace",
    "convert_orchestrate_workflow",
    "convert_user_prompt_submit",
    "register_tradingcodex_mcp",
    "convert_workflow_files",
]
