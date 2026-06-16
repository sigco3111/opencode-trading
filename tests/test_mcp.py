# Tests for TradingCodex MCP converter (v0.2.0 shape)
from __future__ import annotations

from opencode_trading.converters.mcp import register_tradingcodex_mcp


def test_mcp_default_command_shape() -> None:
    m = register_tradingcodex_mcp()
    assert m.command == (
        "uvx",
        "--refresh",
        "--python",
        "3.14",
        "--from",
        "tradingcodex",
        "python",
        "-m",
        "tradingcodex_cli",
        "mcp",
        "stdio",
    )


def test_mcp_default_service_addr() -> None:
    m = register_tradingcodex_mcp()
    assert m.env["TRADINGCODEX_SERVICE_ADDR"] == "127.0.0.1:48267"


def test_mcp_custom_package_spec() -> None:
    m = register_tradingcodex_mcp(package_spec="git+https://example.com/x@v1")
    assert m.command[5] == "git+https://example.com/x@v1"


def test_mcp_custom_workspace_root() -> None:
    m = register_tradingcodex_mcp(workspace_root="/abs/path")
    assert m.env["TRADINGCODEX_WORKSPACE_ROOT"] == "/abs/path"
