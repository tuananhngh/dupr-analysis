<script lang="ts">
	// Win % with each partner (2+ matches), most-played first, with a reference line at 50%.
	import { Axis, Bars, Chart, Labels, Layer, Rule, Tooltip } from 'layerchart';
	import { scaleBand } from 'd3-scale';
	import { m } from '../messages.ts';
	import { pct, signed } from '../format.ts';
	import type { FormatData } from '../types.ts';
	import { TEAL, MUTED, PAD, barWidth } from './common.ts';

	let { d }: { d: FormatData } = $props();
	const rows = $derived(
		d.partners
			.filter((p) => p.matches >= 2)
			.slice(0, 12)
			.sort((a, b) => (b.win_pct ?? 0) - (a.win_pct ?? 0))
	);
	const height = $derived(Math.max(220, 36 * rows.length + 60));
	// Size the name column to the longest name (≈7px per char at 12px), truncating very long ones.
	const MAX_CHARS = 24;
	const short = (s: string) => (s.length > MAX_CHARS ? s.slice(0, MAX_CHARS - 1) + '…' : s);
	const left = $derived(
		Math.min(MAX_CHARS, Math.max(8, ...rows.map((r) => r.partner.length))) * 7 + 16
	);
</script>

<div class="box" style:height="{height}px">
	<Chart
		data={rows}
		x="win_pct"
		xDomain={[0, 100]}
		y="partner"
		yScale={scaleBand().padding(0.3)}
		padding={{ ...PAD, left, right: 56 }}
		tooltipContext={{ mode: 'band' }}
	>
		{#snippet children({ context })}
			<Layer type="svg">
				<Axis placement="bottom" grid format={(v: number) => pct(v)} ticks={[0, 25, 50, 75, 100]} />
				<Axis placement="left" format={(v: string) => short(v)} />
				<Bars height={barWidth(context.yScale.bandwidth?.())} radius={4} rounded="right" fill={TEAL} />
				<Rule x={50} stroke={MUTED} dashArray="2 3" />
				<Labels format={(v: number) => pct(v)} class="lbl" />
			</Layer>
			<Tooltip.Root>
				{#snippet children({ data })}
					<Tooltip.Header value={data.partner} />
					<Tooltip.List>
						<Tooltip.Item label={m().col.winPct} value={`${pct(data.win_pct)} (${m().charts.winsOf(data.wins, data.matches)})`} />
						<Tooltip.Item label={m().col.ratingChange} value={signed(data.rating_gained)} />
					</Tooltip.List>
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
