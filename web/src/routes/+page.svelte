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
	import ReportPreview from '#lib/components/ReportPreview.svelte';
	import logo from '#lib/assets/favicon.svg';
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

	const features: { title: Key; text: Key; icon: string }[] = [
		{ title: 'f1t', text: 'f1d', icon: 'M3 17l6-6 4 4 8-8M15 7h6v6' },
		{ title: 'f2t', text: 'f2d', icon: 'M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM3 20c0-3.3 2.7-6 6-6s6 2.7 6 6M17 11a3 3 0 1 0 0-6M21 20c0-2.6-1.6-4.8-4-5.6' },
		{ title: 'f3t', text: 'f3d', icon: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM12 12h.01' },
		{ title: 'f4t', text: 'f4d', icon: 'M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.4 1 1.1 1 1.8V16h5v-.3c0-.7.4-1.4 1-1.8A6 6 0 0 0 12 3z' }
	];

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
		<nav class="top">
			<span class="brand">
				<img src={logo} alt="" width="30" height="30" />
				<span>{t('title')}<span class="tagline">{t('tagline')}</span></span>
			</span>
			<LangSwitch />
		</nav>

		<section class="hero">
			<div class="pitch">
				<h1>{t('heroTitle')}</h1>
				<p class="sub">{t('heroSub')}</p>
				{#if job}
					<ProgressCard {...job} />
				{/if}
				{#if !busy}
					{#if lastSync}
						<LastSyncCard at={lastSync.at} onopen={() => run(lastSync!.payload)} onforget={forget} />
					{/if}
					<div class="ctas">
						{#if !lastSync}<a class="btn" href="#steps">{t('ctaStart')}</a>{/if}
						<button class="secondary" onclick={() => run(null)}>{t('ctaDemo')}</button>
					</div>
					<p class="small">{t('free')}</p>
				{/if}
			</div>
			<div class="shot"><ReportPreview /></div>
		</section>

		<section class="features">
			<h2>{t('featuresTitle')}</h2>
			<div class="grid">
				{#each features as f (f.title)}
					<div class="feature">
						<span class="icon" aria-hidden="true">
							<svg viewBox="0 0 24 24"><path d={f.icon} /></svg>
						</span>
						<h3>{t(f.title)}</h3>
						<p>{t(f.text)}</p>
					</div>
				{/each}
			</div>
		</section>

		<SyncSteps href={bookmark} />
	</main>
{/if}

<style>
	main {
		max-width: 1080px;
		margin: 0 auto;
		padding: 0 16px 64px;
	}
	.top {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 12px;
		padding: 18px 0;
	}
	.brand {
		display: flex;
		align-items: center;
		gap: 10px;
		font-weight: 700;
		font-size: 17px;
	}
	.tagline {
		margin-left: 10px;
		padding-left: 10px;
		border-left: 1px solid var(--faint);
		font-weight: 500;
		font-size: 14px;
		color: var(--ink2);
	}
	@media (max-width: 520px) {
		.tagline {
			display: none;
		}
	}
	.top :global(.lang) {
		margin-top: 0;
	}
	.hero {
		display: grid;
		grid-template-columns: 1.1fr 1fr;
		gap: 48px;
		align-items: center;
		padding: 48px 44px;
		border-radius: 24px;
		background: linear-gradient(135deg, var(--accent-soft) 0%, var(--surface) 70%);
		border: 1px solid var(--line);
	}
	h1 {
		font-size: 44px;
		line-height: 1.1;
		letter-spacing: -0.02em;
		margin: 0 0 16px;
	}
	.sub {
		font-size: 17px;
		color: var(--ink2);
		margin: 0 0 24px;
	}
	.ctas {
		display: flex;
		gap: 12px;
		flex-wrap: wrap;
		margin: 8px 0 10px;
	}
	.btn,
	.ctas button {
		padding: 12px 22px;
		font-size: 16px;
	}
	a.btn {
		display: inline-block;
		border-radius: 8px;
		background: var(--accent);
		color: #fff;
		font-weight: 600;
		text-decoration: none;
		box-shadow: 0 2px 8px rgb(11 122 124 / 0.35);
	}
	.features {
		margin: 56px 0;
	}
	h2 {
		font-size: 24px;
		margin: 0 0 16px;
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 14px;
	}
	.feature {
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: 14px;
		padding: 18px 20px;
	}
	.feature h3 {
		font-size: 16px;
		margin: 12px 0 6px;
	}
	.feature p {
		font-size: 14px;
		margin: 0;
	}
	.icon {
		width: 40px;
		height: 40px;
		border-radius: 10px;
		background: var(--accent-soft);
		display: grid;
		place-items: center;
	}
	.icon svg {
		width: 22px;
		height: 22px;
		fill: none;
		stroke: var(--accent);
		stroke-width: 2;
		stroke-linecap: round;
		stroke-linejoin: round;
	}
	p {
		color: var(--ink2);
	}
	@media (max-width: 900px) {
		.hero {
			grid-template-columns: 1fr;
			padding: 32px 24px;
		}
		.grid {
			grid-template-columns: 1fr 1fr;
		}
	}
	@media (max-width: 520px) {
		h1 {
			font-size: 32px;
		}
		.hero {
			padding: 24px 18px;
			gap: 32px;
		}
		.grid {
			grid-template-columns: 1fr;
		}
	}
	/* Shared by the cards (components) */
	main :global(.card) {
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: 12px;
		padding: 16px 20px;
		margin: 0 0 14px;
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
