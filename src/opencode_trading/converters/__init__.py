"""Converters: TradingCodex v0.2.0 (Codex-native) → OpenCode.

Each submodule handles one conversion concern. The orchestrator
:func:`convert_workspace` (in ``codex_to_opencode.py``) calls all of them
in order and bundles the results into an :class:`OpenCodeWorkspace`.

The 6 conversion responsibilities
----------------------------------
1. ``codex_to_opencode.convert_workspace`` — orchestrator
2. ``agents.convert_agents``                — 9 specialist TOML + head-manager YAML
3. ``hooks.convert_hooks``                  — ``.codex/hooks.json`` → OpenCode hooks
4. ``commands.convert_orchestrate_workflow`` — head-manager system prompt
5. ``commands.collect_orchestrator_skills``  — ``.agents/skills/*/SKILL.md``
6. ``workflows.convert_workflow_files``     — ``.tradingcodex/workflows/*.yaml``
7. ``mcp.register_tradingcodex_mcp``        — TradingCodex MCP server block

Trade-off: TOML parsing
-----------------------
TradingCodex uses TOML for ``.codex/agents/*.toml``. Python 3.11+ ships
``tomllib`` in stdlib (read-only). No extra dependency required.

Trade-off: YAML parsing
-----------------------
We hand-roll a minimal YAML reader (``_yaml_min``) that supports the
specific TCX v0.2.0 schemas. Full PyYAML is not added to keep zero-deps.
"""

from __future__ import annotations

from opencode_trading.converters.agents import convert_agents
from opencode_trading.converters.codex_to_opencode import convert_workspace
from opencode_trading.converters.commands import (
    collect_orchestrator_skills,
    convert_orchestrate_workflow,
)
from opencode_trading.converters.hooks import convert_hooks
from opencode_trading.converters.mcp import register_tradingcodex_mcp
from opencode_trading.converters.workflows import convert_workflow_files

__all__ = [
    "convert_workspace",
    "convert_agents",
    "convert_hooks",
    "convert_orchestrate_workflow",
    "collect_orchestrator_skills",
    "register_tradingcodex_mcp",
    "convert_workflow_files",
]
