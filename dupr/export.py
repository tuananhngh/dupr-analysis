"""Turn the analyses into plain JSON for the website, which writes all the text and draws the charts.

Only numbers, dates (ISO strings), names from DUPR and codes go out; no sentences. Missing values
are null. The shape is described by `ReportData` in web/src/lib/report/types.ts: keep both in sync.
"""
from __future__ import annotations

import json
import math
from datetime import datetime

import numpy as np
import pandas as pd

from .analysis import Analysis

VERSION = 1   # bump when the shape changes in a way the website must know about


# ------------------------------------------------------------------ JSON helpers
def clean(v):
    """Make a value JSON-safe: NaN -> None, numpy -> Python, timestamps -> ISO strings."""
    if isinstance(v, dict):
        return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [clean(x) for x in v]
    if isinstance(v, (pd.Timestamp, datetime)):
        return None if pd.isna(v) else v.strftime("%Y-%m-%dT%H:%M:%S")
    if isinstance(v, np.generic):
        v = v.item()
    if isinstance(v, float):
        return None if not math.isfinite(v) else round(v, 6)
    if v is pd.NA or v is pd.NaT:
        return None
    return v


def records(df: pd.DataFrame | None, cols: list[str] | None = None, index: str | None = None) -> list[dict]:
    """DataFrame rows as dicts. `index` names the column the index goes into."""
    if df is None or df.empty:
        return []
    d = df.reset_index(names=index) if index else df
    if cols:
        d = d[[c for c in ([index] if index else []) + cols if c in d]]
    return [clean(r) for r in d.to_dict("records")]


# ------------------------------------------------------------------ chart data
def _end_of_day(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """One row per day (the value after that day's last match), so days with several matches
    don't draw vertical spikes."""
    d = df.assign(day=df["date"].dt.normalize())[["day", *cols]]
    return d.groupby("day", as_index=False).last().dropna(subset=cols, how="all")


def win_form(a: Analysis) -> list[dict]:
    """Rolling win % over the last N matches vs the win % the ratings predict, one point per day."""
    df, w = a.matches, a.summary["rolling_window"]
    df = df.assign(expected=df["exp_win"].rolling(w, min_periods=max(3, w // 2)).mean() * 100)
    daily = _end_of_day(df, ["rolling_win_pct", "expected"]).rename(columns={"rolling_win_pct": "actual"})
    return records(daily, ["day", "actual", "expected"])


def monthly_rating_change(a: Analysis) -> pd.DataFrame:
    """Net rating change in each month played (from the rating curve), with the record that month."""
    r, df = a.rating, a.matches
    if r.empty or df.empty:
        return pd.DataFrame()
    month_end = r.set_index("date")["rating"].resample("ME").last().ffill()
    change = month_end.diff()
    change.iloc[0] = month_end.iloc[0] - r["rating"].iloc[0]
    month = df["date"].dt.to_period("M").dt.to_timestamp(how="end").dt.normalize()
    played = df.assign(month=month).groupby("month").agg(matches=("won", "size"), wins=("won", "sum"))
    out = played.join(change.rename("change").rename_axis("month"), how="left")
    out["rating_end"] = month_end.reindex(out.index)
    return out.dropna(subset=["change"])


def monthly_points(a: Analysis) -> pd.DataFrame:
    """Per month: actual vs expected point win %, matches, and the rating change that month."""
    df = a.matches.dropna(subset=["point_share"])
    if df.empty:
        return pd.DataFrame()
    month = df["date"].dt.to_period("M").dt.to_timestamp(how="end").dt.normalize()
    t = df.assign(month=month).groupby("month").agg(
        matches=("won", "size"),
        actual=("point_share", lambda x: x.mean() * 100),
        expected=("exp_point_share", lambda x: x.mean() * 100),
    )
    t["gap"] = t["actual"] - t["expected"]
    rc = monthly_rating_change(a)
    t["rating_change"] = rc["change"].reindex(t.index) if not rc.empty else math.nan
    return t.dropna(subset=["expected"])


def point_form_hits(t: pd.DataFrame) -> dict | None:
    """Does beating the expected points go with rating gains? Months above expectation that raised
    the rating, and months below that lowered it."""
    if t.empty:
        return None
    m = t.dropna(subset=["gap", "rating_change"])
    above, below = m[m["gap"] > 0], m[m["gap"] < 0]
    if len(above) < 2 or len(below) < 2:
        return None
    return {"up": int((above["rating_change"] > 0).sum()), "above": len(above),
            "down": int((below["rating_change"] < 0).sum()), "below": len(below)}


def trend_line(a: Analysis) -> dict | None:
    """End points of the dashed average-progress line on the rating chart."""
    r, s = a.rating, a.summary
    if "trend_per_month" not in s or len(r) < 3:
        return None
    days = (r["date"] - r["date"].iloc[0]).dt.days
    slope = s["trend_per_month"] / 30.44
    intercept = r["rating"].mean() - slope * days.mean()
    return clean({"from": r["date"].iloc[0], "to": r["date"].iloc[-1],
                  "start": intercept, "end": intercept + slope * days.iloc[-1]})


def opponent_level(a: Analysis) -> list[dict]:
    """Opponents' average rating in each match, its rolling mean, and your rating before the match."""
    df, w = a.matches.dropna(subset=["opp_rating_avg"]), a.summary["rolling_window"]
    if len(df) < 5:
        return []
    df = df.assign(opp_rolling=df["opp_rating_avg"].rolling(w, min_periods=3).mean())
    return records(df, ["date", "opp_rating_avg", "opp_rolling", "rating_before", "opponents"])


def game_margins(a: Analysis) -> list[dict]:
    """How many games ended with each score difference (your points minus theirs)."""
    margins = [m for ms in a.matches["game_margins"] for m in ms]
    s = pd.Series(margins, dtype=int).value_counts().sort_index()
    return [{"margin": int(k), "games": int(v)} for k, v in s.items()]


# ------------------------------------------------------------------ one format
MATCH_COLS = ["date", "won", "game_scores", "partner", "opponents", "opp_rating_avg", "rating_diff",
              "rating_before", "rating_after", "rating_impact", "point_share", "exp_win", "scoring", "source"]
AGG_COLS = ["matches", "wins", "win_pct", "point_share", "avg_point_diff", "avg_opp_rating", "rating_gained",
            "exp_win_pct", "avg_impact"]


def _effect(eff: dict) -> dict:
    """Partner / opponent strength groups (0 = much weaker … 4 = much stronger) and the verdict."""
    if not eff:
        return {"measure": None, "groups": [], "verdict": {"status": "no_data"}}
    return {"measure": eff.get("col"), "groups": records(eff.get("table"), index="group"),
            "verdict": clean(eff.get("verdict", {"status": "no_data"}))}


def format_data(a: Analysis) -> dict:
    s, df = a.summary, a.matches
    months = monthly_points(a)
    rc = monthly_rating_change(a)
    return {
        "format": a.fmt,
        "summary": clean(s),
        "close_games": clean(a.close_games),
        "level": clean(a.tip_level),
        "tips": clean(a.tips),
        "findings": clean(a.insights),
        "rating": records(a.rating, ["date", "rating"]),
        "trend": trend_line(a),
        "matches": records(df, [c for c in MATCH_COLS if c in df]),
        "win_form": win_form(a),
        "opponent_level": opponent_level(a),
        "monthly_rating": records(rc, ["matches", "wins", "change", "rating_end"], index="month"),
        "monthly_points": records(months, ["matches", "actual", "expected", "gap", "rating_change"], index="month"),
        "point_form_hits": point_form_hits(months),
        "periods": records(a.periods, [*AGG_COLS, "rating_end"], index="period_end"),
        "margins": game_margins(a),
        "partners": records(a.partners, [*AGG_COLS, "partner_rating", "last_played"], index="partner"),
        "opponents": records(a.opponents, ["matches", "wins", "win_pct", "point_share"], index="opponent"),
        "by_source": records(a.by_source, AGG_COLS, index="source"),
        "by_rest": records(a.by_rest, AGG_COLS, index="rest"),
        "best": records(a.best, index=None),
        "worst": records(a.worst, index=None),
        "partner_effect": _effect(a.partner_effect) if a.fmt == "DOUBLES" else None,
        "opponent_effect": _effect(a.opponent_effect),
    }


def report_data(analyses: list[Analysis], player_name: str) -> dict:
    return {
        "version": VERSION,
        "player": player_name,
        "generated": clean(pd.Timestamp.now()),
        "formats": [format_data(a) for a in analyses if len(a.matches)],
    }


def to_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, allow_nan=False)
