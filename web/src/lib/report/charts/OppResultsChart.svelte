<script lang="ts">
	// Win % (actual vs expected) against weaker, similar and stronger opponents.
	import { Tooltip } from 'layerchart';
	import { m } from '../messages.ts';
	import { pct } from '../format.ts';
	import type { FormatData, Group } from '../types.ts';
	import { TEAL, ORANGE } from './common.ts';
	import BarsWithLine from './BarsWithLine.svelte';

	let { d }: { d: FormatData } = $props();
</script>

<BarsWithLine
	data={d.opponent_effect.groups}
	bar="win_pct"
	line="exp_win_pct"
	xLabel={(g: Group) => `${m().groups[g.group]}\n${m().groupRanges[g.group]}\n${m().charts.matchesN(g.matches)}`}
	barName={m().charts.winPct}
	lineName={m().charts.expectedWin}
	axisTitle={m().charts.oppAxis}
	height={380}
>
	{#snippet tooltip(g: Group)}
		<Tooltip.Header value={`${m().groups[g.group]} (${m().groupRanges[g.group]})`} />
		<Tooltip.List>
			<Tooltip.Item label={m().charts.winPct} value={pct(g.win_pct)} color={TEAL} />
			<Tooltip.Item label={m().charts.expectedWin} value={pct(g.exp_win_pct)} color={ORANGE} />
			<Tooltip.Item label={m().col.pointWin} value={pct(g.point_share, 1)} />
			<Tooltip.Item label={m().col.matches} value={g.matches} />
		</Tooltip.List>
	{/snippet}
</BarsWithLine>
