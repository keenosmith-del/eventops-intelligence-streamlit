# Observed release checks — 21 October 2026

These are local release results, not evidence of a public deployment. Gemini remained disabled at the owner's instruction. No model request, email send, cloud provisioning, DNS change or paid resource creation was performed.

| Check | Observed result | Evidence |
| --- | --- | --- |
| Baseline | 135 tests passed; exact merged baseline GitHub CI completed successfully | `evidence/baseline-tests.txt`, `baseline-ci.json` |
| Updated macOS regression | 147 passed; one Starlette/httpx deprecation warning | `evidence/pytest.txt` |
| Disposable Linux ARM64 regression | 147 passed; same warning; no release database/provider credentials supplied | `evidence/linux-pytest.txt` |
| Static checks | Ruff, compilation, workflow generation drift, both workflow contracts and production/Funnel topology validation passed | Reproducible commands below; CI repeats these |
| Gateway | Caddy HTTPS configuration validates. Real loopback gateway serves app HTML; webhook/editor/API/health routes return404; security headers asserted | `evidence/gateway-validation.txt`, `proxy-smoke.json` |
| Workflow publication | Actual verification31-node and Gemini agent11-node graphs imported and published into isolated n8n; revision and hashes recorded | `evidence/workflow-publication.txt` |
| Processing | Real n8n reads private synthetic Calendar/Web HTTP and actual synthetic Mailtrap messages. Main scenario: 8 records, 3 verified, 2 review, 2 rejected, 1 incomplete, 2 duplicates merged. Partial scenario: 4 records, 2 verified, 1 review, 1 rejected | `evidence/release-rehearsal.json` |
| Boundaries | Protected service/webhook authentication, owner isolation, replay, persisted reviewer action and CSV equality passed | Same rehearsal report |
| Interruption | Actual rehearsal n8n SIGKILL after Calendar/Email checkpoints; uncertain delivery requires intervention; replay does not repeat sources; no fabricated automatic recovery | Same report, `n8n-executions.json` |
| Restart | All8 rehearsal services return healthy; object/review/claim payload hashes remain equal across restart | Same report |
| Database | PostgreSQL17, non-superuser/no-CREATEDB/no-CREATEROLE app role, additive schema versions1/2, indexes, transactional insert/rollback probe passed. Local TLS is intentionally absent; hosted verified TLS remains pending | `evidence/semantic-retrieval.json` |
| Backup/restore | Real custom PostgreSQL archive restored into a new empty isolated destination; all object payloads and request claims match. Complete stopped n8n state copied privately; original key preserved | Rehearsal report; private archives are ignored, never published |
| Real semantic retrieval | 19x384 vectors from three documents; 30/30 behavior cases; 25 retrieval cases recall@5=1.0, MRR=1.0. Successful initial download/index about19.9s, warm initialization0.069s, single local samples | `evidence/semantic-retrieval.json` |
| Secrets | No configured secret values/patterns found in current files or scanned history. Historical provider account/inbox identifiers remain; history was not rewritten | `evidence/security-audit.json` |
| Browser | Browser tool refused localhost8503 with ERR_BLOCKED_BY_CLIENT. Native Streamlit AppTest covers rendering/password tests, but real release websocket/login browser acceptance remains pending | Tool refusal recorded here; no screenshot/browser pass invented |
| Gemini agent/RAG | No new generation requested. Prior genuine model/tool execution evidence remains historical Iteration002 evidence | `../002/evidence`; not a new-release model pass |
| Cloud | No hosted URL, Neon remote TLS, real Funnel route, ACME issuance/renewal, provider entitlement or public acceptance verified | Deliberately pending |

## Reproduce

From the repository root, Python3.12 and Docker available:

```bash
.venv/bin/pytest -q
.venv/bin/ruff check app.py eventops scripts tests deploy
.venv/bin/python -m compileall -q app.py eventops scripts deploy
.venv/bin/python scripts/build_workflows.py --check
.venv/bin/python scripts/validate_workflows.py
.venv/bin/python scripts/security_audit.py
.venv/bin/python -m deploy.ci_check
```

The [smoke/rehearsal instructions](SMOKE_TESTS.md) give explicit local-only commands. Do not add `--models` while Gemini is disabled. Release orchestration stops only its dedicated rehearsal n8n for the deliberate interruption and consistent backup; it never removes volumes or resets another application.

## Failures found and resolved

Initial attempts exposed invalid comma-separated tmpfs parsing, an unreliable executable SQL init mount, read-only n8n cache permissions, Caddy file-capability execution failure under dropped capabilities, manifest self-inclusion during publication, developer dotenv precedence over the release file, backup TLS argument handling, host-side restore DNS resolution and a read-only Hugging Face/Xet download cache. The corrected release was rebuilt and exercised rather than marking failed attempts as passing.

One first host test run lacked sandbox permission for its ephemeral loopback listener; rerunning with local-network permission passed147. Running unit tests inside an already configured production service was also inappropriate: production validation deliberately rejects test SQLite settings, and the cold download exposed the cache defect. The final Linux regression ran in a separate disposable container without release configuration and passed147; the actual protected runtime separately passed retrieval and end-to-end acceptance. The model cache fix uses persistent `HF_HOME` alongside `FASTEMBED_CACHE_PATH`.

Resource samples in the rehearsal report are post-restart idle samples, not peak load or hosted sizing proof. Configured production container memory ceilings total about4.1GiB; a roughly6GB ARM host leaves operating-system/build headroom but still needs real hosted measurement. No load/uptime SLA or production-grade free-tier reliability is claimed.
