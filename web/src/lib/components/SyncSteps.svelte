<script lang="ts">
	import { onMount } from 'svelte';
	import { t, type Key } from '#lib/i18n.svelte.ts';

	let { href }: { href: string } = $props();

	// Phones have no bookmarks bar and no drag and drop, so there the bookmark is made by hand:
	// copy the code, bookmark any page, then paste the code as that bookmark's address.
	type Device = 'computer' | 'iphone' | 'android';
	const devices: { id: Device; label: Key }[] = [
		{ id: 'computer', label: 'devComputer' },
		{ id: 'iphone', label: 'devIphone' },
		{ id: 'android', label: 'devAndroid' }
	];
	let device = $state<Device>('computer');
	let copied = $state(false);
	let copyFailed = $state(false);

	onMount(() => {
		const ua = navigator.userAgent;
		if (/android/i.test(ua)) device = 'android';
		// iPadOS reports itself as a Mac, so also check for touch.
		else if (/iphone|ipad|ipod/i.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1))
			device = 'iphone';
	});

	function explain(e: MouseEvent) {
		e.preventDefault();
		alert(t('dragAlert'));
	}

	async function copy() {
		try {
			await navigator.clipboard.writeText(href);
			copied = true;
			copyFailed = false;
			setTimeout(() => (copied = false), 2500);
		} catch {
			copyFailed = true;
		}
	}
</script>

<!-- The step texts are our own fixed strings (i18n.svelte.ts) with a little markup, so {@html} is safe. -->
<section id="steps">
	<h2>{t('stepsTitle')}</h2>
	<div class="devices" role="tablist">
		{#each devices as d (d.id)}
			<button
				role="tab"
				aria-selected={device === d.id}
				class:on={device === d.id}
				onclick={() => (device = d.id)}>{t(d.label)}</button
			>
		{/each}
	</div>
	<ol class="steps">
		{#if device === 'computer'}
			<li>
				<span class="n">1</span>
				<p>{@html t('step1')}</p>
				<!-- svelte-ignore a11y_invalid_attribute -->
				<a class="bm" href={href || '#'} onclick={explain}>⟳ Sync DUPR</a>
			</li>
			<li>
				<span class="n">2</span>
				<p>{@html t('step2')}</p>
			</li>
			<li>
				<span class="n">3</span>
				<p>{@html t('step3')}</p>
			</li>
		{:else}
			<li>
				<span class="n">1</span>
				<p>{@html t('copyStep')}</p>
				<button class="bm" onclick={copy} disabled={!href}>{copied ? t('copied') : t('copyBtn')}</button>
				{#if copyFailed}
					<p class="small">{t('copyManual')}</p>
					<textarea readonly rows="3" value={href} onfocus={(e) => e.currentTarget.select()}></textarea>
				{/if}
			</li>
			<li>
				<span class="n">2</span>
				<p>{@html t(device === 'iphone' ? 'iosStep2' : 'androidStep2')}</p>
			</li>
			<li>
				<span class="n">3</span>
				<p>{@html t(device === 'iphone' ? 'iosStep3' : 'androidStep3')}</p>
			</li>
		{/if}
	</ol>
	<p class="privacy"><span aria-hidden="true">🔒</span> {t('privacy')}</p>
</section>

<style>
	section {
		scroll-margin-top: 24px;
	}
	h2 {
		font-size: 24px;
		margin: 0 0 16px;
	}
	ol {
		list-style: none;
		padding: 0;
		margin: 0;
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 14px;
	}
	li {
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: 14px;
		padding: 18px 20px 20px;
	}
	li p {
		margin: 10px 0 0;
		color: var(--ink);
	}
	.n {
		width: 32px;
		height: 32px;
		border-radius: 50%;
		background: var(--accent-soft);
		color: var(--accent);
		font-weight: 700;
		display: grid;
		place-items: center;
	}
	.devices {
		display: inline-flex;
		gap: 4px;
		padding: 4px;
		margin: 0 0 14px;
		border-radius: 10px;
		background: var(--surface);
		border: 1px solid var(--line);
		max-width: 100%;
		overflow-x: auto;
	}
	.devices button {
		background: none;
		color: var(--ink2);
		padding: 8px 14px;
		font-weight: 600;
		white-space: nowrap;
	}
	.devices button.on {
		background: var(--accent-soft);
		color: var(--accent);
	}
	textarea {
		width: 100%;
		margin-top: 6px;
		/* 16px stops iPhone Safari from zooming in when the box is tapped. */
		font: 16px/1.4 ui-monospace, monospace;
		border: 1px solid var(--line);
		border-radius: 8px;
		padding: 8px;
		background: var(--bg, #fff);
		color: var(--ink);
		word-break: break-all;
	}
	.bm {
		display: inline-block;
		margin-top: 12px;
		padding: 10px 18px;
		border-radius: 8px;
		background: var(--accent);
		color: #fff;
		font-weight: 600;
		text-decoration: none;
		font-size: 15px;
		cursor: grab;
		box-shadow: 0 2px 6px rgb(11 122 124 / 0.3);
	}
	.privacy {
		margin: 16px 0 0;
		padding: 12px 16px;
		border-radius: 10px;
		background: var(--accent-soft);
		color: var(--ink2);
		font-size: 14px;
	}
	button.bm {
		border: 0;
		cursor: pointer;
	}
	@media (max-width: 760px) {
		ol {
			grid-template-columns: 1fr;
		}
	}
</style>
