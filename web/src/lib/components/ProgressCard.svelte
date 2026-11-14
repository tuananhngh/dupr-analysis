<script lang="ts">
	let { pct, step, error }: { pct: number; step: string; error: boolean } = $props();
</script>

<div class="card">
	<strong class:err={error}>{error ? 'Could not build the report' : 'Building your report…'}</strong>
	<div class="progress"><div style:width="{pct}%"></div></div>
	<p class="small">{step}</p>
</div>

<style>
	.progress {
		height: 6px;
		background: var(--accent-soft);
		border-radius: 3px;
		overflow: hidden;
		margin: 14px 0 8px;
	}
	.progress > div {
		height: 100%;
		background: var(--accent);
		transition: width 0.4s;
	}
	.err {
		color: var(--err);
	}
</style>
