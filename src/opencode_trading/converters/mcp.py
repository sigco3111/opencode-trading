"""Register the TradingCodex MCP server in an OpenCode workspace.

Implementation note (for other-PC worker)
----------------------------------------
TradingCodex ships an MCP server (the Django service) that exposes typed
tools like ``create_research_artifact``, ``create_order_ticket``, etc.
OpenCode's MCP client can connect to it via stdio or HTTP.

The cleanest integration: register the TradingCodex MCP server in
``opencode.json`` so every OpenCode session has it available.

Command shape (v0.2.0)
----------------------
stdio transport (preferred — works offline, no auth dance):
    command = ["uvx", "--from", "tradingcodex", "tcx", "mcp", "serve"]
    env = {"TRADINGCODEX_MCP_KEY": "<random-32-char>"}

http transport (for when TradingCodex is already running as a service):
    transport = "streamable-http"
    url = "http://127.0.0.1:48267/mcp"
    env = {"TRADINGCODEX_MCP_KEY": "<same-key-as-the-server>"}

For v0.1.0, we emit the stdio form (always works without pre-existing service).
"""
from __future__ import annotations

from opencode_trading.models import OpenCodeMCP


def register_tradingcodex_mcp() -> OpenCodeMCP:
    """Build the OpenCodeMCP entry for the TradingCodex MCP server.

    Returns
    -------
    OpenCodeMCP
        A stdio-transport MCP server config that spawns TradingCodex via uvx.
    """
    # v0.1.0: hard-coded — v0.2.0 will read TRADINGCODEX_MCP_KEY from the
    # workspace's .tradingcodex/config.yaml if present, else generate one.
    return OpenCodeMCP(
        name="tradingcodex",
        transport="stdio",
        command=("uvx", "--from", "tradingcodex", "tcx", "mcp", "serve"),
        env={"TRADINGCODEX_MCP_SAFE_TOOLS": "1"},
    )
