<script lang="ts">
	import { t } from '#lib/i18n.svelte.ts';

	let { href }: { href: string } = $props();

	function explain(e: MouseEvent) {
		e.preventDefault();
		alert(t('dragAlert'));
	}
</script>

<!-- The step texts are our own fixed strings (i18n.svelte.ts) with a little markup, so {@html} is safe. -->
<section id="steps">
	<h2>{t('stepsTitle')}</h2>
	<ol class="steps">
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
	a.bm {
		display: inline-block;
		margin-top: 12px;
		padding: 10px 18px;
		border-radius: 8px;
		background: var(--accent);
		color: #fff;
		font-weight: 600;
		text-decoration: none;
		cursor: grab;
		box-shadow: 0 2px 6px rgb(42 120 214 / 0.3);
	}
	.privacy {
		margin: 16px 0 0;
		padding: 12px 16px;
		border-radius: 10px;
		background: var(--accent-soft);
		color: var(--ink2);
		font-size: 14px;
	}
	@media (max-width: 760px) {
		ol {
			grid-template-columns: 1fr;
		}
	}
</style>
