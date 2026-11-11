"""Performance analytics on the tidy match table produced by parse.py."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# Approximate win-probability model: a 0.25 team-rating edge ~ 76% to win.
# DUPR doesn't publish its model; this is only used as a yardstick.
EXPECTATION_SCALE = 0.5


def expected_win_prob(diff: pd.Series | float) -> pd.Series | float:
    return 1.0 / (1.0 + np.power(10.0, -np.asarray(diff, dtype=float) / EXPECTATION_SCALE))


# Fallback when there aren't enough matches to learn it: each 0.1 of team-rating edge
# is worth about 2.5% of the points.
DEFAULT_POINTS_PER_RATING = 0.25


def expected_point_share(df: pd.DataFrame) -> pd.Series:
    """Share of points a team 'should' win given the rating gap: 50% when even, plus a slope.

    The slope is learned from the player's own matches (a line through 50% at a gap of 0), so it
    reflects how much rating gaps really matter in their games. Falls back to a default slope.
    """
    d = df.dropna(subset=["rating_diff", "point_share"])
    x, y = d["rating_diff"].to_numpy(float), d["point_share"].to_numpy(float) - 0.5
    slope = DEFAULT_POINTS_PER_RATING
    if len(d) >= 15 and (x ** 2).sum() > 0.05:
        slope = float(np.clip((x * y).sum() / (x ** 2).sum(), 0.05, 0.6))
    return (0.5 + slope * df["rating_diff"]).clip(0.05, 0.95)


@dataclass
class Analysis:
    fmt: str
    matches: pd.DataFrame
    rating: pd.DataFrame                       # date, rating
    summary: dict = field(default_factory=dict)
    periods: pd.DataFrame | None = None
    diff_buckets: pd.DataFrame | None = None
    partners: pd.DataFrame | None = None
    opponents: pd.DataFrame | None = None
    by_source: pd.DataFrame | None = None
    by_rest: pd.DataFrame | None = None
    by_weekday: pd.DataFrame | None = None
    close_games: dict = field(default_factory=dict)
    best: pd.DataFrame | None = None
    worst: pd.DataFrame | None = None
    insights: list[str] = field(default_factory=list)
    partner_effect: dict = field(default_factory=dict)    # "does a weaker partner drag me down?"
    opponent_effect: dict = field(default_factory=dict)   # "do stronger opponents help my rating?"
    tracker: pd.DataFrame | None = None                   # recent matches vs the ones before
    tips: list[dict] = field(default_factory=list)        # "how to improve" findings
    tip_level: dict = field(default_factory=dict)         # rating band used for the tips


# ------------------------------------------------------------ how to improve
def _wins_match(ms: list[float]) -> bool:
    return sum(m > 0 for m in ms) > len(ms) / 2


def _tip(kind: str, title: str, finding: str, advice: str) -> dict:
    """kind: 'work' (weak spot), 'strength', or 'info'."""
    return {"kind": kind, "title": title, "finding": finding, "advice": advice}


# Rating bands. Thresholds and advice below have one value per band, in this order.
# The thresholds are coaching heuristics (what is unusual for a level), not DUPR figures.
BANDS = [
    {"label": "below 3.0", "name": "Beginner", "max": 3.0},
    {"label": "3.0–3.5", "name": "Improving", "max": 3.5},
    {"label": "3.5–4.0", "name": "Intermediate", "max": 4.0},
    {"label": "4.0–4.5", "name": "Advanced", "max": 4.5},
    {"label": "4.5 and above", "name": "Expert", "max": math.inf},
]

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

ADVICE = {
    "slow_starts": (
        "Warm up for 10 minutes before your first match: serves, returns and short dink rallies. "
        "In game 1, just aim to get every serve and return in.",
        "Warm up dinks and third-shot drops before you start. In game 1, play the percentages: deep serve, "
        "deep return, get to the kitchen line, no early speed-ups.",
        "Use the warm-up to groove drops and resets. Early in game 1, test the opponents with safe patterns "
        "(middle, backhands) before taking risks.",
        "Warm up like for a tournament: movement, a few fast hands exchanges, then start game 1 with "
        "high-percentage resets until you have read the opponents' tendencies.",
        "Go in with a first-game plan (targets, serve and return patterns) and a short activation routine: "
        "at this level the first points often decide game 1.",
    ),
    "fading": (
        "Your opponents adapt after game 1. Between games, agree on one simple thing with your partner "
        "(for example: keep the ball in the middle) and stick to it. Drink and breathe.",
        "Between games, pick one change together: aim more at the weaker player, return deeper, or move up "
        "to the kitchen faster. Keep your energy up.",
        "Opponents adjust in game 2. Prepare a plan B (stacking, new targets, slower pace with more dinks) "
        "and decide it together between games.",
        "Expect a change after they lose game 1. Spot it in the first points of game 2 and counter quickly: "
        "switch targets, vary pace and height.",
        "Review game 1 with your partner: what worked for them and what they will change. Have counters "
        "ready, and watch your fitness: game 2 is often won on conditioning and adjustments.",
    ),
    "comeback": (
        "After losing a game, slow down: make the opponents hit more balls. Fewer mistakes is the fastest way back.",
        "After a lost game, change one concrete thing: more dinks and drops, aim at the weaker opponent, "
        "and cut return errors.",
        "After a lost game, find the 1–2 patterns that cost you points and change them: stack or switch sides, "
        "slow the pace, target the middle.",
        "Treat game 2 as a new match: change targets, use resets to break their rhythm, and take a time-out "
        "early if they go on a run.",
        "Prepare a plan B and C in advance (stacking variations, serve and return changes), use time-outs "
        "tactically and reset mentally between games.",
    ),
    "closeout": (
        "After winning game 1, keep doing exactly what worked: same targets, same patience.",
        "Don't relax after game 1: start game 2 with the same focus and tactics until the opponents change something.",
        "In game 2, watch for the opponents' adjustment (new targets, stacking, more speed) and adapt early "
        "instead of waiting to fall behind.",
        "Expect the opponents to change after game 1 and stay one step ahead: vary your serves and returns "
        "early in game 2.",
        "Keep the pressure on: opponents at this level adapt fast, so change patterns before they settle "
        "and don't give away cheap points.",
    ),
    "tight_endings": (
        "At 8-8 and later, just get your serve and return deep and in, then dink until someone makes a "
        "mistake. Practise games that start at 7-7.",
        "Practise games that start at 8-8. At game point, play your safest pattern: deep serve, deep return, "
        "drop, dink, and no risky speed-ups.",
        "In tight endings, don't speed up balls below the net; reset instead. Agree with your partner on a "
        "go-to pattern for big points.",
        "At the end of games, attack only high balls, take a time-out to reset when needed, and rely on "
        "your most reliable patterns.",
        "Work on your routine between points (breathing, a set reset) and on a few clutch patterns you "
        "trust. Note which opponent tightens up on big points.",
    ),
    "heavy_losses": (
        "When you start losing points in a row, slow down: high, deep returns and safe dinks. Take a time-out "
        "to break their run.",
        "Stop runs early: take a time-out after 3–4 points in a row, then play safer (deep returns, "
        "third-shot drops) to keep the game close.",
        "When a game slips away, break their momentum: time-out, change formation (stack) or targets. "
        "Keeping the score close protects your rating.",
        "Find what produces their runs (your speed-ups being countered, one side being targeted) and shut "
        "it down with resets and patience.",
        "Heavy losses at this level usually come from a matchup problem: prepare counters for that style "
        "and take time-outs earlier.",
    ),
    "favourite_losses": (
        "Against weaker teams keep it simple: get the ball in and let them make the mistakes. "
        "Don't try difficult shots.",
        "Against weaker teams stay patient: dink and drop until there's a real opening, and don't get "
        "dragged into sloppy rallies.",
        "As the favourite, keep unforced errors low: play the percentages and only speed up high balls.",
        "Stay focused on the process against weaker teams: target the weaker player, keep errors low and "
        "close out games firmly.",
        "Losing as the favourite costs a lot of rating at this level: take every rated match seriously and "
        "don't experiment in them.",
    ),
    "vs_stronger_gap": (
        "Stronger players punish high balls. Practise keeping your dinks low and your returns deep, and play "
        "with better players when you can.",
        "Drill third-shot drops and dinks: better players attack anything high. Play up regularly to get "
        "used to the pace.",
        "Work on resets in the transition zone and on blocking hard drives: that's where stronger players "
        "win their points.",
        "Work on fast hands exchanges, counter-attacks and patience in long dink rallies; play up in drills "
        "and open play.",
        "Study matches against top players (video if possible): shot selection, positioning and variety. "
        "Train with stronger partners.",
    ),
    "energy": (
        "Eat and drink between matches and take short breaks. Play fewer matches in a row if you get tired.",
        "Pace yourself in long sessions: water, a snack and a short rest between matches, or fewer matches per day.",
        "Pace yourself in long sessions: water, a snack and a short rest between matches, or fewer matches per day.",
        "Work on fitness and recovery between matches (hydration, food, mobility), and plan your session load "
        "before events.",
        "Work on fitness and recovery between matches (hydration, food, mobility), and plan your session load "
        "before events.",
    ),
}


def level_band(rating: float) -> int:
    """Index in BANDS for a DUPR rating; the middle band if the rating is unknown."""
    if rating is None or math.isnan(rating):
        return 2
    return next(i for i, b in enumerate(BANDS) if rating < b["max"])


def improvement_tips(a: "Analysis") -> list[dict]:
    """Concrete, data-backed things to work on, adapted to the player's rating band.

    Each rule compares the player with themself where possible, needs a minimum number of
    matches, and uses thresholds and advice from the player's rating band.
    """
    df, c, tips = a.matches, a.close_games, []
    rating = a.summary.get("rating_now", math.nan)
    lvl = level_band(rating)
    a.tip_level = {**BANDS[lvl], "rating": rating}
    t = {k: v[lvl] for k, v in THRESHOLDS.items()}
    adv = {k: v[lvl] for k, v in ADVICE.items()}

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
            tips.append(_tip("work", "Slow starts",
                             f"You win {p1:.0f}% of first games but {p2:.0f}% of second games "
                             f"({len(g1)} multi-game matches).", adv["slow_starts"]))
        elif p1 >= p2 + 8:
            tips.append(_tip("work", "Fading after game 1",
                             f"You win {p1:.0f}% of first games but only {p2:.0f}% of second games "
                             f"({len(g1)} multi-game matches).", adv["fading"]))

    # 2. After losing / winning the first game
    multi = [ms for ms in df["game_margins"] if len(ms) >= 2]
    lost1 = [ms for ms in multi if ms[0] < 0]
    won1 = [ms for ms in multi if ms[0] > 0]
    if len(lost1) >= 5:
        cb = np.mean([_wins_match(ms) for ms in lost1]) * 100
        if cb >= t["comeback_strong_pct"]:
            tips.append(_tip("strength", "Comebacks",
                             f"After losing the first game you still win {cb:.0f}% of matches ({len(lost1)} matches).",
                             "Keep doing what you do between games: your adjustments work."))
        elif cb <= t["comeback_weak_pct"]:
            tips.append(_tip("work", "Hard to come back",
                             f"After losing the first game you win only {cb:.0f}% of matches ({len(lost1)} matches).",
                             adv["comeback"]))
    if len(won1) >= 5:
        co = np.mean([_wins_match(ms) for ms in won1]) * 100
        if co <= t["closeout_pct"]:
            tips.append(_tip("work", "Closing out matches",
                             f"After winning the first game you go on to win only {co:.0f}% of matches "
                             f"({len(won1)} matches).", adv["closeout"]))

    # 3. Tight endings, compared with the player's own game win %
    if c.get("close_games", 0) >= 8:
        cw = c["close_win_pct"]
        if cw <= game_win - 8:
            tips.append(_tip("work", "Tight endings",
                             f"You win {cw:.0f}% of close games (decided by 2 points or fewer) vs {game_win:.0f}% "
                             "of all your games.", adv["tight_endings"]))
        elif cw >= game_win + 8:
            tips.append(_tip("strength", "Clutch in tight endings",
                             f"You win {cw:.0f}% of close games vs {game_win:.0f}% of all your games.",
                             "You handle pressure well; the gains are earlier in the game, before it gets tight."))

    # 4. Heavy losses
    lost = [m for m in margins if m < 0]
    if len(lost) >= 8:
        heavy = np.mean([m <= -7 for m in lost]) * 100
        if heavy >= t["heavy_loss_pct"]:
            tips.append(_tip("work", "Heavy losses",
                             f"{heavy:.0f}% of the games you lose are by 7 points or more "
                             f"(more than usual for your level, where {t['heavy_loss_pct']}% is already high).",
                             adv["heavy_losses"]))

    # 5. Losses you were expected to win
    exp = df.dropna(subset=["exp_win"])
    upsets = exp[(~exp["won"]) & (exp["exp_win"] >= 0.6)]
    if len(exp) >= 15 and len(upsets) >= 3:
        cost = upsets["rating_impact"].sum(min_count=1)
        cost_txt = f", costing {abs(cost):.3f} rating in total" if not math.isnan(cost) and cost < 0 else ""
        tips.append(_tip("work", "Losses as the favourite",
                         f"You lost {len(upsets)} matches where your team was the clear favourite "
                         f"(60%+ expected){cost_txt}.", adv["favourite_losses"]))

    # 6. Against stronger opponents (rated 0.1+ above you)
    st = df[df["opp_gap"] > 0.1]
    if len(st) >= 8:
        ps = st["point_share"].mean() * 100
        if ps >= t["vs_stronger_ok_pct"]:
            tips.append(_tip("strength", "Competitive against stronger players",
                             f"Against stronger opponents you still win {ps:.0f}% of points ({len(st)} matches).",
                             "Keep playing up regularly: close scores against better players raise your rating."))
        else:
            tips.append(_tip("work", "Gap against stronger players",
                             f"Against stronger opponents you win {ps:.0f}% of points ({len(st)} matches).",
                             adv["vs_stronger_gap"]))

    # 7. Energy: performance by match number within a day
    d = df.assign(day=df["date"].dt.normalize()).sort_values(["date", "match_id"])
    d["nth"] = d.groupby("day").cumcount() + 1
    early, late = d[d["nth"] <= 2], d[d["nth"] >= 4]
    if len(late) >= 8 and len(early) >= 8:
        pe, pl = early["point_share"].mean() * 100, late["point_share"].mean() * 100
        if pl <= pe - 3:
            tips.append(_tip("work", "Energy over a long session",
                             f"Point win % drops from {pe:.0f}% in your first 2 matches of a day to {pl:.0f}% "
                             "from the 4th match on.", adv["energy"]))

    # 8. Best partner fit
    if a.partners is not None and a.partners["avg_impact"].notna().any():
        p = a.partners[a.partners["matches"] >= 5].dropna(subset=["avg_impact"])
        if len(p) >= 2:
            best = p["avg_impact"].idxmax()
            tips.append(_tip("info", "Your best partnership",
                             f"With {best} you gain {p.loc[best, 'avg_impact']:+.3f} rating per match on average "
                             f"({int(p.loc[best, 'matches'])} matches, {p.loc[best, 'win_pct']:.0f}% wins).",
                             "Look at what works in this pairing (who covers the middle, who attacks) and bring "
                             "it to your other partnerships."))

    order = {"work": 0, "strength": 1, "info": 2}
    return sorted(tips, key=lambda x: order[x["kind"]])


GAP_BINS = [-np.inf, -0.3, -0.1, 0.1, 0.3, np.inf]


def _gap_labels(who: str) -> list[str]:
    return [f"Much weaker {who} (0.3+ below you)", f"Weaker {who} (0.1–0.3 below)", f"Similar {who} (±0.1)",
            f"Stronger {who} (0.1–0.3 above)", f"Much stronger {who} (0.3+ above)"]


def _perf_col(df: pd.DataFrame) -> tuple[str, str]:
    """What counts as 'doing well' in a match: DUPR's own rating change if we have it."""
    if df["rating_impact"].notna().sum() >= 5:
        return "rating_impact", "rating change per match"
    return "vs_exp", "wins above expectation per match"


def gap_effect(df: pd.DataFrame, gap_col: str, who: str) -> dict:
    """Group matches by rating gap (partner or opponents vs you) and compare outcomes."""
    d = df.dropna(subset=[gap_col]).copy()
    if len(d) < 5:
        return {}
    col, col_label = _perf_col(d)
    d["bucket"] = pd.cut(d[gap_col], GAP_BINS, labels=_gap_labels(who))
    table = d.groupby("bucket", observed=True).agg(
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
    return {"table": table, "col": col, "col_label": col_label, "data": d, "gap_col": gap_col,
            "slope_per_0_1": slope * 0.1, "slope_se_per_0_1": se * 0.1}


def _compare(a_: pd.Series, b_: pd.Series) -> tuple[float, float, float, str]:
    """Mean of a, mean of b, difference, and how clear the difference is."""
    ma, mb = a_.mean(), b_.mean()
    se = math.sqrt(a_.var(ddof=1) / len(a_) + b_.var(ddof=1) / len(b_)) if len(a_) > 1 and len(b_) > 1 else math.inf
    diff = ma - mb
    clarity = "clear" if abs(diff) > 2 * se else "unclear"
    return ma, mb, diff, clarity


def _move(v: float, col: str) -> str:
    """'gain 0.004 rating' / 'lose 0.009 rating' (or the same in wins vs expected)."""
    if col == "rating_impact":
        return f"gain {v:.3f} rating" if v >= 0 else f"lose {abs(v):.3f} rating"
    return f"win {v:.2f} more matches than expected" if v >= 0 else f"win {abs(v):.2f} fewer matches than expected"


def _vs_prediction(actual: float, predicted: float) -> str:
    if actual >= predicted + 3:
        return f"more than the {predicted:.0f}% the ratings predict"
    if actual <= predicted - 3:
        return f"less than the {predicted:.0f}% the ratings predict"
    return f"about what the ratings predict ({predicted:.0f}%)"


def partner_verdict(eff: dict) -> dict:
    if not eff:
        return {"answer": "Not enough doubles matches with known partner ratings yet.", "detail": ""}
    d, col = eff["data"], eff["col"]
    weak, rest = d[d["partner_gap"] < -0.1], d[d["partner_gap"] >= -0.1]
    if len(weak) < 5 or len(rest) < 5:
        return {"answer": f"Not enough matches yet to tell ({len(weak)} with weaker partners, "
                          f"{len(rest)} with similar or stronger ones; need 5 of each).", "detail": ""}
    mw, mr, diff, clarity = _compare(weak[col], rest[col])
    wins_w, exp_w = weak["won"].mean() * 100, weak["exp_win"].mean() * 100
    answer = (f"With weaker partners you {_move(mw, col)} per match on average ({len(weak)} matches); "
              f"with similar or stronger partners you {_move(mr, col)} ({len(rest)} matches).")
    if clarity == "clear":
        answer += (" So weaker partners are pulling your rating down." if diff < 0 else
                   " So weaker partners are not pulling you down: you actually do better with them.")
    else:
        answer += (f" Weaker partners look {'slightly worse' if diff < 0 else 'no worse'} for your rating, but the "
                   "difference is small compared with normal match-to-match variation, so it's not a firm conclusion yet.")
    detail = (f"With weaker partners you win {wins_w:.0f}% of matches, {_vs_prediction(wins_w, exp_w)}. "
              "DUPR already expects less from your team when your partner is weaker, so a weaker partner only "
              "costs you rating if your team does worse than that lower expectation.")
    return {"answer": answer, "detail": detail}


def opponent_verdict(eff: dict) -> dict:
    if not eff:
        return {"answer": "Not enough matches with known opponent ratings yet.", "detail": ""}
    d, col = eff["data"], eff["col"]
    strong, rest = d[d["opp_gap"] > 0.1], d[d["opp_gap"] <= 0.1]
    if len(strong) < 5 or len(rest) < 5:
        return {"answer": f"Not enough matches yet to tell ({len(strong)} against stronger opponents, "
                          f"{len(rest)} against similar or weaker ones; need 5 of each).", "detail": ""}
    ms, mr, diff, clarity = _compare(strong[col], rest[col])
    answer = (f"Against stronger opponents you {_move(ms, col)} per match on average ({len(strong)} matches); "
              f"against similar or weaker opponents you {_move(mr, col)} ({len(rest)} matches).")
    if clarity == "clear":
        answer += (" So playing stronger opponents is helping your rating." if diff > 0 else
                   " So far, playing stronger opponents has cost you rating.")
    else:
        answer += (f" Playing up looks {'better' if diff > 0 else 'worse'} for your rating, but the difference is "
                   "small compared with normal match-to-match variation, so it's not a firm conclusion yet.")
    ws, es = strong["won"].mean() * 100, strong["exp_win"].mean() * 100
    detail = f"You win {ws:.0f}% of your matches against stronger opponents, {_vs_prediction(ws, es)}."
    lost = strong[~strong["won"]]
    if col == "rating_impact" and len(lost) >= 3:
        ml = lost[col].mean()
        all_losses = d.loc[~d["won"], col].mean()
        if ml >= 0:
            detail += (f" Even when you lose to them, you still gain {ml:.3f} rating on average: DUPR expects you "
                       "to lose those matches, so a close score is enough to raise your rating.")
        else:
            compare = (f", less than an average loss ({abs(all_losses):.3f})"
                       if abs(ml) < abs(all_losses) else "")
            detail += (f" When you lose to them, you lose {abs(ml):.3f} rating on average{compare}: DUPR expects "
                       "those losses, so they cost little, and a close score can even turn one into a small gain.")
    return {"answer": answer, "detail": detail}


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


def _streak_sentence(s: dict) -> str:
    text = (f"Your longest winning streak is {s['longest_win_streak']} matches in a row, and your longest "
            f"losing streak is {s['longest_loss_streak']}.")
    n, won = s.get("current_streak_n", 0), s.get("current_streak_won")
    if won is None or not n:
        return text
    if n == 1:
        return text + f" You {'won' if won else 'lost'} your last match."
    return text + f" Right now you have {'won' if won else 'lost'} your last {n} matches in a row."


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
    if span_days > 2 * 365 and n >= 40:
        return "QE", "Quarter"
    if span_days > 120:
        return "ME", "Month"
    return "W", "Week"


# ----------------------------------------------------------------- main
def analyze(df: pd.DataFrame, fmt: str, history: pd.DataFrame | None = None) -> Analysis:
    df = df[df["format"] == fmt].copy().reset_index(drop=True)
    a = Analysis(fmt=fmt, matches=df, rating=rating_series(df, history) if len(df) else pd.DataFrame())
    if df.empty:
        return a

    df["exp_win"] = expected_win_prob(df["rating_diff"])
    df.loc[df["rating_diff"].isna(), "exp_win"] = np.nan
    df["exp_point_share"] = expected_point_share(df)
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
    if df["exp_win"].notna().any():
        s["expected_wins"] = df["exp_win"].sum()
        s["wins_above_expected"] = (df["won"].astype(float) - df["exp_win"]).sum(min_count=1)

    # -------- periods
    freq, label = _period_freq(span_days, len(df))
    s["period_label"] = label
    per = df.groupby(pd.Grouper(key="date", freq=freq)).apply(_agg, include_groups=False)
    per = per[per["matches"] > 0]
    if len(r):
        end = r.set_index("date")["rating"].resample(freq).last().ffill()
        per["rating_end"] = end.reindex(per.index)
    fmt_label = {"QE": lambda d: f"{d.year} Q{d.quarter}", "ME": lambda d: f"{d:%b %Y}",
                 "W": lambda d: f"wk {d:%d %b %Y}"}[freq]
    per.index = pd.Index([fmt_label(d) for d in per.index], name=label)
    a.periods = per

    # -------- by rating difference
    bins = [-np.inf, -0.5, -0.25, -0.1, 0.1, 0.25, 0.5, np.inf]
    labels = ["< -0.50", "-0.50 to -0.25", "-0.25 to -0.10", "even (±0.10)",
              "+0.10 to +0.25", "+0.25 to +0.50", "> +0.50"]
    d = df.dropna(subset=["rating_diff"])
    if len(d):
        d = d.assign(bucket=pd.cut(d["rating_diff"], bins, labels=labels))
        a.diff_buckets = d.groupby("bucket", observed=True).agg(
            matches=("won", "size"), win_pct=("won", lambda x: x.mean() * 100),
            expected_pct=("exp_win", lambda x: x.mean() * 100),
            point_share=("point_share", lambda x: x.mean() * 100))

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
    rest = pd.cut(df["rest_days"], [-1, 0, 3, 7, 14, np.inf], labels=list(REST_PHRASES))
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
        eff = gap_effect(df, "partner_gap", "partner")
        a.partner_effect = {**eff, **partner_verdict(eff)}
    eff = gap_effect(df, "opp_gap", "opponents")
    a.opponent_effect = {**eff, **opponent_verdict(eff)}
    a.tracker = tracker_table(df)
    a.tips = improvement_tips(a)
    a.insights = _insights(a)
    return a


# ---------------------------------------------------------------- insights
def _pct(x):
    return f"{x:.0f}%"


# Rest-time groups: table label -> how to say it in a sentence.
REST_PHRASES = {
    "Same day as previous match": "when you already played earlier the same day",
    "1–3 days after previous match": "when your previous match was 1–3 days before",
    "4–7 days after previous match": "when your previous match was 4–7 days before",
    "8–14 days after previous match": "when your previous match was 1–2 weeks before",
    "15+ days after previous match": "after a break of more than 2 weeks",
}
REST_ORDER = list(REST_PHRASES)


def _rest_sentence(by_rest: pd.DataFrame) -> str:
    br = by_rest[by_rest["matches"] >= 5]
    if len(br) < 2:
        return ""
    best, worst = br["win_pct"].idxmax(), br["win_pct"].idxmin()
    b, w = br.loc[best], br.loc[worst]
    text = (f"Time between matches: you win most often {REST_PHRASES[best]} ({b['win_pct']:.0f}% of "
            f"{int(b['matches'])} matches) and least often {REST_PHRASES[worst]} ({w['win_pct']:.0f}% of "
            f"{int(w['matches'])} matches).")
    if b["win_pct"] - w["win_pct"] < 10:
        return text + " The difference is small, so rest time doesn't seem to matter much for you."
    if worst == REST_ORDER[0]:
        text += " Playing several matches in one session may tire you: watch your energy in later matches."
    elif worst == REST_ORDER[-1]:
        text += " Long breaks seem to cost you rhythm: after time off, a practice session before competing may help."
    elif REST_ORDER.index(best) < REST_ORDER.index(worst):
        text += " Shorter gaps between matches seem to suit you better than longer ones."
    else:
        text += " A bit more rest between matches seems to suit you better than playing very often."
    if min(b["matches"], w["matches"]) < 15:
        text += " Few matches in these groups, so treat this as a hint, not a rule."
    return text


def _span(g: pd.DataFrame) -> str:
    a_, b_ = g["date"].iloc[0], g["date"].iloc[-1]
    return f"{a_:%b %Y}" if (a_.year, a_.month) == (b_.year, b_.month) else f"{a_:%b %Y}–{b_:%b %Y}"


def _halves_sentence(early: pd.DataFrame, late: pd.DataFrame) -> str:
    """Earlier matches vs recent matches, in plain words, with what it means."""
    w0, w1 = early["won"].mean() * 100, late["won"].mean() * 100
    p0, p1 = early["point_share"].mean() * 100, late["point_share"].mean() * 100
    o0, o1 = early["opp_rating_avg"].mean(), late["opp_rating_avg"].mean()
    head = (f"Your first {len(early)} matches ({_span(early)}) compared with your last {len(late)} "
            f"({_span(late)}): you won {w0:.0f}% of matches then, {w1:.0f}% now; "
            f"{p0:.0f}% of points then, {p1:.0f}% now.")
    if math.isnan(o0) or math.isnan(o1):
        return head
    opp_change = o1 - o0
    if opp_change >= 0.05:
        opp = f" Your opponents are also stronger now (average rating {o0:.2f} → {o1:.2f})."
    elif opp_change <= -0.05:
        opp = f" Your opponents are weaker now (average rating {o0:.2f} → {o1:.2f})."
    else:
        opp = f" Your opponents' level is about the same (average rating around {o1:.2f})."

    # "Wins vs what the ratings predicted" takes opponent strength into account.
    dw = w1 - w0
    dv = (late["vs_exp"].mean() - early["vs_exp"].mean()) * 100
    tougher, easier = opp_change >= 0.05, opp_change <= -0.05
    if tougher and dw >= 5:
        meaning = " You win more often even though your opponents are tougher: clear progress."
    elif tougher and dw > -5:
        meaning = " Getting similar results against tougher opponents means your level has gone up."
    elif tougher:
        meaning = (" You win less, but mostly because your opponents are tougher: for their level you are doing "
                   "about as well as before." if not dv <= -5 else
                   " You win less, and more than the tougher opponents explain: worth looking at what changed.")
    elif easier and dw >= 5:
        meaning = (" You win more, but partly because your opponents are weaker." if dv < 5 else
                   " You win more, and by more than the weaker opponents explain: real progress.")
    elif dw >= 5:
        meaning = " Same level of opponents, better results: clear progress."
    elif dw <= -5:
        meaning = " Same or weaker opponents but fewer wins: your results have slipped, worth looking at what changed."
    else:
        meaning = " Overall, your level is stable."
    return head + opp + meaning


def _insights(a: Analysis) -> list[str]:
    s, df, out = a.summary, a.matches, []
    if "rating_change" in s:
        direction = "up" if s["rating_change"] >= 0 else "down"
        out.append(f"Your {a.fmt.lower()} rating went {direction} {abs(s['rating_change']):.3f} "
                   f"({s['rating_start']:.3f} → {s['rating_now']:.3f}) over {s['matches']} matches; "
                   f"peak {s['rating_peak']:.3f} on {s['rating_peak_date']:%d %b %Y}.")
    if "trend_per_month" in s:
        t = f"Long-run trend: {s['trend_per_month']:+.3f} per month"
        if "trend_last_90d_per_month" in s:
            r = s["trend_last_90d_per_month"]
            verb = ("speeding up" if r > s["trend_per_month"] + 0.01 else
                    "slowing down" if r < s["trend_per_month"] - 0.01 else "steady")
            t += f"; last 90 days: {r:+.3f} per month ({verb})"
        out.append(t + ".")
    per = a.periods
    if per is not None and len(per) >= 2:
        solid = per[per["matches"] >= max(5, per["matches"].median() / 2)]
        if len(solid) >= 2:
            best, worst = solid["win_pct"].idxmax(), solid["win_pct"].idxmin()
            out.append(f"Best {s['period_label'].lower()}: {best} ({_pct(solid.loc[best, 'win_pct'])} wins over "
                       f"{int(solid.loc[best, 'matches'])} matches); worst: {worst} "
                       f"({_pct(solid.loc[worst, 'win_pct'])} over {int(solid.loc[worst, 'matches'])}).")
        half = len(df) // 2
        if half >= 5:
            out.append(_halves_sentence(df.iloc[:half], df.iloc[half:]))
    if "wins_above_expected" in s and not math.isnan(s["wins_above_expected"]):
        wae = s["wins_above_expected"]
        out.append(f"Compared with the rating-gap model you won {s['wins']} matches against ~{s['expected_wins']:.1f} "
                   f"expected ({wae:+.1f}): you {'outperform' if wae > 0 else 'underperform'} the ratings on paper.")
    if a.diff_buckets is not None and len(a.diff_buckets):
        db = a.diff_buckets
        under = db[db.index.astype(str).str.startswith(("<", "-"))]
        if len(under) and under["matches"].sum() >= 3:
            wp = (under["win_pct"] * under["matches"]).sum() / under["matches"].sum()
            out.append(f"When your team is rated lower than the opponents you win {_pct(wp)} "
                       f"({int(under['matches'].sum())} matches).")
    c = a.close_games
    if c.get("close_games", 0) >= 5:
        verdict = "clutch" if c["close_win_pct"] >= 55 else "a weak spot" if c["close_win_pct"] <= 45 else "a coin flip"
        out.append(f"Close games (decided by 2 points or fewer): {_pct(c['close_win_pct'])} won over "
                   f"{c['close_games']} games - {verdict}.")
    if c.get("deciders", 0) >= 3:
        out.append(f"Deciding 3rd games: {_pct(c['decider_win_pct'])} won ({c['deciders']} played).")
    if a.partners is not None:
        p = a.partners[a.partners["matches"] >= 3]
        if len(p) >= 2:
            b, w = p["win_pct"].idxmax(), p["win_pct"].idxmin()
            out.append(f"Best regular partner: {b} ({_pct(p.loc[b, 'win_pct'])} in {int(p.loc[b, 'matches'])}); "
                       f"toughest: {w} ({_pct(p.loc[w, 'win_pct'])} in {int(p.loc[w, 'matches'])}).")
    if a.by_rest is not None and len(a.by_rest) >= 2:
        sentence = _rest_sentence(a.by_rest)
        if sentence:
            out.append(sentence)
    if df["rating_impact"].notna().any():
        sentence = _impact_sentence(df)
        if sentence:
            out.append(sentence)
    out.append(_streak_sentence(s))
    return out


def _impact_sentence(df: pd.DataFrame) -> str:
    """Average rating change per win / loss, and how much the score margin changes it."""
    wi = df.loc[df["won"], "rating_impact"].mean()
    li = df.loc[~df["won"], "rating_impact"].mean()
    if math.isnan(wi) or math.isnan(li):
        return ""
    text = (f"On average a win raises your rating by {abs(wi):.3f} and a loss "
            f"{'lowers' if li < 0 else 'still raises'} it by {abs(li):.3f}.")
    # Average points difference per game, to tell close results from heavy ones.
    per_game = df["point_diff"] / df["game_margins"].map(lambda ms: max(len(ms), 1))
    losses = df[~df["won"]].assign(pg=per_game)
    close_l = losses[losses["pg"] >= -3]["rating_impact"].dropna()
    heavy_l = losses[losses["pg"] <= -6]["rating_impact"].dropna()
    if len(close_l) >= 3 and len(heavy_l) >= 3:
        def cost(v: float) -> str:
            return f"costs you {abs(v):.3f}" if v < 0 else f"still gains you {v:.3f}"
        text += (f" The score matters, not just the result: a close loss (3 points or less per game) "
                 f"{cost(close_l.mean())} on average, while a heavy loss (6+ points per game) "
                 f"{cost(heavy_l.mean())}. Keeping lost games close protects your rating.")
    return text
