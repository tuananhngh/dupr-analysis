<script lang="ts">
	import favicon from '#lib/assets/favicon.svg';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>DUPR Analysis</title>
	<meta
		name="description"
		content="See how your pickleball game evolves: your DUPR rating, form, partners, opponents and what to work on."
	/>
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
	}
	:global(*) {
		box-sizing: border-box;
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
