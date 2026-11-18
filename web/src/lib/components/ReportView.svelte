<script lang="ts">
	import { t } from '#lib/i18n.svelte.ts';
	import LangSwitch from './LangSwitch.svelte';
	import Report from '#lib/report/Report.svelte';
	import { printReport } from '#lib/report/print.svelte.ts';
	import logo from '#lib/assets/favicon.svg';
	import type { ReportData } from '#lib/report/types.ts';

	let { data, demo = false, onback }: { data: ReportData; demo?: boolean; onback: () => void } = $props();
</script>

<div class="bar">
	<strong><img src={logo} alt="" width="22" height="22" /><span class="wide">{t('reportTitle')}</span></strong>
	<LangSwitch />
	<button class="secondary" onclick={printReport} aria-label={t('print')}
		><span class="wide">{t('print')}</span><span class="narrow">{t('printShort')}</span></button
	>
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
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.bar button {
		padding: 6px 12px;
		font-size: 14px;
	}
	.bar :global(.lang) {
		margin-top: 0;
	}
	.narrow {
		display: none;
	}
	/* Phones: keep the bar on one row so it does not cover too much of the screen. */
	@media (max-width: 520px) {
		.bar {
			flex-wrap: nowrap;
			gap: 8px;
			padding: 6px 12px;
		}
		.wide {
			display: none;
		}
		.narrow {
			display: inline;
		}
	}
	@media print {
		.bar {
			display: none;
		}
	}
</style>
