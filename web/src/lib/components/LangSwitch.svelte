<script lang="ts">
	import { i18n, LANGS, setLang } from '#lib/i18n.svelte.ts';
</script>

<div class="lang" role="group" aria-label="Language / Langue">
	{#each LANGS as l (l)}
		<button type="button" lang={l} aria-pressed={i18n.lang === l} onclick={() => setLang(l)}>
			{l.toUpperCase()}
		</button>
	{/each}
</div>

<style>
	.lang {
		display: flex;
		border: 1px solid var(--line);
		border-radius: 8px;
		overflow: hidden;
		flex: none;
		margin-top: 4px;
	}
	.lang button {
		background: var(--surface);
		color: var(--ink2);
		border: 0;
		border-radius: 0;
		padding: 5px 10px;
		font-size: 13px;
		font-weight: 600;
	}
	.lang button[aria-pressed='true'] {
		background: var(--accent);
		color: #fff;
	}
</style>
