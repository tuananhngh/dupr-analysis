<script lang="ts">
	import 'layerchart/core.css';
	import favicon from '#lib/assets/favicon.svg';
	import { onMount } from 'svelte';
	import { i18n, initLang, t } from '#lib/i18n.svelte.ts';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();

	onMount(initLang);
	$effect(() => {
		document.documentElement.lang = i18n.lang;
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>{t('docTitle')}</title>
	<meta name="description" content={t('description')} />
</svelte:head>

{@render children()}

<style>
	:global(:root) {
		color-scheme: light;
		--bg: #f4f3f0;
		--surface: #fcfcfb;
		--ink: #0b0b0b;
		--ink2: #52514e;
		--line: #e6e5e0;
		--accent: #2a78d6;
		--accent-soft: #e3edfa;
		--err: #b42318;
		--muted: #8a8984;
		--faint: #c9c8c2;
		/* The report's two data colors: blue = win / above expectation, orange = loss / below. */
		--blue: #2a78d6;
		--orange: #eb6834;
		/* LayerChart theme: text and axes, label halo and tooltip background, default mark color.
		   On :root because LayerChart moves tooltips to <body>. */
		--color-surface-content: var(--ink2);
		--color-surface-100: var(--surface);
		--color-primary: var(--blue);
	}
	:global(*) {
		box-sizing: border-box;
	}
	/* Chart axis text (LayerChart's default is a little small). */
	:global(.lc-axis-tick-label),
	:global(.lc-axis-label) {
		font-size: 12px;
	}
	@media print {
		:global(:root) {
			--bg: #fff;
		}
	}
	:global(html),
	:global(body) {
		margin: 0;
		background: var(--bg);
		color: var(--ink);
		font:
			15px/1.55 Inter,
			-apple-system,
			'Segoe UI',
			sans-serif;
	}
</style>
