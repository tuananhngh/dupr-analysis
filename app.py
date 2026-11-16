#!/usr/bin/env python3
"""Local version of the website: serves the built site (web/build) on your computer.

  cd web && npm install && npm run build      # once, and after changing the site or dupr/*.py
  uv run app.py                               # opens http://127.0.0.1:8000

It is the same site as the online one: the analysis runs in your browser (Python via Pyodide),
and the ⟳ Sync DUPR bookmark you drag from this page sends your data back to this local page.
Your password never goes through it. Each sync is also saved to data/raw/ (for analyze.py and
the scripts). For working on the site, `npm run dev` in web/ is faster.
"""
from __future__ import annotations

import argparse
import threading
import webbrowser
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory

from dupr.pipeline import decode_sync_payload, save_sync

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "web" / "build"
RAW = ROOT / "data" / "raw"

app = Flask(__name__, static_folder=None)


@app.post("/api/save")
def save():
    """The site posts each sync here when it runs locally (see web/src/lib/storage.ts)."""
    try:
        save_sync(decode_sync_payload(request.get_data(as_text=True)), RAW)
    except Exception as e:
        return jsonify(error=f"Could not read the sync data: {e}"), 400
    return jsonify(ok=True)


@app.get("/", defaults={"path": "index.html"})
@app.get("/<path:path>")
def site(path: str):
    if not (SITE / "index.html").exists():
        abort(500, "The site isn't built yet: run `cd web && npm install && npm run build`.")
    return send_from_directory(SITE, path if (SITE / path).is_file() else "index.html")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()
    url = f"http://127.0.0.1:{args.port}"
    if not args.no_open:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    print(f"DUPR analysis running at {url}  (Ctrl+C to stop)")
    app.run(host="127.0.0.1", port=args.port, debug=False)
