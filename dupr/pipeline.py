"""Save synced DUPR data and build the report (shared by the web app and analyze.py)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from . import analysis, parse, report

Log = Callable[[str], None]


def _save(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False))


def build_report(profile: dict, raw_matches: list, history: dict, out: Path, log: Log = print) -> Path:
    player_id = profile.get("id")
    df = parse.parse_matches(raw_matches, player_id)
    log(f"Parsed {len(df)} of {len(raw_matches)} matches for player {player_id}")
    if df.empty:
        raise ValueError("No matches could be parsed. Run `uv run analyze.py --inspect` to see the raw structure.")
    if df["rating_before"].isna().all():
        log("Warning: no per-match ratings found; rating curve comes from rating history only")

    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "matches.csv", index=False)
    results = []
    for fmt in ("DOUBLES", "SINGLES"):
        if (df["format"] == fmt).any():
            a = analysis.analyze(df, fmt, history.get(fmt))
            results.append(a)
            log(f"=== {fmt} ===")
            for line in a.insights:
                log(f" • {line}")
            if a.periods is not None:
                a.periods.to_csv(out / f"periods_{fmt.lower()}.csv")
            if a.partners is not None:
                a.partners.to_csv(out / f"partners_{fmt.lower()}.csv")

    name = profile.get("fullName") or (profile.get("_player") or {}).get("fullName") or f"Player {player_id}"
    path = out / "report.html"
    report.render(results, name, path)
    log(f"Report written: {path}")
    return path


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
