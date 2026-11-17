<script lang="ts">
	// Rolling win % over the last N matches vs the win % the ratings predict.
	import { Axis, Chart, Highlight, Layer, Rule, Spline, Text, Tooltip } from 'layerchart';
	import { scaleTime } from 'd3-scale';
	import { m } from '../messages.ts';
	import { date, pct, timeTicks } from '../format.ts';
	import type { FormatData } from '../types.ts';
	import { TEAL, MUTED, ORANGE, PAD, toDate } from './common.ts';
	import Legend from './Legend.svelte';

	let { d }: { d: FormatData } = $props();
	const w = $derived(d.summary.rolling_window);
	const rows = $derived(d.win_form.map((r) => ({ ...r, day: toDate(r.day) })));
	const actual = $derived(rows.filter((r) => r.actual != null));
	const expected = $derived(rows.filter((r) => r.expected != null));
	const now = $derived(actual.length ? [actual[actual.length - 1]] : []);
	const legend = $derived([
		{ label: m().charts.yourWin(w), color: TEAL, kind: 'line' as const },
		...(expected.length ? [{ label: m().charts.expectedWin, color: ORANGE, kind: 'dash' as const }] : [])
	]);
</script>

<Legend items={legend} />
<div class="box">
	<Chart
		data={rows}
		x="day"
		xScale={scaleTime()}
		y="actual"
		yDomain={[0, 100]}
		padding={{ ...PAD, top: 22, right: 24 }}
		tooltipContext={{ mode: 'bisect-x' }}
	>
		<Layer type="svg">
			<Axis placement="left" grid format={(v: number) => pct(v)} ticks={[0, 25, 50, 75, 100]} />
			<Axis placement="bottom" rule format={timeTicks(rows[0].day, rows[rows.length - 1].day)} ticks={6} />
			<Rule y={50} stroke={MUTED} dashArray="2 3" />
			{#if expected.length}
				<Spline data={expected} y="expected" stroke={ORANGE} stroke-dasharray="4 3" strokeWidth={2} />
			{/if}
			<Spline data={actual} y="actual" stroke={TEAL} strokeWidth={2} />
			{#each now as n (n.day)}
				<Text data={[n]} x="day" y="actual" value={`${m().charts.now} ${pct(n.actual)}`} dy={-12} textAnchor="end" class="annot" />
			{/each}
			<Highlight lines />
		</Layer>
		<Tooltip.Root>
			{#snippet children({ data })}
				<Tooltip.Header value={date(data.day)} />
				<Tooltip.List>
					<Tooltip.Item label={m().charts.yourWin(w)} value={pct(data.actual)} color={TEAL} />
					<Tooltip.Item label={m().charts.expectedWin} value={pct(data.expected)} color={ORANGE} />
				</Tooltip.List>
			{/snippet}
		</Tooltip.Root>
	</Chart>
</div>

<style>
	.box {
		height: 340px;
	}
	.box :global(.annot) {
		font-size: 12px;
		font-weight: 600;
		fill: var(--ink);
	}
</style>
