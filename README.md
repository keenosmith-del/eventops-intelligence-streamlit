# EventOps Intelligence — Streamlit Edition

An independent assessment companion for event knowledge retrieval and auditable operations. It uses Streamlit, FastEmbed, Gemini and genuine n8n workflows. The original React/FastAPI/LangGraph application and its databases are not dependencies.

**Current delivery: running and validated locally; not publicly deployed.** Real Gemini RAG and an n8n Gemini AI Agent execution are recorded in `docs/evidence/`. No repository has been pushed and no existing infrastructure has been changed. See [assessment compliance](docs/ASSESSMENT_COMPLIANCE.md), [observed test results](docs/TEST_REPORT.md), and [deployment](docs/DEPLOYMENT.md).

## What works

- Three validated structured documents: 3 events, 9 policies, 7 synthetic directory records.
- Real FastEmbed BGE-small embeddings (19 × 384), persisted NumPy index, cosine search, event/category filters, query normalization and contextual follow-ups.
- Grounded structured Gemini answers, record citations, explicit unavailable/refusal states, persisted retrieval inspection.
- A protected production n8n webhook performing source reads, conditional replay, source outcome handling, extraction, normalization, duplicate merging, deterministic verification and persistence.
- Genuine remote Calendar and Web reads plus read-only Mailtrap sandbox messages. Public holidays are never presented as registrations.
- A separate n8n AI Agent with a Gemini Chat Model and three read-only tools. Actual selected tool calls and structured explanations are persisted separately from verification rules.
- Seven native Streamlit screens, field checks, raw evidence, conflicts and duplicate groups, review notes, scoped history and two CSV exports.
- Atomic request reservation, daily generation/agent budgets, source bounds, protected processing endpoints, formula-safe CSV, isolated SQLite or dedicated PostgreSQL configuration.

## Quick start — Python 3.12

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python scripts/configure_local.py
# Edit the ignored .env: Gemini and dedicated Mailtrap sandbox credentials.
.venv/bin/python scripts/index_knowledge.py
```

Configure n8n once using [n8n/README.md](n8n/README.md). Then:

```bash
docker compose --env-file .env -f n8n/compose.yaml up -d
./scripts/start_local.sh
```

Open [Streamlit](http://127.0.0.1:8501) and [n8n](http://localhost:5679). Local processing service: port 8766. The service is header-authenticated; its listening address allows the Docker bridge to reach the host. Use a local firewall or the private full-compose network outside this development machine.

Tests:

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
.venv/bin/ruff check app.py eventops scripts tests
```

A live deterministic acceptance run (external reads, no sends, no model calls):

```bash
.venv/bin/python scripts/live_acceptance.py
```

`--rag` explicitly enables two Gemini calls on synthetic reference knowledge. `--agent` invokes the optional AI Agent on a saved run; the service permits only labelled synthetic example.com email evidence. Agent iterations ≤5, workflow duration ≤120 seconds, run budget 5/day. Provider account quotas still apply. Never assume a key is free-tier merely because the model offers one; do not enable billing to make a failed demonstration pass.

## Navigation

Overview → Knowledge Assistant → Agent Workspace → Verification Results → Execution History. Knowledge Sources exposes the actual documents; Architecture & Methodology explains implementation and evidence.

Workspace history uses a random private access capability. Save the key from Execution History to reopen the same workspace. A configured application password gates a shared demo. This is not commercial user authentication or role-based authorization.

## Data and secrets

Only the adapted synthetic assessment source files were copied from v.01. No original Python modules, API results, database URL or production tables are used. `.env`, workspace keys, model caches, databases and n8n credential imports are ignored. `scripts/configure_local.py --provider-env /approved/file` copies only Gemini and Mailtrap variables when expressly authorized; it never imports database settings.

SQLite is durable on your own persistent disk. Streamlit Community Cloud local storage is **ephemeral**. A hosted deployment needs a separate `EVENTOPS_DATABASE_URL=postgresql+psycopg://...` database for durable histories and a hosted HTTPS n8n plus private processing service for automation. No paid service or public endpoint is created by this repository.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [design decisions](docs/DESIGN_DECISIONS.md)
- [Requirement evidence](docs/ASSESSMENT_COMPLIANCE.md) and [test report](docs/TEST_REPORT.md)
- [Deployment](docs/DEPLOYMENT.md) and [n8n operation](n8n/README.md)
- [5–7-minute walkthrough](docs/INTERVIEW_WALKTHROUGH.md), [interview Q&A](docs/INTERVIEW_QA.md), [architecture comparison](docs/COMPARISON.md)
- [Audit of original implementation](docs/ORIGINAL_AUDIT.md)
# eventops-intelligence-streamlit
