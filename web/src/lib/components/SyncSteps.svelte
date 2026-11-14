<script lang="ts">
	let { href }: { href: string } = $props();

	function explain(e: MouseEvent) {
		e.preventDefault();
		alert('Drag this button to your bookmarks bar, then click it while you are on dashboard.dupr.com.');
	}
</script>

<div class="card">
	<strong>Get your report</strong>
	<ol class="steps">
		<li>
			<b>Once:</b> drag this button to your bookmarks bar
			<span class="small">(show the bar with ⌘⇧B on Mac, Ctrl+Shift+B on Windows)</span><br />
			<!-- svelte-ignore a11y_invalid_attribute -->
			<a class="bm" href={href || '#'} onclick={explain}>⟳ Sync DUPR</a>
		</li>
		<li>
			Open <a href="https://dashboard.dupr.com" target="_blank" rel="noopener">dashboard.dupr.com</a> and
			log in as usual.
		</li>
		<li>
			Click the <b>⟳ Sync DUPR</b> bookmark. Your matches are downloaded and you come back here to your
			report.
		</li>
	</ol>
	<p class="small">
		You log in on DUPR's own site: your password never goes through this page. Your data stays in your
		browser. It is never uploaded anywhere. Works on a computer (Chrome, Edge, Firefox, Safari).
	</p>
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
