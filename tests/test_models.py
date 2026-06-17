"""Tests for domain models (v0.2.0)."""

from __future__ import annotations

import json
from pathlib import Path

from opencode_trading.models import (
    OpenCodeAgent,
    OpenCodeHook,
    OpenCodeMCP,
    OpenCodeSkill,
    OpenCodeWorkspace,
)


def test_opencode_agent_is_frozen() -> None:
    agent = OpenCodeAgent(
        name="head-manager",
        kind="primary",
        model="github-copilot/gpt-4o",
        system_prompt="You are the head manager.",
    )
    assert agent.name == "head-manager"
    assert agent.kind == "primary"
    import dataclasses

    try:
        agent.name = "other"  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        return
    raise AssertionError("OpenCodeAgent should be frozen")


def test_opencode_skill_defaults() -> None:
    skill = OpenCodeSkill(name="x", description="d", body="b")
    assert skill.path is None


def test_opencode_hook_to_dict() -> None:
    hook = OpenCodeHook(
        event="user_prompt_submit",
        command=("python3", "hook.py"),
        env={"PAYLOAD": "json"},
        blocking=True,
    )
    d = hook_to_dict_helper(hook)
    assert d["event"] == "user_prompt_submit"
    assert d["command"] == ["python3", "hook.py"]
    assert d["env"] == {"PAYLOAD": "json"}


def test_opencode_mcp_stdio() -> None:
    mcp = OpenCodeMCP(
        name="tradingcodex",
        transport="stdio",
        command=("uvx", "tcx", "mcp", "serve"),
    )
    d = mcp_to_dict_helper(mcp)
    assert d["type"] == "stdio"
    assert d["command"] == ["uvx", "tcx", "mcp", "serve"]


def test_workspace_to_opencode_json_blocks() -> None:
    ws = OpenCodeWorkspace(
        agents=(
            OpenCodeAgent(
                name="head-manager",
                kind="primary",
                model="github-copilot/gpt-4o",
                system_prompt="x",
            ),
        ),
        mcp_servers=(OpenCodeMCP(name="tradingcodex", transport="stdio", command=("uvx",)),),
    )
    blocks = ws.to_opencode_json_blocks()
    assert "head-manager" in blocks["agent"]
    assert "tradingcodex" in blocks["mcp"]
    assert blocks["agent"]["head-manager"]["model"] == "github-copilot/gpt-4o"


def test_workspace_write_creates_agents_json(tmp_path: Path) -> None:
    ws = OpenCodeWorkspace(
        agents=(
            OpenCodeAgent(
                name="head-manager",
                kind="primary",
                model="m",
                system_prompt="p",
            ),
        ),
    )
    written = ws.write(tmp_path)
    agents_json = tmp_path / "agents.json"
    assert agents_json in written
    data = json.loads(agents_json.read_text())
    assert "head-manager" in data


def test_workspace_write_creates_skill_markdown(tmp_path: Path) -> None:
    ws = OpenCodeWorkspace(
        skills=(
            OpenCodeSkill(
                name="orchestrate-workflow",
                description="Coordinate workflows",
                body="# Orchestrate Workflow\n\nBody content.",
            ),
        ),
    )
    written = ws.write(tmp_path)
    skill_md = tmp_path / "skills" / "orchestrate-workflow" / "SKILL.md"
    assert skill_md in written
    text = skill_md.read_text()
    assert text.startswith("---")
    assert "name: orchestrate-workflow" in text
    assert "Body content." in text


def test_workspace_write_refuses_overwrite_by_default(tmp_path: Path) -> None:
    ws = OpenCodeWorkspace(
        agents=(OpenCodeAgent(name="x", kind="primary", model="m", system_prompt="p"),),
    )
    ws.write(tmp_path)
    import pytest

    with pytest.raises(FileExistsError):
        ws.write(tmp_path)


from opencode_trading.models import _mcp_to_dict  # noqa: E402


def hook_to_dict_helper(hook: OpenCodeHook) -> dict:
    from opencode_trading.models import _hooks_to_list

    return _hooks_to_list((hook,))[0]


def mcp_to_dict_helper(mcp: OpenCodeMCP) -> dict:
    return _mcp_to_dict(mcp)
