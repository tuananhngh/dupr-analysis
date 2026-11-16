<script lang="ts" generics="T extends object">
	// Columns on a category axis, blue when the value is >= 0 and orange below, with a zero line.
	// Used for the rating change per month and per opponent group.
	import type { Snippet } from 'svelte';
	import { Axis, Bar, Bars, Chart, Highlight, Labels, Layer, Rule, Tooltip } from 'layerchart';
	import { scaleBand } from 'd3-scale';
	import { MUTED, PAD, barWidth, signColor, thinTicks } from './common.ts';

	let {
		data,
		x,
		y,
		xLabel,
		yFormat,
		label,
		tooltip,
		height = 340,
		axisTitle
	}: {
		data: T[];
		x: keyof T & string;
		y: keyof T & string;
		xLabel: (row: T) => string;
		yFormat: (v: number) => string;
		/** Value printed at each bar end; omitted when there are too many bars to read them. */
		label?: (v: number) => string;
		tooltip: Snippet<[T]>;
		height?: number;
		axisTitle?: string;
	} = $props();

	const rows = $derived(data.map((r) => ({ ...r, _x: xLabel(r) })));
	const showLabels = $derived(!!label && rows.length <= 14);
	// Bars grow from zero, so zero is always on the axis.
	const yDomain = $derived.by(() => {
		const v = data.map((r) => (r as Record<string, unknown>)[y] as number).filter((x) => x != null);
		return [Math.min(0, ...v), Math.max(0, ...v)];
	});
</script>

<div class="box" style:height="{height}px">
	<Chart
		data={rows}
		x="_x"
		xScale={scaleBand().padding(0.3)}
		{y}
		{yDomain}
		yNice
		yPadding={[18, 18]}
		padding={{ ...PAD, bottom: axisTitle ? 44 : PAD.bottom }}
		tooltipContext={{ mode: 'band' }}
	>
		{#snippet children({ context })}
			{@const bw = barWidth(context.xScale.bandwidth?.())}
			<Layer type="svg">
				<Axis placement="left" grid format={yFormat} ticks={5} />
				<Axis placement="bottom" tickMarks={false} label={axisTitle} ticks={thinTicks(rows.map((r) => r._x), context.width, axisTitle ? 90 : 64)} />
				<Highlight area />
				<Bars>
					{#each rows as r, i (i)}
						<Bar data={r} width={bw} radius={4} rounded="edge" fill={signColor(((r as Record<string, unknown>)[y] as number) >= 0)} />
					{/each}
				</Bars>
				<Rule y={0} stroke={MUTED} />
				{#if showLabels && label}<Labels format={label} class="lbl" />{/if}
			</Layer>
			<Tooltip.Root>
				{#snippet children({ data: row })}
					{@render tooltip(row as T)}
				{/snippet}
			</Tooltip.Root>
		{/snippet}
	</Chart>
</div>

<style>
	.box :global(.lbl) {
		font-size: 12px;
		fill: var(--ink2);
	}
</style>
