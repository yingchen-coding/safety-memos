#!/usr/bin/env python3
"""Validate the public research-evolution contract."""
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "RESEARCH_EVOLUTION.md"
PRIVATE_PATTERN = re.compile(
    r"/Users/|@(?:gmail|outlook|yahoo)\.|"
    r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}",
    re.IGNORECASE,
)
REQUIRED_SECTIONS = (
    "# Research Evolution Log",
    "**Owner:** Ying Chen",
    "## Promotion Standard",
    "## Entry Contract",
    "## Evolution",
    "### Verification",
    "### Boundary",
)


def main() -> int:
    text = LOG.read_text(encoding="utf-8")
    missing = [section for section in REQUIRED_SECTIONS if section not in text]
    if missing:
        raise AssertionError("missing evolution sections: " + ", ".join(missing))
    if PRIVATE_PATTERN.search(text):
        raise AssertionError("research evolution log contains private or personal data")
    if "stronger than human" in text.lower() or "superhuman" in text.lower():
        raise AssertionError("research evolution log contains an unbounded capability claim")
    print("research evolution contract verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
