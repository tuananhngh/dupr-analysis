// Runs the Python analysis (dupr/*.py, the same files as the local version) in the browser with Pyodide.
// Python only computes: it returns the report data as JSON, and the page writes the text and draws the charts.
import type { Key } from './i18n.svelte.ts';
import type { ReportData } from './report/types.ts';

const PYODIDE_URL = 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.js';
const PY_FILES = ['__init__.py', 'parse.py', 'analysis.py', 'export.py', 'demo.py', 'pipeline.py'];

const sources = import.meta.glob('../../../dupr/*.py', {
	query: '?raw',
	import: 'default',
	eager: true
}) as Record<string, string>;

/** Reports progress with a translation key (see i18n.svelte.ts). */
type Progress = (pct: number, step: Key) => void;
type Pyodide = {
	loadPackage(pkgs: string[]): Promise<void>;
	runPythonAsync(code: string): Promise<unknown>;
	globals: { set(name: string, value: unknown): void };
	FS: { mkdirTree(path: string): void; writeFile(path: string, data: string): void };
};

declare global {
	interface Window {
		loadPyodide?: () => Promise<Pyodide>;
	}
}

function loadScript(src: string): Promise<void> {
	return new Promise((resolve, reject) => {
		const s = document.createElement('script');
		s.src = src;
		s.onload = () => resolve();
		s.onerror = () => reject(new Error('Could not load the analysis engine. Check your connection.'));
		document.head.appendChild(s);
	});
}

let ready: Promise<Pyodide> | null = null;

function loadPython(progress: Progress): Promise<Pyodide> {
	ready ??= (async () => {
		progress(10, 'loadEngine');
		if (!window.loadPyodide) await loadScript(PYODIDE_URL);
		const py = await window.loadPyodide!();
		progress(35, 'loadData');
		await py.loadPackage(['numpy', 'pandas']);
		py.FS.mkdirTree('/home/pyodide/dupr');
		for (const f of PY_FILES) {
			const code = sources[`../../../dupr/${f}`];
			if (code === undefined) throw new Error(`Missing analysis file dupr/${f}`);
			py.FS.writeFile('/home/pyodide/dupr/' + f, code);
		}
		return py;
	})().catch((e) => {
		ready = null; // allow a retry
		throw e;
	});
	return ready;
}

/** Turn a sync payload (what the bookmark puts in #d=…) into the report data. */
export async function buildReport(payload: string, progress: Progress): Promise<ReportData> {
	const py = await loadPython(progress);
	progress(80, 'analysing');
	py.globals.set('payload', payload);
	const json = await py.runPythonAsync('from dupr.pipeline import report_json\nreport_json(payload)');
	progress(100, 'done');
	return JSON.parse(json as string);
}

/** Report data for the built-in sample player. */
export async function buildDemo(progress: Progress): Promise<ReportData> {
	const py = await loadPython(progress);
	progress(80, 'analysing');
	const json = await py.runPythonAsync('from dupr.pipeline import demo_json\ndemo_json()');
	progress(100, 'done');
	return JSON.parse(json as string);
}
