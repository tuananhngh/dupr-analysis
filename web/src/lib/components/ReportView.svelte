<script lang="ts">
	import { t } from '#lib/i18n.svelte.ts';
	import LangSwitch from './LangSwitch.svelte';
	import Report from '#lib/report/Report.svelte';
	import { printReport } from '#lib/report/print.svelte.ts';
	import type { ReportData } from '#lib/report/types.ts';

	let { data, demo = false, onback }: { data: ReportData; demo?: boolean; onback: () => void } = $props();
</script>

<div class="bar">
	<strong>{t('reportTitle')}</strong>
	<LangSwitch />
	<button class="secondary" onclick={printReport}>{t('print')}</button>
	<button class="secondary" onclick={onback}>{t('back')}</button>
</div>
<Report {data} {demo} />

<style>
	.bar {
		position: sticky;
		top: 0;
		z-index: 10;
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
	.bar :global(.lang) {
		margin-top: 0;
	}
	@media print {
		.bar {
			display: none;
		}
	}
</style>
