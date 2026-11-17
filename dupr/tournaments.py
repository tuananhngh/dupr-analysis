"""Group tournament matches into tournaments.

DUPR sends no tournament id or name. Tournament matches carry a (usually empty)
`tournament` field, and their event name reads "Tournament - Division - Round",
e.g. "Head Nantes Open 2026 - Mixed Double +19 3.0 - Semi Final". We split the
round off the end ("Semi Final", "Poule B"...), then group matches with the same remaining name played
within a few days of each other.
"""
from __future__ import annotations

import re

import pandas as pd

# Round names, only used to strip the round off the event name.
_STAGE_PATTERNS = [  # checked in this order; first match wins
    ("third", r"\b3(e|eme|ème|rd|th)?\b.*place|petite finale|bronze"),
    ("sf", r"semi|demi"),
    ("qf", r"quarter|quart"),
    ("r16", r"round of 16|huiti|1/8"),
    ("knockout", r"phase finale|tableau final|knock ?out|playoff|elimination"),
    ("final", r"\bfinale?s?\b"),
    ("groups", r"poule|pool|group|round robin|phase de groupe"),
]
SAME_TOURNAMENT_DAYS = 3


def stage_of(segment: str) -> str | None:
    s = segment.lower()
    for key, pat in _STAGE_PATTERNS:
        if re.search(pat, s):
            return key
    return None


def split_event(event: str) -> tuple[str, str | None]:
    """'Open X - DH - Quarter Final' -> ('Open X - DH', 'qf'). No round found -> (event, None)."""
    parts = [p.strip() for p in str(event or "").split(" - ") if p.strip()]
    if len(parts) >= 2:
        stage = stage_of(parts[-1])
        if stage:
            return " - ".join(parts[:-1]), stage
    return " - ".join(parts), None


def tournament_matches(df: pd.DataFrame) -> pd.DataFrame:
    """Tournament matches with `tournament_name`, `stage` and a `tournament_id` grouping key."""
    t = df[df["is_tournament"]].copy() if "is_tournament" in df else df.iloc[0:0].copy()
    if t.empty:
        return t
    split = t["event"].map(split_event)
    t["tournament_name"] = split.str[0].replace("", "?")
    t["stage"] = split.str[1]
    # Same name and partner (a doubles draw keeps one partner; organisers sometimes reuse an event
    # name across draws), and no more than a few days since the previous match -> same tournament.
    key = ["tournament_name", "_partner"]
    t["_partner"] = t["partner"].fillna("") if "partner" in t else ""
    t = t.sort_values([*key, "date"])
    gap = t.groupby(key)["date"].diff().dt.days
    t["tournament_id"] = (gap.isna() | (gap > SAME_TOURNAMENT_DAYS)).cumsum()
    return t.drop(columns="_partner")


def tournaments_table(df: pd.DataFrame, agg) -> pd.DataFrame | None:
    """One row per tournament, most recent first. `agg` is the usual per-group stats function."""
    t = tournament_matches(df)
    if t.empty:
        return None
    rows = []
    for _, g in t.groupby("tournament_id"):
        stats = agg(g)
        stats["tournament"] = g["tournament_name"].iloc[0]
        stats["partner"] = g["partner"].iloc[0] if "partner" in g else None
        stats["date"] = g["date"].min()
        stats["losses"] = int(len(g) - g["won"].sum())
        rows.append(stats)
    return pd.DataFrame(rows).sort_values("date", ascending=False).reset_index(drop=True)


def by_context(df: pd.DataFrame, agg) -> pd.DataFrame | None:
    """Tournament matches vs all other matches, when there are some of each."""
    if "is_tournament" not in df or df["is_tournament"].nunique() < 2:
        return None
    ctx = df["is_tournament"].map({True: "tournament", False: "other"})
    return df.assign(context=ctx).groupby("context").apply(agg, include_groups=False).reindex(["tournament", "other"])
