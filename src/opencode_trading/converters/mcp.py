"""Register the TradingCodex MCP server in an OpenCode workspace.

TradingCodex v0.2.0 spawns its MCP server via:
    uvx --refresh --python 3.14 --from {TRADINGCODEX_MCP_PACKAGE_SPEC} \
        python -m tradingcodex_cli mcp stdio

with env vars TRADINGCODEX_MCP_AUTOSTART_SERVICE=1, TRADINGCODEX_SERVICE_ADDR=127.0.0.1:48267,
and TRADINGCODEX_WORKSPACE_ROOT={PROJECT_DIR}.

We emit these as an OpenCodeMCP(stdio) so OpenCode can spawn the server
per-session. The {PACKAGE_SPEC} and {PROJECT_DIR} templates are kept
literal — the user's opencode.json consumer is expected to render them
(or we render at write time in Workspace.write()).
"""

from __future__ import annotations

from opencode_trading.models import OpenCodeMCP


def register_tradingcodex_mcp(
    package_spec: str = "tradingcodex",
    service_addr: str = "127.0.0.1:48267",
    workspace_root: str = "{{PROJECT_DIR}}",
) -> OpenCodeMCP:
    """Build the OpenCodeMCP entry for the TradingCodex MCP server.

    Parameters
    ----------
    package_spec : str
        Value substituted for `{{TRADINGCODEX_MCP_PACKAGE_SPEC}}`. Default
        "tradingcodex" — the published package. Override with a git+https URL
        for pinned versions (e.g. "git+https://github.com/monarchjuno/tradingcodex.git@v0.2.0").
    service_addr : str
        Value for TRADINGCODEX_SERVICE_ADDR env (default "127.0.0.1:48267").
    workspace_root : str
        Value for TRADINGCODEX_WORKSPACE_ROOT env (default "{{PROJECT_DIR}}"
        — kept as template literal for downstream rendering).

    Returns
    -------
    OpenCodeMCP
        stdio-transport MCP server config matching TradingCodex v0.2.0.
    """
    return OpenCodeMCP(
        name="tradingcodex",
        transport="stdio",
        command=(
            "uvx",
            "--refresh",
            "--python",
            "3.14",
            "--from",
            package_spec,
            "python",
            "-m",
            "tradingcodex_cli",
            "mcp",
            "stdio",
        ),
        env={
            "TRADINGCODEX_MCP_AUTOSTART_SERVICE": "1",
            "TRADINGCODEX_SERVICE_ADDR": service_addr,
            "TRADINGCODEX_WORKSPACE_ROOT": workspace_root,
        },
    )
