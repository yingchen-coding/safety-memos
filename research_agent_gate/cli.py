"""Command-line demo for the public research-agent gate kit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .gate import classify_sources, guard_public_output, render_dashboard


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="JSON object with a sources list")
    parser.add_argument("--dashboard", type=Path, required=True, help="output HTML path")
    args = parser.parse_args()
    packet = json.loads(args.input.read_text(encoding="utf-8"))
    classification = classify_sources(packet.get("sources", []))
    release = guard_public_output(packet.get("candidate"))
    args.dashboard.write_text(render_dashboard(classification, release), encoding="utf-8")
    print(json.dumps({"input": classification["verdict"], "release": release["verdict"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
