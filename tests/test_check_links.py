from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_internal_markdown_links_resolve() -> None:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "scripts/check_links.py"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "broken" in result.stdout
