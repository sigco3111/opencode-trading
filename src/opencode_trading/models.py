"""Domain models for OpenCode workspace artifacts.

Implementation note (for other-PC worker)
----------------------------------------
This module is the **single source of truth** for OpenCode data shapes.
It must NOT import from `opencode_trading.converters` or `opencode_trading.cli`
to avoid circular imports — both converters and CLI depend on these models,
but models depend on nothing in this package.

Frozen dataclasses + Literal types give us:
- Immutability (safer multi-step conversion pipelines)
- Auto-generated `__repr__` (helpful in error messages)
- mypy strict-mode friendliness

Use the @dataclass(frozen=True) pattern, NOT pydantic, to keep zero-deps.
If you need pydantic features (validation, JSON schema export), add them
in a separate `models_pydantic.py` (optional dep) — don't pollute this file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

# ---------------------------------------------------------------------------
# Constants (from OpenCode schema observation — verify against latest docs)
# ---------------------------------------------------------------------------

#: OpenCode agent types — `primary` is the main agent, `subagent` for delegates
AgentKind = Literal["primary", "subagent"]

#: Hook event types supported by OpenCode (subset — extend as needed)
HookEvent = Literal[
    "session_start",
    "session_end",
    "user_prompt_submit",
    "tool_call",
    "tool_result",
    "pre_tool_use",
    "post_tool_use",
    "permission_request",
    "subagent_start",
    "subagent_stop",
]

#: OpenCode MCP transport types
MCPTransport = Literal["stdio", "http", "streamable-http"]


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OpenCodeAgent:
    """An OpenCode agent definition (mirrors `opencode.json` `agent` object).

    Attributes
    ----------
    name : str
        Agent identifier (e.g. ``"head-manager"``, ``"fundamental-analyst"``).
    kind : AgentKind
        ``"primary"`` for the main agent, ``"subagent"`` for specialists.
    model : str
        Model identifier in ``provider/model`` format
        (e.g. ``"github-copilot/gpt-4o"``).
    fallback_models : tuple[str, ...]
        Fallback chain tried in order when the primary model fails.
    system_prompt : str
        The agent's system prompt (may be multi-line).
    description : str
        Short human-readable description (used in TUI agent picker).
    tools : tuple[str, ...]
        Tool allowlist (e.g. ``("bash", "edit", "webfetch")``).
    skills : tuple[str, ...]
        Skills auto-loaded for this agent.
    """

    name: str
    kind: AgentKind
    model: str
    system_prompt: str
    description: str = ""
    fallback_models: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    skills: tuple[str, ...] = ()


@dataclass(frozen=True)
class OpenCodeSkill:
    """An OpenCode skill (a markdown file with YAML frontmatter).

    Attributes
    ----------
    name : str
        Skill slug (lowercase, hyphenated).
    description : str
        One-line description (shown in skill picker).
    body : str
        The markdown body (instructions, examples).
    path : Path | None
        Where this skill will be written (None = not yet rendered).
    """

    name: str
    description: str
    body: str
    path: Path | None = None


@dataclass(frozen=True)
class OpenCodeHook:
    """An OpenCode hook configuration (mirrors `opencode.json` `hooks` array).

    Attributes
    ----------
    event : HookEvent
        The lifecycle event that triggers this hook.
    command : tuple[str, ...]
        Shell command to execute (argv form, no shell expansion).
    env : dict[str, str]
        Environment variables passed to the command.
    blocking : bool
        If True, agent waits for the command to exit before proceeding.
    """

    event: HookEvent
    command: tuple[str, ...]
    env: dict[str, str] = field(default_factory=dict)
    blocking: bool = True


@dataclass(frozen=True)
class OpenCodeMCP:
    """An MCP server entry for `opencode.json` `mcp` block.

    Attributes
    ----------
    name : str
        Server identifier (e.g. ``"tradingcodex"``).
    transport : MCPTransport
        Transport protocol.
    command : tuple[str, ...]
        For stdio: the command + args to spawn.
    url : str
        For http/streamable-http: the server URL.
    env : dict[str, str]
        Environment variables for stdio transport.
    """

    name: str
    transport: MCPTransport
    command: tuple[str, ...] = ()
    url: str = ""
    env: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class OpenCodeWorkspace:
    """Bundle of all artifacts generated for an OpenCode workspace.

    Use :meth:`write` to render everything to disk, or
    :meth:`to_opencode_json_blocks` to get dict fragments for merging into
    the user's existing `opencode.json`.
    """

    agents: tuple[OpenCodeAgent, ...] = ()
    skills: tuple[OpenCodeSkill, ...] = ()
    hooks: tuple[OpenCodeHook, ...] = ()
    mcp_servers: tuple[OpenCodeMCP, ...] = ()

    def to_opencode_json_blocks(self) -> dict[str, Any]:
        """Return the dict fragments that should be merged into opencode.json."""
        return {
            "agent": {a.name: _agent_to_dict(a) for a in self.agents},
            "mcp": {m.name: _mcp_to_dict(m) for m in self.mcp_servers},
            "hooks": _hooks_to_list(self.hooks),
        }

    def write(self, out_dir: Path, *, overwrite: bool = False) -> list[Path]:
        """Render the bundle to disk.

        Parameters
        ----------
        out_dir : Path
            Directory to write artifacts into. Created if it doesn't exist.
        overwrite : bool
            If True, overwrite existing files. If False (default), raise
            :class:`FileExistsError` if ``out_dir`` already contains files
            that would be overwritten.

        Returns
        -------
        list[Path]
            Absolute paths of all written files.

        Raises
        ------
        FileExistsError
            If ``out_dir`` exists, has files, and ``overwrite=False``.
        """
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        written: list[Path] = []

        agents_path = out_dir / "agents.json"
        if agents_path.exists() and not overwrite:
            raise FileExistsError(f"refusing to overwrite: {agents_path}")
        agents_data = {a.name: _agent_to_dict(a) for a in self.agents}
        agents_path.write_text(_json_dumps(agents_data), encoding="utf-8")
        written.append(agents_path)

        mcp_path = out_dir / "mcp.json"
        if mcp_path.exists() and not overwrite:
            raise FileExistsError(f"refusing to overwrite: {mcp_path}")
        mcp_data = {m.name: _mcp_to_dict(m) for m in self.mcp_servers}
        mcp_path.write_text(_json_dumps(mcp_data), encoding="utf-8")
        written.append(mcp_path)

        hooks_path = out_dir / "hooks.json"
        if hooks_path.exists() and not overwrite:
            raise FileExistsError(f"refusing to overwrite: {hooks_path}")
        hooks_path.write_text(_json_dumps(_hooks_to_list(self.hooks)), encoding="utf-8")
        written.append(hooks_path)

        skills_dir = out_dir / "skills"
        skills_dir.mkdir(exist_ok=True)
        for skill in self.skills:
            skill_dir = skills_dir / skill.name
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists() and not overwrite:
                raise FileExistsError(f"refusing to overwrite: {skill_md}")
            skill_dir.mkdir(parents=True, exist_ok=True)
            body = _render_skill_md(skill)
            skill_md.write_text(body, encoding="utf-8")
            written.append(skill_md)

        return written


def _agent_to_dict(a: OpenCodeAgent) -> dict[str, Any]:
    """Serialize an OpenCodeAgent to its opencode.json form."""
    d: dict[str, Any] = {
        "model": a.model,
        "prompt": a.system_prompt,
    }
    if a.description:
        d["description"] = a.description
    if a.fallback_models:
        d["fallback_models"] = list(a.fallback_models)
    if a.tools:
        d["tools"] = list(a.tools)
    if a.skills:
        d["skills"] = list(a.skills)
    return d


def _mcp_to_dict(m: OpenCodeMCP) -> dict[str, Any]:
    """Serialize an OpenCodeMCP to its opencode.json form."""
    d: dict[str, Any] = {"type": m.transport}
    if m.command:
        d["command"] = list(m.command)
    if m.url:
        d["url"] = m.url
    if m.env:
        d["environment"] = m.env
    return d


def _hooks_to_list(hooks: tuple[OpenCodeHook, ...]) -> list[dict[str, Any]]:
    """Group hooks by event (OpenCode schema: hooks is a flat list of {event, ...}).

    Note
    ----
    Verify this against the current OpenCode schema when implementing —
    some versions nest hooks under an event key, others flatten. The
    safe default is the flat-list form.
    """
    return [
        {
            "event": h.event,
            "command": list(h.command),
            "env": h.env,
            "blocking": h.blocking,
        }
        for h in hooks
    ]


def _json_dumps(data: dict[str, Any] | list[Any]) -> str:
    """Serialize dict/list as pretty-printed JSON with trailing newline."""
    import json

    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _render_skill_md(skill: OpenCodeSkill) -> str:
    """Render an OpenCodeSkill as a SKILL.md file with frontmatter."""
    # Quote the description for safety (it may contain colons)
    desc = skill.description.replace("\\", "\\\\").replace('"', '\\"')
    return f'---\nname: {skill.name}\ndescription: "{desc}"\n---\n\n{skill.body}\n'
