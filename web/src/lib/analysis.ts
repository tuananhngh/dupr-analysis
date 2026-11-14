// Runs the Python analysis (dupr/*.py, the same files as the local version) in the browser with Pyodide.
const PYODIDE_URL = 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.js';
const PY_FILES = ['__init__.py', 'parse.py', 'analysis.py', 'report.py', 'pipeline.py'];

const sources = import.meta.glob('../../../dupr/*.py', {
	query: '?raw',
	import: 'default',
	eager: true
}) as Record<string, string>;

type Progress = (pct: number, text: string) => void;
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
		progress(10, 'Loading the analysis engine (first time can take 10–20 seconds)…');
		if (!window.loadPyodide) await loadScript(PYODIDE_URL);
		const py = await window.loadPyodide!();
		progress(35, 'Loading data tools…');
		await py.loadPackage(['numpy', 'pandas', 'micropip']);
		progress(60, 'Loading charts…');
		await py.runPythonAsync('import micropip\nawait micropip.install("plotly==7.1.0")');
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

/** Turn a sync payload (what the bookmark puts in #d=…) into the HTML report. */
export async function buildReport(payload: string, progress: Progress): Promise<string> {
	const py = await loadPython(progress);
	progress(80, 'Analysing your matches…');
	py.globals.set('payload', payload);
	const html = await py.runPythonAsync(`
from pathlib import Path
import shutil
from dupr.pipeline import decode_sync_payload, save_sync, load_raw, build_report
shutil.rmtree("/tmp/dupr", ignore_errors=True)
data = decode_sync_payload(payload)
save_sync(data, Path("/tmp/dupr/raw"), lambda m: None)
build_report(*load_raw(Path("/tmp/dupr/raw")), Path("/tmp/dupr/out"), lambda m: None).read_text()
`);
	progress(100, 'Done');
	return html as string;
}
