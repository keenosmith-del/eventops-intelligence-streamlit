# Release deployment

For the protected release topology, use the [Iteration 003 n8n guide](../docs/iterations/003/N8N_DEPLOYMENT.md) and [deployment runbook](../docs/iterations/003/DEPLOYMENT_RUNBOOK.md). Instructions below describe development and historical acceptance. Gemini remains disabled for new release acceptance until the owner confirms its billing-disabled free tier.

# n8n operation — Iteration 002 (historical development guide)

Runtime validated: n8n **2.42.6**. Verification and Gemini agent workflows were actually imported, published and executed. Historical Iteration 001 evidence is in `docs/evidence`; new evidence is under `docs/iterations/002/evidence`. No hosted deployment is claimed.

## Full local topology

```bash
.venv/bin/python scripts/configure_local.py
# Set this companion's server secrets in ignored .env; generation remains opt-in.
docker compose --env-file .env up -d --build
./scripts/setup_n8n.sh
```

Streamlit 8502; n8n loopback editor/webhooks 5680; protected processor loopback 8767. PostgreSQL and controlled HTTP source are internal-only. Separate `iteration002_*` volumes preserve earlier data. The setup helper imports credentials, imports/publishes both workflows, restarts n8n after CLI publication and removes its ignored mode-0600 plaintext credential import. No credentials are embedded in workflow JSON.

For the earlier host-Python topology use `n8n/compose.yaml`, `scripts/setup_n8n.sh development` and `scripts/start_local.sh`. Development definitions are generated into ignored `.local/development` with `http://host.docker.internal:8766`. The committed full definitions use `http://processor:8766`. Set a reviewed HTTPS processor URL with the generator for a hosted environment.

## Verify definitions versus runtime

```bash
.venv/bin/python scripts/build_workflows.py --check
.venv/bin/python scripts/validate_workflows.py
.venv/bin/python scripts/acceptance002.py
```

Static validation is not proof of import/execution. `acceptance002.py` calls actual protected production webhooks and checks source outcomes, records, replay, reconciliation and both exports. `--models` explicitly adds synthetic-only Gemini RAG and tool-using agent calls. Do not repeatedly invoke live model checks without reviewing budget/quota.

## Verification graph

Protected webhook → strict owner/event/scenario/limit reservation → replay or proceed → backend-controlled source configuration → actual Calendar HTTP read/parsing/checkpoint → Mailtrap read adapter/parsing/checkpoint → Web HTTP read/parsing/checkpoint → aggregate → normalization → duplicate preservation → deterministic reference checks → discrepancy branch → immutable final persistence → response.

The n8n graph performs the sequence and branches. Python exposes focused parsing/business-rule primitives, not a complete hidden pipeline. Read and extraction HTTP nodes use supported continue-on-error behavior. Dedicated isolate nodes convert source processing failures into explicit outcomes, so healthy sources still proceed. A failure in later processing/final persistence cannot produce a fake complete result; checkpoints remain available for reconciliation.

Source statuses: completed, completed-empty, failed, unavailable, timed-out, partially processed. Final status is completed only when all three reads/processes complete (including genuinely empty sources), partial when only some do, failed when none do. Record verification remains separate. Source checkpoints use actual n8n execution IDs/timestamps and are persisted with owner scope.

## Scenarios

- `external_reference`: real public holiday ICS/JSON plus the configured Mailtrap inbox; unrelated observations remain unmapped/incomplete.
- `assessment_event`: actual HTTP requests to the independent controlled synthetic Calendar/Web server plus real Mailtrap messages. Correct events, unknown events, inactive/name conflicts, duplicate/complementary claims and missing identity are derived from source inputs.
- `provider_unavailable`: controlled Web returns HTTP 503; Calendar/Email continue.

URLs are server/admin configured, never supplied by the Streamlit operator. Local HTTP fixture access requires an explicit flag and fixed named/loopback host/port. Approved hosted controlled sources require an explicit HTTPS host. No third-party response is fabricated; fixture tests are labelled as such. No email sending adapter exists.

## Request contract

POST `/webhook/eventops-verify`, header `X-EventOps-Webhook: <independent-token>`:

```json
{"owner":"0123456789abcdef0123456789abcdef0123456789abcdef","request_id":"00000000-0000-4000-8000-000000000001","event_id":"EVT-101","limit":5,"scenario":"assessment_event"}
```

The payload above is a safe example, not execution evidence. A repeated request ID with the same inputs replays the original running/final state; changed inputs are rejected. Concurrent acceptance caught and fixed an omitted run ID in in-progress replay. Completed evidence cannot be overwritten. Never generate a new ID blindly after timeout.

Processor endpoints use a different `X-EventOps-Token`. `GET /runs/{id}/reconcile` additionally takes `X-Workspace-Key` and returns only that owner's state. It does not restart anything. Optional n8n metadata uses a separately configured read-only API credential for the already-bound execution. Without it, stale state is intervention required rather than an invented failure/completion.

## Genuine Gemini investigation

Protected Agent webhook → prepare/atomically reserve snapshot → reuse saved investigation or AI Agent → Gemini Chat Model and three Code Tools → validate/save structured evidence → response.

Tools: `reference_lookup`, `inspect_findings`, `inspect_evidence`. Bounded string queries search one run snapshot. They have no URL/SQL/code/write/sending capability. Node environment access is **blocked**; generated trusted processor addresses remove the previous environment-expression dependency.

Contract: intent, summary, top-level evidence IDs, evidence-linked findings/conflicts, advisory review actions, uncertainties, limitations. Server validation compares returned records to the allowed snapshot and rejects unobserved citations, including nested findings. Record IDs must be copied exactly; a live shortened-ID error was rejected and retained separately as failure evidence.

Five iterations, a 120-second workflow deadline, bounded source/output sizes and five investigation reservations/day constrain work. Identical owner/run/intent/evidence snapshots reuse results without model budget. Changed evidence invalidates reuse. A crashed reservation is not automatically retried. Provider failures never trigger paid/provider fallback.

## Controlled failure diagnostics

```bash
.venv/bin/python scripts/build_failure_probe.py
docker compose --env-file .env exec -T n8n n8n import:workflow --input=/workflows/.local/failure-probe.json
docker compose --env-file .env exec -T n8n n8n publish:workflow --id=EventOpsFailureProbe
docker compose --env-file .env restart n8n
.venv/bin/python scripts/acceptance_failure_probe.py
```

This is a separate local-only test graph. It makes actual requests to controlled 401/403/429/500, timeout, malformed JSON, DNS-failure and processing-unavailable destinations. These are not claims of forced external provider outages. The diagnostic graph is ignored and not part of public hosting configuration.

## Troubleshooting and hosting

403: check webhook credential. 404: verify publication/restart. Invalid request: inspect strict contract. Partial run: inspect source outcomes. Empty inbox: zero records, not fake success. Unavailable agent: inspect provider/schema/citation guard and actual tool trace. Stale run: reconcile/inspect n8n; do not silently mark complete or re-run.

The local editor uses loopback HTTP. The Iteration 003 release keeps both webhooks and the editor private, uses an external runner and exposes only the guarded Streamlit interface. Preserve encryption keys, protect credential imports and configure backups/retention. Commercial identity/tenancy remains outside this demonstration. See the current release guide above.
