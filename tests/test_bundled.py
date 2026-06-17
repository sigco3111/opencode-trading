"""Tests for the bundled TradingCodex v0.2.0 template package data.

The ``_bundled/`` directory is shipped inside the wheel and accessed at
runtime via :mod:`importlib.resources`. These tests verify the package
data is correctly wired (MANIFEST.in + pyproject.toml package-data).
"""

from __future__ import annotations

import json
import tomllib
from importlib.resources import files

import pytest

_BUNDLED = files("opencode_trading._bundled")


def test_bundled_root_is_traversable() -> None:
    assert _BUNDLED.is_dir()


def test_bundled_has_9_agent_tomls() -> None:
    agents = list((_BUNDLED / "agents").iterdir())
    tomls = [a for a in agents if a.name.endswith(".toml")]
    assert len(tomls) == 9


def test_bundled_agents_parse_as_valid_toml() -> None:
    for toml_path in (_BUNDLED / "agents").iterdir():
        if toml_path.name.endswith(".toml"):
            data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
            assert "name" in data, f"{toml_path.name} missing 'name'"


def test_bundled_has_head_manager_yaml() -> None:
    mainagent = _BUNDLED / "mainagent"
    assert (mainagent / "head-manager.yaml").is_file()
    assert (mainagent / "subagent-registry.yaml").is_file()


def test_bundled_has_6_orchestrator_skills() -> None:
    skills = list((_BUNDLED / "orchestrator").iterdir())
    assert len(skills) == 6
    for skill_dir in skills:
        assert (skill_dir / "SKILL.md").is_file()


def test_bundled_has_5_role_skills() -> None:
    role_skills = list((_BUNDLED / "role-skills").rglob("SKILL.md"))
    assert len(role_skills) == 5


def test_bundled_has_workflow_yaml() -> None:
    workflows = list((_BUNDLED / "workflows").glob("*.yaml"))
    assert len(workflows) >= 1


def test_bundled_hooks_json_is_valid() -> None:
    hooks = json.loads((_BUNDLED / "hooks.json").read_text(encoding="utf-8"))
    assert "hooks" in hooks
    events = list(hooks["hooks"].keys())
    assert "UserPromptSubmit" in events
    assert "SessionStart" in events


def test_bundled_head_manager_md_nonempty() -> None:
    md = (_BUNDLED / "prompts" / "head-manager.md").read_text(encoding="utf-8")
    assert len(md) > 100
    assert "head-manager" in md.lower()


@pytest.mark.parametrize(
    "name",
    [
        "fundamental-analyst",
        "technical-analyst",
        "news-analyst",
        "macro-analyst",
        "instrument-analyst",
        "valuation-analyst",
        "portfolio-manager",
        "risk-manager",
        "execution-operator",
    ],
)
def test_bundled_each_specialist_present(name: str) -> None:
    assert (_BUNDLED / "agents" / f"{name}.toml").is_file()
