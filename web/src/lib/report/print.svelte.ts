// Tabs show one panel at a time; printing shows them all.
import { flushSync } from 'svelte';

export const printing = $state({ all: false });

function expand() {
	flushSync(() => (printing.all = true));
}

if (typeof window !== 'undefined') {
	window.addEventListener('beforeprint', expand);
	window.addEventListener('afterprint', () => (printing.all = false));
}

/** Render every tab, let the charts measure their new width, then open the print dialog. */
export function printReport() {
	expand();
	requestAnimationFrame(() => requestAnimationFrame(() => window.print()));
}
