<script lang="ts">
	// Top of a format: the rating with its curve, the record and the last results at a glance.
	import { m } from './messages.ts';
	import { date, isNum, monthYear, pct, rating, signed } from './format.ts';
	import type { FormatData } from './types.ts';

	let { d }: { d: FormatData } = $props();
	const M = $derived(m());
	const s = $derived(d.summary);

	const FORM_N = 10;
	const last = $derived(d.matches.slice(-FORM_N));
	const streak = $derived.by(() => {
		const ms = d.matches;
		if (!ms.length) return null;
		const won = ms[ms.length - 1].won;
		let n = 0;
		for (let i = ms.length - 1; i >= 0 && ms[i].won === won; i--) n++;
		return { won, n };
	});

	const W = 240,
		H = 64;
	const spark = $derived.by(() => {
		const pts = d.rating;
		if (pts.length < 2) return null;
		const ys = pts.map((p) => p.rating);
		const lo = Math.min(...ys),
			hi = Math.max(...ys),
			span = hi - lo || 1;
		const xy = pts.map((p, i) => [(i / (pts.length - 1)) * W, H - 4 - ((p.rating - lo) / span) * (H - 8)]);
		const line = xy.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
		return { line, area: `0,${H} ${line} ${W},${H}`, end: xy[xy.length - 1] };
	});
	const up = $derived((s.rating_change ?? 0) >= 0);
</script>

<div class="hero">
	<div class="rating">
		<div class="lbl">{M.ui.ratingLabel}</div>
		<div class="big">{rating(s.rating_now)}</div>
		{#if isNum(s.rating_change)}
			<div class="chg">
				<span class="pill" class:up class:down={!up}>{up ? '▲' : '▼'} {signed(s.rating_change)}</span>
				<span class="muted">{M.ui.since(monthYear(s.first_match))}</span>
			</div>
		{/if}
	</div>

	{#if spark}
		<div class="spark">
			<svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" aria-hidden="true">
				<polygon points={spark.area} class="area" />
				<polyline points={spark.line} class="line" />
			</svg>
			{#if isNum(s.rating_peak)}<div class="muted small">{M.ui.peak(rating(s.rating_peak))}</div>{/if}
		</div>
	{/if}

	<div class="record">
		<div class="lbl">{M.ui.record}</div>
		<div class="mid"><span class="w">{s.wins}</span>–<span class="l">{s.losses}</span></div>
		<div class="muted small">{M.ui.winRate(pct(s.win_pct))} · {M.ui.matchesPlayed(s.matches)}</div>
	</div>

	<div class="form">
		<div class="lbl">{M.ui.lastN(last.length)}</div>
		<div class="dots">
			{#each last as x, i (i)}
				<span
					class="dot"
					class:won={x.won}
					title="{date(x.date)} · {x.game_scores} · {signed(x.rating_impact)}">{x.won ? M.col.w : M.col.l}</span
				>
			{/each}
		</div>
		{#if streak}<div class="muted small">{M.ui.streakNow(streak.won, streak.n)}</div>{/if}
	</div>
</div>

<style>
	.hero {
		display: grid;
		grid-template-columns: auto minmax(160px, 1fr) auto auto;
		gap: 20px 32px;
		align-items: center;
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: 16px;
		padding: 20px 24px;
		break-inside: avoid;
	}
	.lbl {
		font-size: 12px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--ink2);
	}
	.big {
		font-size: 48px;
		font-weight: 700;
		line-height: 1.1;
		font-variant-numeric: tabular-nums;
	}
	.mid {
		font-size: 30px;
		font-weight: 700;
		line-height: 1.25;
		font-variant-numeric: tabular-nums;
	}
	.w {
		color: var(--blue);
	}
	.l {
		color: var(--orange);
	}
	.chg {
		display: flex;
		gap: 8px;
		align-items: center;
		flex-wrap: wrap;
		font-size: 14px;
	}
	.pill {
		font-weight: 650;
		border-radius: 999px;
		padding: 2px 10px;
		font-variant-numeric: tabular-nums;
	}
	.pill.up {
		background: var(--accent-soft);
		color: var(--blue);
	}
	.pill.down {
		background: #fde9e0;
		color: #b4471c;
	}
	.muted {
		color: var(--ink2);
	}
	.small {
		font-size: 13px;
	}
	.spark svg {
		display: block;
		width: 100%;
		height: 64px;
	}
	.line {
		fill: none;
		stroke: var(--blue);
		stroke-width: 2;
		vector-effect: non-scaling-stroke;
		stroke-linejoin: round;
	}
	.area {
		fill: var(--accent-soft);
	}
	.dots {
		display: flex;
		gap: 4px;
		margin: 6px 0 4px;
	}
	.dot {
		width: 22px;
		height: 22px;
		border-radius: 6px;
		display: grid;
		place-items: center;
		font-size: 11px;
		font-weight: 700;
		color: #fff;
		background: var(--orange);
		cursor: default;
	}
	.dot.won {
		background: var(--blue);
	}
	@media (max-width: 820px) {
		.hero {
			grid-template-columns: 1fr 1fr;
		}
		.spark {
			grid-column: 1 / -1;
			grid-row: 2;
		}
	}
	@media (max-width: 480px) {
		.hero {
			grid-template-columns: 1fr;
			padding: 16px;
		}
		.big {
			font-size: 40px;
		}
		.dot {
			width: 20px;
			height: 20px;
		}
	}
</style>
