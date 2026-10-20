# Architecture and data flow

Event coordinators must reconcile schedules, registration messages, policies and directory identities. Automation reduces repetitive comparison; evidence and uncertainty must remain visible. This edition solves the same sample business problem as the original assessment with an independently operating internal tool.

## Components and authority

| Component                        | Responsibility                                                                                                | Authority                                  |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| Streamlit                        | Navigation, questions, run triggering, inspection, review notes, exports                                      | Presentation; cannot override verification |
| FastEmbed + NumPy                | Local document/query embeddings and cosine ranking                                                            | Retrieval relevance, not truth             |
| Gemini Flash-Lite REST           | Structured explanation from retrieved knowledge                                                               | Generated interpretation only              |
| n8n verification graph           | Protected trigger, replay branch, source reads, aggregation, stage calls, discrepancy branch, response        | Orchestration; no model required           |
| Companion Python service         | Bounded parsing, normalization, grouping, reference comparison and storage                                    | Deterministic business rules               |
| n8n AI Agent + Gemini Chat Model | Interpret an investigation request; choose bounded evidence/reference tools; produce a structured explanation | Advisory only                              |
| SQLite / separate PostgreSQL     | Owner-scoped history, executions, reviews, idempotency reservations, budgets                                  | Persisted audit state                      |

The Python service has no endpoint that executes the complete workflow. n8n makes real Calendar and Web HTTP requests, invokes the Mailtrap read adapter, captures individual outcomes, chooses the repeated-request/discrepancy branches, aggregates data, invokes each stage separately and persists the result. Its node execution data proves those transitions occurred.

## RAG

`events.csv`, `policies.csv`, and `directory.json` become 19 complete retrieval records with stable IDs and field-level source selectors. Ingestion rejects malformed schedules, duplicate IDs/emails, unsupported directory versions and invalid associations. Each record includes normalized structured fields and human-readable text.

FastEmbed's `BAAI/bge-small-en-v1.5` produces 384-dimensional passage/query vectors locally using ONNX. Nineteen float32 vectors occupy about 29 KB before metadata; this is a dataset calculation, not a measured application-memory claim. An `.npz` index stores the vectors and a content/model/format fingerprint. Incompatible or corrupt indexes rebuild. No pickle is loaded. No duplicate append operation exists: rebuilding replaces the entire snapshot atomically.

The deterministic query plan normalizes whitespace/event IDs, resolves event titles and inherits event context for a supported follow-up. Metadata filtering respects global policies and participant event registrations. Cosine similarity ranks eligible records; a 0.30 floor and 1–10 result depth bound context. Similarity is not calibrated confidence.

Gemini receives the normalized query and retrieved record text only. The prompt treats all context as untrusted, requests refusal when unsupported, and asks for structured answer/citation IDs. Validation rejects unknown, duplicate or missing citations and incomplete output. Original question, transformed query, matches, response status, provider model/usage and answer are persisted. Citation membership validation does not prove every generated claim is entailed; human-readable evidence is always available.

## Verification

1. Authenticate the production webhook.
2. Validate target event, owner, record limit and request ID; atomically reserve the request.
3. Return saved state for repeated requests, including a still-running state rather than initiating duplicate work.
4. Read Calendar, Email and Web with independent outcome capture. Network failures and invalid schemas contribute failed outcomes while other sources continue.
5. Parse ICS, bounded JSON and explicit registration labels. Retain source IDs, full bounded excerpts and raw fields.
6. Normalize Unicode, whitespace, IDs, email casing and timezone-aware timestamps. Missing zones are flagged rather than guessed.
7. Merge event/email duplicates conservatively. Keep every input, evidence reference and conflicting field value. Similar-name/different-email records are only marked potentially related.
8. Compare event scope, directory email, active status, event registration, exact normalized name, optional participant ID, and supplied schedule/title/venue against reference records.
9. Classify each record independently: verified, review required, rejected, incomplete. A workflow can complete while records are rejected or incomplete.
10. Reapply deterministic verification at persistence, store actual n8n execution ID/outcomes/timestamps, return results and expose exports/history.

Calendar/Web holiday observations lack event identity and therefore remain incomplete. Synthetic Mailtrap positives/duplicates and inactive-conflict messages provide the participant demonstration without fabricating real registrations.

## Optional genuine AI agent

The second workflow uses `@n8n/n8n-nodes-langchain.agent` v3, the installed Gemini Chat Model integration v1.2, and three Code Tools v1.3. The model selects tool calls using a string query. `reference_lookup` searches only the target event's authoritative records; `inspect_findings` returns recorded deterministic findings; `inspect_evidence` returns the bounded source excerpts. None accepts URLs, SQL, scripts, credentials or write actions.

The agent sees user intent and event identity initially, then obtains records through tools. A five-iteration cap, 120-second workflow limit and five-run daily budget bound work. The demonstration service allows only explicitly labelled synthetic example.com email evidence. Output requires interpreted intent, summary, evidence IDs and limitations. Unknown tools/citations, invalid JSON, model failures, and outputs without actual tool calls yield unavailable. Private chain-of-thought is neither requested nor stored in application evidence; observable tool arguments/results are stored.

A model explanation cannot write participant state or verification statuses. Human review updates a separate review status and append-only note record; it never promotes a record to verified.

## Persistence and ownership

All objects use independent companion tables. A 192-bit workspace capability scopes reads and updates; the app does not cache per-user history. Only the public synthetic index/model is process-cached. Save the workspace key to restore a session. The app password is a demonstration gate, not a user identity provider.

SQLite supports isolated local operation. The same SQLAlchemy store accepts an independently provisioned PostgreSQL/psycopg URL. Hosted local files are ephemeral: the vector index may rebuild, but histories require durable storage. PostgreSQL support is implemented, not live-tested against a managed account.

## Reliability and commercial evolution

Source and model requests have explicit timeouts and no application-level retries. n8n source failures are represented per source; unavailable configuration is distinct from empty inbox. A delivery timeout leaves an uncertain request record; reconcile the persisted run before retrying the same request ID. An interrupted run remains running/uncertain and is never reported as complete. This edition does not implement automatic stale-run recovery or background-job polling.

For commercial multi-user service: add OIDC identities, tenant membership and row-level authorization; per-user/tenant budgets; durable queues and cancellation; monitored worker health; managed PostgreSQL migrations/backups; managed n8n external runners; deployment TLS and private networking; retention/deletion controls; redaction and a data-processing agreement; claim-level grounding evaluation; and broader format/date/language extraction coverage. Do not infer these capabilities from the demonstration password or a successful local run.
