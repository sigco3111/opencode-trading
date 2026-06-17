"""Tests for ``opencode_trading.converters.workflows``.

TradingCodex v0.2.0 stores workflows at
``<workspace>/.tradingcodex/workflows/<name>.yaml``. Each YAML describes a
workflow (triggers + outputs) that the converter turns into a single
:class:`OpenCodeSkill` whose body tells the agent which TradingCodex MCP
tools to call and where to write artifacts.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from opencode_trading.converters.workflows import convert_workflow_files
from opencode_trading.models import OpenCodeSkill


def test_workflows_empty_when_no_dir(tmp_tcx_workspace: Path) -> None:
    """No ``.tradingcodex/workflows`` directory -> empty tuple."""
    # The tmp fixture creates an empty workflows dir; remove it to model
    # the "no workflows dir" scenario described in the spec.
    shutil.rmtree(tmp_tcx_workspace / ".tradingcodex" / "workflows")
    assert convert_workflow_files(tmp_tcx_workspace) == ()


def test_workflows_discovers_yaml_files(sample_tcx_workspace: Path) -> None:
    """Real sample workspace has 3 workflow YAMLs -> exactly 3 skills."""
    skills = convert_workflow_files(sample_tcx_workspace)
    assert isinstance(skills, tuple)
    assert len(skills) == 3
    for s in skills:
        assert isinstance(s, OpenCodeSkill)


def test_workflow_skill_name_matches_yaml(sample_tcx_workspace: Path) -> None:
    """A skill named ``postmortem`` is emitted from ``postmortem.yaml``."""
    skills = convert_workflow_files(sample_tcx_workspace)
    names = {s.name for s in skills}
    assert "postmortem" in names


def test_workflow_skill_body_mentions_mcp_tools(sample_tcx_workspace: Path) -> None:
    """The postmortem skill body tells the agent to use TradingCodex MCP tools."""
    skills = convert_workflow_files(sample_tcx_workspace)
    postmortem = next(s for s in skills if s.name == "postmortem")
    assert "TradingCodex MCP" in postmortem.body


def test_workflow_skill_includes_output_directory(sample_tcx_workspace: Path) -> None:
    """The postmortem skill body embeds the output directory from the YAML."""
    skills = convert_workflow_files(sample_tcx_workspace)
    postmortem = next(s for s in skills if s.name == "postmortem")
    assert "trading/reports/postmortem" in postmortem.body
