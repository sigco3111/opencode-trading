"""Tests for :mod:`opencode_trading.converters.agents` (TradingCodex v0.2.0).

The v0.1.0 stub is replaced in v0.2.0 by ``convert_agents``, which discovers
all 1+9 TradingCodex agents and emits :class:`OpenCodeAgent` instances:

- 1 ``kind="primary"`` agent (``head-manager``) from
  ``.tradingcodex/mainagent/head-manager.yaml`` + system prompt at
  ``.codex/prompts/base_instructions/head-manager.md``.
- 9 ``kind="subagent"`` agents from ``.codex/agents/*.toml`` whose
  ``skills`` field is enriched from
  ``.tradingcodex/mainagent/subagent-registry.yaml``.

These tests use the shared fixtures from ``tests/conftest.py``:

- ``sample_tcx_workspace`` — real TradingCodex v0.2.0 fixture (30+ files).
- ``tmp_tcx_workspace`` — minimal skeleton (no agent TOML, no head-manager.yaml).
"""

from __future__ import annotations

from pathlib import Path

from opencode_trading.converters.agents import convert_agents
from opencode_trading.models import OpenCodeAgent


def test_agents_discovers_nine_specialists(sample_tcx_workspace: Path) -> None:
    """``convert_agents`` returns 10 agents (1 primary + 9 subagents)."""
    agents = convert_agents(sample_tcx_workspace)
    assert len(agents) == 10
    # Sanity: every entry is an OpenCodeAgent
    assert all(isinstance(a, OpenCodeAgent) for a in agents)


def test_agents_includes_head_manager_primary(sample_tcx_workspace: Path) -> None:
    """At least one agent is named ``head-manager`` with ``kind == "primary"``."""
    agents = convert_agents(sample_tcx_workspace)
    primaries = [a for a in agents if a.name == "head-manager" and a.kind == "primary"]
    assert len(primaries) == 1
    head = primaries[0]
    # Description is built from responsibilities; non-empty
    assert head.description
    # System prompt came from the .md file (non-trivial length)
    assert len(head.system_prompt) > 100


def test_agents_risk_manager_subagent(sample_tcx_workspace: Path) -> None:
    """``risk-manager`` exists as a subagent with non-empty tools tuple."""
    agents = convert_agents(sample_tcx_workspace)
    risk = [a for a in agents if a.name == "risk-manager"]
    assert len(risk) == 1
    r = risk[0]
    assert r.kind == "subagent"
    assert r.tools  # non-empty


def test_agent_tools_from_enabled_tools_list(sample_tcx_workspace: Path) -> None:
    """``risk-manager``'s tools list is sourced from ``enabled_tools`` in TOML.

    Verified from the risk-manager.toml fixture: ``list_broker_connections``
    appears in ``[mcp_servers.tradingcodex].enabled_tools``.
    """
    agents = convert_agents(sample_tcx_workspace)
    risk = next(a for a in agents if a.name == "risk-manager")
    assert "list_broker_connections" in risk.tools
    # Also confirm the disabled tool is NOT in the allowlist
    assert "submit_approved_order" not in risk.tools


def test_agents_skills_from_registry(sample_tcx_workspace: Path) -> None:
    """``risk-manager``'s skills list is sourced from subagent-registry.yaml.

    Verified from subagent-registry.yaml: ``risk-manager.skills`` includes
    ``review-risk``, ``policy-review``, and ``approve-order``.
    """
    agents = convert_agents(sample_tcx_workspace)
    risk = next(a for a in agents if a.name == "risk-manager")
    assert "review-risk" in risk.skills
    assert "policy-review" in risk.skills
    assert "approve-order" in risk.skills


def test_agents_empty_when_no_codex_dir(tmp_tcx_workspace: Path) -> None:
    """Empty ``.codex/agents/`` and no head-manager.yaml → 0 agents.

    ``tmp_tcx_workspace`` creates the .codex/agents and .tradingcodex/mainagent
    directories but leaves them empty.
    """
    agents = convert_agents(tmp_tcx_workspace)
    assert agents == ()
