"""Smoke tests for domain models (v0.1.0)."""
from __future__ import annotations

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
    # Frozen dataclass: assignment must raise
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
        mcp_servers=(
            OpenCodeMCP(name="tradingcodex", transport="stdio", command=("uvx",)),
        ),
    )
    blocks = ws.to_opencode_json_blocks()
    assert "head-manager" in blocks["agent"]
    assert "tradingcodex" in blocks["mcp"]
    assert blocks["agent"]["head-manager"]["model"] == "github-copilot/gpt-4o"


# ---- helpers (use the private functions from models.py) --------------------
from opencode_trading.models import _agent_to_dict, _mcp_to_dict  # noqa: E402


def hook_to_dict_helper(hook: OpenCodeHook) -> dict:
    from opencode_trading.models import _hooks_to_list

    return _hooks_to_list((hook,))[0]


def mcp_to_dict_helper(mcp: OpenCodeMCP) -> dict:
    return _mcp_to_dict(mcp)
