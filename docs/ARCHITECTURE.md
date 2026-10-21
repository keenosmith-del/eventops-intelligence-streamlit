# Architecture and trust boundaries

The public GitHub repository contains an independently operating companion to the submitted full-stack assessment. Public application hosting is still pending. Iteration 001 evidence is historical; current changes/evidence are under `docs/iterations/002`.

| Component | Work | Authority |
| --- | --- | --- |
| Streamlit | Questions, scenario/run controls, reviews, exports, history | Presentation and advisory review annotations |
| FastEmbed/NumPy | Local 384-dimensional embeddings, metadata filters, cosine ranking | Relevance, not truth or confidence |
| Gemini RAG | Structured explanation from retrieved context | Generated interpretation with validated citations |
| n8n verification | Protected trigger/replay, actual source HTTP reads, transforms/branches/checkpoints, stage orchestration | Workflow execution |
| Python processing | Bounded parsing, normalization, duplicates and reference comparison | Deterministic verification rules |
| n8n Gemini AI Agent | Select read-only reference/findings/evidence tools; structured investigation | Advisory explanation only |
| SQLAlchemy store | Owner-scoped snapshots, revisions, reviews, reservations and investigation claims | Persisted audit state |

## Retrieval

Three original documents yield 19 stable event/policy/participant units. Complete structured rows keep identity and provenance together. BGE-small passage/query embeddings form a fingerprinted atomic NumPy index; corrupt or incompatible snapshots rebuild, with unique temporary files preventing concurrent write collisions. No vector service or original API is used.

The v2 deterministic query plan resolves explicit IDs/titles before optional follow-up context, preserves global policy scope and permits cross-document evidence. Vague or multiple event references clarify rather than silently choosing. Cosine ranking/depth is inspectable and is never displayed as confidence. Supplementary mapped CSV/schema JSON knowledge is workspace-scoped, versioned and protected; it cannot replace identity verification references.

Gemini receives only retrieved context. Schema, citation membership, conservative numeric/source mismatches and prohibited action claims are checked. Unsupported output is not displayed as a valid generated answer. Those checks and curated fact-alias tests are not a full proof of entailment. No additional evaluator-model call is added to ordinary questions. Questions, plans, hits, provider status and responses are persisted.

## Source scenarios and orchestration

`external_reference` preserves real Office Holidays/Nager.Date reads. `assessment_event` uses a controlled synthetic event Calendar/Web service independently fetched over HTTP plus real Mailtrap GET reads. `provider_unavailable` makes the controlled Web source return HTTP 503. No frontend fabricates results and no provider adapter sends email. The local fixture is labelled local synthetic transport, never a live external event authority.

n8n owns the sequence: authenticated production webhook → strict atomic reservation/replay → backend-owned configuration → independent source reads/parsing → source checkpoints → aggregate → normalize → deduplicate → deterministic verification → discrepancy branch → guarded final persistence → response. There is no Python endpoint that secretly executes this graph. Read/parsing failures are isolated; stage/finalization failures leave an uncertain/incomplete execution rather than fabricated success.

Source outcomes distinguish completed, completed-empty, failed, unavailable, timed out and partially processed. Final workflow status reflects all three outcomes. Record statuses are separate. Correct event observations may verify as event records; they are not participant registrations. All inputs/conflicts/raw excerpts and field-level provenance remain inspectable.

## Execution state, concurrency and review

Request IDs bind owner, target, scenario and limits. Simultaneous requests reserve one run; others replay its in-progress/final state. Checkpoints bind actual n8n IDs and timestamps. Reconciliation uses persisted state and optional read-only owner-bound n8n metadata. Missing reservation means not observed, not proof of nondelivery. An old checkpoint means intervention; no queue, automatic replay or durable job recovery is claimed.

The existing object table is preserved with revision counters. Compare-and-swap updates prevent lost evidence; final results cannot be overwritten by a later replay. Migration versions are recorded and startup serialized/locked. Pooled connections, SQLite WAL/busy timeout and dedicated PostgreSQL support are explicit. Reviews update review state and append the reason/note/action/correction proposal atomically; source claims and authoritative statuses never change. Workspace capability holders are not identified employees.

## Genuine model-assisted investigation

The actual n8n AI Agent connects to Gemini Chat Model and three read-only tools. Initial user intent is interpreted by the model; tools expose only one permitted snapshot. They accept bounded search strings and no URL, SQL, code, secrets or write action. Prompts treat all source material as untrusted. Five iterations, a workflow deadline, output bounds and daily budgets constrain work.

The output contract includes intent, summary, evidence-linked findings/conflicts, advisory review actions, uncertainties and limitations. Server validation compares actual tool-returned records with permitted snapshot records and rejects unknown/nested unsupported citations. Repeated identical investigations reuse an atomic owner/run/intent/evidence-hash claim; changed evidence invalidates reuse. A model-produced identifier error was actually observed and rejected in execution 24, separately from successful agent executions.

## Deployment boundary

The full Linux local topology uses non-root Python services, internal PostgreSQL and scenario service, private container networking, health checks, memory limits and separate volumes. Only loopback development ports are published. n8n node environment access is blocked; credentials are separate encrypted objects. Hosted preparation adds an HTTPS gateway that exposes only production webhook paths and keeps the processor/editor private. No hosted verification has occurred. Commercial identity/tenancy, queues, operational backups/retention and external n8n runners remain further work.
