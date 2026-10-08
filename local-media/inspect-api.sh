#!/usr/bin/env bash
set -euo pipefail
data=/opt/media-app/local-media/data
latest=$(find "$data" -mindepth 2 -maxdepth 2 -name run.log -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
test -n "$latest"
echo "Latest job: $(basename "$(dirname "$latest")")"
tail -n 120 "$latest"
