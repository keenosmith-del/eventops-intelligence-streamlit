# Genuine n8n orchestration and Gemini agent

Runtime actually validated: **n8n 2.42.6**. `verification.json` and `gemini-agent.json` were imported, published and executed through real protected **production** webhooks. JSON parsing alone was not used as proof of integration. See [execution evidence](../docs/evidence/live-acceptance.json) and [Gemini tool evidence](../docs/evidence/final-live-agent.json).

The image tagged `stable` was already available locally and reported 2.42.6; it was locally tagged to that explicit version before starting the isolated companion. Future official releases may differ; the definitions are pinned to the version actually tested. Verify your image with `n8n --version`.

## Start and import

From the repository root after the Python setup:

```bash
.venv/bin/python scripts/configure_local.py
.venv/bin/python scripts/build_workflows.py
.venv/bin/python scripts/prepare_n8n_credentials.py
docker compose --env-file .env -f n8n/compose.yaml up -d
# Wait for the editor/startup to be ready, then:
docker compose --env-file .env -f n8n/compose.yaml exec -T n8n n8n import:credentials --input=/workflows/.local/credentials.json
docker compose --env-file .env -f n8n/compose.yaml exec -T n8n n8n import:workflow --input=/workflows/verification.json
docker compose --env-file .env -f n8n/compose.yaml exec -T n8n n8n import:workflow --input=/workflows/gemini-agent.json
docker compose --env-file .env -f n8n/compose.yaml exec -T n8n n8n publish:workflow --id=EventOpsVerify01
docker compose --env-file .env -f n8n/compose.yaml exec -T n8n n8n publish:workflow --id=EventOpsAgent01
docker compose --env-file .env -f n8n/compose.yaml restart n8n
```

Delete the ignored plaintext credential import immediately after successful import. Its content is never committed. CLI imports create encrypted credentials in this separate n8n volume. Alternatively, bind credentials interactively in the editor: EventOps companion service (`X-EventOps-Token`), EventOps webhook (`X-EventOps-Webhook`) and EventOps Gemini (`googlePalmApi`). A running n8n process must restart after CLI publishing to reload production webhooks.

Run `./scripts/start_local.sh` in another terminal. Do not reuse ports, databases or credentials from unrelated workflow instances. The standalone development compose publishes only loopback port 5679. `host.docker.internal:8766` connects to this companion's protected processor on the host.

## Verification graph

| Important node                 | Work performed                                                                                  |
| ------------------------------ | ----------------------------------------------------------------------------------------------- |
| Verification webhook           | Production POST endpoint with Header Auth                                                       |
| Validate and reserve request   | Strict contract, known target event, atomic owner-scoped request ID                             |
| Repeated request?              | Real If branch returns saved state without repeating source calls                               |
| Allowed source configuration   | Loads server-controlled, HTTPS allowlisted sources                                              |
| Read Calendar / Read Web       | Actual built-in HTTP Request nodes, 12-second request timeout, no redirects, full text response |
| Capture outcome                | Focused Code node interprets HTTP/network status; installed version returns text as `data`      |
| Read Email                     | HTTP call to a bounded read-only Mailtrap adapter that reads list/body API endpoints            |
| Extract Calendar / Email / Web | Separate parsing calls with source-specific outcome/error capture                               |
| Aggregate source evidence      | Code node combines the three real outputs and keeps all outcomes                                |
| Normalize fields               | Unicode/whitespace/email/ID/date normalization primitive                                        |
| Merge duplicates               | Conservative grouping primitive preserving inputs/conflicts/provenance                          |
| Deterministic verification     | Authoritative event/directory checks, no model override                                         |
| Any discrepancies?             | Real If branch to review-queue or all-checks-passed node                                        |
| Persist authoritative results  | Reapplies verification; saves n8n execution ID, timestamps and all outcomes                     |
| Return verification result     | Respond to Webhook with actual persisted result                                                 |

The processor does not run the whole sequence behind one endpoint. Python owns testable parsing/business rules; n8n owns the observable orchestration, actual Calendar/Web connections and conditional routing.

## Gemini graph

Agent webhook → Prepare agent context → **AI Agent** → validate/save result → webhook response.

The AI Agent is connected by `ai_languageModel` to **Google Gemini Chat Model**, default `models/gemini-3.5-flash-lite`, and by `ai_tool` to three Code Tools. These tools query a bounded snapshot of one finished run:

- `reference_lookup`: event-scoped authoritative source records.
- `inspect_findings`: deterministic issues and field checks.
- `inspect_evidence`: raw untrusted source excerpts/provenance.

The model interprets the request and chooses tools; this is actual model-assisted analysis rather than a conventional fixed source-processing sequence. It cannot send email, execute supplied code, browse arbitrary URLs, write records or change verification statuses. Tools receive a string query, never executable instructions. Maximum 5 agent iterations; workflow execution timeout 120 seconds; 5 agent runs/day. n8n's underlying model integration can perform its own SDK retry behavior; no application-level retry is added and the workflow deadline remains the outer bound.

Output schema: `{intent: string, summary: string, evidence_ids: string[], limitations: string[]}`. Validation also requires observable tool calls and allowed tool names/citation membership. Invalid or unavailable model output produces `unavailable`. Observable tool calls/results are saved; private chain-of-thought is not presented as evidence. The current demonstration refuses non-labelled/non-example.com email evidence before sending anything to Gemini.

## Contracts and authentication

Verification POST body:

```json
{
  "owner": "0123456789abcdef0123456789abcdef0123456789abcdef",
  "request_id": "00000000-0000-4000-8000-000000000001",
  "event_id": "EVT-101",
  "limit": 3
}
```

Use a new request UUID for a new run. Reuse the **same** UUID to retrieve/reconcile the original run. The header is `X-EventOps-Webhook: <independent-token>`. Never put it in a URL or client-side browser script. This example is synthetic test data, not a real execution ID.

Response: `run_id`, `execution_id`, `orchestrator`, workflow `status`, timestamps, `outcomes[calendar,email,web]`, `records`, `summary`, and separate `agent` status. Individual record `status` is independent of workflow status.

Agent POST body: `{owner, run_id, intent}` to `/webhook/eventops-agent`; the same protected header applies. The owner must match a finished persisted run.

Processor APIs use a different `X-EventOps-Token`. n8n credential objects contain these headers, not the workflow JSON. No secrets appear in example payloads.

## Sources

Calendar default: Office Holidays HTTPS ICS. Web default: Nager.Date South Africa public holidays. Both are real public observations. URLs are configured server-side and restricted to the fixed approved provider hosts; user payloads cannot supply URLs. Calendar/Web network requests are performed inside n8n and their bodies are bounded at parsing; unlike the Python Mailtrap stream reader, the n8n node may buffer the fixed provider response before parsing.

Mailtrap uses only the dedicated Email Testing inbox and GET requests to list messages/read text bodies. Configure account/inbox IDs and read-only API token in the processor environment. No send adapter exists. Existing controlled synthetic examples are read, never injected or repeatedly sent by the application. An empty inbox is a completed read with zero records, not fabricated extraction success.

## Failure behavior and troubleshooting

| Symptom                           | Meaning / action                                                                         |
| --------------------------------- | ---------------------------------------------------------------------------------------- |
| 401 at webhook                    | Missing/wrong Header Auth credential; verify independent webhook token                   |
| 404 webhook                       | Workflow unpublished or running process not restarted after CLI publish                  |
| Processor connection refused      | Start the protected service; check Docker host routing/port 8766                         |
| Partial run                       | Inspect per-source HTTP/schema/unavailable error; other sources still processed          |
| HTTP 429                          | Provider quota; no paid fallback, respect reset before another deliberate run            |
| Completed run, incomplete records | Public holidays lack authoritative event/participant identity; expected                  |
| Empty inbox                       | Successful zero-message read; insert controlled data manually only if explicitly desired |
| Running/uncertain after timeout   | Inspect real n8n execution; do not generate a new request ID blindly                     |
| Agent unavailable                 | Check Gemini credential/model/quota, output schema, tool traces and synthetic-data guard |
| Invalid input                     | Service rejects strict schema/unknown target; workflow must not be reported completed    |

The regression suite covers simulated timeouts, rate limits, auth errors, bad schemas, missing configuration/reference data, duplicates/conflicts and invalid model output. Live evidence is separately labelled; it does not imply every external failure condition was forced against the real providers.

The local setup uses n8n's internal task runner. Hosted/commercial operation should use external runners, HTTPS, a protected editor, private processor networking, retained encryption keys, execution pruning and a dedicated database. See [deployment](../docs/DEPLOYMENT.md).
