// Shape of the report data made by dupr/export.py (keep both in sync).
// Dates are ISO strings ("2026-05-31T00:00:00"); missing numbers are null.

export type Num = number | null;
export type Period = 'week' | 'month' | 'quarter';
export type RestKey = 'same_day' | '1_3' | '4_7' | '8_14' | '15_plus';

export interface ReportData {
	version: number;
	player: string;
	generated: string;
	formats: FormatData[];
}

export interface Summary {
	matches: number;
	wins: number;
	losses: number;
	win_pct: number;
	first_match: string;
	last_match: string;
	span_days: number;
	games_won: number;
	games_lost: number;
	point_share: Num;
	rally_share?: Num;
	rolling_window: number;
	period: Period;
	win_scale: number;
	win_scale_fitted: boolean;
	rating_start?: Num;
	rating_now?: Num;
	rating_peak?: Num;
	rating_peak_date?: string;
	rating_change?: Num;
	trend_per_month?: Num;
	exp_win_pct?: Num;
	expected_wins?: Num;
	rated_wins?: number; // wins in the matches that have expected wins
	rated_matches?: number;
	wins_above_expected?: Num;
	longest_win_streak: number;
	longest_loss_streak: number;
}

export interface CloseGames {
	games: number;
	game_win_pct: Num;
	close_games: number;
	close_win_pct: Num;
	blowouts: number;
	blowout_win_pct: Num;
	deciders: number;
	decider_win_pct: Num;
	avg_margin_win: Num;
	avg_margin_loss: Num;
}

export interface Match {
	date: string;
	won: boolean;
	game_scores: string;
	partner?: string | null;
	opponents: string;
	opp_rating_avg: Num;
	rating_diff: Num;
	rating_before: Num;
	rating_after: Num;
	rating_impact: Num;
	point_share: Num;
	exp_win: Num;
	scoring?: string;
	source?: string;
}

/** Aggregates of a group of matches (a period, a partner, a match type…). */
export interface Agg {
	matches: number;
	wins: number;
	win_pct: Num;
	point_share: Num;
	avg_point_diff: Num;
	avg_opp_rating: Num;
	rating_gained: Num;
	exp_win_pct: Num;
	avg_impact: Num;
}

export interface Group {
	/** 0 = much weaker (0.3+ below you) … 2 = similar (±0.1) … 4 = much stronger (0.3+ above). */
	group: number;
	matches: number;
	win_pct: Num;
	exp_win_pct: Num;
	point_share: Num;
	avg_impact: Num;
	total_impact: Num;
}

export type Measure = 'rating_impact' | 'vs_exp';

export interface Effect {
	measure: Measure | null;
	groups: Group[];
	verdict: Verdict;
}

/** See partner_verdict / opponent_verdict in dupr/analysis.py. */
export type Verdict =
	| { status: 'no_data' }
	| { status: 'few'; n_weak?: number; n_strong?: number; n_rest: number }
	| {
			status: 'ok';
			measure: Measure;
			n_weak?: number;
			n_strong?: number;
			n_rest: number;
			mean_weak?: number;
			mean_strong?: number;
			mean_rest: number;
			diff: number;
			clear: boolean;
			win_pct_weak?: number;
			exp_win_pct_weak?: Num;
			win_pct_strong?: number;
			exp_win_pct_strong?: Num;
			loss_mean?: number;
			all_losses_mean?: number;
	  };

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Finding = { id: string } & Record<string, any>;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Tip = { id: string; kind: 'work' | 'strength' | 'info'; params: Record<string, any> };

export type Tournament = Agg & {
	tournament: string;
	partner: string | null;
	date: string;
	losses: number;
};

export interface FormatData {
	format: 'DOUBLES' | 'SINGLES';
	summary: Summary;
	close_games: CloseGames;
	level: { band: number; rating: Num };
	tips: Tip[];
	findings: Finding[];
	rating: { date: string; rating: number }[];
	trend: { from: string; to: string; start: number; end: number } | null;
	matches: Match[];
	win_form: { day: string; actual: Num; expected: Num }[];
	opponent_level: { date: string; opp_rating_avg: number; opp_rolling: Num; rating_before: Num; opponents: string }[];
	monthly_rating: { month: string; matches: number; wins: number; change: number; rating_end: Num }[];
	monthly_points: { month: string; matches: number; actual: number; expected: number; gap: number; rating_change: Num }[];
	point_form_hits: { up: number; above: number; down: number; below: number } | null;
	periods: (Agg & { period_end: string; rating_end?: Num })[];
	margins: { margin: number; games: number }[];
	partners: (Agg & { partner: string; partner_rating: Num; last_played: string })[];
	opponents: { opponent: string; matches: number; wins: number; win_pct: Num; point_share: Num }[];
	by_source: (Agg & { source: string })[];
	by_rest: (Agg & { rest: RestKey })[];
	// Optional: reports made before tournaments were added don't have these.
	tournaments?: Tournament[];
	by_context?: (Agg & { context: 'tournament' | 'other' })[];
	best: Match[];
	worst: Match[];
	partner_effect: Effect | null;
	opponent_effect: Effect;
}
