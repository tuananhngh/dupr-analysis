<script lang="ts">
	// Your rating vs the average rating of the opponents you face: are you playing up?
	import { Axis, Chart, Circle, Highlight, Layer, Points, Spline, Tooltip } from 'layerchart';
	import { scaleTime } from 'd3-scale';
	import { curveStepAfter } from 'd3-shape';
	import { m } from '../messages.ts';
	import { date, num, rating, timeTicks } from '../format.ts';
	import type { FormatData } from '../types.ts';
	import { TEAL, FAINT, ORANGE, PAD, toDate } from './common.ts';
	import Legend from './Legend.svelte';

	let { d }: { d: FormatData } = $props();
	const rows = $derived(d.opponent_level.map((r) => ({ ...r, date: toDate(r.date) })));
	const rolling = $derived(rows.filter((r) => r.opp_rolling != null));
	const mine = $derived(rows.filter((r) => r.rating_before != null));
	// Range covering every opponent dot and your rating, with some room above and below.
	const yDomain = $derived.by(() => {
		const ys = [...rows.map((r) => r.opp_rating_avg), ...mine.map((r) => r.rating_before as number)];
		const lo = Math.min(...ys),
			hi = Math.max(...ys);
		const pad = Math.max((hi - lo) * 0.08, 0.05);
		return [lo - pad, hi + pad];
	});
	const legend = $derived([
		{ label: m().charts.oppEach, color: FAINT, kind: 'dot' as const },
		{ label: m().charts.oppLevel(d.summary.rolling_window), color: ORANGE, kind: 'line' as const },
		{ label: m().charts.yourRating, color: TEAL, kind: 'line' as const }
	]);
</script>

<Legend items={legend} />
<div class="box">
	<Chart
		data={rows}
		x="date"
		xScale={scaleTime()}
		y="opp_rating_avg"
		{yDomain}
		padding={PAD}
		tooltipContext={{ mode: 'quadtree-x' }}
	>
		<Layer type="svg">
			<Axis placement="left" grid format={(v: number) => num(v, 2)} ticks={5} />
			<Axis placement="bottom" rule format={timeTicks(rows[0].date, rows[rows.length - 1].date)} ticks={6} />
			<Points y="opp_rating_avg">
				{#snippet children({ points })}
					{#each points as p, i (i)}<Circle cx={p.x} cy={p.y} r={3} fill={FAINT} />{/each}
				{/snippet}
			</Points>
			<Spline data={rolling} y="opp_rolling" stroke={ORANGE} strokeWidth={2} />
			<Spline data={mine} y="rating_before" curve={curveStepAfter} stroke={TEAL} strokeWidth={2} />
			<Highlight lines />
		</Layer>
		<Tooltip.Root>
			{#snippet children({ data })}
				<Tooltip.Header value={date(data.date)} />
				<Tooltip.List>
					<Tooltip.Item label={data.opponents} value={rating(data.opp_rating_avg)} color={FAINT} />
					<Tooltip.Item label={m().charts.oppLevel(d.summary.rolling_window)} value={rating(data.opp_rolling)} color={ORANGE} />
					<Tooltip.Item label={m().charts.yourRating} value={rating(data.rating_before)} color={TEAL} />
				</Tooltip.List>
			{/snippet}
		</Tooltip.Root>
	</Chart>
</div>

<style>
	.box {
		height: 360px;
	}
</style>
