// Front-page language (English / French). Saved per browser; defaults to the browser's language.
// The report itself is in English.
const LANG_KEY = 'dupr-analysis:lang';

const en = {
	docTitle: 'PickleStats · Performance analysis for DUPR players',
	description:
		'See how your pickleball game evolves: your DUPR rating, form, partners, opponents and what to work on.',
	title: 'PickleStats',
	tagline: 'Performance analysis for DUPR players',
	heroTitle: 'Your pickleball game, by the numbers',
	heroSub:
		'Turn your DUPR matches into a clear picture: how your rating moves, your form, who you play best with, which opponents give you trouble, and what to work on next.',
	ctaStart: 'Get my report',
	ctaDemo: 'See an example',
	free: 'Free · no sign-up · nothing leaves your browser',
	welcomeBack: 'Welcome back',
	previewTag: 'Example report',
	pvRating: 'DUPR rating',
	pvLast: 'Last 10',
	pvStreak: 'Longest win streak',
	pvStreakSub: 'matches in a row',
	pvOdds: 'Beating the odds',
	pvOddsSub: 'wins above expected',
	featuresTitle: 'What your report shows',
	f1t: 'Rating and form',
	f1d: 'Your rating curve, your trend per month, and whether your recent results are above or below what your rating predicts.',
	f2t: 'Partners',
	f2d: 'Who you win with most often, and which partnerships actually raise your rating.',
	f3t: 'Opponents',
	f3d: 'How you do against weaker, similar and stronger teams, and whether playing up is paying off.',
	f4t: 'What to work on',
	f4d: 'Concrete tips from patterns in your own games (slow starts, tight endings, heavy losses), adapted to your level.',
	stepsTitle: 'Get your report in 3 steps',
	lastSync: 'Your last sync',
	openLast: 'Open my report',
	forget: 'Forget my data',
	step1:
		'<b>Once:</b> drag this button to your bookmarks bar <span class="small">(show the bar with ⌘⇧B on Mac, Ctrl+Shift+B on Windows)</span>',
	step2:
		'Open <a href="https://dashboard.dupr.com" target="_blank" rel="noopener">dashboard.dupr.com</a> and log in as usual.',
	step3:
		'Click the <b>⟳ Sync DUPR</b> bookmark. Your matches are downloaded and you come back here to your report.',
	privacy:
		"You log in on DUPR's own site: your password never goes through this page. Your data stays in your browser. It is never uploaded anywhere.",
	dragAlert:
		'Drag this button to your bookmarks bar, then click it while you are on dashboard.dupr.com.',
	devComputer: 'Computer',
	devIphone: 'iPhone / iPad',
	devAndroid: 'Android',
	copyStep: '<b>Once:</b> tap this button to copy the bookmark code.',
	copyBtn: '⧉ Copy the code',
	copied: '✓ Copied',
	copyManual: 'Copying was blocked. Select all the text below and copy it.',
	iosStep2:
		'<b>Once, in Safari:</b> bookmark this page (Share button, then <b>Add Bookmark</b>). Open your bookmarks, tap <b>Edit</b>, tap the new bookmark, rename it <b>Sync DUPR</b> and replace its address with the code you copied.',
	iosStep3:
		'Open <a href="https://dashboard.dupr.com" target="_blank" rel="noopener">dashboard.dupr.com</a> in Safari and log in. Open your bookmarks (book icon) and tap <b>Sync DUPR</b>. Your matches are downloaded and you come back here.',
	androidStep2:
		'<b>Once, in Chrome:</b> bookmark this page (⋮ menu, then ☆). Open ⋮ → <b>Bookmarks</b>, tap ⋮ next to the new bookmark, then <b>Edit</b>. Name it <b>Sync DUPR</b> and paste the code you copied as its URL.',
	androidStep3:
		'Open <a href="https://dashboard.dupr.com" target="_blank" rel="noopener">dashboard.dupr.com</a> and log in. Tap the address bar, type <b>Sync DUPR</b> and tap the bookmark in the suggestions <span class="small">(opening it from the bookmarks list does not work in Chrome)</span>. Your matches are downloaded and you come back here.',
	reportTitle: 'PickleStats',
	print: 'Print / save as PDF',
	printShort: 'PDF',
	back: 'Back',
	building: 'Building your report…',
	starting: 'Starting…',
	loadEngine: 'Loading the analysis engine (first time can take 10–20 seconds)…',
	loadData: 'Loading data tools…',
	analysing: 'Analysing your matches…',
	done: 'Done',
	failed: 'Could not build the report',
	syncedOn: (date: string, time: string) =>
		`Synced on ${date} at ${time}. To update it, use the Sync DUPR bookmark on dupr.com again.`
};

export type Key = keyof typeof en;

const fr: typeof en = {
	docTitle: 'PickleStats · Analyse de performance pour les joueurs DUPR',
	description:
		'Suis l\'évolution de ton jeu de pickleball : ta note DUPR, ta forme, tes partenaires, tes adversaires et les points à travailler.',
	title: 'PickleStats',
	tagline: 'Analyse de performance pour les joueurs DUPR',
	heroTitle: 'Ton jeu de pickleball, en chiffres',
	heroSub:
		'Transforme tes matchs DUPR en une vue claire : l’évolution de ta note, ta forme, avec qui tu gagnes le plus, quels adversaires te posent problème et quoi travailler ensuite.',
	ctaStart: 'Obtenir mon rapport',
	ctaDemo: 'Voir un exemple',
	free: 'Gratuit · sans inscription · rien ne quitte ton navigateur',
	welcomeBack: 'Bon retour',
	previewTag: 'Exemple de rapport',
	pvRating: 'Note DUPR',
	pvLast: '10 derniers',
	pvStreak: 'Plus longue série de victoires',
	pvStreakSub: 'matchs d’affilée',
	pvOdds: 'Au-dessus des pronostics',
	pvOddsSub: 'victoires de plus que prévu',
	featuresTitle: 'Ce que montre ton rapport',
	f1t: 'Note et forme',
	f1d: 'La courbe de ta note, ta tendance par mois, et si tes résultats récents sont au-dessus ou en dessous de ce que prévoit ta note.',
	f2t: 'Partenaires',
	f2d: 'Avec qui tu gagnes le plus souvent, et quels duos font vraiment monter ta note.',
	f3t: 'Adversaires',
	f3d: 'Tes résultats contre des équipes plus faibles, de même niveau ou plus fortes, et si jouer contre plus fort te rapporte.',
	f4t: 'À travailler',
	f4d: 'Des conseils concrets tirés de tes propres jeux (débuts lents, fins serrées, lourdes défaites), adaptés à ton niveau.',
	stepsTitle: 'Ton rapport en 3 étapes',
	lastSync: 'Ta dernière synchronisation',
	openLast: 'Ouvrir mon rapport',
	forget: 'Effacer mes données',
	step1:
		'<b>Une seule fois :</b> fais glisser ce bouton dans ta barre de favoris <span class="small">(affiche la barre avec ⌘⇧B sur Mac, Ctrl+Maj+B sur Windows)</span>',
	step2:
		'Ouvre <a href="https://dashboard.dupr.com" target="_blank" rel="noopener">dashboard.dupr.com</a> et connecte-toi comme d\'habitude.',
	step3:
		'Clique sur le favori <b>⟳ Sync DUPR</b>. Tes matchs sont téléchargés et tu reviens ici pour voir ton rapport.',
	privacy:
		'Tu te connectes sur le site de DUPR, ton mot de passe ne passe jamais par cette page. Tes données restent dans ton navigateur et ne sont jamais envoyées ailleurs.',
	dragAlert:
		'Fais glisser ce bouton dans ta barre de favoris, puis clique dessus quand tu es sur dashboard.dupr.com.',
	devComputer: 'Ordinateur',
	devIphone: 'iPhone / iPad',
	devAndroid: 'Android',
	copyStep: '<b>Une seule fois.</b> Touche ce bouton pour copier le code du favori.',
	copyBtn: '⧉ Copier le code',
	copied: '✓ Copié',
	copyManual: 'La copie a été bloquée. Sélectionne tout le texte ci-dessous et copie-le.',
	iosStep2:
		'<b>Une seule fois, dans Safari.</b> Ajoute cette page aux signets (bouton Partager, puis <b>Ajouter un signet</b>). Ouvre ensuite tes signets, touche <b>Modifier</b>, touche le nouveau signet, renomme-le <b>Sync DUPR</b> et remplace son adresse par le code copié.',
	iosStep3:
		'Ouvre <a href="https://dashboard.dupr.com" target="_blank" rel="noopener">dashboard.dupr.com</a> dans Safari et connecte-toi. Ouvre ensuite tes signets (icône livre) et touche <b>Sync DUPR</b>. Tes matchs sont téléchargés et tu reviens ici.',
	androidStep2:
		'<b>Une seule fois, dans Chrome.</b> Ajoute cette page aux favoris (menu ⋮, puis ☆). Ouvre ⋮ → <b>Favoris</b>, touche ⋮ à côté du nouveau favori, puis <b>Modifier</b>. Nomme-le <b>Sync DUPR</b> et colle le code copié comme URL.',
	androidStep3:
		'Ouvre <a href="https://dashboard.dupr.com" target="_blank" rel="noopener">dashboard.dupr.com</a> et connecte-toi. Touche la barre d\'adresse, tape <b>Sync DUPR</b> et touche le favori dans les suggestions <span class="small">(l\'ouvrir depuis la liste des favoris ne marche pas dans Chrome)</span>. Tes matchs sont téléchargés et tu reviens ici.',
	reportTitle: 'PickleStats',
	print: 'Imprimer / PDF',
	printShort: 'PDF',
	back: 'Retour',
	building: 'Création de ton rapport…',
	starting: 'Démarrage…',
	loadEngine: "Chargement du moteur d'analyse (10 à 20 secondes la première fois)…",
	loadData: 'Chargement des outils de données…',
	analysing: 'Analyse de tes matchs…',
	done: 'Terminé',
	failed: 'Impossible de créer le rapport',
	syncedOn: (date: string, time: string) =>
		`Synchronisé le ${date} à ${time}. Pour le mettre à jour, utilise à nouveau le favori Sync DUPR sur dupr.com.`
};

const I18N = { en, fr };
export type Lang = keyof typeof I18N;
export const LANGS: Lang[] = ['en', 'fr'];

export const i18n = $state({ lang: 'en' as Lang });

/** Pick the saved language, else the browser's. Call once in the browser (the page is prerendered in English). */
export function initLang() {
	let saved: string | null = null;
	try {
		saved = localStorage.getItem(LANG_KEY);
	} catch {
		/* storage blocked */
	}
	if (saved === 'en' || saved === 'fr') i18n.lang = saved;
	else i18n.lang = (navigator.language || 'en').toLowerCase().startsWith('fr') ? 'fr' : 'en';
}

export function setLang(lang: Lang) {
	i18n.lang = lang;
	try {
		localStorage.setItem(LANG_KEY, lang);
	} catch {
		/* storage blocked */
	}
}

/** Translate a key. Reactive: re-runs when the language changes. */
export function t(key: Key, ...args: string[]): string {
	const v = I18N[i18n.lang][key] as string | ((...a: string[]) => string);
	return typeof v === 'function' ? v(...args) : v;
}

/** Locale for dates and times. */
export const locale = () => (i18n.lang === 'fr' ? 'fr-FR' : undefined);
