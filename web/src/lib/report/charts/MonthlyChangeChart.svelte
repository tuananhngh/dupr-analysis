<script lang="ts">
	// Net rating change in each month played.
	import { Tooltip } from 'layerchart';
	import { m } from '../messages.ts';
	import { monthShort, monthYear, rating, signed } from '../format.ts';
	import type { FormatData } from '../types.ts';
	import { signColor } from './common.ts';
	import SignedBars from './SignedBars.svelte';

	let { d }: { d: FormatData } = $props();
	type Row = FormatData['monthly_rating'][number];
</script>

<SignedBars
	data={d.monthly_rating}
	x="month"
	y="change"
	xLabel={(r: Row) => monthShort(r.month)}
	yFormat={(v) => signed(v, 2)}
	label={(v) => signed(v)}
>
	{#snippet tooltip(r: Row)}
		<Tooltip.Header value={monthYear(r.month)} />
		<Tooltip.List>
			<Tooltip.Item label={m().col.ratingChange} value={signed(r.change)} color={signColor(r.change >= 0)} />
			<Tooltip.Item label={m().col.matches} value={m().charts.winsOf(r.wins, r.matches)} />
			<Tooltip.Item label={m().col.ratingEnd} value={rating(r.rating_end)} />
		</Tooltip.List>
	{/snippet}
</SignedBars>
