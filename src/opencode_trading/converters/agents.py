"""Convert TradingCodex v0.2.0 agent definitions to OpenCode agents.

TradingCodex v0.2.0 has two agent categories:

1. **Subagents** (9 specialists) at ``.codex/agents/<role>.toml``:
   Each TOML has top-level fields ``name``, ``description``, ``model``,
   ``developer_instructions`` (multi-line string), and a
   ``[mcp_servers.tradingcodex]`` table with ``enabled_tools`` list.
   We emit one ``OpenCodeAgent(kind="subagent", ...)`` per TOML.

2. **Main agent** (head-manager) at
   ``.tradingcodex/mainagent/head-manager.yaml`` (id, type, responsibilities,
   workflow_skills) with system prompt at
   ``.codex/prompts/base_instructions/head-manager.md``. We emit
   ``OpenCodeAgent(kind="primary", name="head-manager", ...)``.

The registry at ``.tradingcodex/mainagent/subagent-registry.yaml`` maps each
subagent name to its assigned skills — we use this to populate the
``skills`` field of each ``OpenCodeAgent``.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

from opencode_trading._yaml_min import parse_yaml
from opencode_trading.exceptions import ConversionError
from opencode_trading.models import OpenCodeAgent

_AGENTS_DIR = ".codex/agents"
_MAINAGENT_DIR = ".tradingcodex/mainagent"
_HEAD_MANAGER_PROMPT = ".codex/prompts/base_instructions/head-manager.md"
_REGISTRY = "subagent-registry.yaml"
_HEAD_MANAGER_YAML = "head-manager.yaml"
_DEFAULT_MODEL = "github-copilot/gpt-4o"


def convert_agents(workspace: Path) -> tuple[OpenCodeAgent, ...]:
    """Discover all TradingCodex agents and return as OpenCodeAgent tuple.

    Returns
    -------
    tuple[OpenCodeAgent, ...]
        Head-manager first (primary), then 9 subagents by name.
        Empty tuple if .codex/agents/ doesn't exist AND head-manager.yaml missing.
    """
    registry = _read_registry(workspace)
    result: list[OpenCodeAgent] = []

    # Head manager (primary)
    head_yaml = workspace / _MAINAGENT_DIR / _HEAD_MANAGER_YAML
    if head_yaml.exists():
        result.append(_convert_head_manager(workspace))

    # Subagents
    agents_dir = workspace / _AGENTS_DIR
    if agents_dir.exists():
        for toml_path in sorted(agents_dir.glob("*.toml")):
            skills = tuple(registry.get(_agent_name_from_toml(toml_path), []))
            result.append(_convert_subagent(toml_path, skills))

    return tuple(result)


def _agent_name_from_toml(toml_path: Path) -> str:
    """Extract the agent name from a TOML file (used for registry lookup)."""
    try:
        with toml_path.open("rb") as fh:
            data = tomllib.load(fh)
        return str(data.get("name", toml_path.stem))
    except Exception:
        return toml_path.stem


def _convert_subagent(toml_path: Path, skills: tuple[str, ...] = ()) -> OpenCodeAgent:
    """Convert one specialist TOML to OpenCodeAgent(kind='subagent')."""
    with toml_path.open("rb") as fh:
        data = tomllib.load(fh)

    name = str(data.get("name", toml_path.stem))
    model = str(data.get("model", _DEFAULT_MODEL))
    description = str(data.get("description", ""))
    system_prompt = str(data.get("developer_instructions", "")).strip()
    mcp = data.get("mcp_servers", {}).get("tradingcodex", {})
    tools_raw = mcp.get("enabled_tools", [])
    tools: tuple[str, ...] = tuple(str(t) for t in tools_raw) if tools_raw else ()

    return OpenCodeAgent(
        name=name,
        kind="subagent",
        model=model,
        system_prompt=system_prompt,
        description=description,
        tools=tools,
        skills=skills,
    )


def _convert_head_manager(workspace: Path) -> OpenCodeAgent:
    """Read head-manager.yaml + head-manager.md and emit primary agent."""
    yaml_path = workspace / _MAINAGENT_DIR / _HEAD_MANAGER_YAML
    prompt_path = workspace / _HEAD_MANAGER_PROMPT
    if not prompt_path.exists():
        raise ConversionError(f"head-manager prompt missing: {prompt_path}")

    data = parse_yaml(yaml_path.read_text(encoding="utf-8"))

    responsibilities = data.get("responsibilities") or []
    desc = (
        "head manager: " + ", ".join(str(r) for r in responsibilities[:3])
        if responsibilities
        else "TradingCodex head manager"
    )

    workflow_skills = data.get("workflow_skills") or []
    skills: tuple[str, ...] = tuple(str(s) for s in workflow_skills)

    system_prompt = prompt_path.read_text(encoding="utf-8")

    return OpenCodeAgent(
        name="head-manager",
        kind="primary",
        model=_DEFAULT_MODEL,
        system_prompt=system_prompt,
        description=desc,
        skills=skills,
    )


def _read_registry(workspace: Path) -> dict[str, list[str]]:
    """Read subagent-registry.yaml and return {role_name: [skills]} mapping."""
    registry_path = workspace / _MAINAGENT_DIR / _REGISTRY
    if not registry_path.exists():
        return {}
    try:
        data = parse_yaml(registry_path.read_text(encoding="utf-8"))
    except ValueError:
        return {}
    subagents = data.get("subagents") or {}
    result: dict[str, list[str]] = {}
    for role_name, role_data in subagents.items():
        skills = role_data.get("skills") or []
        result[str(role_name)] = [str(s) for s in skills]
    return result
