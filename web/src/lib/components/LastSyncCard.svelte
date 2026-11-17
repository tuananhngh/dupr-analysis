<script lang="ts">
	import { locale, t } from '#lib/i18n.svelte.ts';

	let { at, onopen, onforget }: { at: number; onopen: () => void; onforget: () => void } = $props();

	const synced = $derived.by(() => {
		const d = new Date(at);
		const date = d.toLocaleDateString(locale());
		const time = d.toLocaleTimeString(locale(), { hour: '2-digit', minute: '2-digit' });
		return t('syncedOn', date, time);
	});
</script>

<div class="card back">
	<strong>{t('welcomeBack')}</strong>
	<p class="small">{synced}</p>
	<div class="row">
		<button onclick={onopen}>{t('openLast')}</button>
		<button class="link" onclick={onforget}>{t('forget')}</button>
	</div>
</div>

<style>
	.back {
		border-left: 4px solid var(--accent);
	}
	p {
		margin: 4px 0 12px;
	}
</style>
