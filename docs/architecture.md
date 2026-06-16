#+ opencode-trading Architecture (v0.2.0)

This document describes how `opencode_trading.convert_workspace()` walks a
TradingCodex v0.2.0 workspace and emits an OpenCode-compatible bundle.

## Pipeline

```
TradingCodex v0.2.0 workspace
│
├─── .codex/agents/*.toml            ──┐
│       (9 specialist TOML files)      │
│                                      │ tomllib (stdlib)
├─── .tradingcodex/mainagent/         │
│       head-manager.yaml             │ _yaml_min (hand-rolled)
│       subagent-registry.yaml ───────┤
│                                      ▼
├─── .codex/hooks.json                ──── json (stdlib)
│                                      │
├─── .codex/prompts/base_instructions/ │
│       head-manager.md               │ text (read)
│                                      │
├─── .tradingcodex/workflows/*.yaml  ── _yaml_min
│                                      │
├─── .agents/skills/*/SKILL.md ──────── _frontmatter (hand-rolled)
│                                      │
└─── .tradingcodex/subagents/skills/   │
        <role>/<skill>/SKILL.md ─────── _frontmatter
                                      │
                                      ▼
                       OpenCodeWorkspace bundle
                       (10 agents + 15 skills + 8 hooks + 1 MCP)
                                      │
                                      ▼
                          Workspace.write(out_dir)
                                      │
                                      ▼
                  <out_dir>/
                  ├── agents.json     (dict of {name: agent})
                  ├── mcp.json        (dict of {name: mcp})
                  ├── hooks.json      (list of {event, command, env, blocking})
                  └── skills/
                      └── <name>/SKILL.md   (frontmatter + body)
```

## Conversion responsibilities

| Subconverter | Input | Output | Parser |
|---|---|---|---|
| `convert_agents` | 9 specialist TOML + head-manager YAML + registry | 10 OpenCodeAgent | `tomllib`, `_yaml_min` |
| `convert_hooks` | `.codex/hooks.json` | 8+ OpenCodeHook | `json` |
| `convert_orchestrate_workflow` | head-manager.md | 1 OpenCodeSkill | text read |
| `collect_orchestrator_skills` | `.agents/skills/*/SKILL.md` | 6 OpenCodeSkill | `_frontmatter` |
| `_collect_role_skills` (private) | `.tradingcodex/subagents/skills/<role>/<skill>/SKILL.md` | 5 OpenCodeSkill | `_frontmatter` |
| `convert_workflow_files` | `.tradingcodex/workflows/*.yaml` | 3 OpenCodeSkill | `_yaml_min` |
| `register_tradingcodex_mcp` | (none — constants) | 1 OpenCodeMCP | — |

## Zero-deps design

- **TOML**: `tomllib` (Python 3.11+ stdlib)
- **JSON**: `json` (stdlib)
- **YAML**: hand-rolled `_yaml_min.py` — supports only the TCX v0.2.0 schemas (top-level scalars, sequences, 2-space nested mappings, `{{TEMPLATE}}` placeholders). NO PyYAML.
- **Frontmatter**: hand-rolled `_frontmatter.py` — simple `---` delimited block parser.

## CLI surface

```
# Convert to default out (./.opencode)
opencode-trading convert --workspace <path>

# Convert to custom dir
opencode-trading convert --workspace <path> --out <dir>

# Preview without writing
opencode-trading convert --workspace <path> --dry-run
```

## Future (v0.3.0+)

- `opencode-trading attach <path>` — generate a fresh TradingCodex workspace
  pre-converted to OpenCode format
- `opencode-trading verify <path>` — round-trip integrity check
