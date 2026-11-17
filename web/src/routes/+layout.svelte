<script lang="ts">
	import 'layerchart/core.css';
	import '@fontsource-variable/inter';
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
		--accent: #0b7a7c;
		--accent-soft: #e0f1f0;
		--err: #b42318;
		--muted: #8a8984;
		--faint: #c9c8c2;
		/* The report's two data colors: teal = win / above expectation, orange = loss / below.
		   Small text in the win color uses --accent (darker teal) for contrast. */
		--teal: #13958f;
		--teal-soft: #e0f1f0;
		--orange: #eb6834;
		/* LayerChart theme: text and axes, label halo and tooltip background, default mark color.
		   On :root because LayerChart moves tooltips to <body>. */
		--color-surface-content: var(--ink2);
		--color-surface-100: var(--surface);
		--color-primary: var(--teal);
	}
	:global(*) {
		box-sizing: border-box;
	}
	:global(a) {
		color: var(--accent);
	}
	:global(body) {
		-webkit-font-smoothing: antialiased;
		font-feature-settings: 'cv11', 'ss01';
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
			15px/1.55 'Inter Variable',
			Inter,
			-apple-system,
			'Segoe UI',
			sans-serif;
	}
</style>
