#!/usr/bin/env bash
# Re-download Ramp's machine-readable docs and regenerate the endpoint cheatsheet.
# Ramp publishes these directly; no scraping and no CLI needed.
set -euo pipefail
cd "$(dirname "$0")"

for f in openapi/developer-api.json llms.txt llms-api.txt llms-guides.txt; do
  curl -sSfL -o "$(basename "$f")" "https://docs.ramp.com/$f"
  echo "fetched $(basename "$f") ($(wc -c < "$(basename "$f")") bytes)"
done

python gen-cheatsheet.py
