<script lang="ts">
	// Everything runs in this browser tab: Python (Pyodide) runs the analysis (dupr/*.py) on the data
	// the Sync DUPR bookmark brings in the #fragment and returns numbers; the report is drawn here.
	// #demo opens the report for the built-in sample player.
	import { onMount } from 'svelte';
	import { buildDemo, buildReport } from '#lib/analysis.ts';
	import { bookmarkletHref } from '#lib/bookmarklet.ts';
	import { lastSyncStore, saveLocally, type LastSync } from '#lib/storage.ts';
	import type { ReportData } from '#lib/report/types.ts';
	import SyncSteps from '#lib/components/SyncSteps.svelte';
	import LastSyncCard from '#lib/components/LastSyncCard.svelte';
	import ProgressCard from '#lib/components/ProgressCard.svelte';
	import ReportView from '#lib/components/ReportView.svelte';
	import LangSwitch from '#lib/components/LangSwitch.svelte';
	import { t, type Key } from '#lib/i18n.svelte.ts';

	// `step` is a translation key while building; on error it holds the raw error message.
	type Job = { pct: number; step: string; error: boolean };

	let bookmark = $state('');
	let lastSync = $state<LastSync | null>(null);
	let job = $state<Job | null>(null);
	let report = $state<ReportData | null>(null);
	let demo = $state(false);
	let showReport = $state(false);

	const busy = $derived(job !== null && !job.error);

	/** `payload` from the bookmark, or null for the sample player. */
	async function run(payload: string | null) {
		job = { pct: 0, step: 'starting', error: false };
		const progress = (pct: number, step: Key) => {
			if (job) Object.assign(job, { pct, step });
		};
		try {
			report = payload === null ? await buildDemo(progress) : await buildReport(payload, progress);
			demo = payload === null;
			job = null;
			showReport = true;
		} catch (e) {
			console.error(e);
			const msg = String((e as Error)?.message ?? e).split('\n').slice(-2).join(' ');
			job = { pct: 0, step: msg, error: true };
		} finally {
			lastSync = lastSyncStore.get();
		}
	}

	function forget() {
		lastSyncStore.clear();
		lastSync = null;
	}

	onMount(() => {
		// The bookmark sends the data back to this exact page.
		bookmark = bookmarkletHref(location.origin + location.pathname);
		if (location.hash.startsWith('#d=')) {
			// Data just arrived from the bookmark.
			const payload = location.hash.slice(1);
			history.replaceState(history.state, '', location.pathname); // remove the data from the address bar
			lastSyncStore.set({ payload, at: Date.now() });
			saveLocally(payload);
			run(payload);
		} else if (location.hash === '#demo') {
			lastSync = lastSyncStore.get();
			run(null);
		} else {
			lastSync = lastSyncStore.get();
		}
	});
</script>

{#if showReport && report}
	<ReportView data={report} {demo} onback={() => (showReport = false)} />
{:else}
	<main>
		<div class="top">
			<h1>{t('title')}</h1>
			<LangSwitch />
		</div>
		<p>{t('intro')}</p>

		{#if lastSync && !busy}
			<LastSyncCard at={lastSync.at} onopen={() => run(lastSync!.payload)} onforget={forget} />
		{/if}

		{#if job}
			<ProgressCard {...job} />
		{/if}

		<SyncSteps href={bookmark} />
		{#if !busy}
			<p class="demo"><button class="link" onclick={() => run(null)}>{t('demo')}</button></p>
		{/if}
	</main>
{/if}

<style>
	main {
		max-width: 600px;
		margin: 48px auto;
		padding: 0 16px;
	}
	.top {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 12px;
	}
	h1 {
		font-size: 26px;
		margin: 0 0 4px;
	}
	p {
		color: var(--ink2);
	}
	/* Shared by the cards (components) */
	main :global(.card) {
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: 12px;
		padding: 20px 22px;
		margin: 16px 0;
	}
	main :global(.card p) {
		color: var(--ink2);
	}
	main :global(.small) {
		font-size: 13px;
		color: var(--ink2);
	}
	main :global(.row) {
		display: flex;
		gap: 12px;
		flex-wrap: wrap;
		align-items: center;
	}
	:global(button) {
		display: inline-block;
		padding: 10px 16px;
		border-radius: 8px;
		border: 0;
		background: var(--accent);
		color: #fff;
		font: inherit;
		font-weight: 600;
		cursor: pointer;
	}
	:global(button.secondary) {
		background: #fff;
		color: var(--accent);
		border: 1px solid var(--accent);
	}
	.demo {
		font-size: 14px;
		margin: 4px 0;
	}
	:global(button.link) {
		background: none;
		color: var(--ink2);
		padding: 0;
		font-weight: 500;
		text-decoration: underline;
	}
</style>
