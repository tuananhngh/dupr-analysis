<script lang="ts">
	// Matches as a feed, most recent first.
	import { m } from './messages.ts';
	import { date, isNum, signed } from './format.ts';
	import type { Match } from './types.ts';
	import { printing } from './print.svelte.ts';

	let { matches, doubles }: { matches: Match[]; doubles: boolean } = $props();
	const M = $derived(m());
	const N = 10;

	let all = $state(false);
	const recent = $derived([...matches].reverse());
	const shown = $derived(all || printing.all ? recent : recent.slice(0, N));
</script>

<h3>{M.ui.recentMatches}</h3>
<ol class="feed">
	{#each shown as x, i (i)}
		<li>
			<span class="res" class:won={x.won}>{x.won ? M.col.w : M.col.l}</span>
			<div class="main">
				<div class="score">{x.game_scores}</div>
				<div class="who">
					{#if doubles && x.partner}{M.ui.with} <b>{x.partner}</b> · {/if}{M.ui.vs} {x.opponents}
				</div>
			</div>
			<div class="side">
				{#if isNum(x.rating_impact)}
					<div class="chg" class:up={x.rating_impact > 0} class:down={x.rating_impact < 0}>{signed(x.rating_impact)}</div>
				{/if}
				<div class="date">{date(x.date)}</div>
			</div>
		</li>
	{/each}
</ol>
{#if recent.length > N && !printing.all}
	<button class="secondary more" onclick={() => (all = !all)}>{all ? M.ui.showFewer : M.ui.showAll(recent.length)}</button>
{/if}

<style>
	h3 {
		font-size: 18px;
		margin: 8px 0 10px;
	}
	.feed {
		list-style: none;
		margin: 0;
		padding: 0;
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: 12px;
		overflow: hidden;
	}
	li {
		display: grid;
		grid-template-columns: auto 1fr auto;
		gap: 14px;
		align-items: center;
		padding: 10px 16px;
		border-top: 1px solid var(--line);
		break-inside: avoid;
	}
	li:first-child {
		border-top: 0;
	}
	.res {
		width: 30px;
		height: 30px;
		border-radius: 8px;
		display: grid;
		place-items: center;
		font-weight: 700;
		color: #fff;
		background: var(--orange);
	}
	.res.won {
		background: var(--teal);
	}
	.main {
		min-width: 0;
	}
	.score {
		font-weight: 650;
		font-variant-numeric: tabular-nums;
	}
	.who {
		font-size: 13px;
		color: var(--ink2);
		overflow-wrap: anywhere;
	}
	.who b {
		font-weight: 600;
		color: var(--ink);
	}
	.side {
		text-align: right;
	}
	.chg {
		font-weight: 650;
		font-variant-numeric: tabular-nums;
		color: var(--ink2);
	}
	.chg.up {
		color: var(--accent);
	}
	.chg.down {
		color: var(--orange);
	}
	.date {
		font-size: 12px;
		color: var(--ink2);
		white-space: nowrap;
	}
	.more {
		margin-top: 10px;
	}
</style>
