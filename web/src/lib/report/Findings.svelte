<script lang="ts">
	// The key findings as cards: a title, the headline number and the sentence.
	import { m } from './messages.ts';
	import type { FindingText } from './messages.en.ts';
	import { date, num, pct, periodLabel, rating, signed, span } from './format.ts';
	import type { Finding, Period } from './types.ts';

	let { findings, fmt }: { findings: Finding[]; fmt: string } = $props();
	const M = $derived(m());

	type Tone = 'good' | 'bad' | undefined;
	const GOOD = ['progress_tougher', 'level_up', 'progress_easier', 'progress'];
	const BAD = ['worse_than_tougher', 'slipped'];
	const sign = (v: number): Tone => (v >= 0 ? 'good' : 'bad');

	function headline(f: Finding): { value: string; tone: Tone } | null {
		switch (f.id) {
			case 'rating_change':
				return { value: signed(f.change), tone: sign(f.change) };
			case 'trend':
				return { value: signed(f.per_month) + M.ui.perMonth, tone: sign(f.per_month) };
			case 'halves':
				return {
					value: `${pct(f.win_early)} → ${pct(f.win_late)}`,
					tone: GOOD.includes(f.meaning) ? 'good' : BAD.includes(f.meaning) ? 'bad' : undefined
				};
			case 'vs_expected':
				return { value: signed(f.above, 1), tone: sign(f.above) };
			case 'close_games':
				return { value: pct(f.pct), tone: f.verdict === 'clutch' ? 'good' : f.verdict === 'weak' ? 'bad' : undefined };
			case 'best_period':
			case 'partners':
				return { value: pct(f.best_pct), tone: undefined };
			case 'underdog':
			case 'favourite':
				return { value: pct(f.win_pct), tone: undefined };
			case 'deciders':
				return { value: pct(f.pct), tone: undefined };
			case 'impact':
				return { value: signed(f.win), tone: undefined };
			case 'streaks':
				return { value: String(f.longest_win), tone: undefined };
		}
		return null;
	}

	// Some cards show their numbers as a small table, so the text can be just the conclusion.
	type Head = { label: string; sub?: string };
	type Row = { label: string; sub?: string; cells: string[] };
	type Cmp = { head: Head[]; rows: Row[] };
	function compare(f: Finding): Cmp | null {
		const U = M.ui;
		switch (f.id) {
			case 'rating_change': {
				const rows: Row[] = [{ label: U.cmp.start, sub: f.start_date ? date(f.start_date) : undefined, cells: [rating(f.start)] }];
				if (f.peak != null && f.peak !== f.start)
					rows.push({ label: U.cmp.peak, sub: date(f.peak_date), cells: [rating(f.peak)] });
				rows.push({ label: U.cmp.now, cells: [rating(f.now)] });
				return { head: [{ label: U.cmp.rating }], rows };
			}
			case 'trend':
				if (f.last_90d == null) return null;
				return {
					head: [{ label: U.cmp.perMonth }],
					rows: [
						{ label: U.cmp.sinceStart, cells: [signed(f.per_month)] },
						{ label: U.cmp.last90, cells: [signed(f.last_90d)] }
					]
				};
			case 'best_period': {
				const p = f.period as Period;
				return {
					head: [{ label: U.cmp.winPct }, { label: U.cmp.matches }],
					rows: [
						{ label: U.cmp.best(p), sub: periodLabel(f.best, p), cells: [pct(f.best_pct), String(f.best_n)] },
						{ label: U.cmp.worst(p), sub: periodLabel(f.worst, p), cells: [pct(f.worst_pct), String(f.worst_n)] }
					]
				};
			}
			case 'halves': {
				const rows: Row[] = [
					{ label: U.halves.matches, cells: [String(f.n_early), String(f.n_late)] },
					{ label: U.halves.won, cells: [pct(f.win_early), pct(f.win_late)] },
					{ label: U.halves.points, cells: [pct(f.points_early), pct(f.points_late)] }
				];
				if (f.opp_early != null && f.opp_late != null)
					rows.push({ label: U.halves.opp, cells: [num(f.opp_early, 2), num(f.opp_late, 2)] });
				return {
					head: [
						{ label: U.halves.then, sub: span(f.early_from, f.early_to) },
						{ label: U.halves.now, sub: span(f.late_from, f.late_to) }
					],
					rows
				};
			}
			case 'impact': {
				const rows: Row[] = [
					{ label: U.cmp.win, cells: [signed(f.win)] },
					{ label: U.cmp.loss, cells: [signed(f.loss)] }
				];
				if (f.close_loss != null && f.heavy_loss != null)
					rows.push(
						{ label: U.cmp.closeLoss, sub: U.cmp.closeLossSub, cells: [signed(f.close_loss)] },
						{ label: U.cmp.heavyLoss, sub: U.cmp.heavyLossSub, cells: [signed(f.heavy_loss)] }
					);
				return { head: [{ label: U.cmp.avgChange }], rows };
			}
		}
		return null;
	}

	const cards = $derived(
		findings.flatMap((f) => {
			const text = (M.findings as Record<string, FindingText>)[f.id]?.(f, fmt);
			if (!text) return [];
			const h = headline(f);
			return [{ id: f.id, title: M.ui.findingTitles[f.id] ?? '', text, value: h?.value, tone: h?.tone, cmp: compare(f) }];
		})
	);
</script>

<div class="grid">
	{#each cards as c (c.id)}
		<article class="card {c.tone ?? ''}">
			<header>
				<span class="title">{c.title}</span>
				{#if c.value}<span class="value">{c.value}</span>{/if}
			</header>
			{#if c.cmp}
				<table class="cmp">
					<thead>
						<tr>
							<th></th>
							{#each c.cmp.head as h (h.label)}<th>{h.label}{#if h.sub}<span class="sub">{h.sub}</span>{/if}</th>{/each}
						</tr>
					</thead>
					<tbody>
						{#each c.cmp.rows as r (r.label)}
							<tr>
								<td>{r.label}{#if r.sub}<span class="sub">{r.sub}</span>{/if}</td>
								{#each r.cells as v, i (i)}<td>{v}</td>{/each}
							</tr>
						{/each}
					</tbody>
				</table>
			{/if}
			<p>{c.text}</p>
		</article>
	{/each}
</div>

<style>
	.grid {
		columns: 3 300px;
		column-gap: 12px;
	}
	.card {
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: 14px;
		padding: 14px 18px 16px;
		margin: 0 0 12px;
		break-inside: avoid;
		--tone: var(--muted);
	}
	.card.good {
		--tone: var(--teal);
	}
	.card.bad {
		--tone: var(--orange);
	}
	header {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 12px;
		margin-bottom: 6px;
	}
	.title {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 12px;
		font-weight: 650;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--ink2);
	}
	.title::before {
		content: '';
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--tone);
		flex: none;
	}
	.value {
		font-size: 22px;
		font-weight: 700;
		letter-spacing: -0.01em;
		color: var(--tone);
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
	}
	.card:not(.good):not(.bad) .value {
		color: var(--ink);
	}
	.cmp {
		width: 100%;
		border-collapse: collapse;
		margin: 4px 0 10px;
		font-size: 13.5px;
		font-variant-numeric: tabular-nums;
	}
	.cmp th,
	.cmp td {
		padding: 4px 0;
		border-bottom: 1px solid var(--line);
		text-align: right;
	}
	.cmp th {
		font-size: 11.5px;
		font-weight: 600;
		color: var(--ink2);
		vertical-align: bottom;
		padding-left: 8px;
	}
	.cmp .sub {
		display: block;
		font-weight: 400;
		font-size: 11px;
	}
	.cmp td:first-child {
		text-align: left;
		color: var(--ink2);
	}
	.cmp td:not(:first-child) {
		font-weight: 600;
		color: var(--ink);
		white-space: nowrap;
		padding-left: 8px;
	}
	.cmp tr:last-child td {
		border-bottom: 0;
	}
	p {
		margin: 0;
		font-size: 14.5px;
		line-height: 1.6;
		color: var(--ink2);
		text-wrap: pretty;
	}
</style>
