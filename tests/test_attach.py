"""Tests for :mod:`opencode_trading.attach` (v0.3.0).

The attach CLI builds a fresh OpenCode workspace from the bundled
TradingCodex v0.2.0 templates (no TCX install required, no FS read of
an existing TCX workspace).
"""

from __future__ import annotations

import json
from pathlib import Path

from opencode_trading.attach import (
    _BUNDLED,
    _TCX_VERSION,
    _build_agents,
    _build_hooks,
    _build_mcp_servers,
    _build_skills,
    attach_workspace,
)
from opencode_trading.models import OpenCodeWorkspace

# ---------------------------------------------------------------------------
# S5: attach_workspace() public API
# ---------------------------------------------------------------------------


def test_attach_workspace_returns_10_agents(tmp_path: Path) -> None:
    """The full bundle has 1 primary (head-manager) + 9 subagents = 10 agents."""
    ws, _ = attach_workspace(target=tmp_path, package_spec="tradingcodex")
    assert isinstance(ws, OpenCodeWorkspace)
    assert len(ws.agents) == 10


# ---------------------------------------------------------------------------
# Agent builder
# ---------------------------------------------------------------------------


def test_attach_agents_head_manager_is_primary() -> None:
    agents = _build_agents()
    head = next(a for a in agents if a.name == "head-manager")
    assert head.kind == "primary"


def test_attach_agents_head_manager_has_system_prompt() -> None:
    head = next(a for a in _build_agents() if a.name == "head-manager")
    assert head.system_prompt
    assert "head-manager" in head.system_prompt.lower() or "dispatch" in head.system_prompt.lower()


def test_attach_agents_head_manager_has_workflow_skills() -> None:
    head = next(a for a in _build_agents() if a.name == "head-manager")
    assert head.skills
    assert "orchestrate-workflow" in head.skills


def test_attach_agents_9_subagents_present() -> None:
    """The 9 specialist names match the registry."""
    agents = _build_agents()
    subagent_names = {a.name for a in agents if a.kind == "subagent"}
    expected = {
        "fundamental-analyst",
        "technical-analyst",
        "news-analyst",
        "macro-analyst",
        "instrument-analyst",
        "valuation-analyst",
        "portfolio-manager",
        "risk-manager",
        "execution-operator",
    }
    assert subagent_names == expected


def test_attach_agents_risk_manager_tools_from_mcp_table() -> None:
    risk = next(a for a in _build_agents() if a.name == "risk-manager")
    assert "list_broker_connections" in risk.tools


def test_attach_agents_risk_manager_skills_from_registry() -> None:
    risk = next(a for a in _build_agents() if a.name == "risk-manager")
    assert "review-risk" in risk.skills
    assert "policy-review" in risk.skills
    assert "approve-order" in risk.skills


def test_attach_agents_default_model() -> None:
    """Specialists use the model from their TOML (e.g. gpt-5.5); head-manager uses the default."""
    agents = _build_agents()
    head = next(a for a in agents if a.name == "head-manager")
    assert head.model == "github-copilot/gpt-4o"
    for a in agents:
        if a.name == "head-manager":
            continue
        assert a.model  # non-empty (e.g. "gpt-5.5" from bundled TOML)


# ---------------------------------------------------------------------------
# Hooks builder
# ---------------------------------------------------------------------------


def test_attach_hooks_count_at_least_7() -> None:
    """The bundled hooks.json has 8 Codex events; some expand to multiple hooks."""
    hooks = _build_hooks()
    assert len(hooks) >= 7


def test_attach_hooks_event_names_are_opencode_literals() -> None:
    """All emitted event names must be in the HookEvent Literal."""
    from typing import get_args

    from opencode_trading.models import HookEvent

    valid = set(get_args(HookEvent))
    for h in _build_hooks():
        assert h.event in valid, f"invalid event: {h.event}"


def test_attach_hooks_command_split_via_shlex() -> None:
    hooks = _build_hooks()
    assert all(len(h.command) >= 1 for h in hooks)


# ---------------------------------------------------------------------------
# MCP builder
# ---------------------------------------------------------------------------


def test_attach_mcp_registers_tradingcodex() -> None:
    servers = _build_mcp_servers(target=Path("/tmp/x"), package_spec="tradingcodex")
    assert len(servers) == 1
    assert servers[0].name == "tradingcodex"
    assert servers[0].transport == "stdio"


def test_attach_mcp_command_is_uvx_chain() -> None:
    servers = _build_mcp_servers(target=Path("/tmp/x"), package_spec="custom-pkg")
    cmd = servers[0].command
    assert cmd[0] == "uvx"
    assert "--from" in cmd
    assert "custom-pkg" in cmd
    assert "tradingcodex_cli" in cmd


def test_attach_mcp_workspace_root_substituted(tmp_path: Path) -> None:
    servers = _build_mcp_servers(target=tmp_path, package_spec="tradingcodex")
    assert servers[0].env["TRADINGCODEX_WORKSPACE_ROOT"] == str(tmp_path)


# ---------------------------------------------------------------------------
# Skills builder
# ---------------------------------------------------------------------------


def test_attach_skills_count(tmp_path: Path) -> None:
    """head-manager + 6 orchestrator + 5 role + 1 workflow - 1 dedup = 12 skills.

    The orchestrator ``postmortem`` skill and the workflow ``postmortem`` skill
    share a name; the orchestrator version wins (deduped).
    """
    skills = _build_skills()
    assert len(skills) == 12


def test_attach_skill_head_manager_present() -> None:
    skills = _build_skills()
    head = next(s for s in skills if s.name == "head-manager")
    assert "head-manager" in head.body.lower() or "dispatch" in head.body.lower()


def test_attach_skill_orchestrator_workflow_present() -> None:
    skills = _build_skills()
    orchestrate = next(s for s in skills if s.name == "orchestrate-workflow")
    assert "Orchestrate Workflow" in orchestrate.body


def test_attach_skill_role_skill_named() -> None:
    """Role skills keep their TCX names (e.g. review-risk, not role-prefixed)."""
    skills = _build_skills()
    names = {s.name for s in skills}
    assert "review-risk" in names
    assert "policy-review" in names
    assert "portfolio-review" in names
    assert "create-order-ticket" in names
    assert "execute-paper-order" in names


def test_attach_skill_workflow_postmortem_present() -> None:
    skills = _build_skills()
    postmortem = next(s for s in skills if s.name == "postmortem")
    assert "trading/reports/postmortem" in postmortem.body


# ---------------------------------------------------------------------------
# S1: integration — public API → write → re-read
# ---------------------------------------------------------------------------


def test_attach_workspace_then_write_round_trip(tmp_path: Path) -> None:
    """attach_workspace() produces a workspace that write() renders correctly."""
    ws, _ = attach_workspace(target=tmp_path, package_spec="tradingcodex")
    ws.write(tmp_path / ".opencode", overwrite=True)
    assert (tmp_path / ".opencode" / "agents.json").exists()
    assert (tmp_path / ".opencode" / "mcp.json").exists()
    assert (tmp_path / ".opencode" / "hooks.json").exists()
    assert (tmp_path / ".opencode" / "skills").is_dir()
    data = json.loads((tmp_path / ".opencode" / "agents.json").read_text())
    assert len(data) == 10


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def test_attach_bundled_tcx_version_constant() -> None:
    """The snapshot version is exposed for future migrations."""
    assert _TCX_VERSION == "0.2.0"


def test_attach_bundled_module_path_resolves() -> None:
    """importlib.resources.files() returns a usable Traversable."""
    assert _BUNDLED.is_dir()
    assert (_BUNDLED / "agents").is_dir()
