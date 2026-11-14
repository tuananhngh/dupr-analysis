<script lang="ts">
	let { at, onopen, onforget }: { at: number; onopen: () => void; onforget: () => void } = $props();

	const when = $derived.by(() => {
		const d = new Date(at);
		const time = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
		return `${d.toLocaleDateString()} at ${time}`;
	});
</script>

<div class="card">
	<strong>Your last sync</strong>
	<p>Synced on {when}. To update it, click the bookmark on dupr.com again.</p>
	<div class="row">
		<button onclick={onopen}>Open my report</button>
		<button class="link" onclick={onforget}>Forget my data</button>
	</div>
</div>
