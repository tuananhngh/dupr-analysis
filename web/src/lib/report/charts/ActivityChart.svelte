<script lang="ts">
	// Matches played per week / month / quarter.
	import { Tooltip } from 'layerchart';
	import { m } from '../messages.ts';
	import { pct, periodLabel } from '../format.ts';
	import type { FormatData } from '../types.ts';
	import SignedBars from './SignedBars.svelte';

	let { d }: { d: FormatData } = $props();
	type Row = FormatData['periods'][number];
	const period = $derived(d.summary.period);
</script>

<SignedBars
	data={d.periods}
	x="period_end"
	y="matches"
	xLabel={(r: Row) => periodLabel(r.period_end, period)}
	yFormat={(v) => String(v)}
	label={(v) => String(v)}
	height={300}
>
	{#snippet tooltip(r: Row)}
		<Tooltip.Header value={periodLabel(r.period_end, period)} />
		<Tooltip.List>
			<Tooltip.Item label={m().col.matches} value={r.matches} />
			<Tooltip.Item label={m().col.winPct} value={pct(r.win_pct)} />
		</Tooltip.List>
	{/snippet}
</SignedBars>
