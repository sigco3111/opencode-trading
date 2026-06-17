"""Minimal YAML parser for TradingCodex workspace files.

This module implements a tiny, hand-rolled YAML subset parser tailored to the
specific dialect used by TradingCodex v0.2.0 workspace files (head-manager.yaml,
subagent-registry.yaml, workflow YAMLs, config.yaml). It supports:

- Top-level scalars: strings, integers, booleans, null
- Sequences using leading "- " (2-space indentation for nesting)
- Nested mappings with 2-space indentation
- Quoted strings with single or double quotes (comments inside quotes are
  preserved)
- Preserves template placeholders like "{{TEMPLATE}}" as literal strings

Limitations (intentional): no anchors, tags, flow style, multi-docs, or
advanced YAML features. The parser raises ValueError with line numbers on
malformed input.
"""

from __future__ import annotations

import re
from typing import Any


def _strip_comment(line: str) -> str:
    # Remove comments starting with # unless inside single or double quotes
    in_quote: str | None = None
    escaped = False
    for i, ch in enumerate(line):
        if ch == "\\" and in_quote == '"':
            # allow simple escape inside double quotes
            escaped = not escaped
            continue
        if ch in ('"', "'") and not escaped:
            if in_quote is None:
                in_quote = ch
            elif in_quote == ch:
                in_quote = None
        if ch == "#" and in_quote is None:
            return line[:i].rstrip()
        escaped = False
    return line.rstrip()


def _parse_scalar(raw: str) -> Any:
    s = raw
    if s == "":
        return None
    # quoted
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        # remove surrounding quotes, keep interior verbatim (minimal handling)
        return s[1:-1]

    low = s.lower()
    if low in ("null", "~", "none"):
        return None
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    # integers
    if re.fullmatch(r"-?\d+", s):
        try:
            return int(s)
        except ValueError:
            pass
    # preserve template placeholders as literal strings
    if re.fullmatch(r"\{\{.*\}\}", s):
        return s
    return s


def parse_yaml(text: str) -> Any:
    """Parse a very small YAML subset and return Python objects.

    Args:
        text: YAML content as a string.

    Returns:
        dict, list, or scalar parsed from the input.

    Raises:
        ValueError: on malformed input with approximate line number.
    """
    lines = text.splitlines()
    # stack of frames: each is dict with keys: indent(int), container(list|dict), last_key(str|None)
    stack: list[dict[str, Any]] = [{"indent": -1, "container": None, "last_key": None}]
    root: Any = None

    for idx, raw_line in enumerate(lines, start=1):
        line = _strip_comment(raw_line)
        if not line.strip():
            continue
        # count leading spaces
        m = re.match(r"^( *)", line)
        indent = len(m.group(1)) if m else 0
        if indent % 2 != 0:
            raise ValueError(f"Invalid indent (must be multiple of 2) at line {idx}")
        content = line.lstrip()

        # pop stack entries with indent greater than current (preserve same-level frame)
        while stack and stack[-1]["indent"] > indent:
            stack.pop()
        parent = stack[-1]

        # helper to ensure parent container exists
        if parent["container"] is None:
            # decide root container based on current line
            if content.startswith("- ") or content == "-":
                root = []
                parent["container"] = root
            else:
                root = {}
                parent["container"] = root

        # determine current container (after potential root init)
        cur_container = parent["container"]

        # If parent key is waiting for children and this line is more indented,
        # create the nested container (dict or list) and attach it.
        if parent.get("last_key") and indent > parent["indent"]:
            pending_key = parent["last_key"]
            if parent["container"].get(pending_key) is None:
                # decide container type by looking at the current content
                if content.startswith("- ") or content == "-":
                    parent["container"][pending_key] = []
                else:
                    parent["container"][pending_key] = {}
            # replace current container with the newly created child
            cur_container = parent["container"][pending_key]
            # push a new frame for this nested container so deeper lines attach
            stack.append({"indent": indent, "container": cur_container, "last_key": None})
            # clear the parent's last_key flag
            parent["last_key"] = None

        try:
            if content.startswith("- ") or content == "-":
                # list item
                val_text = content[1:].lstrip()
                # if parent is dict and expecting a value for last_key
                if isinstance(cur_container, dict) and parent.get("last_key"):
                    # convert the dict key to a list
                    key = parent["last_key"]
                    new_list: list[Any] = []
                    cur_container[key] = new_list
                    # update stack so that subsequent siblings attach to this list
                    stack.append({"indent": indent - 1, "container": new_list, "last_key": None})
                    cur_container = new_list

                if isinstance(cur_container, list):
                    if val_text == "":
                        # nested structure for this list item not supported deeply; append None
                        cur_container.append(None)
                    else:
                        cur_container.append(_parse_scalar(val_text))
                else:
                    raise ValueError(f"List item but parent is not a list at line {idx}")
            else:
                # mapping key[: value]
                if ":" not in content:
                    raise ValueError(f"Expected ':' in mapping at line {idx}")
                key, rest = content.split(":", 1)
                key = key.strip()
                val_text = rest.lstrip()
                if isinstance(cur_container, list):
                    raise ValueError(f"Mapping key under list not supported at line {idx}")
                # if value is empty -> placeholder for nested mapping or list
                if val_text == "":
                    # set placeholder None for now; remember this key is waiting for children
                    cur_container[key] = None
                    # push a frame so children with greater indent can attach
                    stack.append({"indent": indent, "container": cur_container, "last_key": key})
                else:
                    # strip quotes/comments already handled
                    cur_container[key] = _parse_scalar(val_text)
                    parent["last_key"] = None
        except ValueError:
            raise

    return root
