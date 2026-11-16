// Front-page language (English / French). Saved per browser; defaults to the browser's language.
// The report itself is in English.
const LANG_KEY = 'dupr-analysis:lang';

const en = {
	docTitle: 'DUPR Analysis',
	description:
		'See how your pickleball game evolves: your DUPR rating, form, partners, opponents and what to work on.',
	title: 'DUPR performance analysis',
	intro:
		'See how your pickleball game evolves: your rating over time, form, results against what the ratings predict, partners, opponents and what to work on.',
	lastSync: 'Your last sync',
	openLast: 'Open my report',
	forget: 'Forget my data',
	getReport: 'Get your report',
	step1:
		'<b>Once:</b> drag this button to your bookmarks bar <span class="small">(show the bar with ⌘⇧B on Mac, Ctrl+Shift+B on Windows)</span>',
	step2:
		'Open <a href="https://dashboard.dupr.com" target="_blank" rel="noopener">dashboard.dupr.com</a> and log in as usual.',
	step3:
		'Click the <b>⟳ Sync DUPR</b> bookmark. Your matches are downloaded and you come back here to your report.',
	privacy:
		"You log in on DUPR's own site: your password never goes through this page. Your data stays in your browser. It is never uploaded anywhere. Works on a computer (Chrome, Edge, Firefox, Safari).",
	dragAlert:
		'Drag this button to your bookmarks bar, then click it while you are on dashboard.dupr.com.',
	reportTitle: 'DUPR performance report',
	print: 'Print / save as PDF',
	back: 'Back',
	building: 'Building your report…',
	starting: 'Starting…',
	loadEngine: 'Loading the analysis engine (first time can take 10–20 seconds)…',
	loadData: 'Loading data tools…',
	demo: 'No DUPR account at hand? See an example report',
	analysing: 'Analysing your matches…',
	done: 'Done',
	failed: 'Could not build the report',
	syncedOn: (date: string, time: string) =>
		`Synced on ${date} at ${time}. To update it, click the bookmark on dupr.com again.`
};

export type Key = keyof typeof en;

const fr: typeof en = {
	docTitle: 'Analyse DUPR',
	description:
		'Suivez l\'évolution de votre jeu de pickleball : votre note DUPR, votre forme, vos partenaires, vos adversaires et les points à travailler.',
	title: 'Analyse de performance DUPR',
	intro:
		"Suivez l'évolution de votre jeu de pickleball : votre note DUPR dans le temps, votre forme, vos résultats par rapport à ce que prévoient les notes, vos partenaires, vos adversaires et les points à travailler.",
	lastSync: 'Votre dernière synchronisation',
	openLast: 'Ouvrir mon rapport',
	forget: 'Effacer mes données',
	getReport: 'Obtenir votre rapport',
	step1:
		'<b>Une seule fois :</b> faites glisser ce bouton dans votre barre de favoris <span class="small">(affichez la barre avec ⌘⇧B sur Mac, Ctrl+Maj+B sur Windows)</span>',
	step2:
		'Ouvrez <a href="https://dashboard.dupr.com" target="_blank" rel="noopener">dashboard.dupr.com</a> et connectez-vous comme d\'habitude.',
	step3:
		'Cliquez sur le favori <b>⟳ Sync DUPR</b>. Vos matchs sont téléchargés et vous revenez ici pour voir votre rapport.',
	privacy:
		'Vous vous connectez sur le site de DUPR : votre mot de passe ne passe jamais par cette page. Vos données restent dans votre navigateur et ne sont jamais envoyées ailleurs. Fonctionne sur ordinateur (Chrome, Edge, Firefox, Safari).',
	dragAlert:
		'Faites glisser ce bouton dans votre barre de favoris, puis cliquez dessus quand vous êtes sur dashboard.dupr.com.',
	reportTitle: 'Rapport de performance DUPR',
	print: 'Imprimer / PDF',
	back: 'Retour',
	building: 'Création de votre rapport…',
	starting: 'Démarrage…',
	loadEngine: "Chargement du moteur d'analyse (10 à 20 secondes la première fois)…",
	loadData: 'Chargement des outils de données…',
	demo: 'Pas de compte DUPR sous la main ? Voir un exemple de rapport',
	analysing: 'Analyse de vos matchs…',
	done: 'Terminé',
	failed: 'Impossible de créer le rapport',
	syncedOn: (date: string, time: string) =>
		`Synchronisé le ${date} à ${time}. Pour le mettre à jour, cliquez à nouveau sur le favori sur dupr.com.`
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
