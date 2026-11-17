<script lang="ts">
	// A static picture of the report's top (made-up numbers), so visitors see what they will get.
	import { locale, t } from '#lib/i18n.svelte.ts';

	const n = (v: number, d: number, sign = false) =>
		v.toLocaleString(locale(), { minimumFractionDigits: d, maximumFractionDigits: d, signDisplay: sign ? 'exceptZero' : 'auto' });
	const form = [true, false, true, true, true, true, true, true, true, true];
	const curve = '0,54 20,52 40,55 60,47 80,44 100,40 120,36 140,30 160,27 180,20 200,16 220,12 240,8';
</script>

<div class="preview" aria-hidden="true">
	<span class="tag">{t('previewTag')}</span>
	<div class="hero">
		<div>
			<div class="lbl">{t('pvRating')}</div>
			<div class="big">{n(4.258, 3)}</div>
			<span class="pill">▲ {n(1.208, 3, true)}</span>
		</div>
		<svg viewBox="0 0 240 64" preserveAspectRatio="none">
			<polygon points="0,64 {curve} 240,64" class="area" />
			<polyline points={curve} class="line" />
		</svg>
	</div>
	<div class="lbl">{t('pvLast')}</div>
	<div class="dots">
		{#each form as won, i (i)}<span class:won></span>{/each}
	</div>
	<div class="cards">
		<div class="card">
			<div class="clbl">{t('pvStreak')}</div>
			<div class="val">8</div>
			<div class="clbl">{t('pvStreakSub')}</div>
		</div>
		<div class="card">
			<div class="clbl">{t('pvOdds')}</div>
			<div class="val">{n(8.5, 1, true)}</div>
			<div class="clbl">{t('pvOddsSub')}</div>
		</div>
	</div>
</div>

<style>
	.preview {
		position: relative;
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: 18px;
		padding: 22px;
		box-shadow:
			0 20px 40px -18px rgb(20 40 80 / 0.25),
			0 2px 6px rgb(0 0 0 / 0.04);
		transform: rotate(1deg);
	}
	.tag {
		position: absolute;
		top: -12px;
		right: 18px;
		background: var(--ink);
		color: #fff;
		font-size: 12px;
		font-weight: 600;
		padding: 3px 10px;
		border-radius: 999px;
	}
	.hero {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 18px;
		align-items: center;
		margin-bottom: 14px;
	}
	.lbl {
		font-size: 11px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--ink2);
	}
	.big {
		font-size: 40px;
		font-weight: 700;
		line-height: 1.1;
	}
	.pill {
		display: inline-block;
		margin-top: 4px;
		font-size: 13px;
		font-weight: 650;
		border-radius: 999px;
		padding: 2px 10px;
		background: var(--teal-soft);
		color: var(--accent);
	}
	svg {
		width: 100%;
		height: 64px;
	}
	.line {
		fill: none;
		stroke: var(--teal);
		stroke-width: 2;
		vector-effect: non-scaling-stroke;
	}
	.area {
		fill: var(--teal-soft);
	}
	.dots {
		display: flex;
		gap: 4px;
		margin: 6px 0 16px;
	}
	.dots span {
		flex: 1;
		max-width: 22px;
		aspect-ratio: 1;
		border-radius: 5px;
		background: var(--orange);
	}
	.dots span.won {
		background: var(--teal);
	}
	.cards {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 10px;
	}
	.card {
		border: 1px solid var(--line);
		border-top: 3px solid var(--teal);
		border-radius: 10px;
		padding: 10px 12px;
	}
	.clbl {
		font-size: 12px;
		color: var(--ink2);
	}
	.val {
		font-size: 22px;
		font-weight: 700;
	}
</style>
