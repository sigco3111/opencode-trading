"""Tests for ``opencode_trading.converters.commands``.

TradingCodex v0.2.0 has two distinct command-shaped artifacts:

1. The head-manager system prompt at
   ``.codex/prompts/base_instructions/head-manager.md`` — wrapped as a
   single :class:`OpenCodeSkill` used as the primary agent's system prompt.

2. Orchestrator skills at ``.agents/skills/<name>/SKILL.md`` — collected
   in directory order and returned as a tuple of :class:`OpenCodeSkill`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from opencode_trading.converters.commands import (
    collect_orchestrator_skills,
    convert_orchestrate_workflow,
)
from opencode_trading.exceptions import ConversionError


def test_head_manager_prompt_reads_base_instructions(sample_tcx_workspace: Path) -> None:
    """``convert_orchestrate_workflow`` returns a skill named ``head-manager``.

    The body must come from ``head-manager.md`` and contain the agent's
    domain language (``head-manager`` or ``dispatch``).
    """
    skill = convert_orchestrate_workflow(sample_tcx_workspace)

    assert skill.name == "head-manager"
    assert skill.body  # non-empty
    lowered = skill.body.lower()
    assert "head-manager" in lowered or "dispatch" in lowered


def test_collect_orchestrator_skills_finds_six(sample_tcx_workspace: Path) -> None:
    """The sample workspace contains exactly six ``.agents/skills/*/SKILL.md``."""
    skills = collect_orchestrator_skills(sample_tcx_workspace)

    assert len(skills) == 6


def test_skill_frontmatter_parsed_correctly(sample_tcx_workspace: Path) -> None:
    """At least one collected skill is ``orchestrate-workflow`` from its SKILL.md frontmatter."""
    skills = collect_orchestrator_skills(sample_tcx_workspace)

    names = {s.name for s in skills}
    assert "orchestrate-workflow" in names


def test_skill_body_preserved(sample_tcx_workspace: Path) -> None:
    """The ``orchestrate-workflow`` skill's body contains its H1 heading."""
    skills = collect_orchestrator_skills(sample_tcx_workspace)

    orchestrate = next(s for s in skills if s.name == "orchestrate-workflow")
    assert "Orchestrate Workflow" in orchestrate.body


def test_head_manager_prompt_missing_raises(tmp_tcx_workspace: Path) -> None:
    """When ``head-manager.md`` is absent, :class:`ConversionError` is raised.

    The ``tmp_tcx_workspace`` fixture creates the directory skeleton but
    intentionally does NOT include ``head-manager.md``.
    """
    # Confirm pre-condition: tmp_tcx_workspace has no head-manager.md
    prompt = tmp_tcx_workspace / ".codex" / "prompts" / "base_instructions" / "head-manager.md"
    assert not prompt.exists()

    with pytest.raises(ConversionError):
        convert_orchestrate_workflow(tmp_tcx_workspace)
