"""Convert Codex ``.codex/hooks.json`` to OpenCode hook objects.

TradingCodex v0.2.0 declares all hooks in a single JSON file at
``.codex/hooks.json`` with this structure:

    {
      "hooks": {
        "SessionStart": [{"hooks": [{"type": "command", "command": "...",
                                     "timeout": 10, "statusMessage": "..."}]}],
        "PreToolUse": [{"matcher": "Bash|mcp__.*", "hooks": [...]}],
        "UserPromptSubmit": [...],
        "SubagentStart": [...],
        "SubagentStop": [...],
        "Stop": [...],
        "PostToolUse": [...],
        "PermissionRequest": [...]
      }
    }

We map each Codex event+hook entry to an :class:`OpenCodeHook`. The
``command`` string is split via :func:`shlex.split` into an argv tuple.
Matchers, timeouts, and statusMessages are preserved in ``env``.
"""

from __future__ import annotations

import json
import shlex
from pathlib import Path

from opencode_trading.exceptions import ConversionError
from opencode_trading.models import OpenCodeHook

# Codex event name → OpenCode event name
_EVENT_MAP: dict[str, str] = {
    "SessionStart": "session_start",
    "PreToolUse": "pre_tool_use",
    "PermissionRequest": "permission_request",
    "PostToolUse": "post_tool_use",
    "UserPromptSubmit": "user_prompt_submit",
    "SubagentStart": "subagent_start",
    "SubagentStop": "subagent_stop",
    "Stop": "session_end",
}


def convert_hooks(workspace: Path) -> tuple[OpenCodeHook, ...]:
    """Read ``.codex/hooks.json`` and convert each hook to OpenCodeHook.

    Returns
    -------
    tuple[OpenCodeHook, ...]
        One OpenCodeHook per inner hook in the JSON. Empty tuple if
        the file does not exist.

    Raises
    ------
    ConversionError
        If ``.codex/hooks.json`` exists but is not valid JSON.
    """
    hooks_path = workspace / ".codex" / "hooks.json"
    if not hooks_path.exists():
        return ()

    try:
        with hooks_path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ConversionError(f"invalid JSON in {hooks_path}: {exc}") from exc

    return convert_hooks_dict(data, source_label=str(hooks_path))


def convert_hooks_dict(
    data: dict[str, object],
    *,
    source_label: str = "<dict>",
) -> tuple[OpenCodeHook, ...]:
    """Convert an already-parsed hooks.json dict to OpenCodeHook tuple.

    Public for reuse by :mod:`opencode_trading.attach` which reads the
    bundled hooks.json via :mod:`importlib.resources` rather than from a
    TCX workspace on disk.

    Parameters
    ----------
    data : dict
        Parsed ``.codex/hooks.json`` content (must have a top-level
        ``"hooks"`` key mapping event names to a list of matcher entries).
    source_label : str
        Used only in error messages; default is fine for in-memory data.

    Returns
    -------
    tuple[OpenCodeHook, ...]
        One OpenCodeHook per inner hook in the dict.
    """
    hooks_section = data.get("hooks", {})
    if not isinstance(hooks_section, dict):
        return ()
    result: list[OpenCodeHook] = []
    for codex_event, entries in hooks_section.items():
        opencode_event = _EVENT_MAP.get(str(codex_event))
        if opencode_event is None:
            continue
        for entry in entries or []:
            if not isinstance(entry, dict):
                continue
            matcher = str(entry.get("matcher", "") or "")
            for inner in entry.get("hooks") or []:
                if not isinstance(inner, dict) or inner.get("type") != "command":
                    continue
                cmd = str(inner.get("command", "") or "")
                env: dict[str, str] = {}
                if matcher:
                    env["OPENCODE_HOOK_MATCHER"] = matcher
                if "timeout" in inner:
                    env["OPENCODE_HOOK_TIMEOUT"] = str(inner["timeout"])
                if "statusMessage" in inner:
                    env["OPENCODE_HOOK_STATUS_MESSAGE"] = str(inner["statusMessage"])
                result.append(
                    OpenCodeHook(
                        event=opencode_event,  # type: ignore[arg-type]
                        command=_split_command(cmd),
                        env=env,
                        blocking=True,
                    )
                )
    return tuple(result)


def _split_command(command: str) -> tuple[str, ...]:
    """Split a shell command string into argv tuple using shlex.

    Falls back to a single-element tuple on parse error.
    """
    try:
        return tuple(shlex.split(command))
    except ValueError:
        return (command,)
