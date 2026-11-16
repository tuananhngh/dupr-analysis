<script lang="ts">
	import { t } from '#lib/i18n.svelte.ts';

	let { href }: { href: string } = $props();

	function explain(e: MouseEvent) {
		e.preventDefault();
		alert(t('dragAlert'));
	}
</script>

<!-- The step texts are our own fixed strings (i18n.svelte.ts) with a little markup, so {@html} is safe. -->
<div class="card">
	<strong>{t('getReport')}</strong>
	<ol class="steps">
		<li>
			{@html t('step1')}<br />
			<!-- svelte-ignore a11y_invalid_attribute -->
			<a class="bm" href={href || '#'} onclick={explain}>⟳ Sync DUPR</a>
		</li>
		<li>{@html t('step2')}</li>
		<li>{@html t('step3')}</li>
	</ol>
	<p class="small">{t('privacy')}</p>
</div>

<style>
	ol {
		list-style: none;
		counter-reset: step;
		padding: 0;
		margin: 14px 0 4px;
	}
	li {
		counter-increment: step;
		position: relative;
		padding: 0 0 18px 42px;
	}
	li::before {
		content: counter(step);
		position: absolute;
		left: 0;
		top: -2px;
		width: 28px;
		height: 28px;
		border-radius: 50%;
		background: var(--accent-soft);
		color: var(--accent);
		font-weight: 700;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	a.bm {
		display: inline-block;
		margin-top: 8px;
		padding: 9px 16px;
		border-radius: 8px;
		background: var(--accent);
		color: #fff;
		font-weight: 600;
		text-decoration: none;
		cursor: grab;
	}
</style>
