#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -f .env ]]; then
  .venv/bin/python scripts/configure_local.py
fi
.venv/bin/python -m uvicorn eventops.service:app --host 0.0.0.0 --port 8766 &
processor_pid=$!
trap 'kill "$processor_pid" 2>/dev/null || true' EXIT INT TERM
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
