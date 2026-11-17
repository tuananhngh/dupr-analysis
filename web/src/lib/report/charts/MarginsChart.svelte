<script lang="ts">
	// How games end: number of games for each score difference (teal = won, orange = lost).
	import { Axis, Bar, Bars, Chart, Highlight, Layer, Tooltip } from 'layerchart';
	import { scaleBand } from 'd3-scale';
	import { m } from '../messages.ts';
	import { signed } from '../format.ts';
	import type { FormatData } from '../types.ts';
	import { PAD, barWidth, signColor } from './common.ts';

	let { d }: { d: FormatData } = $props();
	// Every margin from the worst loss to the best win keeps its slot, even with no games.
	const domain = $derived.by(() => {
		const ms = d.margins.map((r) => r.margin);
		const lo = Math.min(-11, ...ms),
			hi = Math.max(11, ...ms);
		return Array.from({ length: hi - lo + 1 }, (_, i) => lo + i).filter((x) => x !== 0);
	});
	const ticks = $derived(domain.filter((x) => Math.abs(x) % 2 === 1 || Math.abs(x) === 2));
</script>

<div class="box">
	<Chart
		data={d.margins}
		x="margin"
		xScale={scaleBand().padding(0.15)}
		xDomain={domain}
		y="games"
		yDomain={[0, null]}
		yNice
		padding={{ ...PAD, bottom: 44 }}
		tooltipContext={{ mode: 'band' }}
	>
		{#snippet children({ context })}
			{@const bw = barWidth(context.xScale.bandwidth?.())}
			<Layer type="svg">
				<Axis placement="left" grid ticks={5} format="integer" />
				<Axis placement="bottom" tickMarks={false} {ticks} format={(v: number) => signed(v, 0)} label={m().charts.marginAxis} />
				<Highlight area />
				<Bars>
					{#each d.margins as r (r.margin)}
						<Bar data={r} width={bw} radius={4} rounded="top" fill={signColor(r.margin > 0)} />
					{/each}
				</Bars>
			</Layer>
			<Tooltip.Root>
				{#snippet children({ data })}
					{m().charts.marginTip(signed(data.margin, 0), data.games)}
				{/snippet}
			</Tooltip.Root>
		{/snippet}
	</Chart>
</div>

<style>
	.box {
		height: 320px;
	}
</style>
