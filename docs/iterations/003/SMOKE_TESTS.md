# Smoke tests and operating procedures

Public smoke is read-only and never triggers a model/workflow:

```bash
.venv/bin/python -m deploy.smoke --url https://APPROVED-PROVIDER-HOST.ts.net --output deploy/.local/public-smoke.json
```

It checks the app HTML/security headers and verifies that editor/API/webhook/health/debug paths return404. HTTPS certificate validation remains enabled. It cannot prove password behavior, provider availability, a healthy DB or working model tools. A real browser must verify wrong/right password, websocket interaction, source evidence, both downloads, review persistence and workspace-key recovery. Do not publish the password or workspace key in screenshots.

## Local release rehearsal

New volumes, keys, credentials and ports are independent from all earlier applications. With existing approved companion Mailtrap inputs:

```bash
.venv/bin/python -m deploy.prepare_rehearsal
.venv/bin/python -m deploy.check --env-file deploy/.local/rehearsal.env --rehearsal
mkdir -p deploy/.local/workflows
docker compose --env-file deploy/.local/rehearsal.env -f deploy/compose.hosted.yaml -f deploy/compose.rehearsal.yaml up -d --build
.venv/bin/python -m deploy.publish --env-file deploy/.local/rehearsal.env --rehearsal --publish
.venv/bin/python -m deploy.rehearse --interrupt
```

`--interrupt` deliberately SIGKILLs **only the new rehearsal n8n** after observing Calendar/Email checkpoints in a private diagnostic graph. It confirms uncertain delivery, persisted running state, conservative stale reconciliation and a replay branch that does not repeat sources. No existing app or production execution is interrupted. The restart/backup phase creates a fresh local restore database; it does not clear/reseed any existing DB. Use `--resume` only after a failure in the backup/restore phase, to finish from saved in-progress evidence without new source/model calls.

Model acceptance is explicitly optional. The owner said the Gemini billing status is unknown and requested disabled: do not pass `--models`, enable either model flag or infer a new model pass from Iteration002 evidence. After a later confirmed billing-disabled Free project, a fresh controlled rehearsal may pass `--models` for one bounded analyst investigation and one grounded answer. The agent can take multiple turns, but budgets/iterations/timeouts remain bounded; there is no paid fallback.

The rehearsal checks actual n8n imports/publication/auth, independent HTTP sources and real Mailtrap reads, all decision classes, duplicates, source failure isolation, persisted CSV equality, review audit/owner isolation, interruption/reconciliation, complete n8n stopped-state backup, restart persistence and PostgreSQL custom-archive restoration with matching hashes. `release-rehearsal.json` is machine-readable; failures stay failures. It is not public TLS/Neon acceptance.

## Readiness and monitoring

- Streamlit `/_stcore/health`: container-local liveness only; public gateway blocks it. Password UI is separately checked in a browser.
- Processor `/health`: liveness; one DB query at process startup. Authenticated `/readyz` performs a manual dependency check and explicitly does not test providers. Do not poll SQL readiness continuously on Neon Free.
- n8n `/healthz/readiness`: private n8n readiness; actual webhooks/credentials/tasks require acceptance.
- Runner5680 `/healthz`: private launcher health; verify registration/actual Code tasks separately.
- PostgreSQL: version/schema/role/TLS checks on demand; backup restoration periodically into a new empty target, within free quota.
- Logs: `docker compose ... logs --since=30m processor n8n runners gateway`; restrict operator access and redact before sharing. Rotation bounds on-host files. Structured processor logs contain request/run/execution/revision/stage/source/status/duration, never bodies, capabilities or tokens.

## Incident actions

| Condition | Severity / action |
| --- | --- |
| n8n unavailable / uncertain webhook delivery | Operational failure. Inspect readiness/logs and reconcile the original request ID before retrying; never mint another ID to hide uncertainty. |
| One provider timeout/401/429 | Source warning if other sources survive. Check the outcome, approved credentials and provider quota; retain partial records. Do not manufacture replacement data. |
| Gemini429/quota/billing unknown | Model unavailable; deterministic results remain. Wait for free quota or owner verification. No paid fallback, automatic upgrade or extra judge calls. |
| Mailtrap auth failure | Credential/source failure. Owner checks the approved sandbox/token scope/Free quota; never send new emails just to mask a failed read. |
| Database unavailable / Neon quota exhausted | Critical persistence failure. Stop new processing, inspect quota/connectivity privately, restore availability, then reconcile. Liveness alone does not imply safe writes. |
| Interrupted workflow | Preserve checkpoints and stale/intervention status. Inspect actual n8n execution; no automatic recovery/replay claim. |
| Migration failure/newer ledger | Critical release stop. Keep previous data and manifests; use compatible application or reviewed restore into a new target. No reset/reseed/downgrade. |
| Service restart | Check all health states, persisted row/hash/review evidence and decrypted credential operation. Preserve encryption keys/volumes. |
| Lost FastEmbed cache | Retrieval cold start. Download the public model again into the dedicated cache and measure readiness; no paid embedding fallback. |
| Expired/rotated credential | Deliberate private update/rebind, then auth/source acceptance. Keep n8n encryption key compatible with saved state. |
| Free-host reclamation or unavailable capacity | Hosting blocked. Recover from encrypted off-host backups when free capacity exists; do not upgrade/pay or fake load to avoid reclamation. |
| Disk/storage/transfer cap | Warning before cap; failure at cap. Export/approved archive policy and stop before limits; never silently delete histories or enable overages. |

A lightweight operator review of local logs, plan dashboards and backups is sufficient for this portfolio. No paid monitoring service, keepalive bot, expensive stack or automatic cloud change is configured.
