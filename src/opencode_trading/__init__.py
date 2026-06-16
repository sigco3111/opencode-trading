"""opencode-trading: OpenCode adapter for TradingCodex.

This package converts a TradingCodex (Codex-native) workspace into an
OpenCode-compatible workspace, preserving the 1+9 specialist role topology
and the TradingCodex MCP execution boundary.

Public API
----------
- :func:`convert_workspace` — main entry point (zero-deps, in-process)
- :class:`OpenCodeAgent` — domain model for OpenCode agent definitions
- :class:`OpenCodeSkill` — domain model for OpenCode skill definitions
- :class:`OpenCodeHook` — domain model for OpenCode hook configurations
- :class:`OpenCodeWorkspace` — bundle of all generated artifacts

Example
-------
    >>> from opencode_trading import convert_workspace
    >>> convert_workspace("~/my-tcx-workspace", to="opencode")
    PosixPath('~/my-tcx-workspace/.opencode')

Note
----
The zero-deps guarantee means we do NOT import TradingCodex itself. We read
its generated workspace files (TOML/Markdown/YAML) and emit OpenCode JSON.
This keeps the adapter installable in <1s and independent of TradingCodex
release cycles.
"""
from __future__ import annotations

__version__ = "0.1.0"

__all__ = [
    "OpenCodeAgent",
    "OpenCodeSkill",
    "OpenCodeHook",
    "OpenCodeWorkspace",
    "convert_workspace",
]


def __getattr__(name: str):
    """Lazy import to avoid forcing heavy deps on simple usage."""
    if name in ("OpenCodeAgent", "OpenCodeSkill", "OpenCodeHook", "OpenCodeWorkspace"):
        from .models import (
            OpenCodeAgent,
            OpenCodeHook,
            OpenCodeSkill,
            OpenCodeWorkspace,
        )
        return locals()[name]
    if name == "convert_workspace":
        from .converters.codex_to_opencode import convert_workspace
        return convert_workspace
    raise AttributeError(f"module 'opencode_trading' has no attribute {name!r}")
