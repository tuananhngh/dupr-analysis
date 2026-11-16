<script lang="ts" generics="T extends object">
	// Blue columns (a share in %) with an orange line + dots on the same category axis. No value
	// labels on the bars: they would collide with the line; the tooltip and the tables have them.
	// Used for win % vs expected win % by opponent group, and win % vs point win % per period.
	import type { Snippet } from 'svelte';
	import { Axis, Bar, Bars, Chart, Circle, Highlight, Layer, Points, Rule, Spline, Tooltip } from 'layerchart';
	import { scaleBand } from 'd3-scale';
	import { pct } from '../format.ts';
	import { BLUE, MUTED, ORANGE, PAD, SURFACE, barWidth, thinTicks } from './common.ts';
	import Legend from './Legend.svelte';

	let {
		data,
		bar,
		line,
		xLabel,
		barName,
		lineName,
		tooltip,
		axisTitle,
		rule50 = false,
		height = 340
	}: {
		data: T[];
		bar: keyof T & string;
		line: keyof T & string;
		xLabel: (row: T) => string;
		barName: string;
		lineName: string;
		tooltip: Snippet<[T]>;
		axisTitle?: string;
		rule50?: boolean;
		height?: number;
	} = $props();

	const rows = $derived(data.map((r) => ({ ...r, _x: xLabel(r) })));
	const lineRows = $derived(rows.filter((r) => (r as Record<string, unknown>)[line] != null));
</script>

<Legend
	items={[
		{ label: barName, color: BLUE, kind: 'bar' },
		{ label: lineName, color: ORANGE, kind: 'line' }
	]}
/>
<div class="box" style:height="{height}px">
	<Chart
		data={rows}
		x="_x"
		xScale={scaleBand().padding(0.3)}
		y={bar}
		yDomain={[0, 100]}
		padding={{ ...PAD, top: 22, bottom: axisTitle ? 58 : PAD.bottom }}
		tooltipContext={{ mode: 'band' }}
	>
		{#snippet children({ context })}
			{@const bw = barWidth(context.xScale.bandwidth?.())}
			<Layer type="svg">
				<Axis placement="left" grid format={(v: number) => pct(v)} ticks={[0, 25, 50, 75, 100]} />
				<Axis placement="bottom" tickMarks={false} label={axisTitle} ticks={thinTicks(rows.map((r) => r._x), context.width, axisTitle ? 90 : 64)} />
				<Highlight area />
				<Bars>
					{#each rows as r, i (i)}
						<Bar data={r} width={bw} radius={4} rounded="top" fill={BLUE} />
					{/each}
				</Bars>
				{#if rule50}<Rule y={50} stroke={MUTED} dashArray="2 3" />{/if}
				<Spline data={lineRows} y={line} stroke={ORANGE} strokeWidth={2} />
				<Points data={lineRows} y={line}>
					{#snippet children({ points })}
						{#each points as p, i (i)}<Circle cx={p.x} cy={p.y} r={4.5} fill={ORANGE} stroke={SURFACE} strokeWidth={2} />{/each}
					{/snippet}
				</Points>
			</Layer>
			<Tooltip.Root>
				{#snippet children({ data: row })}
					{@render tooltip(row as T)}
				{/snippet}
			</Tooltip.Root>
		{/snippet}
	</Chart>
</div>

