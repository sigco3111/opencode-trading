"""opencode-trading: OpenCode adapter for TradingCodex.

This package converts a TradingCodex (Codex-native) workspace into an
OpenCode-compatible workspace, preserving the 1+9 specialist role topology
and the TradingCodex MCP execution boundary. It can also scaffold a fresh
OpenCode workspace from bundled TCX v0.2.0 templates without requiring
TradingCodex to be installed.

Public API
----------
- :func:`convert_workspace` — convert an existing TCX workspace (v0.2.0+)
- :func:`attach_workspace` — scaffold a fresh OpenCode workspace (v0.3.0+)
- :class:`OpenCodeAgent` — domain model for OpenCode agent definitions
- :class:`OpenCodeSkill` — domain model for OpenCode skill definitions
- :class:`OpenCodeHook` — domain model for OpenCode hook configurations
- :class:`OpenCodeWorkspace` — bundle of all generated artifacts

Example
-------
    >>> from opencode_trading import convert_workspace, attach_workspace
    >>> # Convert an existing TCX workspace:
    >>> ws = convert_workspace("~/my-tcx-workspace", to="opencode")
    >>> # Or scaffold a fresh OpenCode workspace from bundled templates:
    >>> ws = attach_workspace(target=Path("~/my-trading-ws"))

Note
----
The zero-deps guarantee means we do NOT import TradingCodex itself. We read
its generated workspace files (TOML/Markdown/YAML) and emit OpenCode JSON.
This keeps the adapter installable in <1s and independent of TradingCodex
release cycles.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

__version__ = "0.3.0"

__all__ = [
    "OpenCodeAgent",
    "OpenCodeSkill",
    "OpenCodeHook",
    "OpenCodeWorkspace",
    "convert_workspace",
    "attach_workspace",
]

if TYPE_CHECKING:
    from opencode_trading.attach import attach_workspace
    from opencode_trading.converters.codex_to_opencode import convert_workspace
    from opencode_trading.models import (
        OpenCodeAgent,
        OpenCodeHook,
        OpenCodeSkill,
        OpenCodeWorkspace,
    )


def __getattr__(name: str) -> Any:
    """Lazy import to avoid forcing heavy deps on simple usage."""
    if name in ("OpenCodeAgent", "OpenCodeSkill", "OpenCodeHook", "OpenCodeWorkspace"):
        import importlib

        mod = importlib.import_module(".models", __name__)
        return getattr(mod, name)
    if name == "convert_workspace":
        from .converters.codex_to_opencode import convert_workspace

        return convert_workspace
    if name == "attach_workspace":
        from .attach import attach_workspace

        return attach_workspace
    raise AttributeError(f"module 'opencode_trading' has no attribute {name!r}")
