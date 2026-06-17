"""Convert TradingCodex workflow YAML files to OpenCode workflow skills.

TradingCodex v0.2.0 stores workflows at
``.tradingcodex/workflows/<name>.yaml``:

    name: postmortem
    trigger_examples:
      - rejected_order
      - executed_paper_order
    outputs:
      directory: trading/reports/postmortem
      format: json
      filename_pattern: "*.postmortem_report.json"

Each workflow becomes an :class:`OpenCodeSkill` whose body tells the
agent which TradingCodex MCP tools to call and where to write artifacts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from opencode_trading._yaml_min import parse_yaml
from opencode_trading.exceptions import ConversionError
from opencode_trading.models import OpenCodeSkill

_WORKFLOW_DIR = ".tradingcodex/workflows"


def convert_workflow_files(workspace: Path) -> tuple[OpenCodeSkill, ...]:
    """Discover ``.tradingcodex/workflows/*.yaml`` and convert each.

    Returns
    -------
    tuple[OpenCodeSkill, ...]
        One OpenCodeSkill per workflow YAML, sorted by name for stability.
        Empty tuple if the directory does not exist.

    Raises
    ------
    ConversionError
        If a workflow YAML is malformed or missing ``outputs.directory``.
    """
    workflow_dir = workspace / _WORKFLOW_DIR
    if not workflow_dir.exists():
        return ()

    skills: list[OpenCodeSkill] = []
    for yaml_path in sorted(workflow_dir.glob("*.yaml")):
        text = yaml_path.read_text(encoding="utf-8")
        try:
            data = parse_yaml(text)
        except ValueError as exc:
            raise ConversionError(f"invalid YAML in {yaml_path}: {exc}") from exc

        name = str(data.get("name") or yaml_path.stem)
        outputs = data.get("outputs") or {}
        directory = outputs.get("directory")
        if not directory:
            raise ConversionError(f"workflow {yaml_path} missing outputs.directory")

        description = _make_description(name, data.get("trigger_examples") or [])
        body = _render_skill_body(name, data)
        skills.append(OpenCodeSkill(name=name, description=description, body=body))

    return tuple(skills)


def _make_description(name: str, triggers: list[Any]) -> str:
    """Build a short skill description: 'TradingCodex workflow: X (triggers: a, b)'."""
    sample = ", ".join(str(t) for t in triggers[:2])
    return f"TradingCodex workflow: {name} (triggers: {sample})"


def _render_skill_body(name: str, workflow: dict[str, Any]) -> str:
    """Render a markdown body for an OpenCodeSkill from a workflow dict."""
    triggers = workflow.get("trigger_examples") or []
    outputs = workflow.get("outputs") or {}
    directory = outputs.get("directory", "unknown")
    fmt = outputs.get("format", "json")
    pattern = outputs.get("filename_pattern", "*.json")

    trigger_lines = "\n".join(f"- {t}" for t in triggers) or "(no triggers defined)"
    return f"""# Workflow: {name}

## Triggers

{trigger_lines}

## Outputs

- directory: `{directory}`
- format: `{fmt}`
- filename_pattern: `{pattern}`

## Execution

Use TradingCodex MCP tools to execute this workflow. The TradingCodex
MCP server (registered in opencode.json) exposes tools like
`list_workflow_artifacts`, `create_research_artifact`, and
`request_order_approval` that this workflow orchestrates.

After execution, write artifacts to `{directory}/` matching
the `{pattern}` filename pattern.
"""
