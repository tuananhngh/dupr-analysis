<script lang="ts" module>
	// Cells stay on one line unless `wrap` is set (for long free text such as player names).
	export type Column<R> = { label: string; value: (row: R) => string | number; num?: boolean; wrap?: boolean };
</script>

<script lang="ts" generics="T">
	import { m } from './messages.ts';

	let { rows, columns, limit = 30 }: { rows: T[] | null | undefined; columns: Column<T>[]; limit?: number } = $props();

	const shown = $derived((rows ?? []).slice(0, limit));
</script>

{#if shown.length}
	<div class="tbl">
		<table>
			<thead>
				<tr>
					{#each columns as c, i (i)}<th class:num={c.num}>{c.label}</th>{/each}
				</tr>
			</thead>
			<tbody>
				{#each shown as row, r (r)}
					<tr>
						{#each columns as c, i (i)}<td class:num={c.num} class:wrap={c.wrap}>{c.value(row)}</td>{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
{:else}
	<p class="muted">{m().notEnough}</p>
{/if}

<style>
	.tbl {
		/* Scrolls sideways only as a last resort on very narrow screens, instead of cutting columns off. */
		overflow: auto;
		max-height: 520px;
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: 12px;
	}
	table {
		border-collapse: collapse;
		width: 100%;
		font-size: 14px;
		font-variant-numeric: tabular-nums;
	}
	th,
	td {
		padding: 7px 12px;
		text-align: left;
		border-bottom: 1px solid var(--line);
		white-space: nowrap;
	}
	/* Headers and name columns wrap between words only, never mid-word. */
	th,
	td.wrap {
		white-space: normal;
		overflow-wrap: normal;
		word-break: normal;
		hyphens: none;
	}
	td.wrap {
		min-width: 9em;
	}
	th {
		vertical-align: bottom;
		position: sticky;
		top: 0;
		z-index: 2;
		background: var(--surface);
		font-weight: 600;
		color: var(--ink2);
	}
	.num {
		text-align: right;
	}
	/* First column stays on the left when the table scrolls sideways (phones). */
	th:first-child,
	td:first-child {
		position: sticky;
		left: 0;
		z-index: 1;
		background: var(--surface);
		box-shadow: inset -1px 0 0 var(--line);
	}
	th:first-child {
		z-index: 3;
	}
	td.wrap:first-child {
		min-width: 0;
		max-width: 40vw;
	}
	@media (max-width: 640px) {
		table {
			font-size: 13px;
		}
		th,
		td {
			padding: 6px 6px;
		}
	}
	.muted {
		color: var(--ink2);
	}
</style>
