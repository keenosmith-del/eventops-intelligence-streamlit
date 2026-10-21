# EventOps Intelligence — Streamlit Edition

An independent event operations workspace combining semantic RAG, genuine n8n automation and a bounded Gemini investigation agent. Streamlit presents source evidence, deterministic decisions and AI explanations as separate concepts.

[Public source repository](https://github.com/keenosmith-del/eventops-intelligence-streamlit) · [Iteration 002 report](docs/iterations/002/ACCEPTANCE_REPORT.md) · [Architecture](docs/ARCHITECTURE.md)

**Current state: locally tested, not publicly deployed.** The repository was published after Iteration 001's local acceptance. Iteration 002 makes no GitHub push, paid provisioning or public deployment. Historical evidence is kept separately in `docs/evidence`; new evidence is in `docs/iterations/002/evidence`.

## Capabilities

- Three reproducible reference documents, 19 real FastEmbed vectors, event-aware semantic ranking and grounded Gemini answers with citations.
- Clarification for ambiguous context, cross-document questions, a versioned 30-case RAG evaluation with retrieval metrics and separate curated answer checks.
- Actual n8n source orchestration, source-specific failure isolation, checkpoints, protected webhooks, atomic request replay and conservative reconciliation.
- Controlled event Calendar/Web data fetched from an independent HTTP service alongside real read-only Mailtrap messages. External holiday providers remain a separate connectivity scenario.
- Deterministic normalization, provenance, duplicate/conflict preservation and authoritative event/participant verification.
- A genuine Gemini AI Agent with three read-only tools, evidence-validated structured findings/actions and cached investigations keyed to the run snapshot.
- Native Streamlit result inspection, practical review notes/reasons/actions, exports, history and workspace recovery. Supplemental structured knowledge administration is protected and disabled by default.
- Additive migrations, SQLite development persistence, tested isolated PostgreSQL containers, health checks, non-root Python services and offline CI configuration.

## Recommended local setup: full containers

Use Python 3.12 for configuration and tests; Docker Compose runs the application stack.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python scripts/configure_local.py
# Configure only this companion's .env; keep Gemini disabled until explicitly needed.
docker compose --env-file .env up -d --build
# Once n8n is healthy, import/publish workflows and credentials:
./scripts/setup_n8n.sh
```

Open [Streamlit](http://127.0.0.1:8502). n8n's local editor is at [localhost:5680](http://localhost:5680); the processing API is header-protected on local port 8767. PostgreSQL and the controlled event source are internal-only. This topology uses new `iteration002_*` volumes and never resets earlier SQLite or n8n records.

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check app.py eventops scripts tests
.venv/bin/python scripts/build_workflows.py --check
.venv/bin/python scripts/validate_workflows.py
.venv/bin/python scripts/evaluate_rag.py
.venv/bin/python scripts/security_audit.py
.venv/bin/python scripts/acceptance002.py
```

`acceptance002.py --models` explicitly adds bounded real Gemini calls. It checks controlled synthetic email before transmission; no email is sent. Account quota/billing still requires the operator's attention; there is no paid fallback or billing enablement. Ordinary regression/CI needs no live-provider keys, but downloads a public embedding model on first use.

Stop without deleting data: `docker compose --env-file .env stop`. Never use volume removal as initialization. Back up databases and n8n encryption keys before changes.

## Optional host-Python development

The original local topology remains supported on Streamlit 8501 / processor 8766 / n8n 5679. Start n8n with `docker compose --env-file .env -f n8n/compose.yaml up -d`, import with `./scripts/setup_n8n.sh development`, then `./scripts/start_local.sh`. For controlled scenarios start `scripts/scenario_server.py` on 8090 and explicitly configure the backend source base URL. Details: [deployment](docs/DEPLOYMENT.md), [n8n](n8n/README.md).

## Data, authority and deployment boundaries

All identities and assessment registrations are synthetic. The independent fixture is a real HTTP integration test, not a claimed live third-party event API. Mailtrap is actually read. Public holidays are unrelated observations and never invented registrations. Supplemental documents cannot replace authoritative verification records.

Workspace access uses a random private capability, optionally behind a demo password; it is not commercial employee identity or tenant authorization. Save the key in Execution History to restore that workspace. Public deployment requires proper access decisions, HTTPS, private services and dedicated durable persistence.

SQLite is suitable for local disk. Hosted ephemeral files are not durable history. The tested full topology uses dedicated local PostgreSQL; managed PostgreSQL/HTTPS/public-host acceptance is still pending. The original React/FastAPI/LangGraph project and production infrastructure remain untouched.

## Documentation

[Completion report](docs/COMPLETION_REPORT.md) · [Assessment evidence](docs/ASSESSMENT_COMPLIANCE.md) · [Tests](docs/TEST_REPORT.md) · [Design decisions](docs/DESIGN_DECISIONS.md) · [Comparison](docs/COMPARISON.md) · [Interview walkthrough](docs/INTERVIEW_WALKTHROUGH.md) · [Q&A](docs/INTERVIEW_QA.md) · [Migration policy](migrations/README.md)
