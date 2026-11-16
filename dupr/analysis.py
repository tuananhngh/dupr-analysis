"""Performance analytics on the tidy match table produced by parse.py.

Two reference models say what "should" have happened in each match, given the ratings on court
(details and evidence: MODEL_REPORT.md, sections 3 and 4):

  1. Win model     P(win) = 1 / (1 + 10^(-x / scale)), x = team rating - opponents' rating.
                   `scale` is fitted to the player's own results (default 0.5).
  2. Point model   expected rally share p = 0.5 + slope · x, converted to an expected point share
                   with the match's scoring system (side-out stretches a rally edge into a bigger
                   point edge). `slope` is fitted to the player's own scores (default 0.2).

Both models are fitted per player and per format (doubles / singles), with a default value when
there are too few matches. "Above expectation" in the report means doing better than these models
predict from the ratings.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# ------------------------------------------------------------ model 1: chance of winning a match
# Elo-type logistic curve: P(win) = 1 / (1 + 10^(-gap / scale)). DUPR doesn't publish its model;
# this is only used as a yardstick. Equal teams get 50%, and the two teams' chances add up to 1.
# `scale` is the gap at which the odds are 10:1 (P = 91%): a larger scale means rating gaps matter
# less. It is fitted to each player's own matches by maximum likelihood (fit_expectation_scale);
# with too few matches it falls back to the default 0.5 (a 0.25 edge ~ 76% to win).
EXPECTATION_SCALE = 0.5
# Below 30 matches the fitted scale is too noisy: on random 30-match samples of a 150-match history
# it ranged from 0.47 to 1.15 (10th–90th percentile), around a full-data value of 0.73.
SCALE_MIN_MATCHES = 30
SCALE_BOUNDS = (0.3, 1.5)             # safety limits: 0.3 = near-deterministic, 1.5 = near coin flip
_SCALE_GRID = np.round(np.arange(SCALE_BOUNDS[0], SCALE_BOUNDS[1] + 1e-9, 0.01), 2)


def expected_win_prob(diff: pd.Series | float, scale: float = EXPECTATION_SCALE) -> pd.Series | float:
    """Chance that a team wins the match, from its rating gap (team mean minus opponents' mean).

    Example with scale 0.5: gap 0.10 -> 61%, 0.25 -> 76%, 0.50 -> 91%; a negative gap mirrors these.
    """
    return 1.0 / (1.0 + np.power(10.0, -np.asarray(diff, dtype=float) / scale))


def win_loglik(diff, won, scale: float) -> float:
    """Bernoulli log-likelihood of the results under the win model with this scale.

    Each match is a yes/no trial: a win adds ln P(win), a loss adds ln(1 - P(win)). Higher is a
    better fit. The clip avoids ln(0) for extreme gaps.
    """
    p = np.clip(expected_win_prob(diff, scale), 1e-12, 1 - 1e-12)
    w = np.asarray(won, dtype=float)
    return float((w * np.log(p) + (1 - w) * np.log(1 - p)).sum())


def fit_expectation_scale(df: pd.DataFrame) -> tuple[float, bool]:
    """Scale of the win model for this player: (value, fitted?).

    Maximum likelihood over a grid of scales in SCALE_BOUNDS, on the matches with a known rating
    gap. Falls back to EXPECTATION_SCALE when there are fewer than SCALE_MIN_MATCHES of them, or
    when every match was won (or every one lost), since then the likelihood has no maximum.
    """
    d = df.dropna(subset=["rating_diff"])         # matches with ratings for all players on court
    won = d["won"].astype(float)
    if len(d) < SCALE_MIN_MATCHES or won.nunique() < 2:
        return EXPECTATION_SCALE, False
    # A grid search is enough for one parameter and never fails to converge. A step of 0.01 is far
    # finer than the uncertainty of the estimate (95% interval about ±0.3 at 150 matches).
    ll = [win_loglik(d["rating_diff"], won, s) for s in _SCALE_GRID]
    return float(_SCALE_GRID[int(np.argmax(ll))]), True


# ------------------------------------------------------------ model 2: share of points won
# Points vs rallies. In rally scoring every rally gives a point, so point share = rally share p.
# In side-out scoring only the serving team scores: per serving turn a team expects 2p/(1-p) points
# (2 servers in doubles; the ratio is the same in singles), the other team 2(1-p)/p, so in the long run
#     point share s = p² / (p² + (1-p)²)        i.e.  logit(s) = 2·logit(p).
# Side-out roughly doubles any rally edge in the points (55% of rallies ≈ 60% of points), so the model
# works in rally share and converts back to points for each match's own scoring.
#
# Serve effect: in real pickleball the receiving team wins more rallies. If that effect adds to a
# team's strength in log-odds, it cancels out of the formula above, so it stays exact; p is then the
# team's strength with the serve effect removed. Otherwise the error is under 1 point of point share
# (scripts/sideout_serve_effect.py). Games to 11 rather than "the long run" also cost under 1 point.
def point_share_from_rally_share(p, side_out):
    """Expected share of points from a share of rallies (side_out: bool per match)."""
    p = np.asarray(p, dtype=float)
    return np.where(side_out, p ** 2 / (p ** 2 + (1 - p) ** 2), p)


def rally_share_from_point_share(s, side_out):
    """Inverse of the above: logit(p) = logit(s) / 2, i.e. p = √s / (√s + √(1-s)).

    Measures a match's rally share from its score. Example: side-out 11-7 -> s = 0.611 -> p = 0.556.
    """
    s = np.asarray(s, dtype=float)
    r = np.sqrt(s)
    return np.where(side_out, r / (r + np.sqrt(1 - s)), s)


# Fallback slope when there aren't enough matches to learn it, in rally share per rating point:
# each 0.1 of team-rating edge is worth about 2% of the rallies. With it, a 0.25 edge gives ~76% to
# win one game (rally to 21 or side-out to 11), matching expected_win_prob above.
DEFAULT_RALLIES_PER_RATING = 0.2


def expected_point_share(df: pd.DataFrame) -> pd.Series:
    """Share of points a team 'should' win given the rating gap and the match's scoring system.

    Model: expected rally share = 50% + slope × rating gap (a line through 50% at a gap of 0).
    Each match's point share is first turned into a rally share (side-out matches are "un-stretched"),
    the slope is learned from the player's own matches by least squares, and the prediction is turned
    back into a point share with each match's scoring. Falls back to a default slope.
    """
    # Untagged matches count as side-out: DUPR tags rally matches explicitly (see parse.py).
    side_out = (df["scoring"] != "RALLY").to_numpy() if "scoring" in df else np.ones(len(df), bool)
    # 1. Measure: each match's rally share, from its score.
    rally = rally_share_from_point_share(df["point_share"], side_out)
    ok = (df["rating_diff"].notna() & df["point_share"].notna()).to_numpy()
    x, y = df["rating_diff"].to_numpy(float)[ok], rally[ok] - 0.5
    # 2. Fit: least squares through (gap 0, 50%), slope = Σxy / Σx². The intercept is fixed at 50%
    #    because equal teams must split the rallies (the two teams' shares add up to 1), and so that
    #    a player who beats their ratings shows up as above the line instead of moving it.
    #    Needs 15+ matches and enough spread in the gaps (Σx² > 0.05; below it the standard error is
    #    about as large as the slope). Bounds [0.05, 0.4] guard against nonsense estimates.
    slope = DEFAULT_RALLIES_PER_RATING
    if ok.sum() >= 15 and (x ** 2).sum() > 0.05:
        slope = float(np.clip((x * y).sum() / (x ** 2).sum(), 0.05, 0.4))
    # 3. Predict: rally share from the gap, kept within [5%, 95%] for large gaps (a line would leave
    #    [0, 1]), then back to a point share with each match's own scoring.
    p = (0.5 + slope * df["rating_diff"]).clip(0.05, 0.95)
    return pd.Series(point_share_from_rally_share(p, side_out), index=df.index)


@dataclass
class Analysis:
    fmt: str
    matches: pd.DataFrame
    rating: pd.DataFrame                       # date, rating
    summary: dict = field(default_factory=dict)
    periods: pd.DataFrame | None = None
    partners: pd.DataFrame | None = None
    opponents: pd.DataFrame | None = None
    by_source: pd.DataFrame | None = None
    by_rest: pd.DataFrame | None = None
    by_weekday: pd.DataFrame | None = None
    close_games: dict = field(default_factory=dict)
    best: pd.DataFrame | None = None
    worst: pd.DataFrame | None = None
    insights: list[dict] = field(default_factory=list)     # key findings: {"id": ..., numbers}
    partner_effect: dict = field(default_factory=dict)    # "does a weaker partner drag me down?"
    opponent_effect: dict = field(default_factory=dict)   # "do stronger opponents help my rating?"
    tracker: pd.DataFrame | None = None                   # recent matches vs the ones before
    tips: list[dict] = field(default_factory=list)        # "how to improve" findings
    tip_level: dict = field(default_factory=dict)         # rating band used for the tips


# ------------------------------------------------------------ how to improve
def _wins_match(ms: list[float]) -> bool:
    return sum(m > 0 for m in ms) > len(ms) / 2


def _tip(kind: str, id_: str, **params) -> dict:
    """A finding for the "How to improve" section.

    kind: 'work' (weak spot), 'strength' or 'info'. `id_` names the finding; the website holds the
    wording (title, sentence, advice per rating band) and fills in `params`.
    """
    return {"id": id_, "kind": kind, "params": params}


# Rating bands. Thresholds below have one value per band, in this order. The band names and the
# advice for each band are in the website (web/src/lib/i18n). The thresholds are coaching
# heuristics (what is unusual for a level), not DUPR figures.
BAND_MAX = [3.0, 3.5, 4.0, 4.5, math.inf]

THRESHOLDS = {
    # Share of lost games lost by 7+ points that counts as "too many heavy losses".
    "heavy_loss_pct": (45, 38, 30, 25, 20),
    # Win % after winning game 1 below which closing out is a weak spot.
    "closeout_pct": (60, 65, 70, 75, 78),
    # Win % after losing game 1: at or below = weak spot, at or above = strength.
    "comeback_weak_pct": (15, 18, 20, 22, 25),
    "comeback_strong_pct": (30, 32, 35, 38, 40),
    # Point win % against stronger opponents that counts as competitive.
    "vs_stronger_ok_pct": (44, 45, 46, 47, 48),
}


def level_band(rating: float) -> int:
    """Rating band index (0-4) for a DUPR rating; the middle band if the rating is unknown."""
    if rating is None or math.isnan(rating):
        return 2
    return next(i for i, m in enumerate(BAND_MAX) if rating < m)


def improvement_tips(a: "Analysis") -> list[dict]:
    """Concrete, data-backed things to work on, adapted to the player's rating band.

    Each rule compares the player with themself where possible, needs a minimum number of
    matches, and uses thresholds from the player's rating band. Returns codes and numbers;
    the website writes the sentences and the advice for the band.
    """
    df, c, tips = a.matches, a.close_games, []
    rating = a.summary.get("rating_now", math.nan)
    lvl = level_band(rating)
    a.tip_level = {"band": lvl, "rating": rating}
    t = {k: v[lvl] for k, v in THRESHOLDS.items()}

    margins = [m for ms in df["game_margins"] for m in ms]
    if len(margins) < 10:
        return tips
    game_win = np.mean([m > 0 for m in margins]) * 100

    # 1. Game 1 vs game 2: slow starter or fading?
    g1 = [ms[0] > 0 for ms in df["game_margins"] if len(ms) >= 2]
    g2 = [ms[1] > 0 for ms in df["game_margins"] if len(ms) >= 2]
    if len(g1) >= 10:
        p1, p2 = np.mean(g1) * 100, np.mean(g2) * 100
        if p1 <= p2 - 8:
            tips.append(_tip("work", "slow_starts", game1_pct=p1, game2_pct=p2, matches=len(g1)))
        elif p1 >= p2 + 8:
            tips.append(_tip("work", "fading", game1_pct=p1, game2_pct=p2, matches=len(g1)))

    # 2. After losing / winning the first game
    multi = [ms for ms in df["game_margins"] if len(ms) >= 2]
    lost1 = [ms for ms in multi if ms[0] < 0]
    won1 = [ms for ms in multi if ms[0] > 0]
    if len(lost1) >= 5:
        cb = np.mean([_wins_match(ms) for ms in lost1]) * 100
        if cb >= t["comeback_strong_pct"]:
            tips.append(_tip("strength", "comebacks", pct=cb, matches=len(lost1)))
        elif cb <= t["comeback_weak_pct"]:
            tips.append(_tip("work", "comeback", pct=cb, matches=len(lost1)))
    if len(won1) >= 5:
        co = np.mean([_wins_match(ms) for ms in won1]) * 100
        if co <= t["closeout_pct"]:
            tips.append(_tip("work", "closeout", pct=co, matches=len(won1)))

    # 3. Tight endings, compared with the player's own game win %
    if c.get("close_games", 0) >= 8:
        cw = c["close_win_pct"]
        if cw <= game_win - 8:
            tips.append(_tip("work", "tight_endings", close_pct=cw, game_pct=game_win))
        elif cw >= game_win + 8:
            tips.append(_tip("strength", "clutch", close_pct=cw, game_pct=game_win))

    # 4. Heavy losses
    lost = [m for m in margins if m < 0]
    if len(lost) >= 8:
        heavy = np.mean([m <= -7 for m in lost]) * 100
        if heavy >= t["heavy_loss_pct"]:
            tips.append(_tip("work", "heavy_losses", pct=heavy, threshold=t["heavy_loss_pct"]))

    # 5. Losses you were expected to win. "Expected" = win model gives 60%+ (a gap of about
    #    +0.09 with scale 0.5, +0.13 with scale 0.73), so it adapts to the player's fitted scale.
    exp = df.dropna(subset=["exp_win"])
    upsets = exp[(~exp["won"]) & (exp["exp_win"] >= 0.6)]
    if len(exp) >= 15 and len(upsets) >= 3:
        cost = upsets["rating_impact"].sum(min_count=1)
        tips.append(_tip("work", "favourite_losses", matches=len(upsets),
                         cost=abs(cost) if not math.isnan(cost) and cost < 0 else None))

    # 6. Against stronger opponents (rated 0.1+ above you)
    st = df[df["opp_gap"] > 0.1]
    if len(st) >= 8:
        ps = st["point_share"].mean() * 100
        if ps >= t["vs_stronger_ok_pct"]:
            tips.append(_tip("strength", "vs_stronger_ok", pct=ps, matches=len(st)))
        else:
            tips.append(_tip("work", "vs_stronger_gap", pct=ps, matches=len(st)))

    # 7. Energy: performance by match number within a day
    d = df.assign(day=df["date"].dt.normalize()).sort_values(["date", "match_id"])
    d["nth"] = d.groupby("day").cumcount() + 1
    early, late = d[d["nth"] <= 2], d[d["nth"] >= 4]
    if len(late) >= 8 and len(early) >= 8:
        pe, pl = early["point_share"].mean() * 100, late["point_share"].mean() * 100
        if pl <= pe - 3:
            tips.append(_tip("work", "energy", early_pct=pe, late_pct=pl))

    # 8. Best partner fit
    if a.partners is not None and a.partners["avg_impact"].notna().any():
        p = a.partners[a.partners["matches"] >= 5].dropna(subset=["avg_impact"])
        if len(p) >= 2:
            best = p["avg_impact"].idxmax()
            tips.append(_tip("info", "best_partner", partner=best, avg_impact=p.loc[best, "avg_impact"],
                             matches=int(p.loc[best, "matches"]), win_pct=p.loc[best, "win_pct"]))

    order = {"work": 0, "strength": 1, "info": 2}
    return sorted(tips, key=lambda x: order[x["kind"]])


GAP_BINS = [-np.inf, -0.3, -0.1, 0.1, 0.3, np.inf]


# Rating-gap groups, from much weaker (0) to much stronger (4): 0.3+ below you, 0.1–0.3 below,
# within ±0.1, 0.1–0.3 above, 0.3+ above.
GAP_GROUPS = [0, 1, 2, 3, 4]


def _perf_col(df: pd.DataFrame) -> str:
    """What counts as 'doing well' in a match: DUPR's own rating change if we have it, else
    wins above expectation."""
    return "rating_impact" if df["rating_impact"].notna().sum() >= 5 else "vs_exp"


def gap_effect(df: pd.DataFrame, gap_col: str) -> dict:
    """Group matches by rating gap (partner or opponents vs you) and compare outcomes."""
    d = df.dropna(subset=[gap_col]).copy()
    if len(d) < 5:
        return {}
    col = _perf_col(d)
    d["group"] = pd.cut(d[gap_col], GAP_BINS, labels=GAP_GROUPS)
    table = d.groupby("group", observed=True).agg(
        matches=("won", "size"),
        win_pct=("won", lambda x: x.mean() * 100),
        exp_win_pct=("exp_win", lambda x: x.mean() * 100),
        point_share=("point_share", lambda x: x.mean() * 100),
        avg_impact=(col, "mean"),
        total_impact=(col, "sum"),
    )
    d = d.dropna(subset=[col])
    slope = se = math.nan
    if len(d) >= 8 and d[gap_col].std() > 0:
        x, y = d[gap_col].to_numpy(float), d[col].to_numpy(float)
        slope, intercept = np.polyfit(x, y, 1)
        resid = y - (slope * x + intercept)
        se = math.sqrt((resid ** 2).sum() / (len(x) - 2) / ((x - x.mean()) ** 2).sum())
    return {"table": table, "col": col, "data": d, "gap_col": gap_col,
            "slope_per_0_1": slope * 0.1, "slope_se_per_0_1": se * 0.1}


def _compare(a_: pd.Series, b_: pd.Series) -> tuple[float, float, float, bool]:
    """Mean of a, mean of b, difference, and whether the difference is clear (> 2 standard errors)."""
    ma, mb = a_.mean(), b_.mean()
    se = math.sqrt(a_.var(ddof=1) / len(a_) + b_.var(ddof=1) / len(b_)) if len(a_) > 1 and len(b_) > 1 else math.inf
    diff = ma - mb
    return ma, mb, diff, abs(diff) > 2 * se


def partner_verdict(eff: dict) -> dict:
    """Does a weaker partner pull the player's rating down? Codes and numbers for the website.

    status: 'no_data' (no known partner ratings), 'few' (fewer than 5 matches in a group) or 'ok'.
    measure: 'rating_impact' (rating change per match) or 'vs_exp' (wins above expectation per match).
    """
    if not eff:
        return {"status": "no_data"}
    d, col = eff["data"], eff["col"]
    weak, rest = d[d["partner_gap"] < -0.1], d[d["partner_gap"] >= -0.1]
    if len(weak) < 5 or len(rest) < 5:
        return {"status": "few", "n_weak": len(weak), "n_rest": len(rest)}
    mw, mr, diff, clear = _compare(weak[col], rest[col])
    return {"status": "ok", "measure": col, "n_weak": len(weak), "n_rest": len(rest),
            "mean_weak": mw, "mean_rest": mr, "diff": diff, "clear": clear,
            "win_pct_weak": weak["won"].mean() * 100, "exp_win_pct_weak": weak["exp_win"].mean() * 100}


def opponent_verdict(eff: dict) -> dict:
    """Do stronger opponents help the player's rating? Same structure as partner_verdict, plus the
    average rating change in losses to stronger opponents (loss_mean) and in all losses."""
    if not eff:
        return {"status": "no_data"}
    d, col = eff["data"], eff["col"]
    strong, rest = d[d["opp_gap"] > 0.1], d[d["opp_gap"] <= 0.1]
    if len(strong) < 5 or len(rest) < 5:
        return {"status": "few", "n_strong": len(strong), "n_rest": len(rest)}
    ms, mr, diff, clear = _compare(strong[col], rest[col])
    out = {"status": "ok", "measure": col, "n_strong": len(strong), "n_rest": len(rest),
           "mean_strong": ms, "mean_rest": mr, "diff": diff, "clear": clear,
           "win_pct_strong": strong["won"].mean() * 100, "exp_win_pct_strong": strong["exp_win"].mean() * 100}
    lost = strong[~strong["won"]]
    if col == "rating_impact" and len(lost) >= 3:
        out["loss_mean"] = lost[col].mean()
        out["all_losses_mean"] = d.loc[~d["won"], col].mean()
    return out


def tracker_table(df: pd.DataFrame) -> pd.DataFrame | None:
    """Recent form vs the period before: the numbers to watch for improvement."""
    n = len(df)
    if n < 10:
        return None
    k = min(20, n // 2)
    recent, before = df.iloc[-k:], df.iloc[-2 * k:-k]

    def stats(g: pd.DataFrame) -> dict:
        cp, cw = g["close_played"].sum(), g["close_won"].sum()
        return {
            "Point win %": g["point_share"].mean() * 100,
            "Win %": g["won"].mean() * 100,
            "Expected win %": g["exp_win"].mean() * 100,
            "Wins above expectation": (g["won"].astype(float) - g["exp_win"]).sum(min_count=1),
            "Avg rating change per match": g["rating_impact"].mean(),
            "Close games won % (≤2 pts)": cw / cp * 100 if cp else math.nan,
            "Avg opponent rating vs yours": g["opp_gap"].mean(),
            "Avg partner rating vs yours": g["partner_gap"].mean(),
        }
    t = pd.DataFrame({f"Previous {k} matches": stats(before), f"Last {k} matches": stats(recent)})
    t["Change"] = t.iloc[:, 1] - t.iloc[:, 0]
    return t


# ---------------------------------------------------------------- helpers
def rating_series(df: pd.DataFrame, history: pd.DataFrame | None) -> pd.DataFrame:
    if history is not None and len(history) >= 2:
        return history[["date", "rating"]].copy()
    pts = df[["date", "rating_after"]].rename(columns={"rating_after": "rating"}).dropna()
    first = df.dropna(subset=["rating_before"]).head(1)
    if len(first):
        start = pd.DataFrame({"date": [first["date"].iloc[0] - pd.Timedelta(hours=1)],
                              "rating": [first["rating_before"].iloc[0]]})
        pts = pd.concat([start, pts], ignore_index=True)
    return pts.reset_index(drop=True)


def streaks(won: pd.Series) -> dict:
    best_w = best_l = cur = 0
    last = None
    for w in won:
        cur = cur + 1 if w == last else 1
        last = w
        if w:
            best_w = max(best_w, cur)
        else:
            best_l = max(best_l, cur)
    return {"longest_win_streak": best_w, "longest_loss_streak": best_l,
            "current_streak": f"{cur}{'W' if last else 'L'}" if last is not None else "-",
            "current_streak_n": cur, "current_streak_won": last}


def _agg(g: pd.DataFrame) -> pd.Series:
    return pd.Series({
        "matches": len(g),
        "wins": int(g["won"].sum()),
        "win_pct": g["won"].mean() * 100,
        "point_share": g["point_share"].mean() * 100,
        "avg_point_diff": g["point_diff"].mean(),
        "avg_opp_rating": g["opp_rating_avg"].mean(),
        "avg_rating_diff": g["rating_diff"].mean(),
        "rating_gained": g["rating_impact"].sum(min_count=1),
        "expected_wins": g["exp_win"].sum(min_count=1),
        "exp_win_pct": g["exp_win"].mean() * 100,
        "avg_impact": g["rating_impact"].mean(),
        "partner_gap": g["partner_gap"].mean() if "partner_gap" in g else math.nan,
    })


def _period_freq(span_days: float, n: int) -> tuple[str, str]:
    """pandas frequency and name of the period used to group matches over time."""
    if span_days > 2 * 365 and n >= 40:
        return "QE", "quarter"
    if span_days > 120:
        return "ME", "month"
    return "W", "week"


# ----------------------------------------------------------------- main
def analyze(df: pd.DataFrame, fmt: str, history: pd.DataFrame | None = None) -> Analysis:
    df = df[df["format"] == fmt].copy().reset_index(drop=True)
    a = Analysis(fmt=fmt, matches=df, rating=rating_series(df, history) if len(df) else pd.DataFrame())
    if df.empty:
        return a

    # -------- reference models (fitted on this format's matches only)
    # Win model: the scale is fitted on this player's results; exp_win is each match's predicted
    # chance to win, and won - exp_win sums to "wins above expectation".
    scale, scale_fitted = fit_expectation_scale(df)
    a.summary.update(win_scale=scale, win_scale_fitted=scale_fitted)
    df["exp_win"] = expected_win_prob(df["rating_diff"], scale)
    df.loc[df["rating_diff"].isna(), "exp_win"] = np.nan
    # Point model: expected point share from the gap and the match's scoring system.
    df["exp_point_share"] = expected_point_share(df)
    # Measured rally share of each match (the "Rally win %" tile): strength with the side-out
    # stretch, and the serve effect, removed. Equal to the point share in rally scoring.
    side_out = (df["scoring"] != "RALLY").to_numpy() if "scoring" in df else np.ones(len(df), bool)
    df["rally_share"] = rally_share_from_point_share(df["point_share"], side_out)
    df["match_no"] = np.arange(1, len(df) + 1)
    w = min(10, max(3, len(df) // 5))
    df["rolling_win_pct"] = df["won"].rolling(w, min_periods=w).mean() * 100
    df["rolling_point_share"] = df["point_share"].rolling(w, min_periods=w).mean() * 100
    df["perf_vs_exp"] = (df["won"].astype(float) - df["exp_win"]).fillna(0).cumsum()
    df["rest_days"] = df["date"].diff().dt.days
    df["partner_gap"] = df["partner_rating"] - df["rating_before"]   # < 0: partner weaker than you
    df["opp_gap"] = df["opp_rating_avg"] - df["rating_before"]       # > 0: opponents stronger than you
    df["vs_exp"] = df["won"].astype(float) - df["exp_win"]
    df["close_played"] = [sum(abs(m) <= 2 for m in ms) for ms in df["game_margins"]]
    df["close_won"] = [sum(0 < m <= 2 for m in ms) for ms in df["game_margins"]]
    a.matches = df
    a.summary["rolling_window"] = w

    # -------- summary
    r = a.rating
    span_days = (df["date"].iloc[-1] - df["date"].iloc[0]).days
    s = a.summary
    s.update({
        "matches": len(df), "wins": int(df["won"].sum()), "losses": int((~df["won"]).sum()),
        "win_pct": df["won"].mean() * 100,
        "first_match": df["date"].iloc[0], "last_match": df["date"].iloc[-1], "span_days": span_days,
        "games_won": int(df["games_won"].sum()), "games_lost": int(df["games_lost"].sum()),
        "point_share": df["point_share"].mean() * 100,
        "avg_opp_rating": df["opp_rating_avg"].mean(),
        "avg_partner_rating": df["partner_rating"].mean(),
        "matches_per_month": len(df) / max(span_days / 30.44, 1),
        **streaks(df["won"]),
    })
    if len(r):
        s.update({
            "rating_start": r["rating"].iloc[0], "rating_now": r["rating"].iloc[-1],
            "rating_peak": r["rating"].max(), "rating_peak_date": r.loc[r["rating"].idxmax(), "date"],
            "rating_low": r["rating"].min(),
        })
        s["rating_change"] = s["rating_now"] - s["rating_start"]
        if len(r) >= 3 and span_days > 14:
            x = (r["date"] - r["date"].iloc[0]).dt.days.to_numpy(float)
            s["trend_per_month"] = np.polyfit(x, r["rating"].to_numpy(float), 1)[0] * 30.44
            recent = r[r["date"] >= r["date"].iloc[-1] - pd.Timedelta(days=90)]
            if len(recent) >= 3 and (recent["date"].iloc[-1] - recent["date"].iloc[0]).days > 7:
                xr = (recent["date"] - recent["date"].iloc[0]).dt.days.to_numpy(float)
                s["trend_last_90d_per_month"] = np.polyfit(xr, recent["rating"].to_numpy(float), 1)[0] * 30.44
            before = r[r["date"] <= r["date"].iloc[-1] - pd.Timedelta(days=90)]
            if len(before):
                s["change_last_90d"] = s["rating_now"] - before["rating"].iloc[-1]
    s["rally_share"] = df["rally_share"].mean() * 100
    if df["exp_win"].notna().any():
        s["exp_win_pct"] = df["exp_win"].mean() * 100
        s["expected_wins"] = df["exp_win"].sum()
        s["wins_above_expected"] = (df["won"].astype(float) - df["exp_win"]).sum(min_count=1)

    # -------- periods
    freq, period = _period_freq(span_days, len(df))
    s["period"] = period
    per = df.groupby(pd.Grouper(key="date", freq=freq)).apply(_agg, include_groups=False)
    per = per[per["matches"] > 0]
    if len(r):
        end = r.set_index("date")["rating"].resample(freq).last().ffill()
        per["rating_end"] = end.reindex(per.index)
    per.index.name = "period_end"           # last day of the week / month / quarter
    a.periods = per

    # -------- partners / opponents
    if fmt == "DOUBLES" and df["partner"].notna().any():
        p = df.dropna(subset=["partner"]).groupby("partner")
        a.partners = p.apply(_agg, include_groups=False).assign(
            partner_rating=p["partner_rating"].mean(), last_played=p["date"].max()
        ).sort_values("matches", ascending=False)
    opp_rows = []
    for m in df.itertuples():
        for nm in str(m.opponents).split(" & "):
            opp_rows.append({"opponent": nm, "won": m.won, "point_share": m.point_share})
    if opp_rows:
        od = pd.DataFrame(opp_rows).groupby("opponent").agg(
            matches=("won", "size"), wins=("won", "sum"), win_pct=("won", lambda x: x.mean() * 100),
            point_share=("point_share", lambda x: x.mean() * 100))
        a.opponents = od.sort_values(["matches", "win_pct"], ascending=[False, True])

    # -------- context
    a.by_source = df.groupby("source").apply(_agg, include_groups=False).sort_values("matches", ascending=False)
    rest = pd.cut(df["rest_days"], [-1, 0, 3, 7, 14, np.inf], labels=REST_KEYS)
    a.by_rest = df.assign(rest=rest).dropna(subset=["rest"]).groupby("rest", observed=True).apply(
        _agg, include_groups=False)
    a.by_weekday = df.assign(weekday=df["date"].dt.day_name()).groupby("weekday").apply(
        _agg, include_groups=False).reindex(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]).dropna(how="all")

    # -------- close games & deciders
    margins = [m for ms in df["game_margins"] for m in ms]
    close = [m for m in margins if abs(m) <= 2]
    deciders = [ms[2] for ms in df["game_margins"] if len(ms) == 3]
    a.close_games = {
        "games": len(margins),
        "game_win_pct": np.mean([m > 0 for m in margins]) * 100 if margins else math.nan,
        "close_games": len(close),
        "close_win_pct": np.mean([m > 0 for m in close]) * 100 if close else math.nan,
        "blowouts": sum(abs(m) >= 7 for m in margins),
        "blowout_win_pct": np.mean([m > 0 for m in margins if abs(m) >= 7]) * 100 if any(abs(m) >= 7 for m in margins) else math.nan,
        "deciders": len(deciders),
        "decider_win_pct": np.mean([m > 0 for m in deciders]) * 100 if deciders else math.nan,
        "avg_margin_win": np.mean([m for m in margins if m > 0]) if any(m > 0 for m in margins) else math.nan,
        "avg_margin_loss": np.mean([m for m in margins if m < 0]) if any(m < 0 for m in margins) else math.nan,
    }

    cols = ["date", "won", "game_scores", "partner", "opponents", "rating_diff", "rating_impact"]
    cols = [c for c in cols if c in df]
    if df["rating_impact"].notna().any():
        a.best = df.nlargest(5, "rating_impact")[cols]
        a.worst = df.nsmallest(5, "rating_impact")[cols]

    if fmt == "DOUBLES":
        eff = gap_effect(df, "partner_gap")
        a.partner_effect = {**eff, "verdict": partner_verdict(eff)}
    eff = gap_effect(df, "opp_gap")
    a.opponent_effect = {**eff, "verdict": opponent_verdict(eff)}
    a.tracker = tracker_table(df)
    a.tips = improvement_tips(a)
    a.insights = _insights(a)
    return a


# ---------------------------------------------------------------- key findings
# Each finding is {"id": ..., ...numbers}. The website turns them into sentences (in English or
# French); the choices below (which period is best, what a change means) stay here.

# Rest-time groups (days since the previous match): same day, 1–3, 4–7, 8–14, 15+.
REST_KEYS = ["same_day", "1_3", "4_7", "8_14", "15_plus"]


def _rest_finding(by_rest: pd.DataFrame) -> dict | None:
    br = by_rest[by_rest["matches"] >= 5]
    if len(br) < 2:
        return None
    best, worst = br["win_pct"].idxmax(), br["win_pct"].idxmin()
    b, w = br.loc[best], br.loc[worst]
    if b["win_pct"] - w["win_pct"] < 10:
        meaning = "small"                     # rest time doesn't seem to matter
    elif worst == REST_KEYS[0]:
        meaning = "tiring"                    # same-day matches are the worst: energy
    elif worst == REST_KEYS[-1]:
        meaning = "rhythm"                    # long breaks are the worst: lost rhythm
    elif REST_KEYS.index(best) < REST_KEYS.index(worst):
        meaning = "shorter"                   # shorter gaps suit you better
    else:
        meaning = "longer"                    # more rest suits you better
    return {"id": "rest", "best": best, "best_pct": b["win_pct"], "best_n": int(b["matches"]),
            "worst": worst, "worst_pct": w["win_pct"], "worst_n": int(w["matches"]), "meaning": meaning,
            "few": bool(min(b["matches"], w["matches"]) < 15)}


def _halves_finding(early: pd.DataFrame, late: pd.DataFrame) -> dict:
    """Earlier matches vs recent matches, and what the change means given the opponents' level."""
    w0, w1 = early["won"].mean() * 100, late["won"].mean() * 100
    out = {"id": "halves", "n_early": len(early), "n_late": len(late),
           "early_from": early["date"].iloc[0], "early_to": early["date"].iloc[-1],
           "late_from": late["date"].iloc[0], "late_to": late["date"].iloc[-1],
           "win_early": w0, "win_late": w1,
           "points_early": early["point_share"].mean() * 100, "points_late": late["point_share"].mean() * 100}
    o0, o1 = early["opp_rating_avg"].mean(), late["opp_rating_avg"].mean()
    if math.isnan(o0) or math.isnan(o1):
        return out
    opp_change = o1 - o0
    tougher, easier = opp_change >= 0.05, opp_change <= -0.05
    out.update(opp_early=o0, opp_late=o1, opponents="stronger" if tougher else "weaker" if easier else "same")
    # "Wins vs what the ratings predicted" takes opponent strength into account.
    dw = w1 - w0
    dv = (late["vs_exp"].mean() - early["vs_exp"].mean()) * 100
    if tougher and dw >= 5:
        meaning = "progress_tougher"          # more wins against tougher opponents
    elif tougher and dw > -5:
        meaning = "level_up"                  # similar results against tougher opponents
    elif tougher:
        meaning = "tougher_explains" if not dv <= -5 else "worse_than_tougher"
    elif easier and dw >= 5:
        meaning = "easier_explains" if dv < 5 else "progress_easier"
    elif dw >= 5:
        meaning = "progress"
    elif dw <= -5:
        meaning = "slipped"
    else:
        meaning = "stable"
    out["meaning"] = meaning
    return out


def _impact_finding(df: pd.DataFrame) -> dict | None:
    """Average rating change per win / loss, and per close vs heavy loss."""
    wi = df.loc[df["won"], "rating_impact"].mean()
    li = df.loc[~df["won"], "rating_impact"].mean()
    if math.isnan(wi) or math.isnan(li):
        return None
    out = {"id": "impact", "win": wi, "loss": li}
    # Average points difference per game, to tell close results from heavy ones.
    per_game = df["point_diff"] / df["game_margins"].map(lambda ms: max(len(ms), 1))
    losses = df[~df["won"]].assign(pg=per_game)
    close_l = losses[losses["pg"] >= -3]["rating_impact"].dropna()
    heavy_l = losses[losses["pg"] <= -6]["rating_impact"].dropna()
    if len(close_l) >= 3 and len(heavy_l) >= 3:
        out.update(close_loss=close_l.mean(), heavy_loss=heavy_l.mean())
    return out


def _insights(a: Analysis) -> list[dict]:
    s, df, out = a.summary, a.matches, []
    if "rating_change" in s:
        out.append({"id": "rating_change", "change": s["rating_change"], "start": s["rating_start"],
                    "now": s["rating_now"], "matches": s["matches"], "peak": s["rating_peak"],
                    "peak_date": s["rating_peak_date"]})
    if "trend_per_month" in s:
        f = {"id": "trend", "per_month": s["trend_per_month"]}
        if "trend_last_90d_per_month" in s:
            r = s["trend_last_90d_per_month"]
            f.update(last_90d=r, pace="faster" if r > s["trend_per_month"] + 0.01 else
                     "slower" if r < s["trend_per_month"] - 0.01 else "steady")
        out.append(f)
    per = a.periods
    if per is not None and len(per) >= 2:
        solid = per[per["matches"] >= max(5, per["matches"].median() / 2)]
        if len(solid) >= 2:
            best, worst = solid["win_pct"].idxmax(), solid["win_pct"].idxmin()
            out.append({"id": "best_period", "period": s["period"],
                        "best": best, "best_pct": solid.loc[best, "win_pct"], "best_n": int(solid.loc[best, "matches"]),
                        "worst": worst, "worst_pct": solid.loc[worst, "win_pct"],
                        "worst_n": int(solid.loc[worst, "matches"])})
        half = len(df) // 2
        if half >= 5:
            out.append(_halves_finding(df.iloc[:half], df.iloc[half:]))
    if "wins_above_expected" in s and not math.isnan(s["wins_above_expected"]):
        out.append({"id": "vs_expected", "wins": s["wins"], "expected": s["expected_wins"],
                    "above": s["wins_above_expected"]})
    under = df[df["rating_diff"] <= -0.1]       # team rated 0.1+ below the opponents
    if len(under) >= 3:
        out.append({"id": "underdog", "win_pct": under["won"].mean() * 100, "matches": len(under)})
    c = a.close_games
    if c.get("close_games", 0) >= 5:
        verdict = "clutch" if c["close_win_pct"] >= 55 else "weak" if c["close_win_pct"] <= 45 else "coin_flip"
        out.append({"id": "close_games", "pct": c["close_win_pct"], "games": c["close_games"], "verdict": verdict})
    if c.get("deciders", 0) >= 3:
        out.append({"id": "deciders", "pct": c["decider_win_pct"], "games": c["deciders"]})
    if a.partners is not None:
        p = a.partners[a.partners["matches"] >= 3]
        if len(p) >= 2:
            b, w = p["win_pct"].idxmax(), p["win_pct"].idxmin()
            out.append({"id": "partners", "best": b, "best_pct": p.loc[b, "win_pct"], "best_n": int(p.loc[b, "matches"]),
                        "worst": w, "worst_pct": p.loc[w, "win_pct"], "worst_n": int(p.loc[w, "matches"])})
    if a.by_rest is not None and len(a.by_rest) >= 2:
        f = _rest_finding(a.by_rest)
        if f:
            out.append(f)
    if df["rating_impact"].notna().any():
        f = _impact_finding(df)
        if f:
            out.append(f)
    out.append({"id": "streaks", "longest_win": s["longest_win_streak"], "longest_loss": s["longest_loss_streak"],
                "current": s["current_streak_n"], "current_won": s["current_streak_won"]})
    return out
