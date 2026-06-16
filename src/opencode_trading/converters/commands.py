"""Convert Codex slash commands to OpenCode commands.

Implementation note (for other-PC worker)
----------------------------------------
Codex slash commands (``.codex/prompts/$orchestrate-workflow.md``) are
markdown files with a YAML frontmatter block. The frontmatter declares
the command name and description; the body becomes the prompt.

OpenCode commands are similar but stored under
``~/.config/opencode/command/`` as markdown files with frontmatter.

The good news: **the format is nearly identical** — the conversion is
mostly a frontmatter schema rename (e.g. Codex's ``argument-hint`` →
OpenCode's ``arguments``). v0.2.0 should be a small mapping function.

Key mapping (Codex → OpenCode frontmatter)
------------------------------------------
- ``description:``           → ``description:``           (same)
- ``argument-hint: <text>``  → ``arguments: <text>``      (rename)
- ``allowed-tools:``         → ``tools:``                 (rename)
- ``model:``                 → ``model:``                 (same)
- body                       → body                       (same)
"""
from __future__ import annotations

from pathlib import Path

from opencode_trading.models import OpenCodeSkill


def convert_orchestrate_workflow(workspace: Path) -> OpenCodeSkill:
    """Convert the canonical ``$orchestrate-workflow`` Codex prompt.

    Returns
    -------
    OpenCodeSkill
        The converted OpenCode command as an OpenCodeSkill. v0.1.0 returns
        an empty skill with a placeholder description.
    """
    # v0.1.0: stub — v0.2.0 reads .codex/prompts/$orchestrate-workflow.md,
    # parses the frontmatter, renames keys, and returns a full OpenCodeSkill.
    _ = workspace
    return OpenCodeSkill(
        name="orchestrate-workflow",
        description="(stub) Analyze a stock with the full TradingCodex workflow.",
        body=(
            "<!-- v0.1.0 stub. v0.2.0 will read .codex/prompts/$orchestrate-workflow.md "
            "and emit a fully-converted OpenCode command. -->"
        ),
    )
