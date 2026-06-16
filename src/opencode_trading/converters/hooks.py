"""Convert Codex ``UserPromptSubmit`` hooks to OpenCode hook objects.

Implementation note (for other-PC worker)
----------------------------------------
Codex hooks are Python files in ``.codex/hooks/`` that get executed by
Codex's runtime. They use a specific function signature
(``def hook(payload: dict) -> dict:``) and modify the payload in place.

OpenCode hooks are different — they're declared in ``opencode.json`` as
a list of ``{event, command, env, blocking}`` objects, and the ``command``
is a shell command (argv), not a Python function.

Conversion strategy (v0.2.0)
----------------------------
For each ``.codex/hooks/<name>.py``:
1. Parse the file's AST to extract the function docstring (description)
2. Wrap the Python invocation in a shell command:
   ``python3 <workspace>/.codex/hooks/<name>.py``
3. Preserve the env vars Codex passed (PAYLOAD, ROLE, etc.)
4. Mark as ``blocking=True`` (Codex hooks are sync by default)

Edge case: a Codex hook may import other modules from the workspace.
For v0.2.0, set the working directory to the workspace root in env.
"""
from __future__ import annotations

from pathlib import Path

from opencode_trading.models import OpenCodeHook


def convert_user_prompt_submit(workspace: Path) -> tuple[OpenCodeHook, ...]:
    """Discover and convert Codex ``UserPromptSubmit`` hooks.

    Returns
    -------
    tuple[OpenCodeHook, ...]
        One OpenCodeHook per discovered ``.codex/hooks/*-submit.py`` file.
        Empty tuple in v0.1.0 (stub).
    """
    # v0.1.0: stub — v0.2.0 implements AST parsing + shell wrapping
    _ = workspace
    return ()
