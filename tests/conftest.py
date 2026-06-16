"""pytest fixtures for opencode-trading.

Implementation note (for other-PC worker)
----------------------------------------
A real TradingCodex workspace fixture is expensive to construct (needs
`tcx attach` + Django service). For v0.1.0 tests, we use a minimal
in-memory structure that mimics the expected layout.

When v0.2.0 adds round-trip tests, generate a real workspace via:
    uvx --from tradingcodex tcx attach /tmp/tcx-test-fixture
and copy it under ``tests/fixtures/sample-tcx-workspace/``.
"""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_tcx_workspace(tmp_path: Path) -> Path:
    """Build a minimal TradingCodex workspace skeleton in tmp_path."""
    ws = tmp_path / "tcx-workspace"
    ws.mkdir()
    (ws / ".codex").mkdir()
    (ws / ".codex" / "agents").mkdir()
    (ws / ".codex" / "prompts").mkdir()
    (ws / ".codex" / "hooks").mkdir()
    (ws / ".tradingcodex").mkdir()
    (ws / ".tradingcodex" / "workflows").mkdir()
    (ws / ".agents").mkdir()
    (ws / ".agents" / "skills").mkdir()
    return ws


@pytest.fixture
def tmp_opencode_workspace(tmp_path: Path) -> Path:
    """Empty OpenCode workspace target."""
    ws = tmp_path / "opencode-workspace"
    ws.mkdir()
    return ws
