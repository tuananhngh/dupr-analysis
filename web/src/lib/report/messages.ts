// The report text in the page language. `m()` is reactive: components re-render on a language switch.
import { i18n } from '#lib/i18n.svelte.ts';
import { en, type Messages } from './messages.en.ts';
import { fr } from './messages.fr.ts';

const ALL: Record<string, Messages> = { en, fr };

export const m = (): Messages => ALL[i18n.lang] ?? en;
