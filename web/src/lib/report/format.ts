// Number and date formatting in the page language (French: "3,383", "47 %", "mai 2026").
import { i18n } from '#lib/i18n.svelte.ts';
import type { Num, Period } from './types.ts';

const tag = () => (i18n.lang === 'fr' ? 'fr-FR' : 'en-GB');
const DASH = '–';

const cache = new Map<string, Intl.NumberFormat>();
function nf(opts: Intl.NumberFormatOptions): Intl.NumberFormat {
	const key = tag() + JSON.stringify(opts);
	let f = cache.get(key);
	if (!f) cache.set(key, (f = new Intl.NumberFormat(tag(), opts)));
	return f;
}

const ok = (v: Num | undefined): v is number => typeof v === 'number' && Number.isFinite(v);

/** Fixed decimals: num(3.38324, 3) -> "3.383". */
export const num = (v: Num | undefined, digits = 0) =>
	ok(v) ? nf({ minimumFractionDigits: digits, maximumFractionDigits: digits }).format(v) : DASH;

/** Signed: signed(0.0123, 3) -> "+0.012" ("−0.012" for negatives). */
export const signed = (v: Num | undefined, digits = 3) =>
	ok(v)
		? nf({ minimumFractionDigits: digits, maximumFractionDigits: digits, signDisplay: 'exceptZero' })
				.format(v)
				.replace('-', '−')
		: DASH;

/** A value already in percent: pct(47.2) -> "47%" ("47 %" in French). */
export const pct = (v: Num | undefined, digits = 0) =>
	ok(v) ? nf({ style: 'percent', minimumFractionDigits: digits, maximumFractionDigits: digits }).format(v / 100) : DASH;

/** Signed percentage points: pp(4.2) -> "+4". */
export const pp = (v: Num | undefined) => signed(v, 0);

export const rating = (v: Num | undefined) => num(v, 3);

const d = (x: string | Date) => (x instanceof Date ? x : new Date(x.length === 10 ? x + 'T00:00:00' : x));

export const date = (iso: string | Date | null | undefined) =>
	iso ? d(iso).toLocaleDateString(tag(), { day: 'numeric', month: 'short', year: 'numeric' }) : DASH;

export const monthYear = (iso: string | Date) => d(iso).toLocaleDateString(tag(), { month: 'short', year: 'numeric' });

/** "May '26": a short month label for crowded chart axes. */
export const monthShort = (iso: string | Date) => {
	const x = d(iso);
	return `${x.toLocaleDateString(tag(), { month: 'short' })} ’${String(x.getFullYear()).slice(2)}`;
};

/** Label of a week / month / quarter from its last day (as grouped in dupr/analysis.py). */
export function periodLabel(iso: string, period: Period): string {
	const x = d(iso);
	if (period === 'quarter') {
		const q = Math.floor(x.getMonth() / 3) + 1;
		return i18n.lang === 'fr' ? `T${q} ${x.getFullYear()}` : `Q${q} ${x.getFullYear()}`;
	}
	if (period === 'month') return monthYear(iso);
	return (i18n.lang === 'fr' ? 'sem. du ' : 'wk ') + date(iso);
}

/** "Sep 2025" or "Sep 2025–Nov 2026". */
export function span(from: string, to: string): string {
	const a = monthYear(from),
		b = monthYear(to);
	return a === b ? a : `${a}–${b}`;
}

/** Axis tick for a date: "May 26" / "mai 26". */
export const dateTick = (x: Date) => x.toLocaleDateString(tag(), { month: 'short', year: '2-digit' });

/** Tick formatter for a time axis: month + year, or day + month when the axis covers under ~4 months. */
export function timeTicks(from: Date, to: Date): (x: Date) => string {
	if (to.getTime() - from.getTime() > 120 * 86_400_000) return dateTick;
	return (x) => x.toLocaleDateString(tag(), { day: 'numeric', month: 'short' });
}

export { ok as isNum };
