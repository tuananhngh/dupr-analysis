<script lang="ts">
	import { m } from './messages.ts';
	import type { TipText } from './messages.en.ts';
	import { rating } from './format.ts';
	import type { Num, Tip } from './types.ts';

	let { tips, level }: { tips: Tip[]; level: { band: number; rating: Num } } = $props();

	const note = $derived(
		m().levelNote(m().bands[level.band], m().bandRanges[level.band], level.rating == null ? null : rating(level.rating))
	);

	function text(t: Tip) {
		const tt = (m().tips as Record<string, TipText>)[t.id];
		if (!tt) return null;
		const advice = Array.isArray(tt.advice) ? tt.advice[level.band] : tt.advice;
		return { title: tt.title, finding: tt.finding(t.params), advice };
	}
</script>

<p class="muted">{m().improveIntro} {note}</p>
{#if tips.length}
	<div class="tips">
		{#each tips as t (t.id)}
			{@const x = text(t)}
			{#if x}
				<div class="tip {t.kind}">
					<span class="badge">{m().tipBadge[t.kind]}</span>
					<h4>{x.title}</h4>
					<p class="finding">{x.finding}</p>
					<p class="advice"><b>{m().tryLabel}</b> {x.advice}</p>
				</div>
			{/if}
		{/each}
	</div>
{:else}
	<p class="muted">{m().noTips}</p>
{/if}

<style>
	.muted {
		color: var(--ink2);
	}
	.tips {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(min(100%, 320px), 1fr));
		gap: 12px;
	}
	.tip {
		background: var(--surface);
		border: 1px solid var(--line);
		border-left: 4px solid var(--muted);
		border-radius: 12px;
		padding: 14px 16px;
		break-inside: avoid;
	}
	.tip.work {
		border-left-color: var(--orange);
	}
	.tip.strength {
		border-left-color: var(--blue);
	}
	.badge {
		font-size: 12px;
		font-weight: 600;
		color: var(--ink2);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}
	h4 {
		font-size: 16px;
		margin: 4px 0 6px;
	}
	.finding {
		margin: 4px 0;
	}
	.advice {
		margin: 6px 0 0;
		color: var(--ink2);
	}
</style>
