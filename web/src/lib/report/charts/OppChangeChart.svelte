<script lang="ts">
	// Average rating change per match against each opponent-strength group.
	import { Tooltip } from 'layerchart';
	import { m } from '../messages.ts';
	import { pct, signed } from '../format.ts';
	import type { FormatData, Group } from '../types.ts';
	import { signColor } from './common.ts';
	import SignedBars from './SignedBars.svelte';

	let { d }: { d: FormatData } = $props();
	const groups = $derived(d.opponent_effect.groups.filter((g) => g.avg_impact != null));
</script>

<SignedBars
	data={groups}
	x="group"
	y="avg_impact"
	xLabel={(g: Group) => `${m().groups[g.group]}\n${m().groupRanges[g.group]}`}
	yFormat={(v) => signed(v, 3)}
	label={(v) => signed(v)}
	axisTitle={m().charts.oppAxis}
	height={360}
>
	{#snippet tooltip(g: Group)}
		<Tooltip.Header value={`${m().groups[g.group]} (${m().groupRanges[g.group]})`} />
		<Tooltip.List>
			<Tooltip.Item label={m().charts.perMatch} value={signed(g.avg_impact)} color={signColor((g.avg_impact ?? 0) >= 0)} />
			<Tooltip.Item label={m().col.pointWin} value={pct(g.point_share)} />
			<Tooltip.Item label={m().col.matches} value={g.matches} />
		</Tooltip.List>
	{/snippet}
</SignedBars>
