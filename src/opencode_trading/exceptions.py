"""Exception hierarchy for opencode-trading.

All library exceptions inherit from :class:`OpenCodeTradingError` so users
can catch everything with a single ``except`` clause.

Implementation note (for other-PC worker)
----------------------------------------
Keep this file dependency-free (only stdlib). It's imported by every other
module, so anything added here propagates everywhere.
"""

from __future__ import annotations


class OpenCodeTradingError(Exception):
    """Base class for all opencode-trading errors."""


class ConversionError(OpenCodeTradingError):
    """Raised when a TradingCodex → OpenCode conversion fails.

    The original exception (TOML parse error, missing field, etc.) should
    be chained via ``raise ConversionError(...) from original``.
    """


class MissingWorkspaceError(OpenCodeTradingError):
    """Raised when the target workspace path doesn't exist or is invalid."""


class UnsupportedTradingCodexVersion(OpenCodeTradingError):
    """Raised when the TradingCodex workspace version is not supported."""
