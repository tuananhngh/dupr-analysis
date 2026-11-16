<script lang="ts">
	import { m } from '../messages.ts';

	export type Range = '3m' | '6m' | '1y' | 'all';
	let { value = $bindable('all') }: { value: Range } = $props();
	const RANGES: Range[] = ['3m', '6m', '1y', 'all'];
</script>

<div class="ranges" role="group">
	{#each RANGES as r (r)}
		<button type="button" aria-pressed={value === r} onclick={() => (value = r)}>{m().charts.ranges[r]}</button>
	{/each}
</div>

<style>
	.ranges {
		display: inline-flex;
		border: 1px solid var(--line);
		border-radius: 8px;
		overflow: hidden;
		margin: 0 0 8px;
	}
	button {
		background: var(--surface);
		color: var(--ink2);
		border: 0;
		border-radius: 0;
		padding: 4px 10px;
		font-size: 13px;
		font-weight: 600;
	}
	button[aria-pressed='true'] {
		background: var(--accent-soft);
		color: var(--ink);
	}
	@media print {
		.ranges {
			display: none;
		}
	}
</style>
