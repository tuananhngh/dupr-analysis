<script lang="ts">
	let { html, onback }: { html: string; onback: () => void } = $props();

	// The report is a standalone HTML document (plotly charts included): show it from a blob URL.
	const url = $derived(URL.createObjectURL(new Blob([html], { type: 'text/html' })));
	$effect(() => {
		const u = url;
		return () => URL.revokeObjectURL(u);
	});

	function download() {
		const a = document.createElement('a');
		a.href = url;
		a.download = `dupr-report-${new Date().toISOString().slice(0, 10)}.html`;
		a.click();
	}
</script>

<div class="view">
	<div class="bar">
		<strong>DUPR performance report</strong>
		<button class="secondary" onclick={download}>Download report</button>
		<button class="secondary" onclick={onback}>Back</button>
	</div>
	<iframe src={url} title="Your DUPR performance report"></iframe>
</div>

<style>
	.view {
		position: fixed;
		inset: 0;
		display: flex;
		flex-direction: column;
		background: var(--bg);
	}
	.bar {
		display: flex;
		gap: 10px;
		align-items: center;
		flex-wrap: wrap;
		padding: 8px 16px;
		background: var(--surface);
		border-bottom: 1px solid var(--line);
	}
	.bar strong {
		margin-right: auto;
	}
	.bar button {
		padding: 6px 12px;
		font-size: 14px;
	}
	iframe {
		flex: 1;
		width: 100%;
		border: 0;
	}
</style>
