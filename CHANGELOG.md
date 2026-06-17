# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-17

### Added
- `CONTRIBUTING.md` — bug reports, feature requests, PR workflow
- `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1
- `SECURITY.md` — private vulnerability disclosure policy
- `AUTHORS` — maintainer + upstream acknowledgements
- Coverage reporting in CI (`coverage[toml]>=7`, threshold 60% with
  show_missing + exclude_lines; baseline 63% — raise to 80 in v1.1.0
  once direct-call CLI tests land)
- Release workflow (`.github/workflows/release.yml`) — sdist + wheel
  build, PyPI trusted publishing (OIDC), GitHub Release on `v*` tags
- 7 new edge-case tests (verify + attach --with-tcx)
- `## FAQ` section in README (5 Q/A pairs covering convert vs attach,
  Python 3.14 requirement, byte-identical output, upstream-merge
  readiness, security disclosure)
- v0.4.0 retroactively tagged at `9211212` (the v0.4.0 release commit)

### Changed
- README: install block updated to `@v0.4.0`, roadmap marks v0.4.0
  as Released, contributing section links to `CONTRIBUTING.md` /
  `SECURITY.md` / `CODE_OF_CONDUCT.md`

### Notes
- This is the upstream-merge hardening release. No public API changes
  since v0.4.0.
- Coverage baseline of 63% reflects subprocess-based CLI testing in
  test_cli.py (coverage does not track child processes). The 60%
  threshold gives headroom; tightening to 80% is a v1.1.0 task.
- Real-world TCX install (tradingcodex v0.2.0) requires Python 3.14.
  The bundled `attach` path works on 3.11+; only `convert` against a
  live TCX workspace needs 3.14. This is documented in the README FAQ.
- Maintainer follow-up before `git push origin v0.4.0 v1.0.0`:
  - Register the project on PyPI (https://pypi.org/project/opencode-trading/)
  - Add a Trusted Publisher on PyPI pointing at this repo +
    `.github/workflows/release.yml` (OIDC, no API token needed)
  - Without the Trusted Publisher, the `publish` job will fail with
    `403 Invalid or non-existent authentication information` — this
    is expected and does not block the tag push.

## [0.4.0] - 2026-06-17

### Added
- `opencode-trading verify <path>` CLI subcommand — validates an OpenCode
  workspace and (optionally) round-trips against a TCX source
- `opencode_trading.verify_workspace(path, *, source=None)` public API
  returns a `VerifyResult` frozen dataclass (passed / errors / warnings / summary)
- `attach --with-tcx` flag — also writes bundled TCX workspace files
  (`.codex/`, `.tradingcodex/`, `.agents/`) to `<target>/` for a dual-use workspace
- `attach_workspace()` signature change: returns `tuple[OpenCodeWorkspace, Path | None]`
  (the second element is the TCX root path when `with_tcx=True`, else `None`)
- Bundled `_bundled/tradingcodex/config.yaml` — synthesized minimal config
  for `--with-tcx` byte-match invariant
- `verify` flags: `--workspace <tcx_src>` (round-trip), `--strict` (warnings as errors)
- 22 new tests: 6 in `test_verify.py`, 5 in `test_with_tcx.py`, 11 in `test_cli.py`
  (102 → 124 tests total)

### Changed
- README roadmap: v0.3.0 marked Released, v0.4.0 added as In progress
- `docs/architecture.md` header bumped to v0.4.0; new sections for
  `verify` and `--with-tcx` with ASCII diagrams + contract scenarios
- `attach_workspace()` is now a 3-kwarg function (backward-incompatible
  return type — callers must unpack the tuple)

### Fixed
- `verify.py` mypy strict errors: renamed `missing_in_actual/expected`
  variables per loop to avoid set-type aliasing
- `attach.py` line-length ruff error in `_tcx_pairs()` body (extracted
  `_BUNDLED_DIR / "role-skills"` to local variable)

### Notes
- `verify_workspace(..., source=...)` round-trip compares **names + signatures**
  only (not full text), so bundled-template drift between attach vs convert
  is detected as a `FAIL` rather than masked.
- TCX v0.3.0 snapshot upgrade remains **deferred** — TradingCodex v0.3.0
  has not been released on PyPI or GitHub (verified 2026-06-17).

## [0.3.0] - 2026-06-17

### Added
- `opencode-trading attach` CLI subcommand — scaffolds a fresh OpenCode
  workspace from bundled TCX v0.2.0 templates (no TCX install required)
- `opencode_trading.attach_workspace()` public API — programmatic equivalent
- Flags: `--target <dir>` (required), `--package-spec <pkg>` (default `tradingcodex`),
  `--overwrite`, `--dry-run`
- Bundled package data: 25 TCX v0.2.0 template files under
  `src/opencode_trading/_bundled/` (9 specialist TOMLs, head-manager YAML
  + registry, hooks.json, head-manager.md, 6 orchestrator + 5 role skill
  MD files, 1 workflow yaml)
- `convert_hooks_dict(data, source_label)` extracted public helper in
  `converters.hooks` for reuse by the attach module
- 30 new tests (test_bundled: 18, test_attach: 22, test_cli attach: +8 = 48;
  plus deduped test count = 30 new effective tests)

### Changed
- Module docstring in `__init__.py` documents both `convert_workspace` and
  `attach_workspace` public APIs
- `_build_skills()` in attach deduplicates by name (orchestrator's
  `postmortem` wins over workflow `postmortem`)

## [0.2.0] - 2026-06-17

### Added
- 5 conversion responsibilities fully implemented (no more stubs):
  - `convert_workspace` orchestrator (wires all sub-converters)
  - `convert_agents` (NEW) — 9 specialist TOML + head-manager YAML + registry → 10 OpenCodeAgent
  - `convert_hooks` — `.codex/hooks.json` → OpenCodeHook (8 event types)
  - `convert_orchestrate_workflow` — head-manager system prompt
  - `collect_orchestrator_skills` — `.agents/skills/*/SKILL.md` → 6 OpenCodeSkill
  - `convert_workflow_files` — `.tradingcodex/workflows/*.yaml` → OpenCodeSkill
  - `register_tradingcodex_mcp` — TradingCodex MCP server (real v0.2.0 command)
- `OpenCodeWorkspace.write(out_dir, overwrite=False)` renderer
- CLI: `convert --out` now writes `agents.json`, `mcp.json`, `hooks.json`, `skills/*/SKILL.md` to disk
- Hand-rolled YAML parser (`_yaml_min.py`) — zero-deps
- Hand-rolled frontmatter parser (`_frontmatter.py`) — zero-deps
- `tests/fixtures/sample-tcx-workspace/` — 30-file real TCX v0.2.0 mirror for round-trip tests
- `HookEvent` extended with `pre_tool_use`, `post_tool_use`, `permission_request`, `subagent_start`, `subagent_stop`
- 54 unit + integration tests (was 18 in v0.1.0)
- Real MCP command: `uvx --refresh --python 3.14 --from {PACKAGE} python -m tradingcodex_cli mcp stdio` (was incorrect v0.1.0 stub)
- CI: Python 3.11/3.12/3.13/3.14 matrix, strict mypy, sample workspace smoke

### Changed
- **BREAKING**: `hooks.convert_user_prompt_submit` renamed to `hooks.convert_hooks` (full hooks.json conversion, not just UserPromptSubmit)
- **BREAKING**: `commands.convert_orchestrate_workflow` now returns head-manager system prompt (was a stub skill)
- **BREAKING**: `commands.collect_orchestrator_skills` NEW — extracts orchestrator skills from `.agents/skills/`
- MCP env vars added: `TRADINGCODEX_MCP_AUTOSTART_SERVICE=1`, `TRADINGCODEX_SERVICE_ADDR=127.0.0.1:48267`, `TRADINGCODEX_WORKSPACE_ROOT={PROJECT_DIR}`

### Fixed
- `cli.py:127` used `callable` (lowercase) as type annotation — now `typing.Callable`
- `tradingcodex>=0.2.1` optional dep unreachable (only v0.2.0 published) — README now references v0.2.0

### Notes
- TradingCodex v0.2.0 source verified by direct clone of `https://github.com/monarchjuno/tradingcodex @ v0.2.0` (NOT v0.2.1 as initially assumed in v0.1.0).
- The adapter remains zero-deps at runtime (TOML via stdlib `tomllib`, JSON via stdlib `json`, YAML via hand-rolled parser).
- v0.3.0 will add `tcx-opencode attach` CLI for generating OpenCode-ready TradingCodex workspaces.

## [0.1.0] - 2026-06-17

### Added
- Initial project skeleton (Phase 0)
- Domain models: `OpenCodeAgent`, `OpenCodeSkill`, `OpenCodeHook`, `OpenCodeMCP`, `OpenCodeWorkspace`
- Exception hierarchy: `OpenCodeTradingError`, `ConversionError`, `MissingWorkspaceError`, `UnsupportedTradingCodexVersion`
- 5 conversion stubs: `convert_workspace`, `convert_orchestrate_workflow`, `convert_user_prompt_submit`, `register_tradingcodex_mcp`, `convert_workflow_files`
- CLI: `opencode-trading convert` (stub — dry-run only in 0.1.0)
- 16 unit + smoke tests across `test_models`, `test_codex_to_opencode`, `test_converters`, `test_cli`
- GitHub Actions CI: Python 3.11/3.12/3.13 + ruff + mypy + pytest
- Korean/English bilingual README with decision-matrix, 6 use-cases, 4-step roadmap
- Zero runtime dependencies (TradingCodex is optional `tradingcodex` extra)

### Notes
- This is a Phase 0 release — skeleton + docs + design only.
- v0.2.0 will implement the 5 converters in full (TOML → JSON, hook AST parsing, command frontmatter mapping, MCP registration, workflow YAML → skills).
- v0.3.0 will add `tcx-opencode attach` CLI for generating OpenCode-ready TradingCodex workspaces.
