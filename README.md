# DUPR performance analysis

See how your pickleball game evolves: your DUPR rating over time, your form, your results against what the
ratings predict, your partners, your opponents, and concrete things to work on.

**👉 Open the app: https://tuananhngh.github.io/dupr-analysis/**

Nothing to install. It works in your browser on a computer (Chrome, Edge, Firefox or Safari).

## How to use it

1. **Once:** on the app page, drag the **⟳ Sync DUPR** button to your browser's bookmarks bar.
   If you don't see the bar, press ⌘⇧B on Mac or Ctrl+Shift+B on Windows.
2. Go to [dashboard.dupr.com](https://dashboard.dupr.com) and log in as usual.
3. Click the **⟳ Sync DUPR** bookmark. A small panel shows your matches downloading, then you're taken back
   to the app and your report appears after a few seconds.

To update your report later, repeat steps 2 and 3. The app also remembers your last sync, so you can
reopen your report from the app page. Use **Download report** to keep a copy or share it.

## Is my data safe?

- You log in on DUPR's own website. Your password never goes through this app.
- Your matches go straight from DUPR to your browser, and the analysis runs inside your browser.
  Nothing is uploaded to any server.
- The app keeps your last sync in your browser only. Click **Forget my data** on the app page to erase it.

## What's in the report

- **Key findings:** the main facts about your game, in plain sentences.
- **How to improve:** patterns found in your matches (slow starts, close games, heavy losses, losses as the
  favourite…), each with something concrete to try.
- **Rating:** your rating curve with start, peak, current value and trend, plus your rating change per month.
- **Form:** how often you win compared with what your rating predicts, and your point win % (the share of rally
  points you win).
- **Performance by opponent rating:** your results and rating gains against weaker, similar and stronger players.
- **Partners, games and detailed tables,** down to every match.

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
pandas, numpy and plotly compiled to WebAssembly), using the same `dupr/*.py` files as the local version
(`app.py`, `analyze.py`). Those files and the bookmarklet are bundled into the site at build time.

| Path | What it does |
|---|---|
| `web/` | The website (SvelteKit): installs the bookmark, receives the data, runs the analysis with Pyodide, shows the report |
| `web/src/lib/analysis.ts` | Loads Pyodide and runs `dupr/pipeline.py` on the synced data |
| `.github/workflows/deploy.yml` | Builds `web/` and deploys it to GitHub Pages on every push to `main` |
| `dupr/bookmarklet.js` | The ⟳ Sync DUPR bookmark (runs on dashboard.dupr.com) |
| `dupr/parse.py` | Turns DUPR's raw match data into a table |
| `dupr/analysis.py` | All the statistics and the written findings |
| `dupr/report.py` | Charts and the HTML report |
| `dupr/pipeline.py` | Decodes the synced data and builds the report |
| `dupr/demo.py` | Sample data for `analyze.py --demo` |
| `app.py` | Optional local version of the website (Flask) |
| `analyze.py` | Rebuild a report from the command line |

### Run it locally

Requires [uv](https://docs.astral.sh/uv/). It installs Python 3.12+ for you if needed.

```bash
uv sync
uv run app.py                 # local version of the website on http://127.0.0.1:8000
uv run analyze.py --demo      # report from sample data, no DUPR account needed
uv run analyze.py             # rebuild the report from the last local sync (data/raw/)
```

The local app gives its own **⟳ Sync DUPR (local)** bookmark, which sends the data to `127.0.0.1:8000` instead of the website, so it only works while `app.py` is running.

To work on the website (requires Node 22.17+):

```bash
cd web
npm install
npm run dev                   # http://localhost:5173, reloads on change (also picks up edits to dupr/*.py)
npm run build                 # static site in web/build
```

The site is deployed by GitHub Actions: in the repo's **Settings → Pages**, set **Source** to **GitHub Actions**.

Personal data (`data/`, `output/`) is gitignored.
