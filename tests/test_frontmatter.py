import pytest

from opencode_trading._frontmatter import Frontmatter, parse_frontmatter, render_frontmatter


def test_parse_basic_frontmatter() -> None:
    text = "---\nname: x\ndescription: y\n---\nbody"
    fm = parse_frontmatter(text)
    assert isinstance(fm, Frontmatter)
    assert fm.name == "x"
    assert fm.description == "y"
    assert fm.extras == {}
    assert fm.body == "body"


def test_parse_missing_frontmatter_raises() -> None:
    with pytest.raises(ValueError):
        parse_frontmatter("body")


def test_parse_extras_collected() -> None:
    text = "---\nname: x\ndescription: y\nauthor: alice\nversion: 1\n---\nbody"
    fm = parse_frontmatter(text)
    assert fm.name == "x"
    assert fm.description == "y"
    assert fm.extras == {"author": "alice", "version": "1"}
    assert fm.body == "body"


def test_render_roundtrip() -> None:
    text = (
        "---\n"
        "name: review-risk\n"
        'description: "Review investment and order risk before drafting or approving an order."\n'
        "---\n\n"
        "# Review Risk\n\nUse through the configured role skill map."
    )

    fm = parse_frontmatter(text)
    rendered = render_frontmatter(fm)
    reparsed = parse_frontmatter(rendered)
    assert reparsed == fm
