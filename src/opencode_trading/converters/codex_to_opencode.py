"""Main orchestrator: convert a TradingCodex v0.2.0 workspace to OpenCode.

This is the only function most users will call. It runs all 5
sub-converters in order, bundles results into an :class:`OpenCodeWorkspace`,
and returns it. The caller (CLI) handles writing to disk via
:meth:`OpenCodeWorkspace.write`.

Public entry point
------------------
    >>> from opencode_trading import convert_workspace
    >>> workspace = convert_workspace(Path("~/my-tcx-workspace"))
    >>> workspace.to_opencode_json_blocks()
    {'agent': {...}, 'mcp': {...}, 'hooks': [...]}

TradingCodex workspace structure (v0.2.0)
------------------------------------------
A ``tcx attach``-generated workspace contains:
- ``.codex/agents/*.toml``            — 9 specialist role definitions
- ``.codex/hooks.json``               — single hook event dispatch
- ``.codex/prompts/base_instructions/head-manager.md`` — head-manager prompt
- ``.tradingcodex/mainagent/head-manager.yaml``       — mainagent metadata
- ``.tradingcodex/mainagent/subagent-registry.yaml``  — role→skill mapping
- ``.tradingcodex/workflows/*.yaml`` — workflow definitions
- ``.agents/skills/*/SKILL.md``       — orchestrator skills
- ``.tradingcodex/subagents/skills/<role>/<skill>/SKILL.md`` — role skills
"""

from __future__ import annotations

from pathlib import Path

from opencode_trading.converters.agents import convert_agents
from opencode_trading.converters.commands import (
    collect_orchestrator_skills,
    convert_orchestrate_workflow,
)
from opencode_trading.converters.hooks import convert_hooks
from opencode_trading.converters.mcp import register_tradingcodex_mcp
from opencode_trading.converters.workflows import convert_workflow_files
from opencode_trading.exceptions import MissingWorkspaceError
from opencode_trading.models import OpenCodeSkill, OpenCodeWorkspace


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
        ``tcx attach <dir>``). Must contain ``.codex/``.
    to : str
        Target format. Only ``"opencode"`` is supported.

    Returns
    -------
    OpenCodeWorkspace
        Bundle of all generated agents, skills, hooks, and MCP servers.

    Raises
    ------
    MissingWorkspaceError
        If ``workspace`` doesn't exist or isn't a TradingCodex workspace.
    ValueError
        If ``to`` is not ``"opencode"``.
    """
    if to != "opencode":
        raise ValueError(f"unsupported target format: {to!r} (only 'opencode' supported)")

    workspace_path = Path(workspace).expanduser().resolve()
    if not workspace_path.exists() or not workspace_path.is_dir():
        raise MissingWorkspaceError(f"not a directory: {workspace_path}")

    codex_dir = workspace_path / ".codex"
    if not codex_dir.exists():
        raise MissingWorkspaceError(
            f"not a TradingCodex workspace (no .codex/ in {workspace_path})"
        )

    # Run all 5 sub-converters
    agents = convert_agents(workspace_path)
    hooks = convert_hooks(workspace_path)
    mcp_servers = (register_tradingcodex_mcp(),)
    head_manager_skill = convert_orchestrate_workflow(workspace_path)
    orchestrator_skills = collect_orchestrator_skills(workspace_path)
    role_skills = _collect_role_skills(workspace_path)
    workflow_skills = convert_workflow_files(workspace_path)

    # Bundle: head-manager prompt + orchestrator skills + role skills + workflow skills
    all_skills: tuple[OpenCodeSkill, ...] = (
        (head_manager_skill,) + orchestrator_skills + role_skills + workflow_skills
    )

    return OpenCodeWorkspace(
        agents=agents,
        skills=all_skills,
        hooks=hooks,
        mcp_servers=mcp_servers,
    )


def _collect_role_skills(workspace: Path) -> tuple[OpenCodeSkill, ...]:
    """Discover role-owned skills under ``.tradingcodex/subagents/skills/``.

    Each role gets one skill per <skill>/SKILL.md file. We synthesize a
    name like ``<role>-<skill>`` (e.g. ``risk-manager-review-risk``) to
    avoid collisions with orchestrator skill names.
    """
    from opencode_trading._frontmatter import parse_frontmatter

    root = workspace / ".tradingcodex" / "subagents" / "skills"
    if not root.exists():
        return ()

    skills: list[OpenCodeSkill] = []
    for skill_md in sorted(root.rglob("SKILL.md")):
        # Path: <root>/<role>/<skill-name>/SKILL.md
        parts = skill_md.relative_to(root).parts
        if len(parts) < 3:
            continue
        role, skill_name = parts[0], parts[1]
        text = skill_md.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        skills.append(
            OpenCodeSkill(
                name=fm.name or f"{role}-{skill_name}",
                description=fm.description,
                body=fm.body,
            )
        )
    return tuple(skills)
