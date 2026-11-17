// English text of the report. The French version (messages.fr.ts) has the same shape.
// Numbers come from dupr/analysis.py and dupr/export.py; the choices (which sentence applies) are
// made there, so these functions only put words around them.
import { date, num, pct, periodLabel, rating, signed, span } from './format.ts';
import type { CloseGames, Finding, Period, RestKey, Verdict } from './types.ts';

const abs3 = (v: number) => num(Math.abs(v), 3);
const periodWord: Record<Period, string> = { week: 'week', month: 'month', quarter: 'quarter' };

const restPhrase: Record<RestKey, string> = {
	same_day: 'when you already played earlier the same day',
	'1_3': 'when your previous match was 1–3 days before',
	'4_7': 'when your previous match was 4–7 days before',
	'8_14': 'when your previous match was 1–2 weeks before',
	'15_plus': 'after a break of more than 2 weeks'
};

function move(v: number, measure: string): string {
	if (measure === 'rating_impact') return v >= 0 ? `gain ${abs3(v)} rating` : `lose ${abs3(v)} rating`;
	return v >= 0
		? `win ${num(v, 2)} more matches than expected`
		: `win ${num(Math.abs(v), 2)} fewer matches than expected`;
}

function vsPrediction(actual: number, predicted: number | null | undefined): string {
	if (predicted == null) return '';
	if (actual >= predicted + 3) return `, more than the ${pct(predicted)} the ratings predict`;
	if (actual <= predicted - 3) return `, less than the ${pct(predicted)} the ratings predict`;
	return `, about what the ratings predict (${pct(predicted)})`;
}

export type FindingText = (f: Finding, fmt: string) => string;

const findings = {
	rating_change: (f, fmt) =>
		`Your ${fmt} rating went ${f.change >= 0 ? 'up' : 'down'} ${abs3(f.change)} (${rating(f.start)} → ` +
		`${rating(f.now)}) over ${f.matches} matches; peak ${rating(f.peak)} on ${date(f.peak_date)}.`,
	trend: (f) =>
		`Long-run trend: ${signed(f.per_month)} per month` +
		(f.last_90d != null
			? `; last 90 days: ${signed(f.last_90d)} per month (${{ faster: 'speeding up', slower: 'slowing down', steady: 'steady' }[f.pace as string]})`
			: '') +
		'.',
	best_period: (f) =>
		`Best ${periodWord[f.period as Period]}: ${periodLabel(f.best, f.period)} (${pct(f.best_pct)} wins over ` +
		`${f.best_n} matches); worst: ${periodLabel(f.worst, f.period)} (${pct(f.worst_pct)} over ${f.worst_n}).`,
	halves: (f) => {
		let s =
			`Your first ${f.n_early} matches (${span(f.early_from, f.early_to)}) compared with your last ${f.n_late} ` +
			`(${span(f.late_from, f.late_to)}): you won ${pct(f.win_early)} of matches then, ${pct(f.win_late)} now; ` +
			`${pct(f.points_early)} of points then, ${pct(f.points_late)} now.`;
		if (!f.opponents) return s;
		const o = `${num(f.opp_early, 2)} → ${num(f.opp_late, 2)}`;
		s += {
			stronger: ` Your opponents are also stronger now (average rating ${o}).`,
			weaker: ` Your opponents are weaker now (average rating ${o}).`,
			same: ` Your opponents' level is about the same (average rating around ${num(f.opp_late, 2)}).`
		}[f.opponents as string];
		s += {
			progress_tougher: ' You win more often even though your opponents are tougher: clear progress.',
			level_up: ' Getting similar results against tougher opponents means your level has gone up.',
			tougher_explains:
				' You win less, but mostly because your opponents are tougher: for their level you are doing about as well as before.',
			worse_than_tougher:
				' You win less, and more than the tougher opponents explain: worth looking at what changed.',
			easier_explains: ' You win more, but partly because your opponents are weaker.',
			progress_easier: ' You win more, and by more than the weaker opponents explain: real progress.',
			progress: ' Same level of opponents, better results: clear progress.',
			slipped: ' Same or weaker opponents but fewer wins: your results have slipped, worth looking at what changed.',
			stable: ' Overall, your level is stable.'
		}[f.meaning as string];
		return s;
	},
	vs_expected: (f) =>
		`Compared with the rating-gap model you won ${f.wins} matches against ~${num(f.expected, 1)} expected ` +
		`(${signed(f.above, 1)}): you ${f.above > 0 ? 'outperform' : 'underperform'} the ratings on paper.`,
	underdog: (f) =>
		`When the ratings give your team 40% or less to win, you win ${pct(f.win_pct)} (${f.matches} matches).`,
	favourite: (f) =>
		`When the ratings give your team 60% or more to win, you win ${pct(f.win_pct)} (${f.matches} matches).`,
	close_games: (f) =>
		`Close games (decided by 2 points or fewer): ${pct(f.pct)} won over ${f.games} games – ` +
		`${{ clutch: 'clutch', weak: 'a weak spot', coin_flip: 'a coin flip' }[f.verdict as string]}.`,
	deciders: (f) => `Deciding 3rd games: ${pct(f.pct)} won (${f.games} played).`,
	partners: (f) =>
		`Best regular partner: ${f.best} (${pct(f.best_pct)} in ${f.best_n}); toughest: ${f.worst} ` +
		`(${pct(f.worst_pct)} in ${f.worst_n}).`,
	rest: (f) => {
		let s =
			`Time between matches: you win most often ${restPhrase[f.best as RestKey]} (${pct(f.best_pct)} of ` +
			`${f.best_n} matches) and least often ${restPhrase[f.worst as RestKey]} (${pct(f.worst_pct)} of ${f.worst_n} matches).`;
		s += {
			small: " The difference is small, so rest time doesn't seem to matter much for you.",
			tiring: ' Playing several matches in one session may tire you: watch your energy in later matches.',
			rhythm: ' Long breaks seem to cost you rhythm: after time off, a practice session before competing may help.',
			shorter: ' Shorter gaps between matches seem to suit you better than longer ones.',
			longer: ' A bit more rest between matches seems to suit you better than playing very often.'
		}[f.meaning as string];
		if (f.few && f.meaning !== 'small') s += ' Few matches in these groups, so treat this as a hint, not a rule.';
		return s;
	},
	impact: (f) => {
		let s =
			`On average a win raises your rating by ${abs3(f.win)} and a loss ` +
			`${f.loss < 0 ? 'lowers' : 'still raises'} it by ${abs3(f.loss)}.`;
		if (f.close_loss != null && f.heavy_loss != null) {
			const cost = (v: number) => (v < 0 ? `costs you ${abs3(v)}` : `still gains you ${abs3(v)}`);
			s +=
				` The score matters, not just the result: a close loss (3 points or less per game) ${cost(f.close_loss)} ` +
				`on average, while a heavy loss (6+ points per game) ${cost(f.heavy_loss)}. Keeping lost games close protects your rating.`;
		}
		return s;
	},
	streaks: (f) => {
		let s = `Your longest winning streak is ${f.longest_win} matches in a row, and your longest losing streak is ${f.longest_loss}.`;
		if (f.current_won == null || !f.current) return s;
		if (f.current === 1) return s + ` You ${f.current_won ? 'won' : 'lost'} your last match.`;
		return s + ` Right now you have ${f.current_won ? 'won' : 'lost'} your last ${f.current} matches in a row.`;
	}
} satisfies Record<string, FindingText>;

export type TipText = {
	title: string;
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	finding: (p: Record<string, any>) => string;
	/** One piece of advice, or one per rating band (below 3.0 … 4.5+). */
	advice: string | string[];
};

const tips = {
	slow_starts: {
		title: 'Slow starts',
		finding: (p) =>
			`You win ${pct(p.game1_pct)} of first games but ${pct(p.game2_pct)} of second games (${p.matches} multi-game matches).`,
		advice: [
			'Warm up for 10 minutes before your first match: serves, returns and short dink rallies. In game 1, just aim to get every serve and return in.',
			'Warm up dinks and third-shot drops before you start. In game 1, play the percentages: deep serve, deep return, get to the kitchen line, no early speed-ups.',
			'Use the warm-up to groove drops and resets. Early in game 1, test the opponents with safe patterns (middle, backhands) before taking risks.',
			"Warm up like for a tournament: movement, a few fast hands exchanges, then start game 1 with high-percentage resets until you have read the opponents' tendencies.",
			'Go in with a first-game plan (targets, serve and return patterns) and a short activation routine: at this level the first points often decide game 1.'
		]
	},
	fading: {
		title: 'Fading after game 1',
		finding: (p) =>
			`You win ${pct(p.game1_pct)} of first games but only ${pct(p.game2_pct)} of second games (${p.matches} multi-game matches).`,
		advice: [
			'Your opponents adapt after game 1. Between games, agree on one simple thing with your partner (for example: keep the ball in the middle) and stick to it. Drink and breathe.',
			'Between games, pick one change together: aim more at the weaker player, return deeper, or move up to the kitchen faster. Keep your energy up.',
			'Opponents adjust in game 2. Prepare a plan B (stacking, new targets, slower pace with more dinks) and decide it together between games.',
			'Expect a change after they lose game 1. Spot it in the first points of game 2 and counter quickly: switch targets, vary pace and height.',
			'Review game 1 with your partner: what worked for them and what they will change. Have counters ready, and watch your fitness: game 2 is often won on conditioning and adjustments.'
		]
	},
	comebacks: {
		title: 'Comebacks',
		finding: (p) => `After losing the first game you still win ${pct(p.pct)} of matches (${p.matches} matches).`,
		advice: 'Keep doing what you do between games: your adjustments work.'
	},
	comeback: {
		title: 'Hard to come back',
		finding: (p) => `After losing the first game you win only ${pct(p.pct)} of matches (${p.matches} matches).`,
		advice: [
			'After losing a game, slow down: make the opponents hit more balls. Fewer mistakes is the fastest way back.',
			'After a lost game, change one concrete thing: more dinks and drops, aim at the weaker opponent, and cut return errors.',
			'After a lost game, find the 1–2 patterns that cost you points and change them: stack or switch sides, slow the pace, target the middle.',
			'Treat game 2 as a new match: change targets, use resets to break their rhythm, and take a time-out early if they go on a run.',
			'Prepare a plan B and C in advance (stacking variations, serve and return changes), use time-outs tactically and reset mentally between games.'
		]
	},
	closeout: {
		title: 'Closing out matches',
		finding: (p) => `After winning the first game you go on to win only ${pct(p.pct)} of matches (${p.matches} matches).`,
		advice: [
			'After winning game 1, keep doing exactly what worked: same targets, same patience.',
			"Don't relax after game 1: start game 2 with the same focus and tactics until the opponents change something.",
			"In game 2, watch for the opponents' adjustment (new targets, stacking, more speed) and adapt early instead of waiting to fall behind.",
			'Expect the opponents to change after game 1 and stay one step ahead: vary your serves and returns early in game 2.',
			"Keep the pressure on: opponents at this level adapt fast, so change patterns before they settle and don't give away cheap points."
		]
	},
	tight_endings: {
		title: 'Tight endings',
		finding: (p) =>
			`You win ${pct(p.close_pct)} of close games (decided by 2 points or fewer) vs ${pct(p.game_pct)} of all your games.`,
		advice: [
			'At 8-8 and later, just get your serve and return deep and in, then dink until someone makes a mistake. Practise games that start at 7-7.',
			'Practise games that start at 8-8. At game point, play your safest pattern: deep serve, deep return, drop, dink, and no risky speed-ups.',
			"In tight endings, don't speed up balls below the net; reset instead. Agree with your partner on a go-to pattern for big points.",
			'At the end of games, attack only high balls, take a time-out to reset when needed, and rely on your most reliable patterns.',
			'Work on your routine between points (breathing, a set reset) and on a few clutch patterns you trust. Note which opponent tightens up on big points.'
		]
	},
	clutch: {
		title: 'Clutch in tight endings',
		finding: (p) => `You win ${pct(p.close_pct)} of close games vs ${pct(p.game_pct)} of all your games.`,
		advice: 'You handle pressure well; the gains are earlier in the game, before it gets tight.'
	},
	heavy_losses: {
		title: 'Heavy losses',
		finding: (p) =>
			`${pct(p.pct)} of the games you lose are by 7 points or more (more than usual for your level, where ${pct(p.threshold)} is already high).`,
		advice: [
			'When you start losing points in a row, slow down: high, deep returns and safe dinks. Take a time-out to break their run.',
			'Stop runs early: take a time-out after 3–4 points in a row, then play safer (deep returns, third-shot drops) to keep the game close.',
			'When a game slips away, break their momentum: time-out, change formation (stack) or targets. Keeping the score close protects your rating.',
			'Find what produces their runs (your speed-ups being countered, one side being targeted) and shut it down with resets and patience.',
			'Heavy losses at this level usually come from a matchup problem: prepare counters for that style and take time-outs earlier.'
		]
	},
	favourite_losses: {
		title: 'Losses as the favourite',
		finding: (p) =>
			`You lost ${p.matches} matches where your team was the clear favourite (60%+ expected)` +
			(p.cost != null ? `, costing ${abs3(p.cost)} rating in total` : '') +
			'.',
		advice: [
			"Against weaker teams keep it simple: get the ball in and let them make the mistakes. Don't try difficult shots.",
			"Against weaker teams stay patient: dink and drop until there's a real opening, and don't get dragged into sloppy rallies.",
			'As the favourite, keep unforced errors low: play the percentages and only speed up high balls.',
			'Stay focused on the process against weaker teams: target the weaker player, keep errors low and close out games firmly.',
			"Losing as the favourite costs a lot of rating at this level: take every rated match seriously and don't experiment in them."
		]
	},
	vs_stronger_ok: {
		title: 'Competitive against stronger players',
		finding: (p) => `Against stronger opponents you still win ${pct(p.pct)} of points (${p.matches} matches).`,
		advice: 'Keep playing up regularly: close scores against better players raise your rating.'
	},
	vs_stronger_gap: {
		title: 'Gap against stronger players',
		finding: (p) => `Against stronger opponents you win ${pct(p.pct)} of points (${p.matches} matches).`,
		advice: [
			'Stronger players punish high balls. Practise keeping your dinks low and your returns deep, and play with better players when you can.',
			'Drill third-shot drops and dinks: better players attack anything high. Play up regularly to get used to the pace.',
			"Work on resets in the transition zone and on blocking hard drives: that's where stronger players win their points.",
			'Work on fast hands exchanges, counter-attacks and patience in long dink rallies; play up in drills and open play.',
			'Study matches against top players (video if possible): shot selection, positioning and variety. Train with stronger partners.'
		]
	},
	energy: {
		title: 'Energy over a long session',
		finding: (p) =>
			`Point win % drops from ${pct(p.early_pct)} in your first 2 matches of a day to ${pct(p.late_pct)} from the 4th match on.`,
		advice: [
			'Eat and drink between matches and take short breaks. Play fewer matches in a row if you get tired.',
			'Pace yourself in long sessions: water, a snack and a short rest between matches, or fewer matches per day.',
			'Pace yourself in long sessions: water, a snack and a short rest between matches, or fewer matches per day.',
			'Work on fitness and recovery between matches (hydration, food, mobility), and plan your session load before events.',
			'Work on fitness and recovery between matches (hydration, food, mobility), and plan your session load before events.'
		]
	},
	best_partner: {
		title: 'Your best partnership',
		finding: (p) =>
			`With ${p.partner} you gain ${signed(p.avg_impact)} rating per match on average (${p.matches} matches, ${pct(p.win_pct)} wins).`,
		advice:
			'Look at what works in this pairing (who covers the middle, who attacks) and bring it to your other partnerships.'
	}
} satisfies Record<string, TipText>;

function opponentVerdict(v: Verdict): string {
	if (v.status === 'no_data') return 'Not enough matches with known opponent ratings yet.';
	if (v.status === 'few')
		return `Not enough matches yet to tell (${v.n_strong} against stronger opponents, ${v.n_rest} against similar or weaker ones; need 5 of each).`;
	let s =
		`Against stronger opponents you ${move(v.mean_strong!, v.measure)} per match on average (${v.n_strong} matches); ` +
		`against similar or weaker opponents you ${move(v.mean_rest, v.measure)} (${v.n_rest} matches).`;
	if (v.clear)
		s += v.diff > 0 ? ' So playing stronger opponents is helping your rating.' : ' So far, playing stronger opponents has cost you rating.';
	else
		s += ` Playing up looks ${v.diff > 0 ? 'better' : 'worse'} for your rating, but the difference is small compared with normal match-to-match variation, so it's not a firm conclusion yet.`;
	s += ` You win ${pct(v.win_pct_strong)} of your matches against stronger opponents${vsPrediction(v.win_pct_strong!, v.exp_win_pct_strong)}.`;
	if (v.loss_mean != null) {
		const ml = v.loss_mean,
			all = v.all_losses_mean ?? 0;
		if (ml >= 0)
			s += ` Even when you lose to them, you still gain ${abs3(ml)} rating on average: DUPR expects you to lose those matches, so a close score is enough to raise your rating.`;
		else
			s +=
				` When you lose to them, you lose ${abs3(ml)} rating on average` +
				(Math.abs(ml) < Math.abs(all) ? `, less than an average loss (${abs3(all)})` : '') +
				': DUPR expects those losses, so they cost little, and a close score can even turn one into a small gain.';
	}
	return s;
}

export const en = {
	reportTitle: 'DUPR performance report',
	generated: (player: string, when: string) => `${player} · generated ${when}`,
	noMatches: 'No matches found.',
	formatName: { DOUBLES: 'Doubles', SINGLES: 'Singles' } as Record<string, string>,
	formatLower: { DOUBLES: 'doubles', SINGLES: 'singles' } as Record<string, string>,
	notEnough: 'Not enough data.',
	print: 'Print / save as PDF',
	exampleBanner: 'Example report with made-up data.',

	glossaryTitle: 'What the numbers mean',
	glossary: [
		['Point win %', 'Share of all points you won. 11-7, 9-11, 11-6 → 31 of 55 points = 56%. 50% = even.'],
		[
			'Expected point win %',
			"The point win % your rating gap predicts. It is computed from the share of rallies you should win, then turned into points for each match's scoring: in side-out scoring only the server scores, which roughly doubles a rally edge (winning 55% of rallies ≈ 60% of the points); in rally scoring both are equal."
		],
		[
			'Rally win %',
			'Share of rallies you win, estimated from your scores. In side-out scoring only the server scores, which stretches a rally edge into a bigger point edge; this undoes it (60% of the points ≈ 55% of the rallies). In rally scoring it equals the point win %.'
		],
		[
			'Win probability',
			'Your average chance of winning a match, from the rating gap between your team and the opponents in each match (the expected win % below, averaged over your matches).'
		],
		[
			'Expected win %',
			"Your chance of winning from the rating gap between your team and the opponents (approximate model: how strongly a rating edge turns into wins is learned from your own matches once you have 30 or more with known ratings; before that, a 0.25 team-rating edge ≈ 76%). DUPR's own model isn't public."
		],
		['Wins above expectation', 'Actual wins minus expected wins. Positive = you beat the ratings.'],
		['Rating change', "How much a match moved your DUPR rating, from DUPR's own data."],
		['Opponent strength', "Your opponents' average rating minus your own rating at the time of the match."],
		['Close game', 'A game decided by 2 points or fewer (11-9, 12-10…).']
	] as [string, string][],

	tiles: {
		rating: 'Current rating',
		peak: (v: string) => `peak ${v}`,
		change: 'Change',
		since: (d: string) => `since ${d}`,
		trend: 'Trend',
		perMonth: 'rating per month',
		record: 'Record',
		winsPct: (v: string) => `${v} wins`,
		winProb: 'Win probability',
		winProbSub: 'per match, from rating gaps',
		winsVsExp: 'Wins vs expected',
		winsVsExpSub: (w: number, e: string) => `${w} wins vs ~${e} expected`,
		pointWin: 'Point win %',
		games: (w: number, l: number) => `games ${w}–${l}`,
		rallyWin: 'Rally win %',
		rallySub: 'estimated from your scores',
		close: 'Close games',
		closeSub: (n: number) => `won · ${n} games decided by ≤2 pts`
	},

	ui: {
		tabs: {
			overview: 'Overview',
			form: 'Form',
			opponents: 'Opponents',
			partners: 'Partners & games',
			games: 'Games',
			matches: 'Matches',
			details: 'All stats'
		},
		ratingLabel: 'DUPR rating',
		since: (d: string) => `since ${d}`,
		peak: (v: string) => `Peak ${v}`,
		record: 'Record',
		winRate: (v: string) => `${v} wins`,
		matchesPlayed: (n: number) => `${n} matches`,
		lastN: (n: number) => `Last ${n}`,
		streakNow: (won: boolean, n: number) =>
			n === 1 ? `${won ? 'Won' : 'Lost'} last match` : `${won ? 'Won' : 'Lost'} last ${n} in a row`,
		highlights: 'Highlights',
		longestStreak: 'Longest win streak',
		inARow: 'matches in a row',
		bestMatch: 'Best match',
		bestPartner: 'Best partner',
		partnerSub: (p: string, n: number) => `${p} wins in ${n} matches`,
		nemesis: 'Toughest opponent',
		nemesisSub: (w: number, l: number) => `you are ${w}–${l} against them`,
		closeGames: 'Close games won',
		closeSub: (n: number) => `of ${n} games decided by ≤2 pts`,
		vsOdds: 'Beating the odds',
		vsOddsSub: (w: number, e: string) => `${w} wins vs ~${e} expected`,
		workOn: 'What to work on',
		insights: 'What the numbers say',
		ratingNow: 'Your rating',
		recentMatches: 'Recent matches',
		showAll: (n: number) => `Show all ${n} matches`,
		showFewer: 'Show fewer',
		with: 'with',
		vs: 'vs',
		allNumbers: 'All numbers',
		perMonth: '/mo',
		findingTitles: {
			rating_change: 'Rating',
			trend: 'Trend',
			best_period: 'Best period',
			halves: 'Then vs now',
			vs_expected: 'Against the odds',
			underdog: 'As the underdog',
			favourite: 'As the favourite',
			close_games: 'Close games',
			deciders: 'Deciding games',
			partners: 'Partners',
			rest: 'Rest between matches',
			impact: 'What a result is worth',
			streaks: 'Streaks'
		} as Record<string, string>
	},

	h: {
		findings: 'Key findings',
		improve: 'How to improve',
		rating: 'Rating',
		form: 'Form',
		opponents: 'Performance by opponent rating',
		byPeriod: (p: Period) => `By ${periodWord[p]}`,
		gamesPartners: 'Games and partners',
		evolution: (p: Period) => `Evolution by ${periodWord[p]}`,
		partners: 'Partners',
		mostFaced: 'Most-faced opponents',
		bySource: 'By match type',
		byRest: 'By rest since previous match',
		gains: 'Biggest rating gains',
		losses: 'Biggest rating losses',
		gameDetails: 'Game details',
		allMatches: 'All matches (most recent first)'
	},

	improveIntro: 'Patterns found in your own matches, with something concrete to try for each.',
	bands: ['Beginner', 'Improving', 'Intermediate', 'Advanced', 'Expert'],
	bandRanges: ['below 3.0', '3.0–3.5', '3.5–4.0', '4.0–4.5', '4.5 and above'],
	levelNote: (name: string, range: string, r: string | null) =>
		r == null
			? 'Your rating is unknown, so the tips are written for an intermediate level (3.5–4.0).'
			: `Tips are adapted to your level: ${name} (${range}), based on your current rating of ${r}.`,
	tipBadge: { work: 'Work on this', strength: 'Strength', info: 'Good to know' },
	tryLabel: 'Try:',
	noTips: 'Not enough matches yet for specific advice (needs a few dozen games).',
	findings,
	tips,
	opponentVerdict,

	gameDetails: (c: CloseGames) =>
		`Games won ${pct(c.game_win_pct)} of ${c.games} · deciding 3rd games won ${pct(c.decider_win_pct)} of ${c.deciders} · ` +
		`heavy games (7+ points difference) won ${pct(c.blowout_win_pct)} of ${c.blowouts} · average margin ` +
		`${signed(c.avg_margin_win, 1)} in games won, ${signed(c.avg_margin_loss, 1)} in games lost.`,

	charts: {
		rating: (fmt: string) => `${fmt} rating over time`,
		ratingLine: 'Your DUPR rating',
		win: 'Win',
		loss: 'Loss',
		trend: (v: string) => `Trend: ${v} per month`,
		start: 'Start',
		peakLbl: 'Peak',
		now: 'Now',
		vs: 'vs',
		ratingAxis: 'DUPR rating',
		ranges: { '3m': '3 months', '6m': '6 months', '1y': '1 year', all: 'All' },
		ratingCap:
			'The blue line is your DUPR rating; each dot is a match (blue = win, orange = loss). The dashed line is your average progress. Use the buttons to zoom on the last months.',
		monthly: 'Rating change per month (months you played)',
		matchesN: (n: number) => `${n} match${n > 1 ? 'es' : ''}`,
		winsOf: (w: number, n: number) => `${w} wins of ${n} matches`,
		ratingEnd: (v: string) => `rating at month end ${v}`,
		monthlyCap:
			'How much your rating went up (blue) or down (orange) over each month you played, with the number of matches. Months without matches are skipped. Your single best and worst matches are listed in the tables below.',
		winForm: 'Win %: actual vs predicted',
		yourWin: (w: number) => `Your win % (last ${w})`,
		expectedWin: 'Expected win %',
		winFormCap: (w: number) =>
			`Blue = how often you won over your last ${w} matches. Orange = how often the ratings say you should win. Blue above orange: you are playing above your rating.`,
		points: 'Points won per month: actual vs expected',
		you: 'You',
		expected: 'Expected',
		above: 'Above',
		below: 'Below',
		pointsTip: (v: string, gap: string) => `won ${v} of points (${gap} vs expected)`,
		ratingThatMonth: (v: string) => `rating that month ${v}`,
		pointsCap: 'Dot = points you won, dash = what the ratings predict. Blue = above, orange = below.',
		pointsHits: (h: { up: number; above: number; down: number; below: number }) =>
			` Blue months raised your rating ${h.up} times out of ${h.above}; orange months lowered it ${h.down} times out of ${h.below}.`,
		oppResults: 'Win % by opponent strength: actual vs expected',
		oppAxis: "Opponents' average rating compared with yours",
		oppResultsCap:
			'Each group is opponents weaker, similar or stronger than you (their average rating minus yours). Blue bars above the orange line mean you beat the odds against that level.',
		oppChange: 'Rating gained per match, by opponent strength',
		perMatch: 'rating per match',
		pointWinShort: (v: string) => `point win ${v}`,
		oppChangeCap:
			'How much rating you gain or lose on average in one match against each level. This shows which opponents actually move your DUPR up.',
		oppTime: "Your rating vs your opponents' level over time",
		oppEach: 'Opponents in each match',
		oppLevel: (w: number) => `Opponents' level (avg of last ${w})`,
		yourRating: 'Your rating',
		oppTimeCap:
			'Orange above blue means you mostly play opponents rated higher than you (playing up). Playing up regularly while keeping scores close is one of the fastest ways to raise your rating.',
		periods: (p: Period) => `Win % and point win % per ${periodWord[p]}`,
		winPct: 'Win %',
		pointWinPct: 'Point win %',
		periodsCap: (p: Period) => `Bars: share of matches won each ${periodWord[p]}. Line: share of points won.`,
		activity: (p: Period) => `Matches played per ${periodWord[p]}`,
		matches: 'Matches',
		activityCap: (p: Period) => `How much you played each ${periodWord[p]}.`,
		margins: 'How your games end (blue = won, orange = lost)',
		marginAxis: 'Score difference in the game (your points − theirs)',
		marginTip: (m: string, n: number) => `won/lost by ${m}: ${n} games`,
		marginsCap:
			'Right side = games won, left side = games lost. Bars near the middle are close games; far-left bars are heavy losses, which cost the most rating.',
		partners: 'Win % with each partner (2+ matches)',
		partnersCap: 'How often you win with each partner. The dotted line marks 50%.'
	},

	groups: ['Much weaker', 'Weaker', 'Similar', 'Stronger', 'Much stronger'],
	groupRanges: ['0.3+ below', '0.1–0.3 below', '±0.1', '0.1–0.3 above', '0.3+ above'],
	rest: {
		same_day: 'Same day as previous match',
		'1_3': '1–3 days after previous match',
		'4_7': '4–7 days after previous match',
		'8_14': '8–14 days after previous match',
		'15_plus': '15+ days after previous match'
	} as Record<RestKey, string>,
	sources: {
		CLUB: 'Club',
		PARTNER: 'Partner',
		DUPR: 'DUPR',
		TOURNAMENT: 'Tournament',
		LEAGUE: 'League',
		UNKNOWN: 'Unknown'
	} as Record<string, string>,

	col: {
		period: (p: Period) => ({ week: 'Week', month: 'Month', quarter: 'Quarter' })[p],
		matches: 'Matches',
		wins: 'Wins',
		winPct: 'Win %',
		pointWin: 'Point win %',
		avgPointDiff: 'Avg point diff',
		avgOppRating: 'Avg opponent rating',
		ratingChange: 'Rating change',
		ratingEnd: 'Rating at end',
		partner: 'Partner',
		partnerRating: 'Partner rating',
		opponent: 'Opponent',
		opponents: 'Opponents',
		source: 'Source',
		rest: 'Rest',
		date: 'Date',
		result: 'W/L',
		score: 'Score',
		oppRating: "Opponents' rating",
		gap: 'Team rating gap',
		expWin: 'Expected win %',
		avgChange: 'Avg rating change',
		totalChange: 'Total rating change',
		w: 'W',
		l: 'L'
	}
};

export type Messages = typeof en;
