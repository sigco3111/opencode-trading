"""pytest fixtures for opencode-trading.

Implementation note (for other-PC worker)
----------------------------------------
A real TradingCodex workspace fixture is included at
``tests/fixtures/sample-tcx-workspace/`` — a 30-file mirror of the
TradingCodex v0.2.0 layout sourced from monarchjuno/tradingcodex@v0.2.0
``.codex/agents/*.toml``, ``.codex/hooks.json``, ``.tradingcodex/mainagent/*.yaml``,
``.tradingcodex/workflows/*.yaml``, ``.agents/skills/*/SKILL.md``, and
``.tradingcodex/subagents/skills/<role>/<skill>/SKILL.md``.

This fixture is the basis for round-trip conversion tests: load it,
run ``convert_workspace()``, verify all 10 agents, 11+ skills, 8 hooks,
and 1 MCP server are emitted.
"""
from __future__ import annotations

from pathlib import Path

import pytest

# Repo root for resolving the sample-tcx-workspace fixture directory
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SAMPLE_TCX = _REPO_ROOT / "tests" / "fixtures" / "sample-tcx-workspace"


@pytest.fixture
def sample_tcx_workspace() -> Path:
    """Real TradingCodex v0.2.0 workspace fixture (30+ files)."""
    assert _SAMPLE_TCX.exists(), f"sample fixture missing: {_SAMPLE_TCX}"
    return _SAMPLE_TCX


@pytest.fixture
def tmp_tcx_workspace(tmp_path: Path) -> Path:
    """Build a minimal TradingCodex v0.2.0 workspace skeleton in tmp_path.

    Mirrors the real layout enough for converter tests that build their own
    content (e.g. write a synthetic ``.codex/agents/x.toml`` and assert it
    is read). For round-trip tests, prefer the ``sample_tcx_workspace``
    fixture.
    """
    ws = tmp_path / "tcx-workspace"
    ws.mkdir()
    # .codex tree
    (ws / ".codex").mkdir()
    (ws / ".codex" / "agents").mkdir()
    (ws / ".codex" / "hooks").mkdir()
    (ws / ".codex" / "prompts" / "base_instructions").mkdir(parents=True)
    # .tradingcodex tree
    (ws / ".tradingcodex").mkdir()
    (ws / ".tradingcodex" / "mainagent").mkdir()
    (ws / ".tradingcodex" / "workflows").mkdir()
    (ws / ".tradingcodex" / "subagents" / "skills").mkdir(parents=True)
    # orchestrator skills
    (ws / ".agents" / "skills").mkdir(parents=True)
    return ws


@pytest.fixture
def tmp_opencode_workspace(tmp_path: Path) -> Path:
    """Empty OpenCode workspace target."""
    ws = tmp_path / "opencode-workspace"
    ws.mkdir()
    return ws
