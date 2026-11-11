#!/usr/bin/env python3
"""Rebuild the HTML report from the last sync (data/raw/*.json), without the web app.

  uv run analyze.py            # uses data/raw/*.json
  uv run analyze.py --demo     # synthetic data, to try the report without an account
  uv run analyze.py --inspect  # print the raw structure of one match (to fix parsing)
"""
from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

from dupr import demo
from dupr.pipeline import build_report, load_raw

ROOT = Path(__file__).resolve().parent


def shape(o, depth=0, max_depth=4):
    pad = "  " * depth
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (dict, list)) and depth < max_depth:
                print(f"{pad}{k}:")
                shape(v, depth + 1)
            else:
                print(f"{pad}{k}: {v!r}"[:120])
    elif isinstance(o, list) and o:
        print(f"{pad}[{len(o)} items] first:")
        shape(o[0], depth + 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=str(ROOT / "data" / "raw"))
    ap.add_argument("--out", default=str(ROOT / "output"))
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--inspect", action="store_true")
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    if args.demo:
        profile, raw_matches = demo.generate()
        history = {}
    else:
        try:
            profile, raw_matches, history = load_raw(Path(args.raw))
        except FileNotFoundError:
            print("No data found. Run `uv run app.py` and sync with the ⟳ Sync DUPR bookmark first (or try --demo).")
            return 1

    if args.inspect:
        shape(raw_matches[0] if raw_matches else {})
        return 0

    try:
        path = build_report(profile, raw_matches, history, Path(args.out))
    except ValueError as e:
        print(e)
        return 1
    if not args.no_open:
        webbrowser.open(path.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
