"""Tests for :mod:`opencode_trading.converters.hooks` (TradingCodex v0.2.0).

The v0.1.0 stub ``convert_user_prompt_submit`` is replaced in v0.2.0 by
``convert_hooks``, which reads ``.codex/hooks.json`` and maps every
Codex event (``SessionStart``, ``PreToolUse``, ``PermissionRequest``,
``PostToolUse``, ``UserPromptSubmit``, ``SubagentStart``,
``SubagentStop``, ``Stop``) to an :class:`OpenCodeHook`.

These tests use the shared fixtures from ``tests/conftest.py``:

- ``sample_tcx_workspace`` — real TradingCodex v0.2.0 fixture with 8 events
- ``tmp_tcx_workspace`` — minimal skeleton (no ``.codex/hooks.json``)
"""
from __future__ import annotations

from pathlib import Path

from opencode_trading.converters.hooks import convert_hooks
from opencode_trading.models import OpenCodeHook


def test_hooks_empty_when_no_hooks_file(tmp_tcx_workspace: Path) -> None:
    """``convert_hooks`` returns ``()`` when ``.codex/hooks.json`` is absent."""
    assert convert_hooks(tmp_tcx_workspace) == ()


def test_hooks_reads_session_start(sample_tcx_workspace: Path) -> None:
    """At least one :class:`OpenCodeHook` for ``session_start`` is produced."""
    hooks = convert_hooks(sample_tcx_workspace)
    session_start_hooks = [h for h in hooks if h.event == "session_start"]
    assert session_start_hooks, "expected at least one session_start hook"
    assert all(isinstance(h, OpenCodeHook) for h in session_start_hooks)


def test_hooks_reads_user_prompt_submit(sample_tcx_workspace: Path) -> None:
    """At least one :class:`OpenCodeHook` for ``user_prompt_submit`` is produced."""
    hooks = convert_hooks(sample_tcx_workspace)
    submit_hooks = [h for h in hooks if h.event == "user_prompt_submit"]
    assert submit_hooks, "expected at least one user_prompt_submit hook"


def test_hooks_maps_pre_tool_use_with_matcher(sample_tcx_workspace: Path) -> None:
    """``PreToolUse`` matcher is preserved as ``OPENCODE_HOOK_MATCHER`` in env."""
    hooks = convert_hooks(sample_tcx_workspace)
    pre_tool_hooks = [h for h in hooks if h.event == "pre_tool_use"]
    assert pre_tool_hooks, "expected at least one pre_tool_use hook"
    # The Codex matcher is "Bash|mcp__.*" — "Bash" must appear in env.
    assert any("Bash" in h.env.get("OPENCODE_HOOK_MATCHER", "") for h in pre_tool_hooks)


def test_hooks_command_split_correctly(sample_tcx_workspace: Path) -> None:
    """The first session_start hook's command is split into argv via shlex."""
    hooks = convert_hooks(sample_tcx_workspace)
    session_start_hooks = [h for h in hooks if h.event == "session_start"]
    assert session_start_hooks
    # The fixture command is:
    #   {{PYTHON_EXECUTABLE}} "{{PROJECT_DIR}}/.codex/hooks/tradingcodex_hook.py" session-start
    # shlex.split yields: ('{{PYTHON_EXECUTABLE}}',
    #                     '{{PROJECT_DIR}}/.codex/hooks/tradingcodex_hook.py',
    #                     'session-start')
    first = session_start_hooks[0]
    assert first.command[0] == "{{PYTHON_EXECUTABLE}}"
    assert len(first.command) >= 2
    assert first.command[-1] == "session-start"
