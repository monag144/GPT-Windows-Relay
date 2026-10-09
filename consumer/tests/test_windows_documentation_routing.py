"""Prevent Windows relay operational docs from pointing to the retired Termux checkout."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINTS = (
    "README.md",
    "docs/index/INDEX_2026-10-07T2034Z_WINDOWS_RELAY_SOURCE_OF_TRUTH.md",
    "docs/windows-relay-established-facts.md",
    "docs/RELAY_OPERATIONAL_RULES.md",
    "windows-relay/TASKS.md",
    "windows-relay/README.md",
)
CANONICAL_REMOTE = "monag144/GPT-Windows-Relay"
CANONICAL_CHECKOUT = r"Downloads\Dev\GPT\GPT-Windows-Relay"


def test_windows_entrypoints_point_to_canonical_repository():
    for relative in ENTRYPOINTS:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert CANONICAL_REMOTE in text, relative
        assert not re.search(r"Canonical local clone[^\n]*GPT-Termux-Relay", text, re.I), relative
        assert not re.search(r"local checkout[^\n]*GPT-Termux-Relay", text, re.I), relative


def test_windows_checkout_and_roadmap_are_indexed():
    index = (ROOT / ENTRYPOINTS[1]).read_text(encoding="utf-8")
    facts = (ROOT / ENTRYPOINTS[2]).read_text(encoding="utf-8")
    backlog = (ROOT / "windows-relay/TASKS.md").read_text(encoding="utf-8")
    for text in (index, facts, backlog):
        assert CANONICAL_CHECKOUT in text
    assert "docs/windows-relay-mission-and-roadmap.md" in index
    assert "windows-relay/TASKS.md" in index


def test_retired_termux_is_historical_not_operational_fallback():
    index = (ROOT / ENTRYPOINTS[1]).read_text(encoding="utf-8")
    assert "Never use it for Windows engineering" in index
    assert "a missing `docs/roadmap/" in index
    assert "nonexistent `engineering_preflight`" in index
