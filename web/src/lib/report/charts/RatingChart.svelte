<script lang="ts">
	// DUPR rating over time: step line, one dot per match (teal win / orange loss), dashed trend,
	// Start / Peak / Now labels, and 3 / 6 / 12 month zoom buttons.
	import { Axis, Chart, Circle, Highlight, Layer, Points, Spline, Text, Tooltip } from 'layerchart';
	import { scaleTime } from 'd3-scale';
	import { curveStepAfter } from 'd3-shape';
	import { m } from '../messages.ts';
	import { date, num, rating, signed, timeTicks } from '../format.ts';
	import type { FormatData } from '../types.ts';
	import { TEAL, MUTED, ORANGE, PAD, SURFACE, rangeStart, signColor, toDate } from './common.ts';
	import Legend from './Legend.svelte';
	import RangeButtons, { type Range } from './RangeButtons.svelte';

	let { d }: { d: FormatData } = $props();
	let range = $state<Range>('all');

	const all = $derived(d.rating.map((r) => ({ date: toDate(r.date), rating: r.rating })));
	const last = $derived(all[all.length - 1].date);
	const start = $derived(rangeStart(last, range) ?? all[0].date);

	// Visible part of the rating line, starting with the value it had at `start`.
	const line = $derived.by(() => {
		const inside = all.filter((r) => r.date >= start);
		const before = all.filter((r) => r.date < start).pop();
		return before ? [{ date: start, rating: before.rating }, ...inside] : inside;
	});
	const dots = $derived(
		d.matches
			.filter((x) => x.rating_after != null && toDate(x.date) >= start)
			.map((x) => ({ ...x, date: toDate(x.date), rating: x.rating_after as number }))
	);
	// Trend line, cut at `start` when zoomed in.
	const trend = $derived.by(() => {
		const t = d.trend;
		if (!t) return [];
		const t0 = toDate(t.from).getTime(),
			t1 = toDate(t.to).getTime();
		const at = (ms: number) => t.start + ((t.end - t.start) * (ms - t0)) / (t1 - t0 || 1);
		const s = Math.max(start.getTime(), t0);
		return [
			{ date: new Date(s), rating: at(s) },
			{ date: new Date(t1), rating: t.end }
		];
	});
	// The tooltip can be given a point of the rating line: show the match nearest to it.
	function nearestMatch(at: Date) {
		let best = dots[0];
		for (const x of dots) if (Math.abs(x.date.getTime() - at.getTime()) < Math.abs(best.date.getTime() - at.getTime())) best = x;
		return best;
	}
	const yDomain = $derived.by(() => {
		const ys = [...line.map((r) => r.rating), ...dots.map((x) => x.rating)];
		const lo = Math.min(...ys),
			hi = Math.max(...ys);
		const pad = Math.max((hi - lo) * 0.15, 0.05);
		return [lo - pad, hi + pad];
	});
	const labels = $derived.by(() => {
		const M = m().charts;
		const first = line[0],
			now = line[line.length - 1];
		const peak = line.reduce((a, b) => (b.rating > a.rating ? b : a));
		type Lbl = { date: Date; rating: number; label: string; anchor: 'start' | 'middle' | 'end' };
		const out: Lbl[] = [{ ...first, label: `${M.start} ${rating(first.rating)}`, anchor: 'start' }];
		if (peak.date.getTime() !== now.date.getTime() && peak.date.getTime() !== first.date.getTime())
			out.push({ ...peak, label: `${M.peakLbl} ${rating(peak.rating)}`, anchor: 'middle' });
		out.push({ ...now, label: `${M.now} ${rating(now.rating)}`, anchor: 'end' });
		return out;
	});
	const legend = $derived([
		{ label: m().charts.ratingLine, color: TEAL, kind: 'line' as const },
		{ label: m().charts.win, color: TEAL, kind: 'dot' as const },
		{ label: m().charts.loss, color: ORANGE, kind: 'dot' as const },
		...(d.trend && d.summary.trend_per_month != null
			? [{ label: m().charts.trend(signed(d.summary.trend_per_month)), color: MUTED, kind: 'dash' as const }]
			: [])
	]);
</script>

<RangeButtons bind:value={range} />
<Legend items={legend} />
<div class="box">
	<Chart
		data={dots}
		x="date"
		xScale={scaleTime()}
		xDomain={[start, last]}
		y="rating"
		{yDomain}
		padding={{ ...PAD, right: 24 }}
		tooltipContext={{ mode: 'quadtree-x' }}
	>
		{#snippet children({ context })}
			<Layer type="svg">
				<Axis placement="left" grid format={(v: number) => num(v, 2)} ticks={5} />
				<Axis placement="bottom" rule format={timeTicks(start, last)} ticks={6} />
				<Spline data={line} curve={curveStepAfter} stroke={TEAL} strokeWidth={2} />
				{#if trend.length}
					<Spline data={trend} stroke={MUTED} stroke-dasharray="5 4" strokeWidth={1.5} />
				{/if}
				<Points>
					{#snippet children({ points })}
						{#each points as p, i (i)}
							<Circle cx={p.x} cy={p.y} r={4.5} fill={signColor(p.data.won)} stroke={SURFACE} strokeWidth={2} />
						{/each}
					{/snippet}
				</Points>
				{#each labels as l (l.label)}
					<Text x={context.xScale(l.date)} y={context.yScale(l.rating)} value={l.label} dy={-12} textAnchor={l.anchor} class="annot" />
				{/each}
				<Highlight points lines />
			</Layer>
			<Tooltip.Root>
				{#snippet children({ data })}
					{@const mt = data.game_scores ? data : nearestMatch(data.date)}
					{#if mt}
						<Tooltip.Header value={`${mt.won ? m().charts.win : m().charts.loss} · ${date(mt.date)}`} />
						<Tooltip.List>
							<Tooltip.Item label={m().col.score} value={mt.game_scores} />
							<Tooltip.Item label={m().charts.vs} value={mt.opponents} />
							<Tooltip.Item label={m().col.ratingChange} value={signed(mt.rating_impact)} color={signColor(mt.won)} />
							<Tooltip.Item label={m().charts.ratingAxis} value={rating(mt.rating)} />
						</Tooltip.List>
					{/if}
				{/snippet}
			</Tooltip.Root>
		{/snippet}
	</Chart>
</div>

<style>
	.box {
		height: 400px;
	}
	.box :global(.annot) {
		font-size: 12px;
		font-weight: 600;
		fill: var(--ink);
	}
</style>
