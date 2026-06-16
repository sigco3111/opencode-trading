# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
