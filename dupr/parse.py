"""Turn raw DUPR JSON into tidy pandas DataFrames.

The API is undocumented, so parsing is defensive: field names are matched
loosely and anything missing becomes NaN rather than crashing.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

MAX_GAMES = 5


def num(x: Any) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return math.nan
    return v if math.isfinite(v) else math.nan


def rating(x: Any) -> float:
    """DUPR ratings live in ~[1, 8]; anything else (0, -1, 'NR') is unrated."""
    v = num(x)
    return v if 1.0 <= v <= 8.5 else math.nan


def first(d: dict, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, ""):
            return d[k]
    return default


def _pmri_value(sources: list[dict], slot: int, fmt: str, kind: str) -> float:
    """Look up e.g. preMatchDoubleRatingPlayer1 / matchDoubleRatingImpactPlayer1."""
    fmt_word = "single" if fmt == "SINGLES" else "double"
    for src in sources:
        if not isinstance(src, dict):
            continue
        for k, v in src.items():
            kl = k.lower()
            if not kl.endswith(f"player{slot}") or fmt_word not in kl:
                continue
            if kind == "pre" and "prematch" in kl and "impact" not in kl:
                return rating(v)
            if kind == "impact" and "impact" in kl:
                return num(v)
    return math.nan


def _player(team: dict, slot: int) -> dict:
    p = team.get(f"player{slot}")
    return p if isinstance(p, dict) else {}


def _player_rating(team: dict, slot: int, fmt: str) -> float:
    p = _player(team, slot)
    pre = _pmri_value([team.get("preMatchRatingAndImpact"), p.get("preMatchRatingAndImpact"), p],
                      slot, fmt, "pre")
    if not math.isnan(pre):
        return pre
    key = "singles" if fmt == "SINGLES" else "doubles"
    ratings = p.get("ratings") if isinstance(p.get("ratings"), dict) else {}
    return rating(first(p, "preRating", "rating", default=ratings.get(key)))


def _games(team: dict) -> list[float]:
    out = []
    for i in range(1, MAX_GAMES + 1):
        v = num(team.get(f"game{i}"))
        out.append(v if v >= 0 else math.nan)
    return out


def parse_matches(raw: list[dict], player_id: int | str) -> pd.DataFrame:
    pid = str(player_id)
    rows = []
    for m in raw:
        teams = [t for t in (m.get("teams") or []) if isinstance(t, dict)]
        if len(teams) != 2:
            continue
        mine_idx, my_slot = None, None
        for ti, t in enumerate(teams):
            for slot in (1, 2):
                if str(_player(t, slot).get("id")) == pid:
                    mine_idx, my_slot = ti, slot
        if mine_idx is None:
            continue
        me, opp = teams[mine_idx], teams[1 - mine_idx]
        fmt = str(first(m, "format", "eventFormat", default="DOUBLES")).upper()
        fmt = "SINGLES" if "SINGLE" in fmt or not _player(me, 2) else "DOUBLES"
        partner_slot = 2 if my_slot == 1 else 1

        g_me, g_op = _games(me), _games(opp)
        played = [(a, b) for a, b in zip(g_me, g_op) if not (math.isnan(a) or math.isnan(b)) and a + b > 0]
        games_won = sum(a > b for a, b in played)
        games_lost = sum(b > a for a, b in played)

        won = me.get("winner")
        if not isinstance(won, bool):
            won = games_won > games_lost

        pre = _player_rating(me, my_slot, fmt)
        impact = _pmri_value([me.get("preMatchRatingAndImpact"), _player(me, my_slot).get("preMatchRatingAndImpact")],
                             my_slot, fmt, "impact")
        partner_rating = _player_rating(me, partner_slot, fmt) if fmt == "DOUBLES" else math.nan
        opp_ratings = [_player_rating(opp, s, fmt) for s in ((1, 2) if fmt == "DOUBLES" else (1,))]

        partner = _player(me, partner_slot) if fmt == "DOUBLES" else {}
        opps = [_player(opp, s) for s in ((1, 2) if fmt == "DOUBLES" else (1,))]

        rows.append({
            "match_id": first(m, "matchId", "id"),
            "date": pd.to_datetime(first(m, "eventDate", "matchDate", "created"), errors="coerce", utc=True),
            "format": fmt,
            "event": first(m, "eventName", "league", "tournament", default=""),
            "source": str(first(m, "matchSource", "source", "matchType", default="UNKNOWN")).upper(),
            # DUPR tags rally games ("RALLY"); side-out ("SIDE_ONLY") is the default when the tag is missing.
            "scoring": "RALLY" if "RALLY" in str(m.get("matchType") or "").upper() else "SIDE_OUT",
            "confirmed": first(m, "confirmed", default=True),
            "won": bool(won),
            "games_won": games_won,
            "games_lost": games_lost,
            "points_for": float(sum(a for a, _ in played)),
            "points_against": float(sum(b for _, b in played)),
            "game_scores": " ".join(f"{int(a)}-{int(b)}" for a, b in played),
            "game_margins": [a - b for a, b in played],
            "rating_before": pre,
            "rating_impact": impact,
            "partner_id": partner.get("id"),
            "partner": first(partner, "fullName", "name", default=None),
            "partner_rating": partner_rating,
            "opponents": " & ".join(str(first(o, "fullName", "name", default="?")) for o in opps),
            "opponent_ids": [o.get("id") for o in opps],
            "opp_rating_avg": np.nanmean(opp_ratings) if not all(map(math.isnan, opp_ratings)) else math.nan,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates("match_id").reset_index(drop=True)
    df["date"] = df["date"].dt.tz_convert(None)
    df["rating_after"] = df["rating_before"] + df["rating_impact"].fillna(0)
    df.loc[df["rating_before"].isna(), "rating_after"] = np.nan
    df["team_rating"] = np.where(df["format"] == "DOUBLES",
                                 df[["rating_before", "partner_rating"]].mean(axis=1), df["rating_before"])
    df["rating_diff"] = df["team_rating"] - df["opp_rating_avg"]
    total = df["points_for"] + df["points_against"]
    df["point_share"] = np.where(total > 0, df["points_for"] / total, np.nan)
    df["point_diff"] = df["points_for"] - df["points_against"]
    return df


def parse_rating_history(raw: Any) -> pd.DataFrame:
    """Find any list of {date, rating} records anywhere in the payload."""
    found: list[dict] = []

    def walk(o):
        if isinstance(o, list):
            if o and all(isinstance(x, dict) for x in o):
                recs = []
                for x in o:
                    d = first(x, "matchDate", "date", "eventDate", "created", "ratingDate")
                    r = first(x, "rating", "doublesRating", "singlesRating", "newRating", "value")
                    if d is not None and r is not None:
                        recs.append({"date": d, "rating": rating(r)})
                if len(recs) > len(found):
                    found[:] = recs
            for x in o:
                walk(x)
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)

    walk(raw)
    df = pd.DataFrame(found, columns=["date", "rating"])
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True).dt.tz_convert(None)
    return df.dropna().sort_values("date").reset_index(drop=True)
