"""Entry point for `python -m opencode_trading`.

Usage:
    python -m opencode_trading convert <workspace> [--to opencode] [--dry-run]
    python -m opencode_trading --version
    python -m opencode_trading --help

Implementation note (for other-PC worker)
----------------------------------------
This file is a thin shim. The actual CLI logic lives in :mod:`opencode_trading.cli`.
`python -m <pkg>` is the universal entry point — it works even when the package
isn't installed (just `cd src && python -m opencode_trading`). Useful for
verifying the package loads correctly during dev without `pip install -e`.
"""
from __future__ import annotations

from opencode_trading.cli import main

if __name__ == "__main__":
    main()
