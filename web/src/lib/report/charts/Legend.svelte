<script lang="ts">
	// HTML legend: the key mirrors the mark (line, dashed line, dot or bar).
	export type LegendItem = { label: string; color: string; kind: 'line' | 'dash' | 'dot' | 'bar' };
	let { items }: { items: LegendItem[] } = $props();
</script>

<ul class="legend">
	{#each items as it (it.label)}
		<li>
			<svg width="18" height="10" aria-hidden="true">
				{#if it.kind === 'line' || it.kind === 'dash'}
					<line x1="1" x2="17" y1="5" y2="5" stroke={it.color} stroke-width="2" stroke-linecap="round"
						stroke-dasharray={it.kind === 'dash' ? '4 3' : undefined} />
				{:else if it.kind === 'dot'}
					<circle cx="9" cy="5" r="4" fill={it.color} />
				{:else}
					<rect x="3" y="0" width="12" height="10" rx="2" fill={it.color} />
				{/if}
			</svg>
			{it.label}
		</li>
	{/each}
</ul>

<style>
	.legend {
		display: flex;
		flex-wrap: wrap;
		gap: 4px 16px;
		list-style: none;
		padding: 0;
		margin: 0 0 6px;
		font-size: 13px;
		color: var(--ink2);
	}
	li {
		display: flex;
		align-items: center;
		gap: 6px;
	}
</style>
