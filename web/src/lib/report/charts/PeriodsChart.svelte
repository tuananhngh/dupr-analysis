<script lang="ts">
	// Share of matches won (bars) and of points won (line) per week / month / quarter.
	import { Tooltip } from 'layerchart';
	import { m } from '../messages.ts';
	import { pct, periodLabel } from '../format.ts';
	import type { FormatData } from '../types.ts';
	import { BLUE, ORANGE } from './common.ts';
	import BarsWithLine from './BarsWithLine.svelte';

	let { d }: { d: FormatData } = $props();
	type Row = FormatData['periods'][number];
	const period = $derived(d.summary.period);
</script>

<BarsWithLine
	data={d.periods}
	bar="win_pct"
	line="point_share"
	xLabel={(r: Row) => periodLabel(r.period_end, period)}
	barName={m().charts.winPct}
	lineName={m().charts.pointWinPct}
	rule50
>
	{#snippet tooltip(r: Row)}
		<Tooltip.Header value={periodLabel(r.period_end, period)} />
		<Tooltip.List>
			<Tooltip.Item label={m().charts.winPct} value={`${pct(r.win_pct)} (${m().charts.winsOf(r.wins, r.matches)})`} color={BLUE} />
			<Tooltip.Item label={m().charts.pointWinPct} value={pct(r.point_share, 1)} color={ORANGE} />
		</Tooltip.List>
	{/snippet}
</BarsWithLine>
