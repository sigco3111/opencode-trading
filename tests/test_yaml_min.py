"""Unit tests for the minimal YAML parser used by TradingCodex workspace files."""
from __future__ import annotations

from opencode_trading._yaml_min import parse_yaml


def test_parse_top_level_scalars() -> None:
    text = """
name: head-manager
type: mainagent
"""
    assert parse_yaml(text) == {"name": "head-manager", "type": "mainagent"}


def test_parse_nested_mapping() -> None:
    text = """
parent:
  child: value
  enabled: true
"""
    assert parse_yaml(text) == {"parent": {"child": "value", "enabled": True}}


def test_parse_list_of_scalars() -> None:
    text = """
- a
- b
- c
"""
    assert parse_yaml(text) == ["a", "b", "c"]


def test_parse_preserves_template_placeholder() -> None:
    text = """
template: "{{TRADINGCODEX_MCP_PACKAGE_SPEC}}"
"""
    parsed = parse_yaml(text)
    assert isinstance(parsed, dict)
    assert parsed["template"] == "{{TRADINGCODEX_MCP_PACKAGE_SPEC}}"
