// Shared bits for the report charts. Colors are CSS variables set on :root (+layout.svelte),
// because LayerChart moves tooltips to <body>, outside any wrapper element.
export const BLUE = 'var(--blue)';
export const ORANGE = 'var(--orange)';
export const MUTED = 'var(--muted)';
export const FAINT = 'var(--faint)';
export const SURFACE = 'var(--surface)';

/** Win / above expectation = blue, loss / below = orange (the report's two-color convention). */
export const signColor = (positive: boolean) => (positive ? BLUE : ORANGE);

export const toDate = (iso: string) => new Date(iso.length === 10 ? iso + 'T00:00:00' : iso);

/** Bars never fill their slot: at most 24px wide. */
export const barWidth = (band: number | undefined) => Math.min(24, band ?? 24);

export const PAD = { top: 16, right: 16, bottom: 28, left: 48 };

/** First date shown for a time-range button (3 / 6 / 12 months before the last date), or null for all. */
export function rangeStart(last: Date, range: '3m' | '6m' | '1y' | 'all'): Date | null {
	if (range === 'all') return null;
	const months = { '3m': 3, '6m': 6, '1y': 12 }[range];
	const d = new Date(last);
	d.setMonth(d.getMonth() - months);
	return d;
}

/** Every k-th category label so they don't overlap: about one label per `px` pixels of width. */
export function thinTicks<T>(values: T[], width: number, px = 64): T[] {
	const k = Math.max(1, Math.ceil(values.length / Math.max(1, Math.floor(width / px))));
	return values.filter((_, i) => i % k === 0);
}
