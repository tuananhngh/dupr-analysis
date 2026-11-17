<script lang="ts">
	// The whole report, written in the page language from the data computed in Python.
	import { m } from './messages.ts';
	import { date } from './format.ts';
	import type { ReportData } from './types.ts';
	import FormatSection from './FormatSection.svelte';
	import { printing } from './print.svelte.ts';

	let { data, demo = false }: { data: ReportData; demo?: boolean } = $props();
	const M = $derived(m());

	let picked = $state(0);
	const current = $derived(data.formats[picked] ?? data.formats[0]);
</script>

<main>
	<header>
		<div class="who">
			<h1>{data.player}</h1>
			<p class="muted">{M.generated(M.reportTitle, date(data.generated))}</p>
		</div>
		{#if data.formats.length > 1}
			<div class="switch" role="tablist">
				{#each data.formats as f, i (f.format)}
					<button role="tab" aria-selected={picked === i} class:active={picked === i} onclick={() => (picked = i)}>
						{M.formatName[f.format] ?? f.format}
					</button>
				{/each}
			</div>
		{/if}
	</header>
	{#if demo}<p class="demo">{M.exampleBanner}</p>{/if}

	{#if printing.all}
		{#each data.formats as f (f.format)}<FormatSection d={f} />{/each}
	{:else if current}
		{#key current.format}<FormatSection d={current} />{/key}
	{:else}
		<p>{M.noMatches}</p>
	{/if}

	<details>
		<summary>{M.glossaryTitle}</summary>
		<dl>
			{#each M.glossary as [term, def] (term)}<dt>{term}</dt><dd>{def}</dd>{/each}
		</dl>
	</details>
</main>

<style>
	main {
		max-width: 1080px;
		margin: 0 auto;
		padding: 24px 16px 72px;
	}
	header {
		display: flex;
		justify-content: space-between;
		align-items: flex-end;
		gap: 12px 24px;
		flex-wrap: wrap;
	}
	h1 {
		font-size: 30px;
		margin: 0;
	}
	.muted {
		color: var(--ink2);
		margin: 0;
	}
	.switch {
		display: inline-flex;
		background: var(--line);
		border-radius: 10px;
		padding: 3px;
	}
	.switch button {
		background: none;
		color: var(--ink2);
		padding: 7px 18px;
		border-radius: 8px;
	}
	.switch button.active {
		background: var(--surface);
		color: var(--ink);
		box-shadow: 0 1px 2px rgb(0 0 0 / 0.12);
	}
	.demo {
		display: inline-block;
		background: var(--accent-soft);
		border-radius: 8px;
		padding: 6px 12px;
		margin: 12px 0 0;
	}
	details {
		margin: 40px 0 0;
		border-top: 1px solid var(--line);
		padding-top: 16px;
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
		.switch,
		details {
			display: none;
		}
	}
</style>
