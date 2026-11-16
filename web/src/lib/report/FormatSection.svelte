<script lang="ts">
	// One format (doubles or singles): same sections, in the same order, as the former Python report.
	import { m } from './messages.ts';
	import type { FindingText } from './messages.en.ts';
	import { date, isNum, monthYear, num, pct, periodLabel, rating, signed } from './format.ts';
	import type { Agg, FormatData, Match } from './types.ts';
	import ChartCard from './ChartCard.svelte';
	import DataTable, { type Column } from './DataTable.svelte';
	import Tips from './Tips.svelte';
	import RatingChart from './charts/RatingChart.svelte';
	import MonthlyChangeChart from './charts/MonthlyChangeChart.svelte';
	import WinFormChart from './charts/WinFormChart.svelte';
	import PointsChart from './charts/PointsChart.svelte';
	import OppResultsChart from './charts/OppResultsChart.svelte';
	import OppChangeChart from './charts/OppChangeChart.svelte';
	import OppTimeChart from './charts/OppTimeChart.svelte';
	import PeriodsChart from './charts/PeriodsChart.svelte';
	import ActivityChart from './charts/ActivityChart.svelte';
	import MarginsChart from './charts/MarginsChart.svelte';
	import PartnersChart from './charts/PartnersChart.svelte';

	let { d }: { d: FormatData } = $props();

	const M = $derived(m());
	const s = $derived(d.summary);
	const c = $derived(d.close_games);
	const period = $derived(s.period);
	const fmtName = $derived(M.formatName[d.format] ?? d.format);
	const doubles = $derived(d.format === 'DOUBLES');
	const opp = $derived(d.opponent_effect);
	const hasOppGroups = $derived(opp.groups.length > 0);

	type TileT = { label: string; value: string; sub: string };
	const tiles = $derived.by(() => {
		const t: TileT[] = [
			{ label: M.tiles.rating, value: rating(s.rating_now), sub: M.tiles.peak(rating(s.rating_peak)) },
			{ label: M.tiles.change, value: signed(s.rating_change), sub: M.tiles.since(monthYear(s.first_match)) },
			{ label: M.tiles.trend, value: signed(s.trend_per_month), sub: M.tiles.perMonth },
			{ label: M.tiles.record, value: `${s.wins}–${s.losses}`, sub: M.tiles.winsPct(pct(s.win_pct)) }
		];
		if (isNum(s.exp_win_pct)) t.push({ label: M.tiles.winProb, value: pct(s.exp_win_pct), sub: M.tiles.winProbSub });
		if (isNum(s.expected_wins) && isNum(s.wins_above_expected))
			t.push({
				label: M.tiles.winsVsExp,
				value: signed(s.wins_above_expected, 1),
				sub: M.tiles.winsVsExpSub(s.wins, num(s.expected_wins))
			});
		t.push({ label: M.tiles.pointWin, value: pct(s.point_share, 1), sub: M.tiles.games(s.games_won, s.games_lost) });
		if (isNum(s.rally_share)) t.push({ label: M.tiles.rallyWin, value: pct(s.rally_share, 1), sub: M.tiles.rallySub });
		t.push({ label: M.tiles.close, value: pct(c.close_win_pct), sub: M.tiles.closeSub(c.close_games) });
		return t;
	});

	const findings = $derived(
		d.findings
			.map((f) => (M.findings as Record<string, FindingText>)[f.id]?.(f, M.formatLower[d.format] ?? ''))
			.filter((x): x is string => !!x)
	);

	// ---- tables
	const aggCols = (): Column<Agg>[] => [
		{ label: M.col.matches, value: (r) => r.matches, num: true },
		{ label: M.col.winPct, value: (r) => pct(r.win_pct), num: true },
		{ label: M.col.pointWin, value: (r) => pct(r.point_share), num: true },
		{ label: M.col.avgPointDiff, value: (r) => signed(r.avg_point_diff, 1), num: true },
		{ label: M.col.avgOppRating, value: (r) => rating(r.avg_opp_rating), num: true },
		{ label: M.col.ratingChange, value: (r) => signed(r.rating_gained), num: true }
	];
	const result = (won: boolean) => (won ? M.col.w : M.col.l);
	const matchCols = (all: boolean): Column<Match>[] => {
		const cols: Column<Match>[] = [
			{ label: M.col.date, value: (r) => date(r.date) },
			{ label: M.col.result, value: (r) => result(r.won) },
			{ label: M.col.score, value: (r) => r.game_scores }
		];
		if (doubles) cols.push({ label: M.col.partner, value: (r) => r.partner ?? '–' });
		if (all) cols.push({ label: M.col.opponents, value: (r) => r.opponents });
		cols.push({ label: M.col.oppRating, value: (r) => rating(r.opp_rating_avg), num: true });
		if (all) cols.push({ label: M.col.gap, value: (r) => signed(r.rating_diff), num: true });
		cols.push({ label: M.col.ratingChange, value: (r) => signed(r.rating_impact), num: true });
		return cols;
	};
	const recent = $derived([...d.matches].reverse());
	const periodsRows = $derived([...d.periods].reverse());
</script>

<section>
	<h2>{fmtName}</h2>
	<div class="tiles">
		{#each tiles as t (t.label)}
			<div class="tile"><div class="lbl">{t.label}</div><div class="val">{t.value}</div><div class="sub">{t.sub}</div></div>
		{/each}
	</div>

	<h3>{M.h.findings}</h3>
	<ul class="findings">
		{#each findings as f, i (i)}<li>{f}</li>{/each}
	</ul>

	<h3>{M.h.improve}</h3>
	<Tips tips={d.tips} level={d.level} />

	<h3>{M.h.rating}</h3>
	{#if d.rating.length}
		<ChartCard title={M.charts.rating(fmtName)} caption={M.charts.ratingCap}><RatingChart {d} /></ChartCard>
	{/if}
	{#if d.monthly_rating.length}
		<ChartCard title={M.charts.monthly} caption={M.charts.monthlyCap}><MonthlyChangeChart {d} /></ChartCard>
	{/if}

	<h3>{M.h.form}</h3>
	{#if d.win_form.length}
		<ChartCard title={M.charts.winForm} caption={M.charts.winFormCap(s.rolling_window)}><WinFormChart {d} /></ChartCard>
	{/if}
	{#if d.monthly_points.length}
		<ChartCard
			title={M.charts.points}
			caption={M.charts.pointsCap + (d.point_form_hits ? M.charts.pointsHits(d.point_form_hits) : '')}
		>
			<PointsChart {d} />
		</ChartCard>
	{/if}

	{#if hasOppGroups}
		<h3>{M.h.opponents}</h3>
		<p class="takeaway">{M.opponentVerdict(opp.verdict)}</p>
		<ChartCard title={M.charts.oppResults} caption={M.charts.oppResultsCap}><OppResultsChart {d} /></ChartCard>
		{#if opp.measure === 'rating_impact'}
			<ChartCard title={M.charts.oppChange} caption={M.charts.oppChangeCap}><OppChangeChart {d} /></ChartCard>
		{/if}
		{#if d.matches.filter((x) => x.opp_rating_avg != null).length >= 5}
			<ChartCard title={M.charts.oppTime} caption={M.charts.oppTimeCap}><OppTimeChart {d} /></ChartCard>
		{/if}
		<DataTable
			rows={opp.groups}
			columns={[
				{ label: M.col.opponents, value: (r) => `${M.groups[r.group]} (${M.groupRanges[r.group]})` },
				{ label: M.col.matches, value: (r) => r.matches, num: true },
				{ label: M.col.winPct, value: (r) => pct(r.win_pct), num: true },
				{ label: M.col.expWin, value: (r) => pct(r.exp_win_pct), num: true },
				{ label: M.col.pointWin, value: (r) => pct(r.point_share), num: true },
				{ label: M.col.avgChange, value: (r) => signed(r.avg_impact), num: true },
				{ label: M.col.totalChange, value: (r) => signed(r.total_impact), num: true }
			]}
		/>
	{/if}

	<h3>{M.h.byPeriod(period)}</h3>
	<ChartCard title={M.charts.periods(period)} caption={M.charts.periodsCap(period)}><PeriodsChart {d} /></ChartCard>
	<ChartCard title={M.charts.activity(period)} caption={M.charts.activityCap(period)}><ActivityChart {d} /></ChartCard>

	<h3>{M.h.gamesPartners}</h3>
	{#if d.margins.length}
		<ChartCard title={M.charts.margins} caption={M.charts.marginsCap}><MarginsChart {d} /></ChartCard>
	{/if}
	{#if d.partners.filter((p) => p.matches >= 2).length}
		<ChartCard title={M.charts.partners} caption={M.charts.partnersCap}><PartnersChart {d} /></ChartCard>
	{/if}

	<h3>{M.h.evolution(period)}</h3>
	<DataTable
		rows={periodsRows}
		columns={[
			{ label: M.col.period(period), value: (r) => periodLabel(r.period_end, period) },
			...(aggCols() as Column<(typeof periodsRows)[number]>[]),
			{ label: M.col.ratingEnd, value: (r) => rating(r.rating_end), num: true }
		]}
	/>
	<div class="grid2">
		{#if doubles}
			<div>
				<h3>{M.h.partners}</h3>
				<DataTable
					rows={d.partners}
					limit={15}
					columns={[
						{ label: M.col.partner, value: (r) => r.partner },
						...(aggCols() as Column<(typeof d.partners)[number]>[]),
						{ label: M.col.partnerRating, value: (r) => rating(r.partner_rating), num: true }
					]}
				/>
			</div>
		{/if}
		<div>
			<h3>{M.h.mostFaced}</h3>
			<DataTable
				rows={d.opponents}
				limit={15}
				columns={[
					{ label: M.col.opponent, value: (r) => r.opponent },
					{ label: M.col.matches, value: (r) => r.matches, num: true },
					{ label: M.col.wins, value: (r) => r.wins, num: true },
					{ label: M.col.winPct, value: (r) => pct(r.win_pct), num: true },
					{ label: M.col.pointWin, value: (r) => pct(r.point_share), num: true }
				]}
			/>
		</div>
	</div>
	<div class="grid2">
		<div>
			<h3>{M.h.bySource}</h3>
			<DataTable
				rows={d.by_source}
				columns={[
					{ label: M.col.source, value: (r) => M.sources[r.source] ?? r.source },
					...(aggCols() as Column<(typeof d.by_source)[number]>[])
				]}
			/>
		</div>
		<div>
			<h3>{M.h.byRest}</h3>
			<DataTable
				rows={d.by_rest}
				columns={[
					{ label: M.col.rest, value: (r) => M.rest[r.rest] ?? r.rest },
					...(aggCols() as Column<(typeof d.by_rest)[number]>[])
				]}
			/>
		</div>
	</div>
	<div class="grid2">
		<div>
			<h3>{M.h.gains}</h3>
			<DataTable rows={d.best} columns={matchCols(false)} />
		</div>
		<div>
			<h3>{M.h.losses}</h3>
			<DataTable rows={d.worst} columns={matchCols(false)} />
		</div>
	</div>
	<h3>{M.h.gameDetails}</h3>
	<p>{M.gameDetails(c)}</p>
	<details>
		<summary>{M.h.allMatches}</summary>
		<DataTable rows={recent} columns={matchCols(true)} limit={10_000} />
	</details>
</section>

<style>
	h2 {
		font-size: 23px;
		margin: 44px 0 14px;
		padding-top: 18px;
		border-top: 1px solid var(--line);
	}
	h3 {
		font-size: 18px;
		margin: 36px 0 10px;
	}
	.tiles {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
		gap: 12px;
	}
	.tile {
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: 12px;
		padding: 14px 16px;
	}
	.lbl,
	.sub {
		font-size: 13px;
		color: var(--ink2);
	}
	.val {
		font-size: 26px;
		font-weight: 650;
	}
	.findings li {
		margin: 6px 0;
	}
	.takeaway {
		max-width: 900px;
		margin: 0 0 8px;
	}
	.grid2 {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(min(100%, 460px), 1fr));
		gap: 4px 16px;
	}
	details {
		margin: 16px 0;
	}
	summary {
		cursor: pointer;
		font-weight: 600;
		font-size: 16px;
		margin-bottom: 8px;
	}
</style>
