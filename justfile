# Project commands. Run `just` to list them.

# The website needs Node 22.17+. If Homebrew's node@26 is installed, use it even when the default
# `node` is older (it is ignored on machines without it).
node26 := "/opt/homebrew/opt/node@26/bin"
export PATH := if path_exists(node26) == "true" { node26 + ":" + env_var("PATH") } else { env_var("PATH") }

# List the commands
default:
    @just --list

# Install the Python and website dependencies
setup:
    uv sync
    cd web && npm install

# Build the website into web/build
build: _node
    cd web && npm run build

# Build the site and run the local app on http://127.0.0.1:8000 (saves each sync to data/raw/)
app: build
    uv run app.py

# Work on the website: http://localhost:5173, reloads on change (add #demo for the example report)
dev: _node
    cd web && npm run dev

# Type-check the website (also catches text missing from the French file)
check: _node
    cd web && npm run check

# Run the analysis on the last local sync (data/raw/) into output/
analyze:
    uv run analyze.py

# Run the analysis on the sample data into output/
demo:
    uv run analyze.py --demo

# Print the raw structure of one synced match (to fix parsing)
inspect:
    uv run analyze.py --inspect

# Fail early with a clear message if Node is too old for the website
_node:
    @node -e 'const [a,b]=process.versions.node.split(".").map(Number); if (a<22||(a===22&&b<17)) { console.error("Node " + process.versions.node + " is too old for the website: install Node 22.17 or later."); process.exit(1) }'
