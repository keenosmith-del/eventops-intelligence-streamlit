#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
compose=(docker compose --env-file .env)
workflow_dir=/workflows
if [[ "${1:-full}" == "development" ]]; then
  compose+=( -f n8n/compose.yaml )
  .venv/bin/python scripts/build_workflows.py --processor-url http://host.docker.internal:8766 --output n8n/.local/development
  workflow_dir=/workflows/.local/development
fi
.venv/bin/python scripts/prepare_n8n_credentials.py
"${compose[@]}" exec -T n8n n8n import:credentials --input=/workflows/.local/credentials.json
"${compose[@]}" exec -T n8n n8n import:workflow --input="$workflow_dir/verification.json"
"${compose[@]}" exec -T n8n n8n import:workflow --input="$workflow_dir/gemini-agent.json"
"${compose[@]}" exec -T n8n n8n publish:workflow --id=EventOpsVerify01
"${compose[@]}" exec -T n8n n8n publish:workflow --id=EventOpsAgent01
"${compose[@]}" restart n8n
.venv/bin/python -c 'from pathlib import Path; Path("n8n/.local/credentials.json").unlink(missing_ok=True)'
