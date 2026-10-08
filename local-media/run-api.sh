#!/usr/bin/env bash
set -euo pipefail

app="/opt/media-app/local-media"
# Windows reaches this listener through a loopback-only port proxy. Binding all
# WSL interfaces also keeps Ubuntu's own 127.0.0.1 health check valid.
exec "$app/.venv/bin/python" -m uvicorn server:app --host 0.0.0.0 --port 8002
