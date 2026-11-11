"""Render an Analysis into a single self-contained interactive HTML report."""

from __future__ import annotations

import html
import math
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs

from .analysis import Analysis

# Reference categorical palette (validated order): blue, orange.
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0", "#fcfcfb"
FAINT = "#c9c8c2"
WIN_COLOR, LOSS_COLOR = BLUE, ORANGE


def _layout(
    fig: go.Figure, title: str, y_title: str = "", height: int = 380
) -> go.Figure:
    fig.update_layout(
        title=dict(
            text=title,
            x=0,
            y=1,
            yref="container",
            yanchor="top",
            pad=dict(t=12, l=4),
            font=dict(size=16, color=INK),
        ),
        height=height,
        margin=dict(l=60, r=24, t=76, b=48),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(
            family="Inter, -apple-system, Segoe UI, sans-serif", size=13, color=INK2
        ),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="white", font_color=INK, font_size=13),
        legend=dict(
            orientation="h",
            y=1.02,
            x=1,
            xanchor="right",
            yanchor="bottom",
            font=dict(size=13),
        ),
        bargap=0.25,
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID, tickcolor=GRID)
    fig.update_yaxes(title=y_title, gridcolor=GRID, zerolinecolor=GRID)
    return fig


def _div(fig: go.Figure) -> str:
    return fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        config={"displaylogo": False, "responsive": True},
    )


def _label(
    fig: go.Figure, x, y, text: str, ay: int = -36, ax: int = 0, color: str = INK
) -> None:
    """A direct label with a thin leader line, so key values are readable without hovering."""
    fig.add_annotation(
        x=x,
        y=y,
        text=f"<b>{text}</b>",
        showarrow=True,
        arrowhead=0,
        arrowwidth=1,
        arrowcolor=MUTED,
        ax=ax,
        ay=ay,
        font=dict(size=12, color=color),
        bgcolor="rgba(252,252,251,.9)",
        borderpad=3,
    )


TIME_BUTTONS = dict(
    buttons=[
        dict(count=3, label="3 months", step="month", stepmode="backward"),
        dict(count=6, label="6 months", step="month", stepmode="backward"),
        dict(count=1, label="1 year", step="year", stepmode="backward"),
        dict(label="All", step="all"),
    ],
    x=0,
    y=1.0,
    yanchor="bottom",
    font=dict(size=12),
    bgcolor="#efeee9",
    activecolor="#d9e6f7",
)


def _short_gap(label: str) -> str:
    """'Much weaker opponents (0.3+ below you)' -> 'Much weaker<br>0.3+ below'."""
    if "(" not in label:
        return label
    name, rng = label.split("(", 1)
    name = name.replace("opponents", "").replace("partner", "").strip()
    return f"{name}<br><span style='font-size:11px'>{rng.rstrip(')').replace(' you', '')}</span>"


# ------------------------------------------------------------------ charts
def chart_rating(a: Analysis) -> str:
    r, df, s = a.rating, a.matches, a.summary
    if r.empty:
        return ""
    fig = go.Figure()
    fig.add_scatter(
        x=r["date"],
        y=r["rating"],
        mode="lines",
        line=dict(color=BLUE, width=3, shape="hv"),
        name="Your DUPR rating",
        hovertemplate="%{y:.3f}<extra>Rating</extra>",
    )
    m = df.dropna(subset=["rating_after"])
    if len(m):
        for won, color, name in ((True, WIN_COLOR, "Win"), (False, LOSS_COLOR, "Loss")):
            g = m[m["won"] == won]
            fig.add_scatter(
                x=g["date"],
                y=g["rating_after"],
                mode="markers",
                name=f"Match: {name.lower()}",
                marker=dict(size=9, color=color, line=dict(color=SURFACE, width=2)),
                customdata=list(
                    zip(g["game_scores"], g["opponents"], g["rating_impact"].fillna(0))
                ),
                hovertemplate=f"{name} %{{customdata[0]}}<br>vs %{{customdata[1]}}<br>"
                "rating %{customdata[2]:+.3f}<extra></extra>",
            )
    if "trend_per_month" in s and len(r) >= 3:
        days = (r["date"] - r["date"].iloc[0]).dt.days
        slope = s["trend_per_month"] / 30.44
        intercept = r["rating"].mean() - slope * days.mean()
        fig.add_scatter(
            x=[r["date"].iloc[0], r["date"].iloc[-1]],
            y=[intercept, intercept + slope * days.iloc[-1]],
            mode="lines",
            line=dict(color=MUTED, width=1.5, dash="dash"),
            name=f"Trend: {s['trend_per_month']:+.3f} per month",
            hoverinfo="skip",
        )
    first, last = r.iloc[0], r.iloc[-1]
    peak = r.loc[r["rating"].idxmax()]
    _label(
        fig,
        first["date"],
        first["rating"],
        f"Start {first['rating']:.3f}",
        ay=-40,
        ax=30,
    )
    if peak["date"] != last["date"]:
        _label(fig, peak["date"], peak["rating"], f"Peak {peak['rating']:.3f}", ay=-40)
    _label(
        fig,
        last["date"],
        last["rating"],
        f"Now {last['rating']:.3f}",
        ay=40 if peak["date"] != last["date"] else -40,
        ax=-30,
        color=BLUE,
    )
    pad = max((r["rating"].max() - r["rating"].min()) * 0.15, 0.05)
    fig.update_yaxes(
        range=[r["rating"].min() - pad, r["rating"].max() + pad], tickformat=".2f"
    )
    fig.update_xaxes(rangeselector=TIME_BUTTONS)
    fig.update_layout(legend=dict(y=1.08))
    return _div(_layout(fig, f"{a.fmt.title()} rating over time", "DUPR rating", 480))


def chart_win_form(a: Analysis) -> str:
    df, w = a.matches, a.summary["rolling_window"]
    exp_roll = df["exp_win"].rolling(w, min_periods=w).mean() * 100
    fig = go.Figure()
    fig.add_scatter(
        x=df["date"],
        y=df["rolling_win_pct"],
        name=f"Your win % (last {w} matches)",
        line=dict(color=BLUE, width=3),
        hovertemplate="%{y:.0f}%",
    )
    if exp_roll.notna().any():
        fig.add_scatter(
            x=df["date"],
            y=exp_roll,
            name="Expected win % (from ratings)",
            line=dict(color=ORANGE, width=2, dash="dot"),
            hovertemplate="%{y:.0f}%",
        )
    fig.add_hline(y=50, line=dict(color=MUTED, width=1, dash="dot"))
    last = df.dropna(subset=["rolling_win_pct"]).tail(1)
    if len(last):
        _label(
            fig,
            last["date"].iloc[0],
            last["rolling_win_pct"].iloc[0],
            f"Now {last['rolling_win_pct'].iloc[0]:.0f}%",
            ay=-34,
            ax=-30,
            color=BLUE,
        )
    fig.update_yaxes(range=[-5, 105], ticksuffix="%")
    return _div(
        _layout(fig, "Winning: your win % vs what the ratings predict", "Win %", 400)
    )


def chart_point_form(a: Analysis) -> str:
    df, w = a.matches, a.summary["rolling_window"]
    fig = go.Figure()
    fig.add_scatter(
        x=df["date"],
        y=df["point_share"] * 100,
        mode="markers",
        name="Each match",
        marker=dict(size=6, color=FAINT),
        hovertemplate="%{y:.0f}%<extra>Match</extra>",
    )
    fig.add_scatter(
        x=df["date"],
        y=df["rolling_point_share"],
        name=f"Average of last {w} matches",
        line=dict(color=BLUE, width=3),
        hovertemplate="%{y:.1f}%<extra>Average</extra>",
    )
    fig.add_hline(
        y=50,
        line=dict(color=MUTED, width=1, dash="dot"),
        annotation_text="50% = even",
        annotation_position="bottom right",
        annotation_font=dict(size=12, color=INK2),
    )
    last = df.dropna(subset=["rolling_point_share"]).tail(1)
    if len(last):
        _label(
            fig,
            last["date"].iloc[0],
            last["rolling_point_share"].iloc[0],
            f"Now {last['rolling_point_share'].iloc[0]:.1f}%",
            ay=-34,
            ax=-30,
            color=BLUE,
        )
    lo = min(30, (df["point_share"] * 100).min() - 2)
    hi = max(70, (df["point_share"] * 100).max() + 2)
    fig.update_yaxes(range=[lo, hi], ticksuffix="%")
    return _div(
        _layout(fig, "Point win %: share of rally points you win", "Point win %", 400)
    )


def chart_opp_results(a: Analysis) -> str:
    """Win % (actual vs expected) against weaker, similar and stronger opponents."""
    t = (a.opponent_effect or {}).get("table")
    if t is None or t.empty:
        return ""
    x = [
        f"{_short_gap(str(i))}<br><span style='font-size:11px'>{int(n)} matches</span>"
        for i, n in zip(t.index, t["matches"])
    ]
    fig = go.Figure()
    fig.add_bar(
        x=x,
        y=t["win_pct"],
        name="Your win %",
        marker=dict(color=BLUE, cornerradius=4),
        text=[f"<b>{v:.0f}%</b>" for v in t["win_pct"]],
        textposition="inside",
        insidetextanchor="end",
        textangle=0,
        textfont=dict(color="white"),
        customdata=t[["matches", "point_share"]],
        hovertemplate="won %{y:.0f}% of %{customdata[0]} matches<br>"
        "point win %{customdata[1]:.1f}%<extra></extra>",
    )
    fig.add_scatter(
        x=x,
        y=t["exp_win_pct"],
        name="Expected win %",
        mode="lines+markers",
        line=dict(color=ORANGE, width=2.5),
        marker=dict(size=9),
        hovertemplate="expected %{y:.0f}%",
    )
    fig.update_layout(hovermode="x")
    fig.update_xaxes(title="Opponents' average rating compared with yours", tickangle=0)
    fig.update_yaxes(range=[0, 120], ticksuffix="%")
    return _div(
        _layout(fig, "Win % by opponent strength: actual vs expected", "Win %", 420)
    )


def chart_opp_rating_change(a: Analysis) -> str:
    """Average rating change per match against each opponent-strength group."""
    eff = a.opponent_effect or {}
    t = eff.get("table")
    if t is None or t.empty or eff.get("col") != "rating_impact":
        return ""
    x = [_short_gap(str(i)) for i in t.index]
    y = t["avg_impact"]
    fig = go.Figure(
        go.Bar(
            x=x,
            y=y,
            marker=dict(color=[BLUE if v >= 0 else ORANGE for v in y], cornerradius=4),
            text=[
                f"{v:+.3f}<br><span style='font-size:11px'>point win {p:.0f}%</span>"
                for v, p in zip(y, t["point_share"])
            ],
            textposition="outside",
            textfont=dict(color=INK2),
            hovertemplate="%{y:+.3f} rating per match<extra></extra>",
        )
    )
    fig.add_hline(y=0, line=dict(color=MUTED, width=1))
    pad = max(abs(y.max()), abs(y.min()), 1e-6) * 0.45
    fig.update_yaxes(range=[min(0, y.min()) - pad, max(0, y.max()) + pad])
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(title="Opponents' average rating compared with yours", tickangle=0)
    return _div(
        _layout(
            fig,
            "Rating gained per match, by opponent strength",
            "Avg rating change",
            420,
        )
    )


def chart_opp_over_time(a: Analysis) -> str:
    """Your rating vs the average rating of the opponents you face: are you playing up?"""
    df, w = a.matches.dropna(subset=["opp_rating_avg"]), a.summary["rolling_window"]
    if len(df) < 5:
        return ""
    fig = go.Figure()
    fig.add_scatter(
        x=df["date"],
        y=df["opp_rating_avg"],
        mode="markers",
        name="Opponents in each match",
        marker=dict(size=6, color=FAINT),
        customdata=df["opponents"],
        hovertemplate="%{y:.3f} · %{customdata}<extra>Opponents</extra>",
    )
    fig.add_scatter(
        x=df["date"],
        y=df["opp_rating_avg"].rolling(w, min_periods=3).mean(),
        name=f"Opponents' level (avg of last {w})",
        line=dict(color=ORANGE, width=3),
        hovertemplate="%{y:.3f}<extra>Opponents avg</extra>",
    )
    mine = df.dropna(subset=["rating_before"])
    fig.add_scatter(
        x=mine["date"],
        y=mine["rating_before"],
        name="Your rating",
        line=dict(color=BLUE, width=3, shape="hv"),
        hovertemplate="%{y:.3f}<extra>You</extra>",
    )
    fig.update_yaxes(tickformat=".2f")
    fig.update_xaxes(rangeselector=TIME_BUTTONS)
    fig.update_layout(legend=dict(y=1.08))
    return _div(
        _layout(
            fig, "Your rating vs your opponents' level over time", "DUPR rating", 440
        )
    )


def chart_periods(a: Analysis) -> str:
    p = a.periods
    fig = go.Figure()
    fig.add_bar(
        x=p.index,
        y=p["win_pct"],
        name="Win %",
        marker=dict(color=BLUE, cornerradius=4),
        text=[f"{v:.0f}%" for v in p["win_pct"]],
        textposition="inside",
        insidetextanchor="end",
        textangle=0,
        textfont=dict(color="white"),
        customdata=p[["matches", "wins"]],
        hovertemplate="%{y:.0f}% (%{customdata[1]} of %{customdata[0]} matches)<extra>Win %</extra>",
    )
    fig.add_scatter(
        x=p.index,
        y=p["point_share"],
        name="Point win %",
        mode="lines+markers",
        line=dict(color=ORANGE, width=2.5),
        marker=dict(size=8),
        hovertemplate="%{y:.1f}%",
    )
    fig.add_hline(y=50, line=dict(color=MUTED, width=1, dash="dot"))
    fig.update_yaxes(range=[0, 112], ticksuffix="%")
    return _div(
        _layout(
            fig,
            f"Win % and point win % per {a.summary['period_label'].lower()}",
            "%",
            380,
        )
    )


def chart_activity(a: Analysis) -> str:
    p = a.periods
    fig = go.Figure(
        go.Bar(
            x=p.index,
            y=p["matches"],
            marker=dict(color=BLUE, cornerradius=4),
            text=p["matches"].astype(int),
            textposition="outside",
            textfont=dict(color=INK2),
            hovertemplate="%{y} matches<extra></extra>",
        )
    )
    fig.update_yaxes(range=[0, p["matches"].max() * 1.2])
    return _div(
        _layout(
            fig,
            f"Matches played per {a.summary['period_label'].lower()}",
            "Matches",
            380,
        )
    )


def monthly_rating_change(a: Analysis) -> pd.DataFrame:
    """Net rating change in each month you played, from the rating curve, with your record that month."""
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


def chart_impact(a: Analysis) -> str:
    """Net rating change per month played (per-match bars were unreadable with sparse, clustered play)."""
    t = monthly_rating_change(a)
    if t.empty:
        return ""
    x = [f"{d:%b %Y}" for d in t.index]
    y = t["change"]
    fig = go.Figure(
        go.Bar(
            x=x,
            y=y,
            marker=dict(color=[BLUE if v >= 0 else ORANGE for v in y], cornerradius=4),
            text=[
                f"<b>{v:+.3f}</b><br><span style='font-size:11px'>{int(n)} match{'es' if n > 1 else ''}</span>"
                for v, n in zip(y, t["matches"])
            ],
            textposition="outside",
            textfont=dict(color=INK2),
            cliponaxis=False,
            customdata=t[["matches", "wins", "rating_end"]],
            hovertemplate="%{x}: %{y:+.3f}<br>%{customdata[1]} wins of %{customdata[0]} matches"
            "<br>rating at month end %{customdata[2]:.3f}<extra></extra>",
        )
    )
    fig.add_hline(y=0, line=dict(color=MUTED, width=1))
    span = (max(y.max(), 0) - min(y.min(), 0)) or 0.01
    fig.update_yaxes(range=[min(y.min(), 0) - span * 0.3, max(y.max(), 0) + span * 0.3], tickformat="+.2f")
    fig.update_xaxes(type="category", tickangle=0 if len(t) <= 12 else -45)
    fig.update_layout(hovermode="closest")
    return _div(_layout(fig, "Rating change per month (months you played)", "Rating change", 400))


def chart_expectation(a: Analysis) -> str:
    db = a.diff_buckets
    if db is None or db.empty:
        return ""
    labels = [str(i) for i in db.index]
    fig = go.Figure()
    fig.add_bar(
        x=labels,
        y=db["win_pct"],
        name="Your actual win %",
        marker=dict(color=BLUE, cornerradius=4),
        text=[f"{v:.0f}%" for v in db["win_pct"]],
        textposition="inside",
        insidetextanchor="end",
        textangle=0,
        textfont=dict(color="white"),
        customdata=db["matches"],
        hovertemplate="%{y:.0f}% over %{customdata} matches",
    )
    fig.add_scatter(
        x=labels,
        y=db["expected_pct"],
        name="Expected win %",
        mode="lines+markers",
        line=dict(color=ORANGE, width=2.5),
        marker=dict(size=9),
        hovertemplate="%{y:.0f}%",
    )
    fig.update_xaxes(title="Your team's rating minus the opponents' team rating")
    fig.update_yaxes(range=[0, 112], ticksuffix="%")
    return _div(
        _layout(fig, "Win % by team rating gap: actual vs expected", "Win %", 400)
    )


def chart_vs_expected(a: Analysis) -> str:
    df = a.matches
    if df["exp_win"].isna().all():
        return ""
    y = df["perf_vs_exp"]
    fig = go.Figure()
    fig.add_scatter(
        x=df["date"],
        y=y.clip(lower=0),
        fill="tozeroy",
        mode="none",
        fillcolor="rgba(42,120,214,.15)",
        hoverinfo="skip",
        showlegend=False,
    )
    fig.add_scatter(
        x=df["date"],
        y=y.clip(upper=0),
        fill="tozeroy",
        mode="none",
        fillcolor="rgba(235,104,52,.15)",
        hoverinfo="skip",
        showlegend=False,
    )
    fig.add_scatter(
        x=df["date"],
        y=y,
        mode="lines",
        line=dict(color=BLUE, width=2.5),
        showlegend=False,
        hovertemplate="%{y:+.1f} wins vs expected<extra></extra>",
    )
    fig.add_hline(y=0, line=dict(color=MUTED, width=1))
    _label(
        fig,
        df["date"].iloc[-1],
        y.iloc[-1],
        f"{y.iloc[-1]:+.1f} wins",
        ay=-30,
        ax=-30,
        color=BLUE,
    )
    return _div(
        _layout(
            fig, "Wins above expectation, added up over time", "Wins vs expected", 400
        )
    )


def chart_partners(a: Analysis) -> str:
    p = a.partners
    if p is None or p.empty:
        return ""
    p = p[p["matches"] >= 2].head(12).sort_values("win_pct")
    if p.empty:
        return ""
    fig = go.Figure(
        go.Bar(
            y=p.index,
            x=p["win_pct"],
            orientation="h",
            marker=dict(color=BLUE, cornerradius=4),
            text=[
                f"{w:.0f}% · {int(n)} matches"
                for w, n in zip(p["win_pct"], p["matches"])
            ],
            textposition="outside",
            textfont=dict(color=INK2),
            hovertemplate="%{y}: %{x:.0f}%<extra></extra>",
        )
    )
    fig.add_vline(x=50, line=dict(color=MUTED, width=1, dash="dot"))
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(range=[0, 125], title="Win %", ticksuffix="%")
    return _div(
        _layout(
            fig, "Win % with each partner (2+ matches)", "", max(300, 34 * len(p) + 110)
        )
    )


def chart_margins(a: Analysis) -> str:
    margins = [m for ms in a.matches["game_margins"] for m in ms]
    if not margins:
        return ""
    s = pd.Series(margins).value_counts().sort_index()
    fig = go.Figure(
        go.Bar(
            x=s.index,
            y=s.values,
            marker=dict(
                color=[WIN_COLOR if x > 0 else LOSS_COLOR for x in s.index],
                cornerradius=4,
            ),
            hovertemplate="won/lost by %{x:+d}: %{y} games<extra></extra>",
        )
    )
    fig.update_layout(hovermode="closest")
    fig.update_xaxes(title="Score difference in the game (your points − theirs)")
    return _div(
        _layout(fig, "How your games end (blue = won, orange = lost)", "Games", 380)
    )


# ------------------------------------------------------------------ tables
def _fmt(v, col: str = ""):
    if isinstance(v, (pd.Timestamp, datetime)):
        return v.strftime("%d %b %Y")
    if isinstance(v, bool):
        return "W" if v else "L"
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "–"
    if isinstance(v, (int, float)):
        if col.endswith("_pct") or col == "point_share":
            return f"{v:.0f}%"
        if col in (
            "rating_gained",
            "rating_impact",
            "avg_impact",
            "total_impact",
            "rating_diff",
            "partner_gap",
        ):
            return f"{v:+.3f}"
        if col == "avg_point_diff":
            return f"{v:+.1f}"
        if "rating" in col:
            return f"{v:.3f}"
        if float(v).is_integer():
            return f"{int(v)}"
        return f"{v:.2f}"
    return html.escape(str(v))


def table(
    df: pd.DataFrame | None,
    cols: dict[str, str],
    index_name: str | None = None,
    limit: int = 30,
) -> str:
    if df is None or df.empty:
        return "<p class='muted'>Not enough data.</p>"
    df = df.head(limit)
    head = (f"<th>{html.escape(index_name)}</th>" if index_name else "") + "".join(
        f"<th>{v}</th>" for v in cols.values()
    )
    rows = []
    for idx, row in df.iterrows():
        first = f"<td>{_fmt(idx)}</td>" if index_name else ""
        rows.append(
            "<tr>"
            + first
            + "".join(f"<td>{_fmt(row[c], c)}</td>" for c in cols if c in row)
            + "</tr>"
        )
    return f"<div class='tbl'><table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"


AGG_COLS = {
    "matches": "Matches",
    "win_pct": "Win %",
    "point_share": "Point win %",
    "avg_point_diff": "Avg point diff",
    "avg_opp_rating": "Avg opponent rating",
    "rating_gained": "Rating change",
}


def tile(label: str, value: str, sub: str = "") -> str:
    return f"<div class='tile'><div class='lbl'>{label}</div><div class='val'>{value}</div><div class='sub'>{sub}</div></div>"


def card(chart: str, caption: str) -> str:
    if not chart:
        return ""
    return f"<div class='card'>{chart}<p class='cap'>{caption}</p></div>"


TIP_BADGE = {
    "work": ("Work on this", "work"),
    "strength": ("Strength", "strength"),
    "info": ("Good to know", "info"),
}


def tips_html(tips: list[dict]) -> str:
    if not tips:
        return "<p class='muted'>Not enough matches yet for specific advice (needs a few dozen games).</p>"
    out = []
    for t in tips:
        label, cls = TIP_BADGE[t["kind"]]
        out.append(
            f"<div class='tip {cls}'><span class='badge'>{label}</span><h4>{html.escape(t['title'])}</h4>"
            f"<p class='finding'>{html.escape(t['finding'])}</p>"
            f"<p class='advice'><b>Try:</b> {html.escape(t['advice'])}</p></div>"
        )
    return f"<div class='tips'>{''.join(out)}</div>"


def opponents_section(a: Analysis) -> str:
    eff = a.opponent_effect or {}
    t = eff.get("table")
    if t is None or t.empty:
        return ""
    labels = {str(i): str(i).replace(" opponents", "") for i in t.index}
    t = t.rename(index=labels)
    summary = " ".join(x for x in (eff.get("answer", ""), eff.get("detail", "")) if x)
    return f"""
<h3>Performance by opponent rating</h3>
<p class="takeaway">{html.escape(summary)}</p>
<div class="grid2">
{card(chart_opp_results(a), "Each group is opponents weaker, similar or stronger than you (their average rating minus yours). "
      "Blue bars above the orange line mean you beat the odds against that level.")}
{card(chart_opp_rating_change(a), "How much rating you gain or lose on average in one match against each level. "
      "This shows which opponents actually move your DUPR up.")}
</div>
{card(chart_opp_over_time(a), "Orange above blue means you mostly play opponents rated higher than you (playing up). "
      "Playing up regularly while keeping scores close is one of the fastest ways to raise your rating.")}
{table(t, {"matches": "Matches", "win_pct": "Win %", "exp_win_pct": "Expected win %", "point_share": "Point win %",
           "avg_impact": "Avg rating change", "total_impact": "Total rating change"}, "Opponents")}
"""


def section(a: Analysis) -> str:
    s, c = a.summary, a.close_games
    if not s:
        return ""
    f = lambda v, p="{:.3f}": (
        "–" if v is None or (isinstance(v, float) and math.isnan(v)) else p.format(v)
    )
    period = s["period_label"].lower()
    tiles = "".join(
        [
            tile(
                "Current rating",
                f(s.get("rating_now")),
                f"peak {f(s.get('rating_peak'))}",
            ),
            tile(
                "Change",
                f(s.get("rating_change"), "{:+.3f}"),
                f"since {s['first_match']:%b %Y}",
            ),
            tile("Trend", f(s.get("trend_per_month"), "{:+.3f}"), "rating per month"),
            tile("Record", f"{s['wins']}–{s['losses']}", f"{s['win_pct']:.0f}% wins"),
            tile(
                "Point win %",
                f"{s['point_share']:.1f}%",
                f"games {s['games_won']}–{s['games_lost']}",
            ),
            tile(
                "Close games",
                f(c.get("close_win_pct"), "{:.0f}%"),
                f"won · {c.get('close_games', 0)} games decided by ≤2 pts",
            ),
        ]
    )
    insights = "".join(f"<li>{html.escape(i)}</li>" for i in a.insights)
    match_cols = {
        "date": "Date",
        "won": "W/L",
        "game_scores": "Score",
        "partner": "Partner",
        "opponents": "Opponents",
        "opp_rating_avg": "Opponents' rating",
        "rating_diff": "Team rating gap",
        "rating_impact": "Rating change",
    }
    if a.fmt != "DOUBLES":
        match_cols.pop("partner")
    gain_cols = {
        k: v for k, v in match_cols.items() if k not in ("opponents", "rating_diff")
    }
    recent = a.matches.iloc[::-1]
    w = s["rolling_window"]
    return f"""
<section>
<h2>{a.fmt.title()}</h2>
<div class="tiles">{tiles}</div>

<h3>Key findings</h3><ul class="insights">{insights}</ul>

<h3>How to improve</h3>
<p class="muted">Patterns found in your own matches, with something concrete to try for each.</p>
{tips_html(a.tips)}

<h3>Rating</h3>
{card(chart_rating(a), "The blue line is your DUPR rating; each dot is a match (blue = win, orange = loss). "
      "The dashed line is your average progress. Use the buttons to zoom on the last months.")}
{card(chart_impact(a), "How much your rating went up (blue) or down (orange) over each month you played, with the "
      "number of matches. Months without matches are skipped. Your single best and worst matches are listed in the tables below.")}

<h3>Form</h3>
{card(chart_win_form(a), f"Blue = how often you actually won over your last {w} matches. Orange dots = how often the "
      "ratings say you should win. Blue above orange means you are playing above your rating.")}
{card(chart_point_form(a), "Grey dots are single matches, the blue line is the trend. Point win % changes more smoothly "
      "than win %: if it rises, your level is improving even before results and rating follow.")}

{opponents_section(a)}

<h3>By {period}</h3>
<div class="grid2">
{card(chart_periods(a), f"Bars: share of matches won each {period}. Line: share of points won.")}
{card(chart_activity(a), f"How much you played each {period}.")}
</div>

<h3>Results vs expectation</h3>
<div class="grid2">
{card(chart_expectation(a), "Left = matches against stronger teams, right = against weaker teams (your team vs theirs, "
      "partner included). Blue bars above the orange line mean you win more than the ratings predict.")}
{card(chart_vs_expected(a), "Goes up when you win matches you were not expected to win, down when you lose matches "
      "you should have won. A rising line usually means your rating will keep going up.")}
</div>

<h3>Games and partners</h3>
<div class="grid2">
{card(chart_margins(a), "Right side = games won, left side = games lost. Bars near the middle are close games; "
      "far-left bars are heavy losses, which cost the most rating.")}
{card(chart_partners(a), "How often you win with each partner. The dotted line marks 50%.")}
</div>

<h3>Evolution by {period}</h3>
{table(a.periods.iloc[::-1], {**AGG_COLS, "rating_end": "Rating at end"}, s['period_label'])}
<div class="grid2">
 <div><h3>Partners</h3>{table(a.partners, {**AGG_COLS, "partner_rating": "Partner rating"}, "Partner", 15)}</div>
 <div><h3>Most-faced opponents</h3>{table(a.opponents, {"matches": "Matches", "wins": "Wins", "win_pct": "Win %", "point_share": "Point win %"}, "Opponent", 15)}</div>
</div>
<div class="grid2">
 <div><h3>By match type</h3>{table(a.by_source, AGG_COLS, "Source")}</div>
 <div><h3>By rest since previous match</h3>{table(a.by_rest, AGG_COLS, "Rest")}</div>
</div>
<div class="grid2">
 <div><h3>Biggest rating gains</h3>{table(a.best, gain_cols)}</div>
 <div><h3>Biggest rating losses</h3>{table(a.worst, gain_cols)}</div>
</div>
<h3>Game details</h3>
<p>Games won {f(c.get('game_win_pct'), '{:.0f}%')} of {c.get('games', 0)} ·
 deciding 3rd games won {f(c.get('decider_win_pct'), '{:.0f}%')} of {c.get('deciders', 0)} ·
 heavy games (7+ points difference) won {f(c.get('blowout_win_pct'), '{:.0f}%')} of {c.get('blowouts', 0)} ·
 average margin {f(c.get('avg_margin_win'), '{:+.1f}')} in games won, {f(c.get('avg_margin_loss'), '{:+.1f}')} in games lost.</p>
<details><summary>All matches (most recent first)</summary>
{table(recent, match_cols, limit=10_000)}
</details>
</section>"""


CSS = """
:root{color-scheme:light;--surface:#fcfcfb;--bg:#f4f3f0;--ink:#0b0b0b;--ink2:#52514e;--muted:#8a8984;--line:#e6e5e0;
--blue:#2a78d6;--orange:#c4501f}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 Inter,-apple-system,"Segoe UI",sans-serif}
main{max-width:1080px;margin:0 auto;padding:28px 16px 72px}
h1{font-size:28px;margin:0 0 4px}h2{font-size:23px;margin:44px 0 14px;padding-top:18px;border-top:1px solid var(--line)}
h3{font-size:18px;margin:36px 0 10px}h4{font-size:16px;margin:4px 0 6px}
.muted,.sub,header p{color:var(--ink2)}
.takeaway{font-size:15px;margin:0 0 8px;max-width:900px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.tile,.card{background:var(--surface);border:1px solid var(--line);border-radius:12px}
.tile{padding:14px 16px}.lbl{font-size:13px;color:var(--ink2)}.val{font-size:26px;font-weight:650;font-variant-numeric:tabular-nums}.sub{font-size:13px}
.card{padding:10px 10px 4px;margin:12px 0;min-width:0}
.cap{margin:2px 10px 10px;font-size:14px;color:var(--ink2)}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,460px),1fr));gap:4px 16px}
.insights li{margin:6px 0}
.tips{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:12px}
.tip{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--muted);border-radius:12px;padding:14px 16px}
.tip.work{border-left-color:var(--orange)}.tip.strength{border-left-color:var(--blue)}
.badge{font-size:12px;font-weight:600;color:var(--ink2);text-transform:uppercase;letter-spacing:.04em}
.tip.work .badge{color:var(--orange)}.tip.strength .badge{color:var(--blue)}
.finding{margin:4px 0}.advice{margin:6px 0 0;color:var(--ink2)}
details{margin:16px 0}summary{cursor:pointer;font-weight:600;font-size:16px}
.tbl{overflow-x:auto;max-height:520px;overflow-y:auto;background:var(--surface);border:1px solid var(--line);border-radius:12px}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums;font-size:14px}
th,td{padding:7px 12px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}
th{position:sticky;top:0;background:var(--surface);font-weight:600;color:var(--ink2)}
dl.gloss{display:grid;grid-template-columns:max-content 1fr;gap:6px 14px;font-size:14px;color:var(--ink2);margin:10px 0 0}
dl.gloss dt{font-weight:600;color:var(--ink)}dl.gloss dd{margin:0}
@media (max-width:600px){dl.gloss{grid-template-columns:1fr}}
"""

GLOSSARY = """<details><summary>What the numbers mean</summary><dl class="gloss">
<dt>Point win %</dt><dd>Share of all rally points you won. 11-7, 9-11, 11-6 → 31 of 55 points = 56%. 50% = even.</dd>
<dt>Expected win %</dt><dd>Your chance of winning from the rating gap between your team and the opponents
(approximate model: a 0.25 team-rating edge ≈ 76%). DUPR's own model isn't public.</dd>
<dt>Wins above expectation</dt><dd>Actual wins minus expected wins. Positive = you beat the ratings.</dd>
<dt>Rating change</dt><dd>How much a match moved your DUPR rating, from DUPR's own data.</dd>
<dt>Opponent strength</dt><dd>Your opponents' average rating minus your own rating at the time of the match.</dd>
<dt>Close game</dt><dd>A game decided by 2 points or fewer (11-9, 12-10…).</dd>
</dl></details>"""


def render(analyses: list[Analysis], player_name: str, out_path) -> None:
    body = "".join(section(a) for a in analyses if len(a.matches))
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>DUPR Performance Report</title>
<style>{CSS}</style><script>{get_plotlyjs()}</script></head><body><main>
<header><h1>DUPR performance report</h1>
<p>{html.escape(player_name)} · generated {datetime.now():%d %b %Y %H:%M}</p>
{GLOSSARY}</header>
{body or "<p>No matches found.</p>"}
</main>
<script>
const fit = () => document.querySelectorAll('.js-plotly-plot').forEach(d => Plotly.Plots.resize(d));
window.addEventListener('load', fit); setTimeout(fit, 50);
document.querySelectorAll('details').forEach(d => d.addEventListener('toggle', fit));
</script></body></html>"""
    out_path.write_text(doc, encoding="utf-8")
