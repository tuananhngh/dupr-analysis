<script lang="ts">
	// Everything runs in this browser tab: Python (Pyodide) runs the same analysis code as
	// the local version (dupr/*.py), on data the Sync DUPR bookmark brings in the #fragment.
	import { onMount } from 'svelte';
	import { buildReport } from '#lib/analysis.ts';
	import { bookmarkletHref } from '#lib/bookmarklet.ts';
	import { lastSyncStore, type LastSync } from '#lib/storage.ts';
	import SyncSteps from '#lib/components/SyncSteps.svelte';
	import LastSyncCard from '#lib/components/LastSyncCard.svelte';
	import ProgressCard from '#lib/components/ProgressCard.svelte';
	import ReportView from '#lib/components/ReportView.svelte';

	type Job = { pct: number; step: string; error: boolean };

	let bookmark = $state('');
	let lastSync = $state<LastSync | null>(null);
	let job = $state<Job | null>(null);
	let reportHtml = $state<string | null>(null);
	let showReport = $state(false);

	const busy = $derived(job !== null && !job.error);

	async function run(payload: string) {
		job = { pct: 0, step: 'Starting…', error: false };
		try {
			reportHtml = await buildReport(payload, (pct, step) => {
				if (job) Object.assign(job, { pct, step });
			});
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
			run(payload);
		} else {
			lastSync = lastSyncStore.get();
		}
	});
</script>

{#if showReport && reportHtml}
	<ReportView html={reportHtml} onback={() => (showReport = false)} />
{:else}
	<main>
		<h1>DUPR performance analysis</h1>
		<p>
			See how your pickleball game evolves: your rating over time, form, results against what the ratings
			predict, partners, opponents and what to work on.
		</p>

		{#if lastSync && !busy}
			<LastSyncCard at={lastSync.at} onopen={() => run(lastSync!.payload)} onforget={forget} />
		{/if}

		{#if job}
			<ProgressCard {...job} />
		{/if}

		<SyncSteps href={bookmark} />
	</main>
{/if}

<style>
	main {
		max-width: 600px;
		margin: 48px auto;
		padding: 0 16px;
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
	:global(button.link) {
		background: none;
		color: var(--ink2);
		padding: 0;
		font-weight: 500;
		text-decoration: underline;
	}
</style>
