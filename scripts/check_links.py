#!/usr/bin/env python3
"""Verify every internal Markdown link resolves (case-sensitive).

A zero-dependency quality gate for a docs repo: catches moved/renamed files and case-only
mismatches that 404 on GitHub's case-sensitive filesystem even though they resolve on macOS.
External (http/https/mailto) links are skipped — this checks repo-internal links only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

LINK = re.compile(r"\]\(([^)]+)\)")


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    broken: list[str] = []
    checked = 0
    for md in root.rglob("*.md"):
        if ".git" in md.parts:
            continue
        for match in LINK.finditer(md.read_text(encoding="utf-8", errors="ignore")):
            link = match.group(1).split("#", 1)[0].strip()
            if not link or link.startswith(("http://", "https://", "mailto:")):
                continue
            checked += 1
            target = (md.parent / link).resolve()
            try:
                ok = target.exists() and target.name in [c.name for c in target.parent.iterdir()]
            except OSError:
                ok = False
            if not ok:
                broken.append(f"{md.relative_to(root)} -> {link}")

    print(f"{checked} internal links checked, {len(broken)} broken")
    for item in broken:
        print(f"  BROKEN: {item}")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
