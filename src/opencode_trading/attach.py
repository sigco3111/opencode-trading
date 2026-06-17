"""opencode_trading.attach — Build a fresh OpenCode workspace from scratch.

Unlike :mod:`opencode_trading.converters` which reads an existing TradingCodex
workspace from disk, this module builds a complete :class:`OpenCodeWorkspace`
from the **bundled** TradingCodex v0.2.0 template data shipped inside the
package (``_bundled/``). The output is identical in shape to what
:func:`opencode_trading.convert_workspace` produces for a TCX workspace.

Usage
-----
    >>> from opencode_trading.attach import attach_workspace
    >>> ws = attach_workspace(target=Path("~/my-trading-ws"))
    >>> ws.write(Path("~/my-trading-ws") / ".opencode", overwrite=True)

Or from the CLI:
    $ opencode-trading attach --target ~/my-trading-ws

Design decisions
----------------
1. **Pure-data builders** — the 4 builders (``_build_agents``,
   ``_build_hooks``, ``_build_mcp_servers``, ``_build_skills``) consume
   parsed TOML / YAML / JSON / Markdown content from the bundled package
   data. They do not read from a TCX workspace on disk. This is the key
   separation from the v0.2.0 ``converters`` module.

2. **MCP env target substitution** — the
   ``TRADINGCODEX_WORKSPACE_ROOT`` env var is set to ``str(target)``
   (the parent dir, where ``.opencode/`` will live). This matches the
   TCX convention where the workspace root contains ``.tradingcodex/``,
   ``.codex/``, ``.agents/``, and ``.opencode/`` as siblings.

3. **Snapshot of TCX v0.2.0** — the bundled data is a fixed snapshot.
   Future TCX versions will require a new bundled snapshot + a v0.4.0
   release.
"""
from __future__ import annotations

import json
import os
import tomllib
from importlib.resources import files
from pathlib import Path

from opencode_trading._frontmatter import parse_frontmatter
from opencode_trading._yaml_min import parse_yaml
from opencode_trading.converters.mcp import register_tradingcodex_mcp
from opencode_trading.converters.workflows import _render_skill_body
from opencode_trading.models import (
    OpenCodeAgent,
    OpenCodeHook,
    OpenCodeMCP,
    OpenCodeSkill,
    OpenCodeWorkspace,
)

_BUNDLED = files("opencode_trading._bundled")
_BUNDLED_DIR = Path(os.path.join(os.path.dirname(__file__), "_bundled"))
_TCX_VERSION = "0.2.0"
_DEFAULT_MODEL = "github-copilot/gpt-4o"

_BUNDLED = files("opencode_trading._bundled")
_BUNDLED_PATH = Path(str(_BUNDLED)) if not isinstance(_BUNDLED, Path) else _BUNDLED
_TCX_VERSION = "0.2.0"
_DEFAULT_MODEL = "github-copilot/gpt-4o"


def attach_workspace(*, target: Path, package_spec: str = "tradingcodex") -> OpenCodeWorkspace:
    """Build a fresh OpenCode workspace bundle from bundled TCX v0.2.0 templates.

    Parameters
    ----------
    target : Path
        The target directory. The OpenCode artifacts will be written under
        ``<target>/.opencode/`` by the caller. The TCX workspace root is
        the parent of ``.opencode/``, i.e. ``target`` itself.
    package_spec : str
        Value for the ``--from`` arg of the TradingCodex MCP ``uvx`` command
        (default ``"tradingcodex"``). Use a git+https URL for pinned versions.

    Returns
    -------
    OpenCodeWorkspace
        Complete bundle (10 agents, 13 skills, 8+ hooks, 1 MCP server).
    """
    agents = _build_agents()
    hooks = _build_hooks()
    mcp_servers = _build_mcp_servers(target=target, package_spec=package_spec)
    skills = _build_skills()
    return OpenCodeWorkspace(
        agents=agents,
        skills=skills,
        hooks=hooks,
        mcp_servers=mcp_servers,
    )


def _read_bundled_text(rel: str) -> str:
    """Read text content from a bundled file."""
    return (_BUNDLED / rel).read_text(encoding="utf-8")


def _build_agents() -> tuple[OpenCodeAgent, ...]:
    """Build 10 OpenCodeAgent: 1 primary (head-manager) + 9 subagents (specialists)."""
    registry_data = parse_yaml(_read_bundled_text("mainagent/subagent-registry.yaml"))
    registry_skills: dict[str, list[str]] = {}
    for role_name, role_data in (registry_data.get("subagents") or {}).items():
        registry_skills[str(role_name)] = [str(s) for s in (role_data.get("skills") or [])]

    subagents: list[OpenCodeAgent] = []
    for toml_path in sorted((_BUNDLED_DIR / "agents").glob("*.toml")):
        data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
        name = str(data.get("name", toml_path.stem))
        model = str(data.get("model", _DEFAULT_MODEL))
        description = str(data.get("description", ""))
        system_prompt = str(data.get("developer_instructions", "")).strip()
        mcp_table = data.get("mcp_servers", {}).get("tradingcodex", {})
        tools_raw = mcp_table.get("enabled_tools", []) or []
        tools: tuple[str, ...] = tuple(str(t) for t in tools_raw)
        skills = tuple(registry_skills.get(name, []))
        subagents.append(
            OpenCodeAgent(
                name=name,
                kind="subagent",
                model=model,
                system_prompt=system_prompt,
                description=description,
                tools=tools,
                skills=skills,
            )
        )

    head_manager = _build_head_manager()
    return (head_manager, *subagents)


def _build_head_manager() -> OpenCodeAgent:
    """Build the primary head-manager agent from bundled YAML + MD."""
    yaml_data = parse_yaml(_read_bundled_text("mainagent/head-manager.yaml"))
    system_prompt = _read_bundled_text("prompts/head-manager.md").strip()

    responsibilities = yaml_data.get("responsibilities") or []
    desc = (
        "head manager: " + ", ".join(str(r) for r in responsibilities[:3])
        if responsibilities
        else "TradingCodex head manager"
    )
    workflow_skills = yaml_data.get("workflow_skills") or []
    skills: tuple[str, ...] = tuple(str(s) for s in workflow_skills)

    return OpenCodeAgent(
        name="head-manager",
        kind="primary",
        model=_DEFAULT_MODEL,
        system_prompt=system_prompt,
        description=desc,
        skills=skills,
    )


def _build_hooks() -> tuple[OpenCodeHook, ...]:
    """Build OpenCodeHook tuple from the bundled .codex/hooks.json."""
    hooks_data = json.loads(_read_bundled_text("hooks.json"))
    from opencode_trading.converters.hooks import convert_hooks_dict

    return convert_hooks_dict(hooks_data, source_label="bundled")


def _build_mcp_servers(*, target: Path, package_spec: str) -> tuple[OpenCodeMCP, ...]:
    """Build the TradingCodex MCP server entry with target-substituted env."""
    workspace_root = str(target)
    return (register_tradingcodex_mcp(
        package_spec=package_spec,
        workspace_root=workspace_root,
    ),)


def _build_skills() -> tuple[OpenCodeSkill, ...]:
    """Build the head-manager skill + orchestrator skills + role skills + workflow skills."""
    skills: list[OpenCodeSkill] = []

    # 1. Head-manager skill (system prompt)
    head_manager_md = _read_bundled_text("prompts/head-manager.md")
    skills.append(OpenCodeSkill(
        name="head-manager",
        description="TradingCodex head-manager system prompt.",
        body=head_manager_md,
    ))

    # 2. Orchestrator skills (6)
    for skill_dir in sorted((_BUNDLED_DIR / "orchestrator").iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        skills.append(OpenCodeSkill(
            name=fm.name,
            description=fm.description,
            body=fm.body,
        ))

    # 3. Role skills (5)
    role_skills_dir = _BUNDLED_DIR / "role-skills"
    for skill_md in sorted(role_skills_dir.rglob("SKILL.md")):
        fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        skills.append(OpenCodeSkill(
            name=fm.name,
            description=fm.description,
            body=fm.body,
        ))

    # 4. Workflow skills (1+)
    for yaml_path in sorted((_BUNDLED_DIR / "workflows").glob("*.yaml")):
        wf_data = parse_yaml(yaml_path.read_text(encoding="utf-8"))
        name = str(wf_data.get("name") or yaml_path.stem)
        triggers = wf_data.get("trigger_examples") or []
        sample = ", ".join(str(t) for t in triggers[:2])
        description = f"TradingCodex workflow: {name} (triggers: {sample})"
        body = _render_skill_body(name, wf_data)
        skills.append(OpenCodeSkill(name=name, description=description, body=body))

    return tuple(skills)
