#+ opencode-trading Architecture (v0.4.0)

This document describes how `opencode_trading.convert_workspace()` walks a
TradingCodex v0.2.0 workspace and emits an OpenCode-compatible bundle, plus
the v0.3.0+ attach path, and the v0.4.0 `verify` and `--with-tcx` features.

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
# v0.2.0+ — Convert an existing TradingCodex workspace
opencode-trading convert --workspace <path>
opencode-trading convert --workspace <path> --out <dir>
opencode-trading convert --workspace <path> --dry-run

# v0.3.0+ — Scaffold a fresh OpenCode workspace from bundled TCX v0.2.0 templates
opencode-trading attach --target <path>
opencode-trading attach --target <path> --package-spec git+https://...
opencode-trading attach --target <path> --overwrite
opencode-trading attach --target <path> --dry-run
```

## v0.3.0 attach path

Unlike `convert` which reads an existing TCX workspace, `attach` builds the
OpenCodeWorkspace in-memory from the bundled TCX v0.2.0 package data:

```
opencode-trading attach --target ~/my-trading-ws
            |
            v
attach_workspace(target=~/my-trading-ws, package_spec="tradingcodex")
            |
            +-- _build_agents()       reads _bundled/agents/*.toml + registry.yaml
            +-- _build_hooks()        reads _bundled/hooks.json
            +-- _build_mcp_servers()  register_tradingcodex_mcp(workspace_root=target)
            +-- _build_skills()       reads _bundled/prompts/head-manager.md
            |                         + _bundled/orchestrator/*/SKILL.md
            |                         + _bundled/role-skills/**/SKILL.md
            |                         + _bundled/workflows/*.yaml
            v
       OpenCodeWorkspace (10 agents, 12 skills, 8 hooks, 1 MCP)
            |
            v
   ws.write(<target>/.opencode, overwrite=args.overwrite)
            |
            v
   ~/my-trading-ws/.opencode/
   ├── agents.json
   ├── mcp.json
   ├── hooks.json
   └── skills/<name>/SKILL.md
```

The MCP `TRADINGCODEX_WORKSPACE_ROOT` env is set to `str(target)` so the
TradingCodex MCP server treats the parent dir as the workspace root
(where `.tradingcodex/secrets.md`, `trading/`, etc. would conventionally live).

## v0.4.0 verify subcommand (Released)

Validates an existing OpenCode workspace (`<path>/.opencode/`) and optionally
round-trips against a TCX source workspace.

```
opencode-trading verify <path> [--workspace <tcx_src>] [--strict]
            |
            v
verify_workspace(path, source=None) -> VerifyResult
            |
            +-- check <path>/.opencode/ exists
            +-- parse agents.json, mcp.json, hooks.json
            |     (each must exist + be valid JSON)
            +-- walk skills/*/SKILL.md
            |     - frontmatter `name` must match dir name
            |     - body must not be empty
            +-- validate every hook event ∈ HookEvent literal
            +-- if --workspace given:
            |     run convert_workspace(source) and compare:
            |     - agent names
            |     - skill names
            |     - hook (event, command, env, blocking) signatures
            v
    VerifyResult(passed, errors, warnings, summary)
            |
            v
   exit 0  ── passed=True, no errors (warnings OK unless --strict)
   exit 1  ── passed=False, list errors
   exit 2  ── usage error (path missing, etc.)
```

**Contract scenarios** (`tests/test_verify.py`):
- S1 happy: `verify` on a valid `attach_workspace` output → exit 0, `passed=True`
- S2 missing file: `agents.json` deleted → exit 1, error names the missing file
- S3 invalid hook event: junk event injected into `hooks.json` → exit 1, error names the bad entry
- S4 round-trip: `verify --workspace <tcx_src>` → cross-checks TCX↔OpenCode equivalence
- S5 frontmatter mismatch: skill dir `review-risk` but `fm.name="totally-different"` → exit 1

## v0.4.0 attach --with-tcx (Released)

When passed to `attach`, the bundled TCX workspace files are also written to
`<target>/` so the user gets a complete, dual-use workspace (TCX + OpenCode).

```
opencode-trading attach --target ~/ws --with-tcx [--overwrite] [--dry-run]
            |
            v
attach_workspace(target=~/ws, package_spec="tradingcodex", with_tcx=True)
            |
            +-- _build_agents / _build_hooks / _build_mcp_servers / _build_skills
            |     (same as default attach)
            +-- _write_tcx_files(target=~/ws, overwrite=...)
            |     - .codex/agents/*.toml            (from _bundled/agents/)
            |     - .codex/hooks.json                (from _bundled/hooks.json)
            |     - .codex/prompts/base_instructions/head-manager.md
            |     - .tradingcodex/mainagent/head-manager.yaml
            |     - .tradingcodex/mainagent/subagent-registry.yaml
            |     - .tradingcodex/config.yaml        (from _bundled/tradingcodex/config.yaml)
            |     - .tradingcodex/workflows/*.yaml
            |     - .tradingcodex/subagents/skills/<role>/<skill>/SKILL.md
            |     - .agents/skills/<skill>/SKILL.md
            v
       OpenCodeWorkspace (10 agents, 13 skills, 8+ hooks, 1 MCP) + TCX root
            |
            v
    ws.write(<target>/.opencode)
    _write_tcx_files(<target>/...)  # raises FileExistsError if existing & no --overwrite
            |
            v
   ~/ws/
   ├── .opencode/        (OpenCode bundle — same as default attach)
   ├── .codex/           (TCX Codex-native shim)
   ├── .tradingcodex/    (TCX config + workflows + subagent skills)
   └── .agents/          (orchestrator skills)
```

**Contract scenarios** (`tests/test_with_tcx.py` + `tests/test_cli.py`):
- S1 happy: writes all four dirs; every file's bytes match the bundled source
- S2 overwrite: `--overwrite` replaces existing TCX files without prompt
- S3 no-overwrite: existing TCX files + no `--overwrite` → exit 2 with clear error
- S4 dry-run: `--dry-run` prints the plan, no FS writes

## Future (v0.5.0+)

- TCX v0.3.0 snapshot upgrade — **DEFERRED**: TradingCodex v0.3.0 has not yet
  been released on PyPI or GitHub (verified 2026-06-17). When TCX v0.3.0 ships,
  the bundled snapshot will be re-cut and `_TCX_VERSION` bumped.
- `attach --with-tcx` is currently a "raw files" copy. Future versions may
  include TCX-side rendering (e.g. `{{GENERATED_AT}}` placeholder substitution)
  and bundled TCX Python hooks (`tradingcodex_hook.py`).
