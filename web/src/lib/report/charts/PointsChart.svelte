<script lang="ts">
	// Per month: points won (dot) vs what the ratings predict (dash), joined by a segment that is
	// teal when above the expectation and orange when below.
	import { Axis, Chart, Circle, Highlight, Layer, Line, Rule, Text, Tooltip } from 'layerchart';
	import { scaleBand } from 'd3-scale';
	import { m } from '../messages.ts';
	import { monthShort, monthYear, pct, signed } from '../format.ts';
	import type { FormatData } from '../types.ts';
	import { TEAL, MUTED, ORANGE, PAD, SURFACE, signColor, thinTicks } from './common.ts';
	import Legend from './Legend.svelte';

	let { d }: { d: FormatData } = $props();
	const rows = $derived(d.monthly_points.map((r) => ({ ...r, _x: monthShort(r.month) })));
	const showLabels = $derived(rows.length <= 14);
	const legend = $derived([
		{ label: m().charts.expected, color: 'var(--ink2)', kind: 'line' as const },
		{ label: m().charts.above, color: TEAL, kind: 'dot' as const },
		{ label: m().charts.below, color: ORANGE, kind: 'dot' as const }
	]);
</script>

<Legend items={legend} />
<div class="box">
	<Chart
		data={rows}
		x="_x"
		xScale={scaleBand().padding(0.3)}
		y={['expected', 'actual']}
		yNice
		yPadding={[20, 20]}
		padding={PAD}
		tooltipContext={{ mode: 'band' }}
	>
		{#snippet children({ context })}
			{@const half = (context.xScale.bandwidth?.() ?? 0) / 2}
			<Layer type="svg">
				<Axis placement="left" grid format={(v: number) => pct(v)} ticks={5} />
				<Axis placement="bottom" tickMarks={false} ticks={thinTicks(rows.map((r) => r._x), context.width)} />
				<Highlight area />
				<Rule y={50} stroke={MUTED} dashArray="2 3" />
				{#each rows as r (r.month)}
					{@const cx = context.xScale(r._x) + half}
					{@const ye = context.yScale(r.expected)}
					{@const ya = context.yScale(r.actual)}
					{@const color = signColor(r.gap >= 0)}
					<Line x1={cx} x2={cx} y1={ye} y2={ya} stroke={color} strokeWidth={4} />
					<Line x1={cx - 9} x2={cx + 9} y1={ye} y2={ye} stroke="var(--ink2)" strokeWidth={2} />
					<Circle {cx} cy={ya} r={5.5} fill={color} stroke={SURFACE} strokeWidth={2} />
					{#if showLabels}
						<Text x={cx} y={ya} dy={r.gap >= 0 ? -12 : 18} value={pct(r.actual)} textAnchor="middle" class="lbl" />
					{/if}
				{/each}
			</Layer>
			<Tooltip.Root>
				{#snippet children({ data })}
					<Tooltip.Header value={monthYear(data.month)} />
					<Tooltip.List>
						<Tooltip.Item label={m().charts.you} value={m().charts.pointsTip(pct(data.actual), signed(data.gap, 0))} color={signColor(data.gap >= 0)} />
						<Tooltip.Item label={m().charts.expected} value={pct(data.expected)} />
						<Tooltip.Item label={m().col.matches} value={data.matches} />
						<Tooltip.Item label={m().col.ratingChange} value={signed(data.rating_change)} />
					</Tooltip.List>
				{/snippet}
			</Tooltip.Root>
		{/snippet}
	</Chart>
</div>

<style>
	.box {
		height: 340px;
	}
	.box :global(.lbl) {
		font-size: 11px;
		fill: var(--ink2);
	}
</style>
