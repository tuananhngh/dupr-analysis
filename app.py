#!/usr/bin/env python3
"""Local web app: sync your DUPR matches and view your performance report.

  uv run app.py            # opens http://127.0.0.1:8000

How data gets here: the "Sync DUPR" bookmark. DUPR's API only trusts requests
coming from a logged-in dashboard.dupr.com page, so the bookmark runs there,
with the session you already have, downloads your data and opens this app with
it (see dupr/bookmarklet.js). Your password never goes through this app.
"""
from __future__ import annotations

import argparse
import re
import threading
import traceback
import urllib.parse
import webbrowser
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template_string, request, send_file, url_for

from dupr.pipeline import build_report, decode_sync_payload, load_raw, save_sync

ROOT = Path(__file__).resolve().parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "output"

app = Flask(__name__)
state = {"running": False, "done": False, "error": None, "log": []}
lock = threading.Lock()


def log(msg: str) -> None:
    state["log"].append(f"{datetime.now():%H:%M:%S}  {msg}")


def run_job(synced: dict) -> None:
    try:
        save_sync(synced, RAW, log)
        build_report(*load_raw(RAW), OUT, log)
        state["done"] = True
    except Exception as e:  # surface anything unexpected in the UI
        state["error"] = f"{type(e).__name__}: {e}"
        log(traceback.format_exc())
    finally:
        state["running"] = False


def start(synced: dict) -> None:
    with lock:
        if not state["running"]:
            state.update(running=True, done=False, error=None, log=[])
            threading.Thread(target=run_job, args=(synced,), daemon=True).start()


def bookmarklet_href(app_url: str) -> str:
    """Turn dupr/bookmarklet.js into a one-line javascript: URL pointing at this app."""
    src = (ROOT / "dupr" / "bookmarklet.js").read_text()
    lines = [ln.strip() for ln in src.splitlines() if ln.strip() and not ln.strip().startswith("//")]
    code = " ".join(lines).replace("__TARGET__", app_url.rstrip("/") + "/import")
    code = re.sub(r"\s+", " ", code)
    return "javascript:" + urllib.parse.quote(code, safe="()=;,'.:/{}[]!?*+-_<>&|$@~ ")


# ----------------------------------------------------------------- templates
BASE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>DUPR Analysis</title>
<style>
:root{color-scheme:light;--bg:#f4f3f0;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--line:#e6e5e0;--accent:#2a78d6}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 Inter,-apple-system,"Segoe UI",sans-serif}
main{max-width:580px;margin:48px auto;padding:0 16px}h1{font-size:25px;margin:0 0 4px}p{color:var(--ink2)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:20px 22px;margin:16px 0}
.btn{display:inline-block;margin-top:6px;padding:10px 16px;border-radius:8px;background:var(--accent);color:white;font-weight:600;text-decoration:none}
.small{font-size:13px;color:var(--ink2)}
ol.steps{list-style:none;counter-reset:step;padding:0;margin:14px 0 4px}
ol.steps li{counter-increment:step;position:relative;padding:0 0 18px 42px}
ol.steps li::before{content:counter(step);position:absolute;left:0;top:-2px;width:28px;height:28px;border-radius:50%;
  background:#e3edfa;color:var(--accent);font-weight:700;display:flex;align-items:center;justify-content:center}
a.bm{display:inline-block;margin-top:8px;padding:9px 16px;border-radius:8px;background:var(--accent);color:white;
  font-weight:600;text-decoration:none;cursor:grab}
</style></head><body><main>
<h1>DUPR performance analysis</h1>
{% block body %}{% endblock %}
</main></body></html>"""

INDEX = BASE.replace("{% block body %}{% endblock %}", """
<p>See how your game evolves: rating, form, results against expectation, partners and opponents.</p>
{% if has_report %}
<div class="card"><strong>Your latest report</strong>
<p>Generated {{ report_time }}. To update it, sync again (step 3).</p>
<a class="btn" href="{{ url_for('report') }}">Open report</a></div>
{% endif %}
<div class="card">
<strong>Get your data from DUPR</strong>
<ol class="steps">
<li><b>Once:</b> drag this button to your bookmarks bar
 <span class="small">(show the bar with ⌘⇧B on Mac, Ctrl+Shift+B on Windows)</span><br>
 <a class="bm" href="{{ bookmarklet }}"
    onclick="alert('Drag this button to your bookmarks bar, then click it while you are on dashboard.dupr.com.'); return false;">⟳ Sync DUPR (local)</a></li>
<li>Open <a href="https://dashboard.dupr.com" target="_blank" rel="noopener">dashboard.dupr.com</a> and log in as usual,
 with the code DUPR emails you.</li>
<li>Click the <b>⟳ Sync DUPR (local)</b> bookmark. It downloads your matches, comes back here and builds your report. This bookmark only works while this local app is running; for the website, use the bookmark from the website.</li>
</ol>
<p class="small">You log in on DUPR's own site: your password never goes through this app.
Keep this app running while you sync. Everything stays on your computer.</p>
</div>
""")

IMPORT = BASE.replace("{% block body %}{% endblock %}", """
<div class="card"><strong id="h">Receiving your DUPR data…</strong><p id="m"></p></div>
<script>
(async () => {
  const say = (h, m) => { document.getElementById("h").textContent = h; document.getElementById("m").textContent = m || ""; };
  const hash = location.hash.slice(1);
  if (!hash.startsWith("d=")) { say("No data received", "Click the ⟳ Sync DUPR (local) bookmark while on dashboard.dupr.com."); return; }
  history.replaceState(null, "", location.pathname);
  try {
    const r = await fetch("{{ url_for('api_import') }}", { method: "POST", headers: { "Content-Type": "text/plain" }, body: hash });
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || r.status);
    location.href = "{{ url_for('progress') }}";
  } catch (e) { say("Could not import the data", String(e.message || e)); }
})();
</script>
""")

STATUS = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>DUPR Analysis</title>
<style>body{margin:0;background:#f4f3f0;color:#0b0b0b;font:15px/1.5 Inter,-apple-system,sans-serif}
main{max-width:720px;margin:48px auto;padding:0 16px}pre{background:#111;color:#ddd;padding:12px;border-radius:8px;font-size:12px;min-height:200px;max-height:60vh;overflow:auto;white-space:pre-wrap}
.err{color:#c0392b;font-weight:600}a{color:#2a78d6}</style></head><body><main>
<h1 id="h">Building your report…</h1><p id="msg"></p><pre id="log"></pre>
<script>
async function poll(){
  const s = await (await fetch("{{ url_for('status') }}")).json();
  const pre = document.getElementById("log");
  pre.textContent = s.log.join("\\n"); pre.scrollTop = pre.scrollHeight;
  if (s.error){ document.getElementById("h").textContent = "Something went wrong";
    document.getElementById("msg").innerHTML = '<span class="err"></span> <a href="/">Back</a>';
    document.querySelector(".err").textContent = s.error; return; }
  if (s.done){ location.href = "{{ url_for('report') }}"; return; }
  setTimeout(poll, 800);
}
poll();
</script></main></body></html>"""


# -------------------------------------------------------------------- routes
@app.get("/")
def index():
    rp = OUT / "report.html"
    return render_template_string(
        INDEX, has_report=rp.exists(), bookmarklet=bookmarklet_href(request.host_url),
        report_time=datetime.fromtimestamp(rp.stat().st_mtime).strftime("%d %b %Y at %H:%M") if rp.exists() else "")


@app.get("/import")
def import_page():
    return render_template_string(IMPORT)


@app.post("/api/import")
def api_import():
    try:
        data = decode_sync_payload(request.get_data(as_text=True))
    except Exception as e:
        return jsonify(error=f"Could not read the sync data: {e}"), 400
    start(data)
    return jsonify(ok=True)


@app.get("/progress")
def progress():
    return render_template_string(STATUS)


@app.get("/api/status")
def status():
    return jsonify({k: state[k] for k in ("running", "done", "error", "log")})


@app.get("/report")
def report():
    rp = OUT / "report.html"
    return send_file(rp) if rp.exists() else redirect(url_for("index"))


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
