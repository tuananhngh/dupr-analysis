"""Decode synced DUPR data and run the analysis (shared by the website, app.py and analyze.py)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from . import analysis, export, parse

Log = Callable[[str], None]


def _save(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False))


def build_data(profile: dict, raw_matches: list, history: dict, out: Path | None = None, log: Log = print) -> dict:
    """Parse and analyse the matches; return the report data (see export.py) for the website.

    With `out`, also writes the tables as CSV and the data as report.json there.
    """
    player_id = profile.get("id")
    df = parse.parse_matches(raw_matches, player_id)
    log(f"Parsed {len(df)} of {len(raw_matches)} matches for player {player_id}")
    if df.empty:
        raise ValueError("No matches could be parsed. Run `uv run analyze.py --inspect` to see the raw structure.")
    if df["rating_before"].isna().all():
        log("Warning: no per-match ratings found; rating curve comes from rating history only")

    results = []
    for fmt in ("DOUBLES", "SINGLES"):
        if (df["format"] == fmt).any():
            a = analysis.analyze(df, fmt, history.get(fmt))
            results.append(a)
            log(f"{fmt.lower()}: {len(a.matches)} matches, findings: {', '.join(f['id'] for f in a.insights)}; "
                f"tips: {', '.join(t['id'] for t in a.tips) or 'none'}")

    name = profile.get("fullName") or (profile.get("_player") or {}).get("fullName") or f"Player {player_id}"
    data = export.report_data(results, name)
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)
        df.to_csv(out / "matches.csv", index=False)
        for a in results:
            if a.periods is not None:
                a.periods.to_csv(out / f"periods_{a.fmt.lower()}.csv")
            if a.partners is not None:
                a.partners.to_csv(out / f"partners_{a.fmt.lower()}.csv")
        (out / "report.json").write_text(export.to_json(data), encoding="utf-8")
        log(f"Data written to {out}")
    return data


def report_json(payload: str) -> str:
    """What the website calls (in Pyodide): sync payload in, report data as a JSON string out."""
    data = decode_sync_payload(payload)
    history = {k.upper(): parse.parse_rating_history(v) for k, v in (data.get("ratingHistory") or {}).items()}
    return export.to_json(build_data(data["profile"], data["matches"], history, log=lambda m: None))


def demo_json() -> str:
    """Report data for the built-in sample player (the website's "See an example" link)."""
    from . import demo
    profile, matches = demo.generate()
    return export.to_json(build_data(profile, matches, {}, log=lambda m: None))


def load_raw(raw_dir: Path) -> tuple[dict, list, dict]:
    profile = json.loads((raw_dir / "profile.json").read_text())
    matches = json.loads((raw_dir / "matches.json").read_text())
    history = {}
    for kind in ("DOUBLES", "SINGLES"):
        f = raw_dir / f"rating_history_{kind.lower()}.json"
        if f.exists():
            history[kind] = parse.parse_rating_history(json.loads(f.read_text()))
    return profile, matches, history


def decode_sync_payload(payload: str) -> dict:
    """Decode what the bookmarklet sends: 'z' + base64url(gzip(json)) or 'j' + base64url(json)."""
    import base64
    import gzip

    payload = payload.strip()
    if payload.startswith("#"):
        payload = payload[1:]
    if payload.startswith("d="):
        payload = payload[2:]
    tag, body = payload[:1], payload[1:]
    raw = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
    if tag == "z":
        raw = gzip.decompress(raw)
    elif tag != "j":
        raise ValueError("Unrecognised sync data. Run the bookmark again from dashboard.dupr.com.")
    data = json.loads(raw)
    if not isinstance(data, dict) or "matches" not in data or "profile" not in data:
        raise ValueError("Sync data is missing the profile or matches.")
    return data


def save_sync(data: dict, raw_dir: Path, log: Log = print) -> None:
    """Store the data sent by the Sync DUPR bookmark in data/raw/."""
    profile = data["profile"]
    _save(profile, raw_dir / "profile.json")
    _save(data["matches"], raw_dir / "matches.json")
    log(f"Received {len(data['matches'])} matches for {profile.get('fullName', '')} (player {profile.get('id')})")
    for kind, rh in (data.get("ratingHistory") or {}).items():
        _save(rh, raw_dir / f"rating_history_{kind.lower()}.json")
        log(f"Rating history ({kind.lower()}) received")
