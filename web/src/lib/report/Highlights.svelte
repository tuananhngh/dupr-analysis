<script lang="ts">
	// A few standout facts, each one number and one line.
	import { m } from './messages.ts';
	import { date, isNum, num, pct, signed } from './format.ts';
	import type { FormatData } from './types.ts';

	let { d }: { d: FormatData } = $props();
	const M = $derived(m());

	type Card = { label: string; value: string; sub: string; tone?: 'good' | 'bad' };
	const cards = $derived.by(() => {
		const s = d.summary,
			c = d.close_games,
			out: Card[] = [];
		if (s.longest_win_streak > 1)
			out.push({ label: M.ui.longestStreak, value: String(s.longest_win_streak), sub: M.ui.inARow, tone: 'good' });
		const best = d.best[0];
		if (best && isNum(best.rating_impact) && best.rating_impact > 0)
			out.push({
				label: M.ui.bestMatch,
				value: signed(best.rating_impact),
				sub: `${date(best.date)} · ${M.ui.vs} ${best.opponents}`,
				tone: 'good'
			});
		const partner = d.partners
			.filter((p) => p.matches >= 3 && isNum(p.win_pct))
			.sort((a, b) => b.win_pct! - a.win_pct! || b.matches - a.matches)[0];
		if (partner)
			out.push({ label: M.ui.bestPartner, value: partner.partner, sub: M.ui.partnerSub(pct(partner.win_pct), partner.matches) });
		const nemesis = d.opponents
			.filter((o) => o.matches >= 2 && isNum(o.win_pct) && o.win_pct < 50)
			.sort((a, b) => a.win_pct! - b.win_pct! || b.matches - a.matches)[0];
		if (nemesis)
			out.push({
				label: M.ui.nemesis,
				value: nemesis.opponent,
				sub: M.ui.nemesisSub(nemesis.wins, nemesis.matches - nemesis.wins),
				tone: 'bad'
			});
		if (c.close_games > 0 && isNum(c.close_win_pct))
			out.push({
				label: M.ui.closeGames,
				value: pct(c.close_win_pct),
				sub: M.ui.closeSub(c.close_games),
				tone: c.close_win_pct >= 50 ? 'good' : 'bad'
			});
		if (isNum(s.wins_above_expected) && isNum(s.expected_wins))
			out.push({
				label: M.ui.vsOdds,
				value: signed(s.wins_above_expected, 1),
				sub: M.ui.vsOddsSub(s.wins, num(s.expected_wins)),
				tone: s.wins_above_expected >= 0 ? 'good' : 'bad'
			});
		return out;
	});
</script>

{#if cards.length}
	<h3>{M.ui.highlights}</h3>
	<div class="cards">
		{#each cards as c (c.label)}
			<div class="card {c.tone ?? ''}">
				<div class="lbl">{c.label}</div>
				<div class="val">{c.value}</div>
				<div class="sub">{c.sub}</div>
			</div>
		{/each}
	</div>
{/if}

<style>
	h3 {
		font-size: 18px;
		margin: 28px 0 10px;
	}
	.cards {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(min(100%, 160px), 1fr));
		gap: 12px;
	}
	.card {
		background: var(--surface);
		border: 1px solid var(--line);
		border-top: 3px solid var(--faint);
		border-radius: 12px;
		padding: 12px 16px 14px;
		min-width: 0;
		break-inside: avoid;
	}
	.card.good {
		border-top-color: var(--teal);
	}
	.card.bad {
		border-top-color: var(--orange);
	}
	.lbl,
	.sub {
		font-size: 13px;
		color: var(--ink2);
	}
	.lbl {
		font-weight: 600;
	}
	.val {
		font-size: 22px;
		font-weight: 700;
		line-height: 1.25;
		margin: 4px 0;
		overflow-wrap: anywhere;
		font-variant-numeric: tabular-nums;
	}
	.sub {
		overflow-wrap: anywhere;
	}
</style>
