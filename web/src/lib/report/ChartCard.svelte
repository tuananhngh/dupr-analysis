<script lang="ts">
	import type { Snippet } from 'svelte';

	let { title, caption, children }: { title: string; caption?: string; children: Snippet } = $props();
</script>

<figure class="card">
	<figcaption class="title">{title}</figcaption>
	{@render children()}
	{#if caption}<p class="cap">{caption}</p>{/if}
</figure>

<style>
	.card {
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: 12px;
		padding: 14px 16px 6px;
		margin: 12px 0;
		min-width: 0;
		break-inside: avoid;
	}
	.title {
		font-size: 16px;
		font-weight: 600;
		color: var(--ink);
		margin: 0 0 8px;
	}
	.cap {
		margin: 6px 0 10px;
		font-size: 14px;
		color: var(--ink2);
	}
</style>
