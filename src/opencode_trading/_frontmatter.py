"""Minimal YAML-frontmatter parser for opencode-trading v0.2.0.

TradingCodex SKILL.md files and prompts use this format:
    ---
    name: review-risk
    description: "Review investment and order risk before..."
    ---
    # Review Risk
    Use through the configured role skill map...

We only need to extract `name` and `description`; other keys are kept
verbatim in `extras` for round-trip preservation.

The frontmatter must:
- Start with `---` on its own line
- End with `---` on its own line
- Contain `key: value` pairs (one per line, simple form only)
- Values may be quoted (`"..."` or `'...'`) — quotes are stripped
- Values may contain colons (e.g. URLs) if quoted
- Empty body is allowed (frontmatter may end with `---` and no body follows)
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Frontmatter:
    """Parsed YAML frontmatter + markdown body.

    Attributes
    ----------
    name : str
        The `name:` field (required; empty string if missing).
    description : str
        The `description:` field (required; empty string if missing).
    extras : dict[str, str]
        All other frontmatter keys preserved verbatim.
    body : str
        The markdown body after the closing `---`.
    """

    name: str
    description: str
    extras: dict[str, str]
    body: str


_CLOSER_RE = re.compile(r"\n---(?:\r?\n|$)")


def _strip_quotes(val: str) -> str:
    if len(val) >= 2 and ((val[0] == val[-1] == '"') or (val[0] == val[-1] == "'")):
        return val[1:-1]
    return val


def parse_frontmatter(text: str) -> Frontmatter:
    """Parse a markdown file with YAML frontmatter.

    Raises
    ------
    ValueError
        If the text does not start with `---` followed by a newline or if the
        closing `---` is missing.
    """
    if not text.startswith("---\n"):
        raise ValueError("missing leading frontmatter '---' delimiter")

    m = _CLOSER_RE.search(text, 4)
    if not m:
        raise ValueError("missing closing frontmatter '---' delimiter")

    fm_text = text[4:m.start()]
    body = text[m.end():]

    name = ""
    description = ""
    extras: dict[str, str] = {}

    for raw_line in fm_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ':' not in line:
            # skip malformed lines
            continue
        key, _, rest = line.partition(':')
        key = key.strip()
        val = rest.lstrip()
        val = _strip_quotes(val.strip())
        if key == 'name':
            name = val
        elif key == 'description':
            description = val
        else:
            extras[key] = val

    return Frontmatter(name=name, description=description, extras=extras, body=body)


def _quote(val: str) -> str:
    # Escape double quotes and wrap in double quotes for safety
    escaped = val.replace('"', '\\"')
    return f'"{escaped}"'


def render_frontmatter(fm: Frontmatter) -> str:
    """Render a Frontmatter back to `---\n...\n---\n<body>` form.

    Includes `extras` in insertion order (Python 3.7+ dict preserves order).
    """
    parts = ["---"]
    # Always emit name and description (may be empty strings)
    parts.append(f"name: {_quote(fm.name)}")
    parts.append(f"description: {_quote(fm.description)}")
    for k, v in fm.extras.items():
        parts.append(f"{k}: {_quote(v)}")

    header = "\n".join(parts)
    return f"{header}\n---\n{fm.body}"
