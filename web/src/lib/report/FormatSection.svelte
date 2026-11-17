<script lang="ts">
	// One format (doubles or singles): hero, highlights, then the details in tabs.
	import { m } from './messages.ts';
	import { date, isNum, monthYear, num, pct, periodLabel, rating, signed } from './format.ts';
	import type { Agg, FormatData, Match, Tournament } from './types.ts';
	import ChartCard from './ChartCard.svelte';
	import DataTable, { type Column } from './DataTable.svelte';
	import Tips from './Tips.svelte';
	import Hero from './Hero.svelte';
	import Highlights from './Highlights.svelte';
	import MatchFeed from './MatchFeed.svelte';
	import Findings from './Findings.svelte';
	import { printing } from './print.svelte.ts';
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
				sub: M.tiles.winsVsExpSub(s.rated_wins ?? s.wins, num(s.expected_wins))
			});
		t.push({ label: M.tiles.pointWin, value: pct(s.point_share, 1), sub: M.tiles.games(s.games_won, s.games_lost) });
		if (isNum(s.rally_share)) t.push({ label: M.tiles.rallyWin, value: pct(s.rally_share, 1), sub: M.tiles.rallySub });
		t.push({ label: M.tiles.close, value: pct(c.close_win_pct), sub: M.tiles.closeSub(c.close_games) });
		return t;
	});

	const findings = $derived(d.findings.filter((f) => f.id in M.findings));

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
	const matchCols = (): Column<Match>[] => {
		const cols: Column<Match>[] = [
			{ label: M.col.date, value: (r) => date(r.date) },
			{ label: M.col.result, value: (r) => result(r.won) },
			{ label: M.col.score, value: (r) => r.game_scores, wrap: true }
		];
		if (doubles) cols.push({ label: M.col.partner, value: (r) => r.partner ?? '–', wrap: true });
		cols.push({ label: M.col.oppRating, value: (r) => rating(r.opp_rating_avg), num: true });
		cols.push({ label: M.col.ratingChange, value: (r) => signed(r.rating_impact), num: true });
		return cols;
	};
	const periodsRows = $derived([...d.periods].reverse());
	const tours = $derived(d.tournaments ?? []);
	const ctx = $derived(d.by_context ?? []);
	const tourCols = (): Column<Tournament>[] => {
		const cols: Column<Tournament>[] = [
			{ label: M.col.date, value: (r) => date(r.date) },
			{ label: M.col.tournament, value: (r) => r.tournament, wrap: true }
		];
		if (doubles) cols.push({ label: M.col.partner, value: (r) => r.partner ?? '–', wrap: true });
		cols.push(
			{ label: M.col.record, value: (r) => `${r.wins}–${r.losses}`, num: true },
			{ label: M.col.pointWin, value: (r) => pct(r.point_share), num: true },
			{ label: M.col.avgOppRating, value: (r) => rating(r.avg_opp_rating), num: true },
			{ label: M.col.ratingChange, value: (r) => signed(r.rating_gained), num: true }
		);
		return cols;
	};

	type TabId = 'overview' | 'form' | 'opponents' | 'partners' | 'matches' | 'tournaments' | 'details';
	const tabs = $derived.by(() => {
		const t: { id: TabId; label: string }[] = [
			{ id: 'overview', label: M.ui.tabs.overview },
			{ id: 'form', label: M.ui.tabs.form },
			{ id: 'matches', label: M.ui.tabs.matches }
		];
		if (tours.length) t.push({ id: 'tournaments', label: M.ui.tabs.tournaments });
		if (hasOppGroups || d.opponents.length) t.push({ id: 'opponents', label: M.ui.tabs.opponents });
		t.push({ id: 'partners', label: doubles ? M.ui.tabs.partners : M.ui.tabs.games });
		t.push({ id: 'details', label: M.ui.tabs.details });
		return t;
	});
	let tab = $state<TabId>('overview');
	const show = (id: TabId) => printing.all || tab === id;
</script>

<section>
	{#if printing.all}<h2>{fmtName}</h2>{/if}
	<Hero {d} />
	<Highlights {d} />

	<div class="tabs" role="tablist">
		{#each tabs as t (t.id)}
			<button role="tab" aria-selected={tab === t.id} class:active={tab === t.id} onclick={() => (tab = t.id)}>{t.label}</button>
		{/each}
	</div>

	{#if show('overview')}
		<div class="panel">
			<h3 class="ptitle">{M.ui.tabs.overview}</h3>
			<h3>{M.ui.workOn}</h3>
			<Tips tips={d.tips} level={d.level} />
			{#if d.rating.length}
				<ChartCard title={M.charts.rating(fmtName)} caption={M.charts.ratingCap}><RatingChart {d} /></ChartCard>
			{/if}
			{#if findings.length}
				<h3>{M.ui.insights}</h3>
				<Findings {findings} fmt={M.formatLower[d.format] ?? ''} />
			{/if}
		</div>
	{/if}

	{#if show('form')}
		<div class="panel">
			<h3 class="ptitle">{M.ui.tabs.form}</h3>
			{#if d.win_form.length}
				<ChartCard title={M.charts.winForm} caption={M.charts.winFormCap(s.rolling_window)}><WinFormChart {d} /></ChartCard>
			{/if}
			{#if d.monthly_rating.length}
				<ChartCard title={M.charts.monthly} caption={M.charts.monthlyCap}><MonthlyChangeChart {d} /></ChartCard>
			{/if}
			{#if d.monthly_points.length}
				<ChartCard
					title={M.charts.points}
					caption={M.charts.pointsCap + (d.point_form_hits ? M.charts.pointsHits(d.point_form_hits) : '')}
				>
					<PointsChart {d} />
				</ChartCard>
			{/if}
			<ChartCard title={M.charts.periods(period)} caption={M.charts.periodsCap(period)}><PeriodsChart {d} /></ChartCard>
			<ChartCard title={M.charts.activity(period)} caption={M.charts.activityCap(period)}><ActivityChart {d} /></ChartCard>
		</div>
	{/if}

	{#if show('matches')}
		<div class="panel">
			<h3 class="ptitle">{M.ui.tabs.matches}</h3>
			<MatchFeed matches={d.matches} {doubles} />
			<h3>{M.h.gains}</h3>
			<DataTable rows={d.best} columns={matchCols()} />
			<h3>{M.h.losses}</h3>
			<DataTable rows={d.worst} columns={matchCols()} />
		</div>
	{/if}

	{#if show('tournaments') && tours.length}
		<div class="panel">
			<h3 class="ptitle">{M.ui.tabs.tournaments}</h3>
			<h3>{M.h.tourSummary}</h3>
			<p class="takeaway">
				{M.tournamentsIntro(
					tours.length,
					ctx.find((r) => r.context === 'tournament'),
					ctx.find((r) => r.context === 'other')
				)}
			</p>
			<p class="note">{M.tournamentsNote}</p>
			<h3>{M.h.tournaments}</h3>
			<DataTable rows={tours} limit={50} columns={tourCols()} />
			{#if ctx.length}
				<h3>{M.h.vsOther}</h3>
				<DataTable
					rows={ctx}
					columns={[
						{ label: '', value: (r) => M.context[r.context] },
						...(aggCols() as Column<(typeof ctx)[number]>[])
					]}
				/>
			{/if}
		</div>
	{/if}

	{#if show('opponents') && tabs.some((t) => t.id === 'opponents')}
		<div class="panel">
			<h3 class="ptitle">{M.ui.tabs.opponents}</h3>
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
						{ label: M.col.opponents, value: (r) => `${M.groups[r.group]} (${M.groupRanges[r.group]})`, wrap: true },
						{ label: M.col.matches, value: (r) => r.matches, num: true },
						{ label: M.col.winPct, value: (r) => pct(r.win_pct), num: true },
						{ label: M.col.expWin, value: (r) => pct(r.exp_win_pct), num: true },
						{ label: M.col.pointWin, value: (r) => pct(r.point_share), num: true },
						{ label: M.col.avgChange, value: (r) => signed(r.avg_impact), num: true },
						{ label: M.col.totalChange, value: (r) => signed(r.total_impact), num: true }
					]}
				/>
			{/if}
			<h3>{M.h.mostFaced}</h3>
			<DataTable
				rows={d.opponents}
				limit={15}
				columns={[
					{ label: M.col.opponent, value: (r) => r.opponent, wrap: true },
					{ label: M.col.matches, value: (r) => r.matches, num: true },
					{ label: M.col.wins, value: (r) => r.wins, num: true },
					{ label: M.col.winPct, value: (r) => pct(r.win_pct), num: true },
					{ label: M.col.pointWin, value: (r) => pct(r.point_share), num: true }
				]}
			/>
		</div>
	{/if}

	{#if show('partners')}
		<div class="panel">
			<h3 class="ptitle">{doubles ? M.ui.tabs.partners : M.ui.tabs.games}</h3>
			{#if d.partners.filter((p) => p.matches >= 2).length}
				<ChartCard title={M.charts.partners} caption={M.charts.partnersCap}><PartnersChart {d} /></ChartCard>
			{/if}
			{#if doubles}
				<h3>{M.h.partners}</h3>
				<DataTable
					rows={d.partners}
					limit={15}
					columns={[
						{ label: M.col.partner, value: (r) => r.partner, wrap: true },
						...(aggCols() as Column<(typeof d.partners)[number]>[]),
						{ label: M.col.partnerRating, value: (r) => rating(r.partner_rating), num: true }
					]}
				/>
			{/if}
			{#if d.margins.length}
				<ChartCard title={M.charts.margins} caption={M.charts.marginsCap}><MarginsChart {d} /></ChartCard>
			{/if}
			<h3>{M.h.gameDetails}</h3>
			<p class="takeaway">{M.gameDetails(c)}</p>
		</div>
	{/if}

	{#if show('details')}
		<div class="panel">
			<h3 class="ptitle">{M.ui.tabs.details}</h3>
			<h3>{M.ui.allNumbers}</h3>
			<div class="tiles">
				{#each tiles as t (t.label)}
					<div class="tile"><div class="lbl">{t.label}</div><div class="val">{t.value}</div><div class="sub">{t.sub}</div></div>
				{/each}
			</div>
			<h3>{M.h.evolution(period)}</h3>
			<DataTable
				rows={periodsRows}
				columns={[
					{ label: M.col.period(period), value: (r) => periodLabel(r.period_end, period) },
					...(aggCols() as Column<(typeof periodsRows)[number]>[]),
					{ label: M.col.ratingEnd, value: (r) => rating(r.rating_end), num: true }
				]}
			/>
			<h3>{M.h.bySource}</h3>
			<DataTable
				rows={d.by_source}
				columns={[
					{ label: M.col.source, value: (r) => M.sources[r.source] ?? r.source },
					...(aggCols() as Column<(typeof d.by_source)[number]>[])
				]}
			/>
			<h3>{M.h.byRest}</h3>
			<DataTable
				rows={d.by_rest}
				columns={[
					{ label: M.col.rest, value: (r) => M.rest[r.rest] ?? r.rest },
					...(aggCols() as Column<(typeof d.by_rest)[number]>[])
				]}
			/>
		</div>
	{/if}
</section>

<style>
	section {
		margin-top: 16px;
	}
	h2 {
		font-size: 23px;
		margin: 32px 0 14px;
	}
	h3 {
		font-size: 18px;
		margin: 28px 0 10px;
	}
	.tabs {
		position: sticky;
		top: 49px;
		z-index: 5;
		display: flex;
		gap: 4px;
		overflow-x: auto;
		margin: 28px 0 0;
		padding-top: 4px;
		background: var(--bg);
		border-bottom: 1px solid var(--line);
		scrollbar-width: none;
	}
	.tabs button {
		flex: none;
		background: none;
		color: var(--ink2);
		border-radius: 0;
		padding: 10px 14px;
		border-bottom: 3px solid transparent;
		font-weight: 600;
	}
	.tabs button:hover {
		color: var(--ink);
	}
	.tabs button.active {
		color: var(--accent);
		border-bottom-color: var(--accent);
	}
	.ptitle {
		display: none;
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
		font-size: 22px;
		font-weight: 650;
	}
	.takeaway {
		margin: 0 0 16px;
	}
	.note {
		margin: -8px 0 0;
		font-size: 13px;
		color: var(--ink2);
	}
	@media (max-width: 640px) {
		.tabs {
			position: static;
		}
	}
	@media print {
		.tabs {
			display: none;
		}
		.ptitle {
			display: block;
			font-size: 20px;
			margin-top: 32px;
			padding-top: 12px;
			border-top: 1px solid var(--line);
		}
	}
</style>
