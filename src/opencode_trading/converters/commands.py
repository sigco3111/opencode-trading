"""Convert Codex prompts and orchestrator skills to OpenCode skills.

TradingCodex v0.2.0 has two distinct command-shaped artifacts:

1. The head-manager system prompt at
   ``.codex/prompts/base_instructions/head-manager.md`` — this becomes
   the primary agent's system prompt.

2. Orchestrator skills at ``.agents/skills/<name>/SKILL.md`` — these
   are user-facing workflow entry points. Each becomes one OpenCodeSkill
   with frontmatter-derived name/description and the markdown body as
   the skill body.
"""

from __future__ import annotations

from pathlib import Path

from opencode_trading._frontmatter import parse_frontmatter
from opencode_trading.exceptions import ConversionError
from opencode_trading.models import OpenCodeSkill

_HEAD_MANAGER_PROMPT = ".codex/prompts/base_instructions/head-manager.md"
_ORCHESTRATOR_SKILLS_DIR = ".agents/skills"


def convert_orchestrate_workflow(workspace: Path) -> OpenCodeSkill:
    """Read the head-manager system prompt as a skill.

    Returns
    -------
    OpenCodeSkill
        The head-manager prompt wrapped as a skill. Used as the
        primary agent's system prompt by the orchestrator.

    Raises
    ------
    ConversionError
        If the head-manager prompt file is missing.
    """
    prompt_path = workspace / _HEAD_MANAGER_PROMPT
    if not prompt_path.exists():
        raise ConversionError(f"head-manager prompt missing: {prompt_path}")
    body = prompt_path.read_text(encoding="utf-8")
    return OpenCodeSkill(
        name="head-manager",
        description="TradingCodex head-manager system prompt.",
        body=body,
    )


def collect_orchestrator_skills(workspace: Path) -> tuple[OpenCodeSkill, ...]:
    """Discover all ``.agents/skills/*/SKILL.md`` and return as skills.

    Returns
    -------
    tuple[OpenCodeSkill, ...]
        Sorted by skill name for stability. Empty tuple if directory
        does not exist or has no SKILL.md files.
    """
    skills_dir = workspace / _ORCHESTRATOR_SKILLS_DIR
    if not skills_dir.exists():
        return ()

    skills: list[OpenCodeSkill] = []
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        skills.append(OpenCodeSkill(name=fm.name, description=fm.description, body=fm.body))
    return tuple(skills)
