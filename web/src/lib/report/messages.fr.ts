// Texte français du rapport : même structure que messages.en.ts.
import { date, num, pct, periodLabel, rating, signed } from './format.ts';
import type { Agg, CloseGames, Finding, Period, RestKey, Verdict } from './types.ts';
import type { Messages } from './messages.en.ts';

const abs3 = (v: number) => num(Math.abs(v), 3);
// Nom de la période et son genre (meilleur mois / meilleure semaine).
const periodWord: Record<Period, string> = { week: 'semaine', month: 'mois', quarter: 'trimestre' };
const fem = (p: Period) => p === 'week';
const par = (p: Period) => ({ week: 'par semaine', month: 'par mois', quarter: 'par trimestre' })[p];


function move(v: number, measure: string): string {
	if (measure === 'rating_impact') return v >= 0 ? `gagnes ${abs3(v)} point de note` : `perds ${abs3(v)} point de note`;
	return v >= 0
		? `gagnes ${num(v, 2)} match de plus que prévu`
		: `gagnes ${num(Math.abs(v), 2)} match de moins que prévu`;
}

function vsPrediction(actual: number, predicted: number | null | undefined): string {
	if (predicted == null) return '';
	if (actual >= predicted + 3) return `, plus que les ${pct(predicted)} prévus par les notes`;
	if (actual <= predicted - 3) return `, moins que les ${pct(predicted)} prévus par les notes`;
	return `, à peu près ce que prévoient les notes (${pct(predicted)})`;
}

// Outsider / favori : victoires réelles comparées aux victoires attendues, en nombre de matchs.
function oddsText(f: Finding, role: string, odds: string): string {
	const s = `Selon les notes, tu étais ${role} dans ${f.matches} matchs (${odds}).`;
	if (f.wins == null || f.exp_win_pct == null) return `${s} Tu en as gagné ${pct(f.win_pct)}.`;
	const exp = num((f.exp_win_pct * f.matches) / 100, 1);
	const diff = f.win_pct - f.exp_win_pct;
	const vs = diff >= 3 ? 'plus que les' : diff <= -3 ? 'moins que les' : 'proche des';
	return `${s} Tu en as gagné ${f.wins} (${pct(f.win_pct)}), ${vs} ${exp} victoires prévues.`;
}

const findings: Messages['findings'] = {
	// Note, tendance et meilleure période : chiffres dans le tableau de la carte (Findings.svelte), ici la conclusion.
	rating_change: (f, fmt) => `En ${f.change >= 0 ? 'hausse' : 'baisse'} de ${abs3(f.change)} sur ${f.matches} matchs en ${fmt}.`,
	trend: (f) => {
		if (f.last_90d == null) return 'Variation moyenne de ta note par mois depuis ton premier match.';
		if (f.pace === 'steady') return 'Même rythme sur les 90 derniers jours.';
		const r = f.last_90d as number,
			t = f.per_month as number;
		if (r >= 0 !== t >= 0) return r >= 0 ? 'Ta note est repartie à la hausse récemment.' : 'Ta note est repartie à la baisse récemment.';
		if (r >= 0) return f.pace === 'faster' ? 'Ta note monte plus vite ces derniers temps.' : 'Ta note monte moins vite ces derniers temps.';
		return f.pace === 'faster' ? 'Ta note baisse moins vite ces derniers temps.' : 'Ta note baisse plus vite ces derniers temps.';
	},
	best_period: (f) => {
		const p = f.period as Period;
		const w = periodWord[p];
		const plural = p === 'month' ? 'mois' : `${w}s`;
		return (
			`${fem(p) ? 'Ta meilleure et ta moins bonne' : 'Ton meilleur et ton moins bon'} ${w} en % de victoires. ` +
			`${fem(p) ? 'Seules' : 'Seuls'} les ${plural} avec ${f.min_matches ?? 5} matchs ou plus comptent.`
		);
	},
	// Les chiffres sont dans un tableau avant/maintenant sur la carte (Findings.svelte) ; ici, la conclusion.
	halves: (f) => {
		const fallback = `Tes ${f.n_early} premiers matchs comparés à tes ${f.n_late} derniers.`;
		if (!f.opponents) return fallback;
		const s = ({
			progress_tougher: ' Tu gagnes plus souvent alors que tes adversaires sont plus forts : net progrès.',
			level_up: ' Des résultats similaires face à des adversaires plus forts : ton niveau a augmenté.',
			tougher_explains:
				' Tu gagnes moins, mais surtout parce que tes adversaires sont plus forts : pour leur niveau, tu fais à peu près aussi bien qu’avant.',
			worse_than_tougher:
				' Tu gagnes moins, et plus que ne l’explique la force de tes adversaires : regarde ce qui a changé.',
			easier_explains: ' Tu gagnes plus, mais en partie parce que tes adversaires sont moins forts.',
			progress_easier: ' Tu gagnes plus, et plus que ne l’explique la faiblesse de tes adversaires : vrai progrès.',
			progress: ' Adversaires de même niveau, meilleurs résultats : net progrès.',
			slipped:
				' Adversaires de même niveau ou moins forts, mais moins de victoires : tes résultats ont baissé, regarde ce qui a changé.',
			stable: ' Dans l’ensemble, ton niveau est stable.'
		} as Record<string, string>)[f.meaning as string];
		return s?.trim() ?? fallback;
	},
	vs_expected: (f) =>
		`Tu as gagné ${f.wins} matchs alors que les notes en prévoyaient environ ${num(f.expected, 1)}` +
		(f.matches ? ` sur ${f.matches}` : '') +
		`, soit ${signed(f.above, 1)}. Tu fais ${f.above > 0 ? 'mieux' : 'moins bien'} que ce que prévoient les notes.`,
	underdog: (f) => oddsText(f, 'outsider', '40 % de chances ou moins'),
	favourite: (f) => oddsText(f, 'favori', '60 % de chances ou plus'),
	close_games: (f) =>
		`Jeux serrés (2 points d’écart ou moins) : ${pct(f.pct)} gagnés sur ${f.games} jeux – ` +
		`${{ clutch: 'tu es solide dans les fins serrées', weak: 'un point faible', coin_flip: 'du pile ou face' }[f.verdict as string]}.`,
	deciders: (f) => `Jeux décisifs (3e jeu) : ${pct(f.pct)} gagnés (${f.games} joués).`,
	partners: (f) =>
		`Meilleur partenaire régulier : ${f.best} (${pct(f.best_pct)} sur ${f.best_n}) ; le plus difficile : ${f.worst} ` +
		`(${pct(f.worst_pct)} sur ${f.worst_n}).`,
	// Les chiffres sont dans le tableau de la carte (Findings.svelte) ; ici, la conclusion.
	impact: (f) =>
		f.close_loss != null && f.heavy_loss != null
			? 'Le score compte, pas seulement le résultat. Rester proche au score protège ta note.'
			: 'Variation moyenne de ta note après une victoire et après une défaite.',
	// Seulement les plus longues séries : la série en cours se voit dans la ligne des derniers matchs.
	streaks: (f) =>
		`Ta plus longue série de victoires est de ${f.longest_win > 1 ? `${f.longest_win} matchs d’affilée` : '1 match'}, et ta plus longue série de défaites de ${f.longest_loss}.`
};

const tips: Messages['tips'] = {
	slow_starts: {
		title: 'Débuts de match lents',
		finding: (p) =>
			`Tu gagnes ${pct(p.game1_pct)} des premiers jeux mais ${pct(p.game2_pct)} des deuxièmes (${p.matches} matchs en plusieurs jeux).`,
		advice: [
			'Échauffe-toi 10 minutes avant ton premier match : services, retours et petits échanges de dinks. Au 1er jeu, vise seulement à mettre chaque service et chaque retour dans le terrain.',
			'Échauffe dinks et drops du 3e coup avant de commencer. Au 1er jeu, joue les pourcentages : service profond, retour profond, montée à la ligne de non-volée, pas d’accélération prématurée.',
			'Profite de l’échauffement pour caler drops et resets. En début de 1er jeu, teste les adversaires avec des schémas sûrs (milieu, revers) avant de prendre des risques.',
			'Échauffe-toi comme en tournoi : déplacements, quelques échanges rapides à la volée, puis commence le 1er jeu avec des resets sûrs jusqu’à avoir lu les habitudes des adversaires.',
			'Arrive avec un plan pour le 1er jeu (cibles, schémas au service et au retour) et une courte routine d’activation : à ce niveau, les premiers points décident souvent du 1er jeu.'
		]
	},
	fading: {
		title: 'Baisse après le 1er jeu',
		finding: (p) =>
			`Tu gagnes ${pct(p.game1_pct)} des premiers jeux mais seulement ${pct(p.game2_pct)} des deuxièmes (${p.matches} matchs en plusieurs jeux).`,
		advice: [
			'Tes adversaires s’adaptent après le 1er jeu. Entre les jeux, mets-toi d’accord avec ton partenaire sur une chose simple (par exemple : garder la balle au milieu) et tiens-t’y. Bois et respire.',
			'Entre les jeux, choisis ensemble un changement : viser davantage le joueur le plus faible, retourner plus profond, ou monter plus vite à la ligne de non-volée. Garde de l’énergie.',
			'Les adversaires s’ajustent au 2e jeu. Prépare un plan B (stacking, nouvelles cibles, rythme plus lent avec plus de dinks) et décide-le ensemble entre les jeux.',
			'Attends-toi à un changement après la perte de leur 1er jeu. Repère-le dès les premiers points du 2e jeu et réponds vite : change de cible, varie rythme et hauteur.',
			'Analyse le 1er jeu avec ton partenaire : ce qui a marché pour eux et ce qu’ils vont changer. Aie des réponses prêtes, et soigne ta condition physique : le 2e jeu se gagne souvent sur le physique et les ajustements.'
		]
	},
	comebacks: {
		title: 'Retours au score',
		finding: (p) => `Après avoir perdu le 1er jeu, tu gagnes encore ${pct(p.pct)} des matchs (${p.matches} matchs).`,
		advice: 'Continue ce que tu fais entre les jeux : tes ajustements fonctionnent.'
	},
	comeback: {
		title: 'Difficile de revenir',
		finding: (p) => `Après avoir perdu le 1er jeu, tu ne gagnes que ${pct(p.pct)} des matchs (${p.matches} matchs).`,
		advice: [
			'Après un jeu perdu, ralentis : fais jouer plus de balles aux adversaires. Moins de fautes, c’est le plus court chemin pour revenir.',
			'Après un jeu perdu, change une chose concrète : plus de dinks et de drops, vise l’adversaire le plus faible, et réduis les fautes au retour.',
			'Après un jeu perdu, trouve les 1 ou 2 schémas qui te coûtent des points et change-les : stacking ou changement de côté, rythme plus lent, jeu au milieu.',
			'Aborde le 2e jeu comme un nouveau match : change de cibles, utilise les resets pour casser leur rythme, et prends un temps mort tôt s’ils enchaînent les points.',
			'Prépare à l’avance un plan B et un plan C (variantes de stacking, changements au service et au retour), utilise les temps morts tactiquement et fais un reset mental entre les jeux.'
		]
	},
	closeout: {
		title: 'Conclure les matchs',
		finding: (p) => `Après avoir gagné le 1er jeu, tu ne gagnes que ${pct(p.pct)} des matchs (${p.matches} matchs).`,
		advice: [
			'Après avoir gagné le 1er jeu, continue exactement ce qui a marché : mêmes cibles, même patience.',
			'Ne relâche pas après le 1er jeu : commence le 2e avec la même concentration et la même tactique tant que les adversaires ne changent rien.',
			'Au 2e jeu, guette l’ajustement des adversaires (nouvelles cibles, stacking, plus de vitesse) et adapte-toi tôt au lieu d’attendre d’être mené.',
			'Attends-toi à ce que les adversaires changent après le 1er jeu et garde un temps d’avance : varie services et retours dès le début du 2e jeu.',
			'Maintiens la pression : à ce niveau, les adversaires s’adaptent vite, alors change de schémas avant qu’ils ne s’installent et ne donne pas de points faciles.'
		]
	},
	tight_endings: {
		title: 'Fins de jeu serrées',
		finding: (p) =>
			`Tu gagnes ${pct(p.close_pct)} des jeux serrés (2 points d’écart ou moins) contre ${pct(p.game_pct)} de l’ensemble de tes jeux.`,
		advice: [
			'À partir de 8-8, mets simplement ton service et ton retour profonds dans le terrain, puis dinke jusqu’à la faute de quelqu’un. Entraîne-toi sur des jeux qui commencent à 7-7.',
			'Entraîne-toi sur des jeux qui commencent à 8-8. Sur balle de jeu, joue ton schéma le plus sûr : service profond, retour profond, drop, dink, et pas d’accélération risquée.',
			'Dans les fins serrées, n’accélère pas les balles sous le filet ; fais un reset. Mets-toi d’accord avec ton partenaire sur un schéma de référence pour les points importants.',
			'En fin de jeu, n’attaque que les balles hautes, prends un temps mort pour souffler si besoin, et appuie-toi sur tes schémas les plus fiables.',
			'Travaille ta routine entre les points (respiration, reset fixe) et quelques schémas fiables pour les points importants. Repère quel adversaire se crispe sur les gros points.'
		]
	},
	clutch: {
		title: 'Solide dans les fins serrées',
		finding: (p) => `Tu gagnes ${pct(p.close_pct)} des jeux serrés contre ${pct(p.game_pct)} de l’ensemble de tes jeux.`,
		advice: 'Tu gères bien la pression ; la marge de progrès est plus tôt dans le jeu, avant que ça se resserre.'
	},
	heavy_losses: {
		title: 'Lourdes défaites',
		finding: (p) =>
			`${pct(p.pct)} des jeux que tu perds le sont par 7 points ou plus (plus que d’habitude pour ton niveau, où ${pct(p.threshold)} est déjà élevé).`,
		advice: [
			'Quand tu commences à perdre des points d’affilée, ralentis : retours hauts et profonds, dinks sûrs. Prends un temps mort pour casser leur série.',
			'Arrête les séries tôt : temps mort après 3 ou 4 points d’affilée, puis joue plus sûr (retours profonds, drops du 3e coup) pour garder le jeu serré.',
			'Quand un jeu t’échappe, casse leur dynamique : temps mort, changement de formation (stacking) ou de cibles. Rester proche au score protège ta note.',
			'Trouve ce qui provoque leurs séries (tes accélérations contrées, un côté ciblé) et coupe-le avec des resets et de la patience.',
			'À ce niveau, les lourdes défaites viennent souvent d’un problème de match-up : prépare des réponses à ce style de jeu et prends tes temps morts plus tôt.'
		]
	},
	favourite_losses: {
		title: 'Défaites en étant favori',
		finding: (p) =>
			`Tu as perdu ${p.matches} matchs où ton équipe était nettement favorite (60 % ou plus de chances)` +
			(p.cost != null ? `, pour un coût total de ${abs3(p.cost)} point de note` : '') +
			'.',
		advice: [
			'Contre des équipes plus faibles, reste simple : mets la balle dans le terrain et laisse-les faire les fautes. Ne tente pas de coups difficiles.',
			'Contre des équipes plus faibles, reste patient : dinks et drops jusqu’à une vraie ouverture, sans te laisser entraîner dans des échanges brouillons.',
			'En favori, limite les fautes directes : joue les pourcentages et n’accélère que les balles hautes.',
			'Reste concentré sur ton jeu contre les équipes plus faibles : cible le joueur le plus faible, limite les fautes et conclus fermement les jeux.',
			'Perdre en favori coûte cher en note à ce niveau : prends chaque match classé au sérieux et n’y fais pas d’expériences.'
		]
	},
	vs_stronger_ok: {
		title: 'Compétitif contre plus fort',
		finding: (p) => `Contre des adversaires plus forts, tu gagnes encore ${pct(p.pct)} des points (${p.matches} matchs).`,
		advice: 'Continue à jouer régulièrement contre plus fort : des scores serrés contre de meilleurs joueurs font monter ta note.'
	},
	vs_stronger_gap: {
		title: 'Écart contre plus fort',
		finding: (p) => `Contre des adversaires plus forts, tu gagnes ${pct(p.pct)} des points (${p.matches} matchs).`,
		advice: [
			'Les joueurs plus forts punissent les balles hautes. Entraîne-toi à garder tes dinks bas et tes retours profonds, et joue avec de meilleurs joueurs quand tu le peux.',
			'Travaille drops du 3e coup et dinks : les meilleurs joueurs attaquent tout ce qui est haut. Joue régulièrement contre plus fort pour t’habituer au rythme.',
			'Travaille les resets dans la zone de transition et le blocage des drives puissants : c’est là que les joueurs plus forts gagnent leurs points.',
			'Travaille les échanges rapides à la volée, les contre-attaques et la patience dans les longs échanges de dinks ; joue contre plus fort à l’entraînement et en jeu libre.',
			'Étudie des matchs de très bons joueurs (en vidéo si possible) : choix de coups, placement et variété. Entraîne-toi avec des partenaires plus forts.'
		]
	},
	energy: {
		title: 'Énergie sur une longue session',
		finding: (p) =>
			`Ton % de points gagnés passe de ${pct(p.early_pct)} sur tes 2 premiers matchs de la journée à ${pct(p.late_pct)} à partir du 4e match.`,
		advice: [
			'Mange et bois entre les matchs et fais de courtes pauses. Joue moins de matchs d’affilée si tu es fatigué.',
			'Gère tes longues sessions : eau, encas et courte pause entre les matchs, ou moins de matchs par jour.',
			'Gère tes longues sessions : eau, encas et courte pause entre les matchs, ou moins de matchs par jour.',
			'Travaille ta condition physique et ta récupération entre les matchs (hydratation, alimentation, mobilité), et planifie ta charge avant les tournois.',
			'Travaille ta condition physique et ta récupération entre les matchs (hydratation, alimentation, mobilité), et planifie ta charge avant les tournois.'
		]
	},
	best_partner: {
		title: 'Ton meilleur duo',
		finding: (p) =>
			`Avec ${p.partner}, tu gagnes ${signed(p.avg_impact)} point de note par match en moyenne (${p.matches} matchs, ${pct(p.win_pct)} de victoires).`,
		advice:
			'Regarde ce qui marche dans ce duo (qui couvre le milieu, qui attaque) et applique-le avec tes autres partenaires.'
	}
};

function opponentVerdict(v: Verdict): string {
	if (v.status === 'no_data') return 'Pas encore assez de matchs avec la note des adversaires.';
	if (v.status === 'few')
		return `Pas encore assez de matchs pour conclure (${v.n_strong} contre des adversaires plus forts, ${v.n_rest} contre des adversaires de niveau égal ou plus faible ; il en faut 5 de chaque).`;
	// Second figure without repeating "point de note" when the measure is rating change.
	const rest =
		v.measure === 'rating_impact'
			? `${v.mean_rest >= 0 ? 'gagnes' : 'perds'} ${abs3(v.mean_rest)}`
			: move(v.mean_rest, v.measure);
	let s =
		`Contre des adversaires plus forts (${v.n_strong} matchs), tu ${move(v.mean_strong!, v.measure)} par match en moyenne ; ` +
		`contre un niveau égal ou plus faible (${v.n_rest} matchs), tu ${rest}.`;
	if (v.clear)
		s += v.diff > 0 ? ' Jouer contre plus fort aide donc ta note.' : ' Jusqu’ici, jouer contre plus fort t’a coûté des points.';
	else
		s += ` Jouer contre plus fort semble ${v.diff > 0 ? 'plus' : 'moins'} favorable, mais l’écart reste faible au regard des variations normales d’un match à l’autre.`;
	s += ` Face à eux, tu gagnes ${pct(v.win_pct_strong)} des matchs${vsPrediction(v.win_pct_strong!, v.exp_win_pct_strong)}.`;
	if (v.loss_mean != null) {
		const ml = v.loss_mean,
			all = v.all_losses_mean ?? 0;
		if (ml >= 0)
			s += ` Même tes défaites contre eux te rapportent ${abs3(ml)} en moyenne. DUPR s’attend à ce que tu les perdes, donc un score serré suffit à faire monter ta note.`;
		else if (Math.abs(ml) < Math.abs(all))
			s += ` Ces défaites ne te coûtent que ${abs3(ml)} en moyenne, contre ${abs3(all)} pour une défaite habituelle. DUPR s’attend à ces défaites, et un score serré peut même en faire un petit gain.`;
		else s += ` Ces défaites te coûtent ${abs3(ml)} en moyenne.`;
	}
	return s;
}

export const fr: Messages = {
	reportTitle: 'PickleStats',
	generated: (player, when) => `${player} · créé le ${when}`,
	noMatches: 'Aucun match trouvé.',
	formatName: { DOUBLES: 'Double', SINGLES: 'Simple' },
	formatLower: { DOUBLES: 'double', SINGLES: 'simple' },
	notEnough: 'Pas assez de données.',
	print: 'Imprimer / enregistrer en PDF',
	exampleBanner: 'Exemple de rapport avec des données inventées.',

	glossaryTitle: 'Ce que veulent dire les chiffres',
	glossary: [
		['% de points gagnés', 'Part de tous les points que tu as gagnés. 11-7, 9-11, 11-6 → 31 points sur 55 = 56 %. 50 % = égalité.'],
		[
			'% de points attendu',
			'Le % de points gagnés que prévoit ton écart de notes. Il est calculé à partir de la part d’échanges que tu devrais gagner, puis converti en points selon le comptage de chaque match : en comptage side-out, seul le serveur marque, ce qui double à peu près un avantage aux échanges (gagner 55 % des échanges ≈ 60 % des points) ; en rally scoring, les deux sont égaux.'
		],
		[
			'% d’échanges gagnés',
			'Part des échanges que tu gagnes, estimée à partir de tes scores. En comptage side-out, seul le serveur marque, ce qui amplifie un avantage aux échanges en un avantage aux points plus grand ; ce chiffre corrige cet effet (60 % des points ≈ 55 % des échanges). En rally scoring, il est égal au % de points gagnés.'
		],
		[
			'Probabilité de victoire',
			'Ta chance moyenne de gagner un match, d’après l’écart de notes entre ton équipe et les adversaires dans chaque match (le % de victoires attendu ci-dessous, en moyenne sur tes matchs).'
		],
		[
			'% de victoires attendu',
			'Ta chance de gagner d’après l’écart de notes entre ton équipe et les adversaires (modèle approximatif : la force avec laquelle un avantage de note se traduit en victoires est apprise sur tes propres matchs dès que tu en as 30 ou plus avec les notes connues ; avant, un avantage de 0,25 de note d’équipe ≈ 76 %). Le modèle de DUPR n’est pas public.'
		],
		['Victoires au-dessus des attentes', 'Victoires réelles moins victoires attendues. Positif = tu fais mieux que les notes.'],
		['Variation de note', 'De combien un match a fait bouger ta note DUPR, d’après les données de DUPR.'],
		['Force des adversaires', 'Note moyenne de tes adversaires moins ta propre note au moment du match.'],
		['Jeu serré', 'Un jeu décidé par 2 points d’écart ou moins (11-9, 12-10…).']
	],

	tiles: {
		rating: 'Note actuelle',
		peak: (v) => `pic ${v}`,
		change: 'Évolution',
		since: (d) => `depuis ${d}`,
		trend: 'Tendance',
		perMonth: 'de note par mois',
		record: 'Bilan',
		winsPct: (v) => `${v} de victoires`,
		winProb: 'Probabilité de victoire',
		winProbSub: 'par match, d’après les écarts de notes',
		winsVsExp: 'Victoires vs attendu',
		winsVsExpSub: (w, e) => `${w} victoires pour ~${e} attendues`,
		pointWin: '% de points gagnés',
		games: (w, l) => `jeux ${w}–${l}`,
		rallyWin: '% d’échanges gagnés',
		rallySub: 'estimé à partir de tes scores',
		close: 'Jeux serrés',
		closeSub: (n) => `gagnés · ${n} jeux à ≤ 2 pts d’écart`
	},

	ui: {
		tabs: {
			overview: 'Vue d’ensemble',
			form: 'Forme',
			opponents: 'Adversaires',
			partners: 'Partenaires et jeux',
			games: 'Jeux',
			matches: 'Matchs',
			tournaments: 'Tournois',
			details: 'Toutes les stats'
		},
		ratingLabel: 'Note DUPR',
		since: (d) => `depuis ${d}`,
		peak: (v) => `Pic ${v}`,
		record: 'Bilan',
		winRate: (v) => `${v} de victoires`,
		matchesPlayed: (n) => `${n} matchs`,
		lastN: (n) => `${n} derniers`,
		streakNow: (won, n) =>
			n === 1 ? `${won ? 'Gagné' : 'Perdu'} le dernier match` : `${n} ${won ? 'victoires' : 'défaites'} d’affilée`,
		highlights: 'Faits marquants',
		longestStreak: 'Plus longue série de victoires',
		inARow: 'matchs d’affilée',
		bestMatch: 'Meilleur match',
		bestPartner: 'Meilleur partenaire',
		partnerSub: (p, n) => `${p} de victoires en ${n} matchs`,
		nemesis: 'Adversaire le plus coriace',
		nemesisSub: (w, l) => `ton bilan : ${w}–${l}`,
		closeGames: 'Jeux serrés gagnés',
		closeSub: (n) => `sur ${n} jeux décidés à ≤2 pts`,
		vsOdds: 'Au-dessus des pronostics',
		vsOddsSub: (w, e) => `${w} victoires pour ~${e} attendues`,
		workOn: 'À travailler',
		insights: 'Ce que disent les chiffres',
		ratingNow: 'Ta note',
		recentMatches: 'Derniers matchs',
		showAll: (n) => `Voir les ${n} matchs`,
		showFewer: 'Voir moins',
		with: 'avec',
		vs: 'contre',
		allNumbers: 'Tous les chiffres',
		perMonth: '/mois',
		cmp: {
			rating: 'Note',
			start: 'Début',
			peak: 'Pic',
			now: 'Actuelle',
			perMonth: 'Par mois',
			sinceStart: 'Depuis le début',
			last90: '90 derniers jours',
			winPct: '% victoires',
			matches: 'Matchs',
			best: (p: Period) => (fem(p) ? 'Meilleure' : 'Meilleur'),
			worst: (p: Period) => (fem(p) ? 'Moins bonne' : 'Moins bon'),
			avgChange: 'Variation moy.',
			win: 'Victoire',
			loss: 'Défaite',
			closeLoss: 'Défaite serrée',
			closeLossSub: '3 points d’écart ou moins par jeu',
			heavyLoss: 'Lourde défaite',
			heavyLossSub: '6 points ou plus par jeu'
		},
		halves: { then: 'Avant', now: 'Maintenant', matches: 'Matchs', won: 'Matchs gagnés', points: 'Points gagnés', opp: 'Note des adversaires' },
		findingTitles: {
			rating_change: 'Note',
			trend: 'Tendance',
			best_period: 'Meilleure période',
			halves: 'Avant / maintenant',
			vs_expected: 'Face aux pronostics',
			underdog: 'En outsider',
			favourite: 'En favori',
			close_games: 'Jeux serrés',
			deciders: 'Jeux décisifs',
			partners: 'Partenaires',
			impact: 'Ce que vaut un résultat',
			streaks: 'Séries'
		}
	},

	h: {
		findings: 'À retenir',
		improve: 'Comment progresser',
		rating: 'Note',
		form: 'Forme',
		opponents: 'Performance selon la note des adversaires',
		byPeriod: (p) => `Par ${periodWord[p]}`,
		gamesPartners: 'Jeux et partenaires',
		evolution: (p) => `Évolution ${par(p)}`,
		partners: 'Partenaires',
		mostFaced: 'Adversaires les plus rencontrés',
		bySource: 'Par type de match',
		byRest: 'Selon le repos depuis le match précédent',
		gains: 'Plus fortes hausses de note',
		losses: 'Plus fortes baisses de note',
		gameDetails: 'Détail des jeux',
		tourSummary: 'En résumé',
		tournaments: 'Tes tournois',
		vsOther: 'Tournois et autres matchs',
		allMatches: 'Tous les matchs (du plus récent au plus ancien)'
	},

	improveIntro: 'Des tendances trouvées dans tes propres matchs, avec pour chacune quelque chose de concret à essayer.',
	bands: ['Débutant', 'En progression', 'Intermédiaire', 'Avancé', 'Expert'],
	bandRanges: ['moins de 3,0', '3,0–3,5', '3,5–4,0', '4,0–4,5', '4,5 et plus'],
	levelNote: (name, range, r) =>
		r == null
			? 'Ta note est inconnue : les conseils sont écrits pour un niveau intermédiaire (3,5–4,0).'
			: `Conseils adaptés à ton niveau : ${name} (${range}), d’après ta note actuelle de ${r}.`,
	tipBadge: { work: 'À travailler', strength: 'Point fort', info: 'Bon à savoir' },
	tryLabel: 'À essayer :',
	noTips: 'Pas encore assez de matchs pour des conseils précis (il faut quelques dizaines de jeux).',
	findings,
	tips,
	opponentVerdict,

	gameDetails: (c: CloseGames) =>
		`Jeux gagnés : ${pct(c.game_win_pct)} sur ${c.games} · 3es jeux décisifs gagnés : ${pct(c.decider_win_pct)} sur ${c.deciders} · ` +
		`jeux à gros écart (7 points ou plus) gagnés : ${pct(c.blowout_win_pct)} sur ${c.blowouts} · écart moyen ` +
		`${signed(c.avg_margin_win, 1)} dans les jeux gagnés, ${signed(c.avg_margin_loss, 1)} dans les jeux perdus.`,

	charts: {
		rating: (fmt) => `Note en ${fmt.toLowerCase()} au fil du temps`,
		ratingLine: 'Ta note DUPR',
		win: 'Victoire',
		loss: 'Défaite',
		trend: (v) => `Tendance : ${v} par mois`,
		start: 'Début',
		peakLbl: 'Pic',
		now: 'Actuelle',
		vs: 'contre',
		ratingAxis: 'Note DUPR',
		ranges: { '3m': '3 mois', '6m': '6 mois', '1y': '1 an', all: 'Tout' },
		ratingCap:
			'La ligne bleu-vert est ta note DUPR ; chaque point est un match (bleu-vert = victoire, orange = défaite). La ligne pointillée montre ta progression moyenne. Utilise les boutons pour zoomer sur les derniers mois.',
		monthly: 'Variation de note par mois (mois joués)',
		matchesN: (n) => `${n} match${n > 1 ? 's' : ''}`,
		winsOf: (w, n) => `${w} victoires sur ${n} matchs`,
		ratingEnd: (v) => `note en fin de mois ${v}`,
		monthlyCap:
			'De combien ta note a monté (bleu-vert) ou baissé (orange) chaque mois où tu as joué, avec le nombre de matchs. Les mois sans match sont omis. Tes meilleurs et pires matchs sont dans les tableaux plus bas.',
		winForm: '% de victoires : réel vs prévu',
		yourWin: (w) => `Ton % de victoires (${w} derniers)`,
		expectedWin: '% de victoires attendu',
		winFormCap: (w) =>
			`Bleu-vert = ta part de victoires sur tes ${w} derniers matchs. Orange = la part que prévoient les notes. Bleu-vert au-dessus de l’orange : tu joues au-dessus de ta note.`,
		points: 'Points gagnés par mois : réel vs attendu',
		you: 'Toi',
		expected: 'Attendu',
		above: 'Au-dessus',
		below: 'En dessous',
		pointsTip: (v, gap) => `${v} des points gagnés (${gap} vs attendu)`,
		ratingThatMonth: (v) => `note ce mois-là ${v}`,
		pointsCap:
			'Le rond est la part des points que tu as gagnés dans le mois. Le trait est la part que ta note laissait prévoir. Bleu-vert, tu fais mieux que prévu. Orange, moins bien.',
		pointsHits: (h) =>
			` Sur ${h.above} mois bleu-vert, ta note a monté ${h.up} fois. Sur ${h.below} mois orange, elle a baissé ${h.down} fois.`,
		oppResults: '% de victoires selon la force des adversaires : réel vs attendu',
		oppAxis: 'Note moyenne des adversaires par rapport à la tienne',
		oppResultsCap:
			'Chaque groupe correspond à des adversaires plus faibles, de même niveau ou plus forts que toi (leur note moyenne moins la tienne). Une barre bleu-vert au-dessus de la ligne orange : tu fais mieux que prévu contre ce niveau.',
		oppChange: 'Note gagnée par match, selon la force des adversaires',
		perMatch: 'de note par match',
		pointWinShort: (v) => `points gagnés ${v}`,
		oppChangeCap:
			'Combien de note tu gagnes ou perds en moyenne en un match contre chaque niveau. Cela montre quels adversaires font vraiment monter ta note DUPR.',
		oppTime: 'Ta note vs le niveau de tes adversaires au fil du temps',
		oppEach: 'Adversaires de chaque match',
		oppLevel: (w) => `Niveau des adversaires (moyenne des ${w} derniers)`,
		yourRating: 'Ta note',
		oppTimeCap:
			'Orange au-dessus du bleu-vert : tu joues surtout contre des adversaires mieux notés que toi. Jouer régulièrement contre plus fort en restant proche au score est l’un des moyens les plus rapides de faire monter ta note.',
		periods: (p) => `% de victoires et de points gagnés ${par(p)}`,
		winPct: '% de victoires',
		pointWinPct: '% de points gagnés',
		periodsCap: (p) => `Barres : part des matchs gagnés ${par(p)}. Ligne : part des points gagnés.`,
		activity: (p) => `Matchs joués ${par(p)}`,
		matches: 'Matchs',
		activityCap: (p) => `Combien tu as joué ${par(p)}.`,
		margins: 'Comment se terminent tes jeux (bleu-vert = gagnés, orange = perdus)',
		marginAxis: 'Écart de score dans le jeu (tes points − les leurs)',
		marginTip: (m, n) => `gagnés/perdus de ${m} : ${n} jeux`,
		marginsCap:
			'À droite les jeux gagnés, à gauche les jeux perdus. Les barres près du centre sont les jeux serrés ; celles tout à gauche sont les lourdes défaites, qui coûtent le plus de note.',
		partners: '% de victoires avec chaque partenaire (2 matchs ou plus)',
		partnersCap: 'À quelle fréquence tu gagnes avec chaque partenaire. La ligne pointillée marque 50 %.'
	},

	groups: ['Beaucoup plus faibles', 'Plus faibles', 'Même niveau', 'Plus forts', 'Beaucoup plus forts'],
	groupRanges: ['0,3+ en dessous', '0,1–0,3 en dessous', '±0,1', '0,1–0,3 au-dessus', '0,3+ au-dessus'],
	rest: {
		same_day: 'Même jour',
		'1_3': '1 à 3 jours',
		'4_7': '4 à 7 jours',
		'8_14': '8 à 14 jours',
		'15_plus': '15 jours ou plus'
	},
	context: { tournament: 'Tournois', other: 'Autres matchs' },
	tournamentsIntro: (n, t, o) =>
		`${n} tournoi${n > 1 ? 's' : ''} trouvé${n > 1 ? 's' : ''} dans tes matchs.` +
		(t && o
			? ` En tournoi, tu gagnes ${pct(t.win_pct)} des matchs (${t.matches}), contre ${pct(o.win_pct)} ailleurs (${o.matches}). ` +
				`Ta note a varié de ${signed(t.rating_gained)} en tournoi et de ${signed(o.rating_gained)} sur les autres matchs.`
			: ''),
	tournamentsNote:
		'DUPR n’envoie pas le nom des tournois. Il est lu dans le nom de l’événement de tes matchs, donc certains tournois peuvent manquer dans cette liste.',
	sources: {
		CLUB: 'Club',
		PARTNER: 'Partenaire',
		DUPR: 'DUPR',
		TOURNAMENT: 'Tournoi',
		LEAGUE: 'Ligue',
		UNKNOWN: 'Inconnu'
	},

	col: {
		period: (p) => ({ week: 'Semaine', month: 'Mois', quarter: 'Trimestre' })[p],
		matches: 'Matchs',
		wins: 'Victoires',
		winPct: '% victoires',
		pointWin: '% points gagnés',
		avgPointDiff: 'Écart moyen de points',
		avgOppRating: 'Note moy. adversaires',
		ratingChange: 'Variation de note',
		ratingEnd: 'Note en fin de période',
		partner: 'Partenaire',
		partnerRating: 'Note du partenaire',
		opponent: 'Adversaire',
		opponents: 'Adversaires',
		source: 'Type',
		rest: 'Repos',
		date: 'Date',
		result: 'V/D',
		score: 'Score',
		oppRating: 'Note des adversaires',
		gap: 'Écart de note d’équipe',
		expWin: '% victoires attendu',
		avgChange: 'Variation moy. de note',
		totalChange: 'Variation totale de note',
		tournament: 'Tournoi',
		record: 'V\u2060–\u2060D', // liants : jamais de coupure au tiret
		w: 'V',
		l: 'D'
	}
};
