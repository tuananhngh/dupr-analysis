"""Synthetic data in the same JSON shape as the DUPR API, for testing the pipeline."""
from __future__ import annotations

import random
from datetime import datetime, timedelta

ME = {"id": 1000, "fullName": "Demo Player"}


def generate(n: int = 160, seed: int = 7) -> tuple[dict, list[dict]]:
    rng = random.Random(seed)
    partners = [{"id": 2000 + i, "fullName": f"Partner {c}", "skill": 3.2 + rng.random() * 0.8}
                for i, c in enumerate("ABCDEF")]
    others = [{"id": 3000 + i, "fullName": f"Opponent {i:02d}", "skill": 2.9 + rng.random() * 1.4} for i in range(40)]
    skill, rating = 3.1, 3.05
    date = datetime(2023, 3, 1)
    matches = []
    for k in range(n):
        date += timedelta(days=rng.choice([0, 1, 2, 3, 4, 7, 7, 10, 14, 21]))
        skill += 0.006 + rng.gauss(0, 0.01)
        p = rng.choice(partners)
        o1, o2 = rng.sample(others, 2)
        mine = (skill + p["skill"]) / 2
        theirs = (o1["skill"] + o2["skill"]) / 2
        n_games = 1 if rng.random() < 0.7 else 3
        g_me, g_op = [], []
        for g in range(n_games):
            pwin = 1 / (1 + 10 ** (-(mine - theirs) / 0.5)) * 0.6 + 0.2
            a = 11 if rng.random() < pwin else rng.randint(2, 10)
            b = rng.randint(2, 10) if a == 11 else 11
            if rng.random() < 0.15:
                a, b = (12, 10) if a == 11 else (10, 12)
            g_me.append(a); g_op.append(b)
        if n_games == 3:
            wins = sum(x > y for x, y in zip(g_me, g_op))
            if wins in (0, 3):  # make it a real 3-gamer
                g_me[1], g_op[1] = g_op[1], g_me[1]
        won = sum(x > y for x, y in zip(g_me, g_op)) > n_games / 2
        share = sum(g_me) / (sum(g_me) + sum(g_op))
        impact = round((share - 0.5) * 0.12 + (skill - rating) * 0.08 + rng.gauss(0, 0.005), 4)

        def team(pa, pb, games, win, pre_a, pre_b, imp):
            t = {"player1": {"id": pa["id"], "fullName": pa["fullName"]},
                 "player2": {"id": pb["id"], "fullName": pb["fullName"]},
                 "winner": win,
                 "preMatchRatingAndImpact": {"preMatchDoubleRatingPlayer1": round(pre_a, 3),
                                             "preMatchDoubleRatingPlayer2": round(pre_b, 3),
                                             "matchDoubleRatingImpactPlayer1": imp,
                                             "matchDoubleRatingImpactPlayer2": imp}}
            for i in range(5):
                t[f"game{i+1}"] = games[i] if i < len(games) else -1
            return t

        teams = [team(ME, p, g_me, won, rating, p["skill"], impact),
                 team(o1, o2, g_op, not won, o1["skill"], o2["skill"], -impact)]
        rng.shuffle(teams)
        matches.append({"matchId": 90000 + k, "eventDate": date.strftime("%Y-%m-%d"), "format": "DOUBLES",
                        "matchSource": rng.choice(["CLUB", "CLUB", "LEAGUE", "TOURNAMENT"]),
                        "eventName": "Demo event", "confirmed": True, "teams": teams})
        rating += impact
    return {"id": ME["id"], "fullName": ME["fullName"]}, matches[::-1]
