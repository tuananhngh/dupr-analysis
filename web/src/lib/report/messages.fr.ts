// Texte français du rapport : même structure que messages.en.ts.
import { date, num, pct, periodLabel, rating, signed, span } from './format.ts';
import type { CloseGames, Finding, Period, RestKey, Verdict } from './types.ts';
import type { Messages } from './messages.en.ts';

const abs3 = (v: number) => num(Math.abs(v), 3);
// Nom de la période et son genre (meilleur mois / meilleure semaine).
const periodWord: Record<Period, string> = { week: 'semaine', month: 'mois', quarter: 'trimestre' };
const fem = (p: Period) => p === 'week';
const par = (p: Period) => ({ week: 'par semaine', month: 'par mois', quarter: 'par trimestre' })[p];

const restPhrase: Record<RestKey, string> = {
	same_day: 'quand vous avez déjà joué plus tôt le même jour',
	'1_3': 'quand votre match précédent date de 1 à 3 jours',
	'4_7': 'quand votre match précédent date de 4 à 7 jours',
	'8_14': 'quand votre match précédent date de 1 à 2 semaines',
	'15_plus': 'après une pause de plus de 2 semaines'
};

function move(v: number, measure: string): string {
	if (measure === 'rating_impact') return v >= 0 ? `gagnez ${abs3(v)} point de note` : `perdez ${abs3(v)} point de note`;
	return v >= 0
		? `gagnez ${num(v, 2)} match de plus que prévu`
		: `gagnez ${num(Math.abs(v), 2)} match de moins que prévu`;
}

function vsPrediction(actual: number, predicted: number | null | undefined): string {
	if (predicted == null) return '';
	if (actual >= predicted + 3) return `, plus que les ${pct(predicted)} prévus par les notes`;
	if (actual <= predicted - 3) return `, moins que les ${pct(predicted)} prévus par les notes`;
	return `, à peu près ce que prévoient les notes (${pct(predicted)})`;
}

const findings: Messages['findings'] = {
	rating_change: (f, fmt) =>
		`Votre note en ${fmt} a ${f.change >= 0 ? 'augmenté' : 'baissé'} de ${abs3(f.change)} (${rating(f.start)} → ` +
		`${rating(f.now)}) sur ${f.matches} matchs ; pic à ${rating(f.peak)} le ${date(f.peak_date)}.`,
	trend: (f) =>
		`Tendance de fond : ${signed(f.per_month)} par mois` +
		(f.last_90d != null
			? ` ; sur les 90 derniers jours : ${signed(f.last_90d)} par mois (${{ faster: 'en accélération', slower: 'en ralentissement', steady: 'stable' }[f.pace as string]})`
			: '') +
		'.',
	best_period: (f) => {
		const p = f.period as Period;
		return (
			`${fem(p) ? 'Meilleure' : 'Meilleur'} ${periodWord[p]} : ${periodLabel(f.best, p)} (${pct(f.best_pct)} de victoires sur ` +
			`${f.best_n} matchs) ; ${fem(p) ? 'la moins bonne' : 'le moins bon'} : ${periodLabel(f.worst, p)} (${pct(f.worst_pct)} sur ${f.worst_n}).`
		);
	},
	halves: (f) => {
		let s =
			`Vos ${f.n_early} premiers matchs (${span(f.early_from, f.early_to)}) comparés à vos ${f.n_late} derniers ` +
			`(${span(f.late_from, f.late_to)}) : vous gagniez ${pct(f.win_early)} des matchs, ${pct(f.win_late)} maintenant ; ` +
			`${pct(f.points_early)} des points, ${pct(f.points_late)} maintenant.`;
		if (!f.opponents) return s;
		const o = `${num(f.opp_early, 2)} → ${num(f.opp_late, 2)}`;
		s += {
			stronger: ` Vos adversaires sont aussi plus forts maintenant (note moyenne ${o}).`,
			weaker: ` Vos adversaires sont moins forts maintenant (note moyenne ${o}).`,
			same: ` Le niveau de vos adversaires est à peu près le même (note moyenne autour de ${num(f.opp_late, 2)}).`
		}[f.opponents as string];
		s += {
			progress_tougher: ' Vous gagnez plus souvent alors que vos adversaires sont plus forts : net progrès.',
			level_up: ' Des résultats similaires face à des adversaires plus forts : votre niveau a augmenté.',
			tougher_explains:
				' Vous gagnez moins, mais surtout parce que vos adversaires sont plus forts : pour leur niveau, vous faites à peu près aussi bien qu’avant.',
			worse_than_tougher:
				' Vous gagnez moins, et plus que ne l’explique la force de vos adversaires : regardez ce qui a changé.',
			easier_explains: ' Vous gagnez plus, mais en partie parce que vos adversaires sont moins forts.',
			progress_easier: ' Vous gagnez plus, et plus que ne l’explique la faiblesse de vos adversaires : vrai progrès.',
			progress: ' Adversaires de même niveau, meilleurs résultats : net progrès.',
			slipped:
				' Adversaires de même niveau ou moins forts, mais moins de victoires : vos résultats ont baissé, regardez ce qui a changé.',
			stable: ' Dans l’ensemble, votre niveau est stable.'
		}[f.meaning as string];
		return s;
	},
	vs_expected: (f) =>
		`D’après l’écart de notes, vous deviez gagner environ ${num(f.expected, 1)} matchs ; vous en avez gagné ${f.wins} ` +
		`(${signed(f.above, 1)}) : vous faites ${f.above > 0 ? 'mieux' : 'moins bien'} que ce que prévoient les notes.`,
	underdog: (f) =>
		`Quand les notes donnent à votre équipe 40 % de chances ou moins, vous gagnez ${pct(f.win_pct)} des matchs (${f.matches} matchs).`,
	favourite: (f) =>
		`Quand les notes donnent à votre équipe 60 % de chances ou plus, vous gagnez ${pct(f.win_pct)} des matchs (${f.matches} matchs).`,
	close_games: (f) =>
		`Jeux serrés (2 points d’écart ou moins) : ${pct(f.pct)} gagnés sur ${f.games} jeux – ` +
		`${{ clutch: 'vous êtes solide dans les fins serrées', weak: 'un point faible', coin_flip: 'du pile ou face' }[f.verdict as string]}.`,
	deciders: (f) => `Jeux décisifs (3e jeu) : ${pct(f.pct)} gagnés (${f.games} joués).`,
	partners: (f) =>
		`Meilleur partenaire régulier : ${f.best} (${pct(f.best_pct)} sur ${f.best_n}) ; le plus difficile : ${f.worst} ` +
		`(${pct(f.worst_pct)} sur ${f.worst_n}).`,
	rest: (f) => {
		let s =
			`Temps entre les matchs : vous gagnez le plus souvent ${restPhrase[f.best as RestKey]} (${pct(f.best_pct)} sur ` +
			`${f.best_n} matchs) et le moins souvent ${restPhrase[f.worst as RestKey]} (${pct(f.worst_pct)} sur ${f.worst_n} matchs).`;
		s += {
			small: ' L’écart est faible : le temps de repos ne semble pas compter beaucoup pour vous.',
			tiring: ' Enchaîner plusieurs matchs dans la même session semble vous fatiguer : surveillez votre énergie sur les derniers matchs.',
			rhythm: ' Les longues pauses semblent vous faire perdre le rythme : après une coupure, un entraînement avant de jouer en compétition peut aider.',
			shorter: ' Des matchs rapprochés semblent mieux vous réussir que des matchs espacés.',
			longer: ' Un peu plus de repos entre les matchs semble mieux vous réussir que jouer très souvent.'
		}[f.meaning as string];
		if (f.few && f.meaning !== 'small') s += ' Peu de matchs dans ces groupes : à prendre comme une piste, pas comme une règle.';
		return s;
	},
	impact: (f) => {
		let s =
			`En moyenne, une victoire augmente votre note de ${abs3(f.win)} et une défaite ` +
			`${f.loss < 0 ? 'la baisse' : 'l’augmente quand même'} de ${abs3(f.loss)}.`;
		if (f.close_loss != null && f.heavy_loss != null) {
			const cost = (v: number) => (v < 0 ? `vous coûte ${abs3(v)}` : `vous rapporte quand même ${abs3(v)}`);
			s +=
				` Le score compte, pas seulement le résultat : une défaite serrée (3 points d’écart ou moins par jeu) ${cost(f.close_loss)} ` +
				`en moyenne, une lourde défaite (6 points ou plus par jeu) ${cost(f.heavy_loss)}. Rester proche au score protège votre note.`;
		}
		return s;
	},
	streaks: (f) => {
		let s = `Votre plus longue série de victoires est de ${f.longest_win} matchs d’affilée, et votre plus longue série de défaites de ${f.longest_loss}.`;
		if (f.current_won == null || !f.current) return s;
		if (f.current === 1) return s + ` Vous avez ${f.current_won ? 'gagné' : 'perdu'} votre dernier match.`;
		return s + ` En ce moment, vous avez ${f.current_won ? 'gagné' : 'perdu'} vos ${f.current} derniers matchs d’affilée.`;
	}
};

const tips: Messages['tips'] = {
	slow_starts: {
		title: 'Débuts de match lents',
		finding: (p) =>
			`Vous gagnez ${pct(p.game1_pct)} des premiers jeux mais ${pct(p.game2_pct)} des deuxièmes (${p.matches} matchs en plusieurs jeux).`,
		advice: [
			'Échauffez-vous 10 minutes avant votre premier match : services, retours et petits échanges de dinks. Au 1er jeu, visez seulement à mettre chaque service et chaque retour dans le terrain.',
			'Échauffez dinks et drops du 3e coup avant de commencer. Au 1er jeu, jouez les pourcentages : service profond, retour profond, montée à la ligne de non-volée, pas d’accélération prématurée.',
			'Profitez de l’échauffement pour caler drops et resets. En début de 1er jeu, testez les adversaires avec des schémas sûrs (milieu, revers) avant de prendre des risques.',
			'Échauffez-vous comme en tournoi : déplacements, quelques échanges rapides à la volée, puis commencez le 1er jeu avec des resets sûrs jusqu’à avoir lu les habitudes des adversaires.',
			'Arrivez avec un plan pour le 1er jeu (cibles, schémas au service et au retour) et une courte routine d’activation : à ce niveau, les premiers points décident souvent du 1er jeu.'
		]
	},
	fading: {
		title: 'Baisse après le 1er jeu',
		finding: (p) =>
			`Vous gagnez ${pct(p.game1_pct)} des premiers jeux mais seulement ${pct(p.game2_pct)} des deuxièmes (${p.matches} matchs en plusieurs jeux).`,
		advice: [
			'Vos adversaires s’adaptent après le 1er jeu. Entre les jeux, mettez-vous d’accord avec votre partenaire sur une chose simple (par exemple : garder la balle au milieu) et tenez-vous-y. Buvez et respirez.',
			'Entre les jeux, choisissez ensemble un changement : viser davantage le joueur le plus faible, retourner plus profond, ou monter plus vite à la ligne de non-volée. Gardez de l’énergie.',
			'Les adversaires s’ajustent au 2e jeu. Préparez un plan B (stacking, nouvelles cibles, rythme plus lent avec plus de dinks) et décidez-le ensemble entre les jeux.',
			'Attendez-vous à un changement après la perte de leur 1er jeu. Repérez-le dès les premiers points du 2e jeu et répondez vite : changez de cible, variez rythme et hauteur.',
			'Analysez le 1er jeu avec votre partenaire : ce qui a marché pour eux et ce qu’ils vont changer. Ayez des réponses prêtes, et soignez votre condition physique : le 2e jeu se gagne souvent sur le physique et les ajustements.'
		]
	},
	comebacks: {
		title: 'Retours au score',
		finding: (p) => `Après avoir perdu le 1er jeu, vous gagnez encore ${pct(p.pct)} des matchs (${p.matches} matchs).`,
		advice: 'Continuez ce que vous faites entre les jeux : vos ajustements fonctionnent.'
	},
	comeback: {
		title: 'Difficile de revenir',
		finding: (p) => `Après avoir perdu le 1er jeu, vous ne gagnez que ${pct(p.pct)} des matchs (${p.matches} matchs).`,
		advice: [
			'Après un jeu perdu, ralentissez : faites jouer plus de balles aux adversaires. Moins de fautes, c’est le plus court chemin pour revenir.',
			'Après un jeu perdu, changez une chose concrète : plus de dinks et de drops, visez l’adversaire le plus faible, et réduisez les fautes au retour.',
			'Après un jeu perdu, trouvez les 1 ou 2 schémas qui vous coûtent des points et changez-les : stacking ou changement de côté, rythme plus lent, jeu au milieu.',
			'Abordez le 2e jeu comme un nouveau match : changez de cibles, utilisez les resets pour casser leur rythme, et prenez un temps mort tôt s’ils enchaînent les points.',
			'Préparez à l’avance un plan B et un plan C (variantes de stacking, changements au service et au retour), utilisez les temps morts tactiquement et faites un reset mental entre les jeux.'
		]
	},
	closeout: {
		title: 'Conclure les matchs',
		finding: (p) => `Après avoir gagné le 1er jeu, vous ne gagnez que ${pct(p.pct)} des matchs (${p.matches} matchs).`,
		advice: [
			'Après avoir gagné le 1er jeu, continuez exactement ce qui a marché : mêmes cibles, même patience.',
			'Ne relâchez pas après le 1er jeu : commencez le 2e avec la même concentration et la même tactique tant que les adversaires ne changent rien.',
			'Au 2e jeu, guettez l’ajustement des adversaires (nouvelles cibles, stacking, plus de vitesse) et adaptez-vous tôt au lieu d’attendre d’être mené.',
			'Attendez-vous à ce que les adversaires changent après le 1er jeu et gardez un temps d’avance : variez services et retours dès le début du 2e jeu.',
			'Maintenez la pression : à ce niveau, les adversaires s’adaptent vite, alors changez de schémas avant qu’ils ne s’installent et ne donnez pas de points faciles.'
		]
	},
	tight_endings: {
		title: 'Fins de jeu serrées',
		finding: (p) =>
			`Vous gagnez ${pct(p.close_pct)} des jeux serrés (2 points d’écart ou moins) contre ${pct(p.game_pct)} de l’ensemble de vos jeux.`,
		advice: [
			'À partir de 8-8, mettez simplement votre service et votre retour profonds dans le terrain, puis dinkez jusqu’à la faute de quelqu’un. Entraînez-vous sur des jeux qui commencent à 7-7.',
			'Entraînez-vous sur des jeux qui commencent à 8-8. Sur balle de jeu, jouez votre schéma le plus sûr : service profond, retour profond, drop, dink, et pas d’accélération risquée.',
			'Dans les fins serrées, n’accélérez pas les balles sous le filet ; faites un reset. Convenez avec votre partenaire d’un schéma de référence pour les points importants.',
			'En fin de jeu, n’attaquez que les balles hautes, prenez un temps mort pour souffler si besoin, et appuyez-vous sur vos schémas les plus fiables.',
			'Travaillez votre routine entre les points (respiration, reset fixe) et quelques schémas fiables pour les points importants. Repérez quel adversaire se crispe sur les gros points.'
		]
	},
	clutch: {
		title: 'Solide dans les fins serrées',
		finding: (p) => `Vous gagnez ${pct(p.close_pct)} des jeux serrés contre ${pct(p.game_pct)} de l’ensemble de vos jeux.`,
		advice: 'Vous gérez bien la pression ; la marge de progrès est plus tôt dans le jeu, avant que ça se resserre.'
	},
	heavy_losses: {
		title: 'Lourdes défaites',
		finding: (p) =>
			`${pct(p.pct)} des jeux que vous perdez le sont par 7 points ou plus (plus que d’habitude pour votre niveau, où ${pct(p.threshold)} est déjà élevé).`,
		advice: [
			'Quand vous commencez à perdre des points d’affilée, ralentissez : retours hauts et profonds, dinks sûrs. Prenez un temps mort pour casser leur série.',
			'Arrêtez les séries tôt : temps mort après 3 ou 4 points d’affilée, puis jouez plus sûr (retours profonds, drops du 3e coup) pour garder le jeu serré.',
			'Quand un jeu vous échappe, cassez leur dynamique : temps mort, changement de formation (stacking) ou de cibles. Rester proche au score protège votre note.',
			'Trouvez ce qui provoque leurs séries (vos accélérations contrées, un côté ciblé) et coupez-le avec des resets et de la patience.',
			'À ce niveau, les lourdes défaites viennent souvent d’un problème de match-up : préparez des réponses à ce style de jeu et prenez vos temps morts plus tôt.'
		]
	},
	favourite_losses: {
		title: 'Défaites en étant favori',
		finding: (p) =>
			`Vous avez perdu ${p.matches} matchs où votre équipe était nettement favorite (60 % ou plus de chances)` +
			(p.cost != null ? `, pour un coût total de ${abs3(p.cost)} point de note` : '') +
			'.',
		advice: [
			'Contre des équipes plus faibles, restez simple : mettez la balle dans le terrain et laissez-les faire les fautes. Ne tentez pas de coups difficiles.',
			'Contre des équipes plus faibles, restez patient : dinks et drops jusqu’à une vraie ouverture, sans vous laisser entraîner dans des échanges brouillons.',
			'En favori, limitez les fautes directes : jouez les pourcentages et n’accélérez que les balles hautes.',
			'Restez concentré sur votre jeu contre les équipes plus faibles : ciblez le joueur le plus faible, limitez les fautes et concluez fermement les jeux.',
			'Perdre en favori coûte cher en note à ce niveau : prenez chaque match classé au sérieux et n’y faites pas d’expériences.'
		]
	},
	vs_stronger_ok: {
		title: 'Compétitif contre plus fort',
		finding: (p) => `Contre des adversaires plus forts, vous gagnez encore ${pct(p.pct)} des points (${p.matches} matchs).`,
		advice: 'Continuez à jouer régulièrement contre plus fort : des scores serrés contre de meilleurs joueurs font monter votre note.'
	},
	vs_stronger_gap: {
		title: 'Écart contre plus fort',
		finding: (p) => `Contre des adversaires plus forts, vous gagnez ${pct(p.pct)} des points (${p.matches} matchs).`,
		advice: [
			'Les joueurs plus forts punissent les balles hautes. Entraînez-vous à garder vos dinks bas et vos retours profonds, et jouez avec de meilleurs joueurs quand vous le pouvez.',
			'Travaillez drops du 3e coup et dinks : les meilleurs joueurs attaquent tout ce qui est haut. Jouez régulièrement contre plus fort pour vous habituer au rythme.',
			'Travaillez les resets dans la zone de transition et le blocage des drives puissants : c’est là que les joueurs plus forts gagnent leurs points.',
			'Travaillez les échanges rapides à la volée, les contre-attaques et la patience dans les longs échanges de dinks ; jouez contre plus fort à l’entraînement et en jeu libre.',
			'Étudiez des matchs de très bons joueurs (en vidéo si possible) : choix de coups, placement et variété. Entraînez-vous avec des partenaires plus forts.'
		]
	},
	energy: {
		title: 'Énergie sur une longue session',
		finding: (p) =>
			`Votre % de points gagnés passe de ${pct(p.early_pct)} sur vos 2 premiers matchs de la journée à ${pct(p.late_pct)} à partir du 4e match.`,
		advice: [
			'Mangez et buvez entre les matchs et faites de courtes pauses. Jouez moins de matchs d’affilée si vous êtes fatigué.',
			'Gérez vos longues sessions : eau, encas et courte pause entre les matchs, ou moins de matchs par jour.',
			'Gérez vos longues sessions : eau, encas et courte pause entre les matchs, ou moins de matchs par jour.',
			'Travaillez votre condition physique et votre récupération entre les matchs (hydratation, alimentation, mobilité), et planifiez votre charge avant les tournois.',
			'Travaillez votre condition physique et votre récupération entre les matchs (hydratation, alimentation, mobilité), et planifiez votre charge avant les tournois.'
		]
	},
	best_partner: {
		title: 'Votre meilleur duo',
		finding: (p) =>
			`Avec ${p.partner}, vous gagnez ${signed(p.avg_impact)} point de note par match en moyenne (${p.matches} matchs, ${pct(p.win_pct)} de victoires).`,
		advice:
			'Regardez ce qui marche dans ce duo (qui couvre le milieu, qui attaque) et appliquez-le avec vos autres partenaires.'
	}
};

function opponentVerdict(v: Verdict): string {
	if (v.status === 'no_data') return 'Pas encore assez de matchs avec la note des adversaires.';
	if (v.status === 'few')
		return `Pas encore assez de matchs pour conclure (${v.n_strong} contre des adversaires plus forts, ${v.n_rest} contre des adversaires de niveau égal ou plus faible ; il en faut 5 de chaque).`;
	let s =
		`Contre des adversaires plus forts, vous ${move(v.mean_strong!, v.measure)} par match en moyenne (${v.n_strong} matchs) ; ` +
		`contre des adversaires de niveau égal ou plus faible, vous ${move(v.mean_rest, v.measure)} (${v.n_rest} matchs).`;
	if (v.clear)
		s += v.diff > 0 ? ' Jouer contre plus fort aide donc votre note.' : ' Jusqu’ici, jouer contre plus fort vous a coûté des points de note.';
	else
		s += ` Jouer contre plus fort semble ${v.diff > 0 ? 'meilleur' : 'moins bon'} pour votre note, mais l’écart est faible par rapport aux variations normales d’un match à l’autre : ce n’est pas encore une conclusion solide.`;
	s += ` Vous gagnez ${pct(v.win_pct_strong)} de vos matchs contre des adversaires plus forts${vsPrediction(v.win_pct_strong!, v.exp_win_pct_strong)}.`;
	if (v.loss_mean != null) {
		const ml = v.loss_mean,
			all = v.all_losses_mean ?? 0;
		if (ml >= 0)
			s += ` Même quand vous perdez contre eux, vous gagnez encore ${abs3(ml)} point de note en moyenne : DUPR s’attend à ce que vous perdiez ces matchs, donc un score serré suffit à faire monter votre note.`;
		else
			s +=
				` Quand vous perdez contre eux, vous perdez ${abs3(ml)} point de note en moyenne` +
				(Math.abs(ml) < Math.abs(all) ? `, moins qu’une défaite moyenne (${abs3(all)})` : '') +
				' : DUPR s’attend à ces défaites, elles coûtent donc peu, et un score serré peut même en faire un petit gain.';
	}
	return s;
}

export const fr: Messages = {
	reportTitle: 'Rapport de performance DUPR',
	generated: (player, when) => `${player} · créé le ${when}`,
	noMatches: 'Aucun match trouvé.',
	formatName: { DOUBLES: 'Double', SINGLES: 'Simple' },
	formatLower: { DOUBLES: 'double', SINGLES: 'simple' },
	notEnough: 'Pas assez de données.',
	print: 'Imprimer / enregistrer en PDF',
	exampleBanner: 'Exemple de rapport avec des données inventées.',

	glossaryTitle: 'Ce que veulent dire les chiffres',
	glossary: [
		['% de points gagnés', 'Part de tous les points que vous avez gagnés. 11-7, 9-11, 11-6 → 31 points sur 55 = 56 %. 50 % = égalité.'],
		[
			'% de points attendu',
			'Le % de points gagnés que prévoit votre écart de notes. Il est calculé à partir de la part d’échanges que vous devriez gagner, puis converti en points selon le comptage de chaque match : en comptage side-out, seul le serveur marque, ce qui double à peu près un avantage aux échanges (gagner 55 % des échanges ≈ 60 % des points) ; en rally scoring, les deux sont égaux.'
		],
		[
			'% d’échanges gagnés',
			'Part des échanges que vous gagnez, estimée à partir de vos scores. En comptage side-out, seul le serveur marque, ce qui amplifie un avantage aux échanges en un avantage aux points plus grand ; ce chiffre corrige cet effet (60 % des points ≈ 55 % des échanges). En rally scoring, il est égal au % de points gagnés.'
		],
		[
			'Probabilité de victoire',
			'Votre chance moyenne de gagner un match, d’après l’écart de notes entre votre équipe et les adversaires dans chaque match (le % de victoires attendu ci-dessous, en moyenne sur vos matchs).'
		],
		[
			'% de victoires attendu',
			'Votre chance de gagner d’après l’écart de notes entre votre équipe et les adversaires (modèle approximatif : la force avec laquelle un avantage de note se traduit en victoires est apprise sur vos propres matchs dès que vous en avez 30 ou plus avec les notes connues ; avant, un avantage de 0,25 de note d’équipe ≈ 76 %). Le modèle de DUPR n’est pas public.'
		],
		['Victoires au-dessus des attentes', 'Victoires réelles moins victoires attendues. Positif = vous faites mieux que les notes.'],
		['Variation de note', 'De combien un match a fait bouger votre note DUPR, d’après les données de DUPR.'],
		['Force des adversaires', 'Note moyenne de vos adversaires moins votre propre note au moment du match.'],
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
		rallySub: 'estimé à partir de vos scores',
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
		nemesisSub: (w, l) => `votre bilan : ${w}–${l}`,
		closeGames: 'Jeux serrés gagnés',
		closeSub: (n) => `sur ${n} jeux décidés à ≤2 pts`,
		vsOdds: 'Au-dessus des pronostics',
		vsOddsSub: (w, e) => `${w} victoires pour ~${e} attendues`,
		workOn: 'À travailler',
		insights: 'Ce que disent les chiffres',
		ratingNow: 'Votre note',
		recentMatches: 'Derniers matchs',
		showAll: (n) => `Voir les ${n} matchs`,
		showFewer: 'Voir moins',
		with: 'avec',
		vs: 'contre',
		allNumbers: 'Tous les chiffres',
		perMonth: '/mois',
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
			rest: 'Repos entre les matchs',
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
		allMatches: 'Tous les matchs (du plus récent au plus ancien)'
	},

	improveIntro: 'Des tendances trouvées dans vos propres matchs, avec pour chacune quelque chose de concret à essayer.',
	bands: ['Débutant', 'En progression', 'Intermédiaire', 'Avancé', 'Expert'],
	bandRanges: ['moins de 3,0', '3,0–3,5', '3,5–4,0', '4,0–4,5', '4,5 et plus'],
	levelNote: (name, range, r) =>
		r == null
			? 'Votre note est inconnue : les conseils sont écrits pour un niveau intermédiaire (3,5–4,0).'
			: `Conseils adaptés à votre niveau : ${name} (${range}), d’après votre note actuelle de ${r}.`,
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
		ratingLine: 'Votre note DUPR',
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
			'La ligne bleue est votre note DUPR ; chaque point est un match (bleu = victoire, orange = défaite). La ligne pointillée montre votre progression moyenne. Utilisez les boutons pour zoomer sur les derniers mois.',
		monthly: 'Variation de note par mois (mois joués)',
		matchesN: (n) => `${n} match${n > 1 ? 's' : ''}`,
		winsOf: (w, n) => `${w} victoires sur ${n} matchs`,
		ratingEnd: (v) => `note en fin de mois ${v}`,
		monthlyCap:
			'De combien votre note a monté (bleu) ou baissé (orange) chaque mois où vous avez joué, avec le nombre de matchs. Les mois sans match sont omis. Vos meilleurs et pires matchs sont dans les tableaux plus bas.',
		winForm: '% de victoires : réel vs prévu',
		yourWin: (w) => `Votre % de victoires (${w} derniers)`,
		expectedWin: '% de victoires attendu',
		winFormCap: (w) =>
			`Bleu = votre part de victoires sur vos ${w} derniers matchs. Orange = la part que prévoient les notes. Bleu au-dessus de l’orange : vous jouez au-dessus de votre note.`,
		points: 'Points gagnés par mois : réel vs attendu',
		you: 'Vous',
		expected: 'Attendu',
		above: 'Au-dessus',
		below: 'En dessous',
		pointsTip: (v, gap) => `${v} des points gagnés (${gap} vs attendu)`,
		ratingThatMonth: (v) => `note ce mois-là ${v}`,
		pointsCap: 'Point = points que vous avez gagnés, tiret = ce que prévoient les notes. Bleu = au-dessus, orange = en dessous.',
		pointsHits: (h) =>
			` Les mois bleus ont fait monter votre note ${h.up} fois sur ${h.above} ; les mois orange l’ont fait baisser ${h.down} fois sur ${h.below}.`,
		oppResults: '% de victoires selon la force des adversaires : réel vs attendu',
		oppAxis: 'Note moyenne des adversaires par rapport à la vôtre',
		oppResultsCap:
			'Chaque groupe correspond à des adversaires plus faibles, de même niveau ou plus forts que vous (leur note moyenne moins la vôtre). Une barre bleue au-dessus de la ligne orange : vous faites mieux que prévu contre ce niveau.',
		oppChange: 'Note gagnée par match, selon la force des adversaires',
		perMatch: 'de note par match',
		pointWinShort: (v) => `points gagnés ${v}`,
		oppChangeCap:
			'Combien de note vous gagnez ou perdez en moyenne en un match contre chaque niveau. Cela montre quels adversaires font vraiment monter votre note DUPR.',
		oppTime: 'Votre note vs le niveau de vos adversaires au fil du temps',
		oppEach: 'Adversaires de chaque match',
		oppLevel: (w) => `Niveau des adversaires (moyenne des ${w} derniers)`,
		yourRating: 'Votre note',
		oppTimeCap:
			'Orange au-dessus du bleu : vous jouez surtout contre des adversaires mieux notés que vous. Jouer régulièrement contre plus fort en restant proche au score est l’un des moyens les plus rapides de faire monter votre note.',
		periods: (p) => `% de victoires et de points gagnés ${par(p)}`,
		winPct: '% de victoires',
		pointWinPct: '% de points gagnés',
		periodsCap: (p) => `Barres : part des matchs gagnés ${par(p)}. Ligne : part des points gagnés.`,
		activity: (p) => `Matchs joués ${par(p)}`,
		matches: 'Matchs',
		activityCap: (p) => `Combien vous avez joué ${par(p)}.`,
		margins: 'Comment se terminent vos jeux (bleu = gagnés, orange = perdus)',
		marginAxis: 'Écart de score dans le jeu (vos points − les leurs)',
		marginTip: (m, n) => `gagnés/perdus de ${m} : ${n} jeux`,
		marginsCap:
			'À droite les jeux gagnés, à gauche les jeux perdus. Les barres près du centre sont les jeux serrés ; celles tout à gauche sont les lourdes défaites, qui coûtent le plus de note.',
		partners: '% de victoires avec chaque partenaire (2 matchs ou plus)',
		partnersCap: 'À quelle fréquence vous gagnez avec chaque partenaire. La ligne pointillée marque 50 %.'
	},

	groups: ['Beaucoup plus faibles', 'Plus faibles', 'Même niveau', 'Plus forts', 'Beaucoup plus forts'],
	groupRanges: ['0,3+ en dessous', '0,1–0,3 en dessous', '±0,1', '0,1–0,3 au-dessus', '0,3+ au-dessus'],
	rest: {
		same_day: 'Même jour que le match précédent',
		'1_3': '1 à 3 jours après le match précédent',
		'4_7': '4 à 7 jours après le match précédent',
		'8_14': '8 à 14 jours après le match précédent',
		'15_plus': '15 jours ou plus après le match précédent'
	},
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
		w: 'V',
		l: 'D'
	}
};
