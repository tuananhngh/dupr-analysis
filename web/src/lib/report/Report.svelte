<script lang="ts">
	// The whole report, written in the page language from the data computed in Python.
	import { m } from './messages.ts';
	import { date } from './format.ts';
	import type { ReportData } from './types.ts';
	import FormatSection from './FormatSection.svelte';

	let { data, demo = false }: { data: ReportData; demo?: boolean } = $props();
	const M = $derived(m());
</script>

<main>
	<header>
		<h1>{M.reportTitle}</h1>
		<p class="muted">{M.generated(data.player, date(data.generated))}</p>
		{#if demo}<p class="demo">{M.exampleBanner}</p>{/if}
		<details>
			<summary>{M.glossaryTitle}</summary>
			<dl>
				{#each M.glossary as [term, def] (term)}<dt>{term}</dt><dd>{def}</dd>{/each}
			</dl>
		</details>
	</header>
	{#each data.formats as f (f.format)}
		<FormatSection d={f} />
	{:else}
		<p>{M.noMatches}</p>
	{/each}
</main>

<style>
	main {
		max-width: 1080px;
		margin: 0 auto;
		padding: 28px 16px 72px;
	}
	h1 {
		font-size: 28px;
		margin: 0 0 4px;
	}
	.muted {
		color: var(--ink2);
		margin: 0 0 8px;
	}
	.demo {
		display: inline-block;
		background: var(--accent-soft);
		border-radius: 8px;
		padding: 6px 12px;
		margin: 4px 0 8px;
	}
	details {
		margin: 12px 0;
	}
	summary {
		cursor: pointer;
		font-weight: 600;
		font-size: 16px;
	}
	dl {
		display: grid;
		grid-template-columns: max-content 1fr;
		gap: 6px 14px;
		font-size: 14px;
		color: var(--ink2);
		margin: 10px 0 0;
	}
	dt {
		font-weight: 600;
		color: var(--ink);
	}
	dd {
		margin: 0;
	}
	@media (max-width: 600px) {
		dl {
			grid-template-columns: 1fr;
		}
	}
	@media print {
		details {
			display: none;
		}
	}
</style>
