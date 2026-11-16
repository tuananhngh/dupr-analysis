<script lang="ts" module>
	export type Column<R> = { label: string; value: (row: R) => string | number; num?: boolean };
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
						{#each columns as c, i (i)}<td class:num={c.num}>{c.value(row)}</td>{/each}
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
	th {
		white-space: normal;
		min-width: 64px;
		vertical-align: bottom;
		position: sticky;
		top: 0;
		background: var(--surface);
		font-weight: 600;
		color: var(--ink2);
	}
	.num {
		text-align: right;
	}
	.muted {
		color: var(--ink2);
	}
</style>
