# PickleStats

Performance analysis for DUPR players.

See how your pickleball game evolves: your DUPR rating over time, your form, your results against what the
ratings predict, your partners, your opponents, and concrete things to work on.

**👉 Open the app: https://tuananhngh.github.io/picklestats/**

Nothing to install. It works in your browser on a computer (Chrome, Edge, Firefox or Safari).

## How to use it

1. **Once:** on the app page, drag the **⟳ Sync DUPR** button to your browser's bookmarks bar.
   If you don't see the bar, press ⌘⇧B on Mac or Ctrl+Shift+B on Windows.
2. Go to [dashboard.dupr.com](https://dashboard.dupr.com) and log in as usual.
3. Click the **⟳ Sync DUPR** bookmark. A small panel shows your matches downloading, then you're taken back
   to the app and your report appears after a few seconds.

To update your report later, repeat steps 2 and 3. The app also remembers your last sync, so you can
reopen your report from the app page. Use **Print / save as PDF** to keep a copy or share it.

The app and the report are in English or French (EN / FR switch at the top). No DUPR account at hand?
**See an example report** on the app page shows a report for a made-up player.

## Is my data safe?

- You log in on DUPR's own website. Your password never goes through this app.
- Your matches go straight from DUPR to your browser, and the analysis runs inside your browser.
  Nothing is uploaded to any server.
- The app keeps your last sync in your browser only. Click **Forget my data** on the app page to erase it.

## What's in the report

- **Key findings:** the main facts about your game, in plain sentences.
- **How to improve:** patterns found in your matches (slow starts, close games, heavy losses, losses as the
  favourite…), each with something concrete to try.
- **Rating:** your rating curve with start, peak, current value and trend (zoom on the last 3, 6 or 12 months),
  plus your rating change per month.
- **Form:** how often you win compared with what your rating predicts, and your point win % (the share of rally
  points you win).
- **Performance by opponent rating:** your results and rating gains against weaker, similar and stronger players.
- **Partners, games and detailed tables,** down to every match.

Hover a chart (or tap it on a phone) to see the details of a match, a month or a group.

---

## For developers

### How it works

DUPR's API only answers requests coming from a logged-in `dashboard.dupr.com` page, using its own session cookie.
Logins from other sites or scripts are blocked. So the **bookmarklet** ([dupr/bookmarklet.js](dupr/bookmarklet.js))
runs on DUPR's page with the user's existing session. It downloads:

- the profile,
- the full match history (`POST /player/v1.0/{id}/history`),
- the rating history, when available.

It then opens the app with the data gzipped in the URL `#fragment`, which browsers never send to a server.

The website ([web/](web/)) is a [SvelteKit](https://svelte.dev/docs/kit) app built as a static site
(`adapter-static`). It runs the Python analysis in the browser with [Pyodide](https://pyodide.org) (Python,
pandas and numpy compiled to WebAssembly). The `dupr/*.py` files and the bookmarklet are bundled into the
site at build time.

Python only computes: [dupr/export.py](dupr/export.py) returns the results as JSON (numbers, dates, names and
codes such as `{"id": "close_games", "verdict": "clutch", ...}`, never sentences). The site writes all the
text, in English or French, and draws the charts with [LayerChart](https://layerchart.com). The JSON shape is
`ReportData` in [web/src/lib/report/types.ts](web/src/lib/report/types.ts): keep it in sync with export.py.

**Adding or changing a finding or a tip** touches three files:

1. [dupr/analysis.py](dupr/analysis.py): the rule, which returns an `id` and its numbers
   (`_insights` for key findings, `improvement_tips` for tips).
2. [messages.en.ts](web/src/lib/report/messages.en.ts): the English sentence for that `id` (`findings` or
   `tips`; a tip's advice can have one version per rating band).
3. [messages.fr.ts](web/src/lib/report/messages.fr.ts): the French sentence. TypeScript reports an error if
   a key is missing from the French file.

A finding whose `id` has no sentence is skipped, so a new rule never shows raw codes.

| Path | What it does |
|---|---|
| `web/` | The website (SvelteKit): installs the bookmark, receives the data, runs the analysis with Pyodide, shows the report |
| `web/src/lib/analysis.ts` | Loads Pyodide and runs `dupr/pipeline.py` on the synced data |
| `web/src/lib/report/` | The report: text in English (`messages.en.ts`) and French (`messages.fr.ts`), charts, tables |
| `web/src/lib/i18n.svelte.ts` | Language switch and the front-page text |
| `.github/workflows/deploy.yml` | Builds `web/` and deploys it to GitHub Pages on every push to `main` |
| `dupr/bookmarklet.js` | The ⟳ Sync DUPR bookmark (runs on dashboard.dupr.com) |
| `dupr/parse.py` | Turns DUPR's raw match data into a table |
| `dupr/analysis.py` | All the statistics, the findings and the tips (as codes and numbers) |
| `dupr/export.py` | Turns the analysis into the JSON the website displays, including the chart data |
| `dupr/pipeline.py` | Decodes the synced data and runs the analysis |
| `dupr/demo.py` | Sample data (the website's example report, `analyze.py --demo`) |
| `app.py` | Serves the built website locally, and saves each sync to `data/raw/` |
| `analyze.py` | Runs the analysis from the command line and writes `output/report.json` and CSV tables |
| `justfile` | The project commands (`just` lists them) |

### Run it locally

Requires [uv](https://docs.astral.sh/uv/), which installs Python 3.12+ for you if needed,
[Node](https://nodejs.org) 22.17 or later, and [just](https://just.systems) (`brew install just`).
Run `just` to list the commands:

```bash
just setup      # once: install the Python and website dependencies
just app        # build the site and run it on http://127.0.0.1:8000
just dev        # work on the website: http://localhost:5173, reloads on change
just check      # type-check the website (also catches text missing from the French file)
just build      # static site in web/build
just demo       # analysis of the sample data into output/ (no DUPR account needed)
just analyze    # analysis of the last local sync (data/raw/) into output/
```

With `just app`, the bookmark you drag from the local page sends the data to `127.0.0.1:8000` instead of
the website, so it only works while the app is running. Each sync received there is also saved to
`data/raw/`. `just dev` picks up edits to `dupr/*.py` too, but doesn't save syncs.

Add `#demo` to the address (for example http://localhost:5173/#demo) to open the example report directly.
If Homebrew's `node@26` is installed, the justfile uses it even when your default `node` is older.

The site is deployed by GitHub Actions: in the repo's **Settings → Pages**, set **Source** to **GitHub Actions**.

Personal data (`data/`, `output/`) is gitignored.
