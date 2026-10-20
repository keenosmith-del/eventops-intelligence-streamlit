# Design decisions

## A second implementation

The original React/FastAPI/LangGraph/PostgreSQL system remains the submitted application. This companion demonstrates how delivery choices change when the goal is a small internal operations tool with a visible automation graph. It neither calls original completed-result endpoints nor shares production tables.

## Streamlit and n8n

Streamlit provides supported navigation, forms, session state, chat, tables, metrics and downloads with little frontend infrastructure. Native widgets, a cream theme and small scoped CSS reduce maintenance. Complex design systems, concurrent collaborative review and highly customized client behavior would justify a dedicated frontend.

n8n makes source connections, branches and stage boundaries inspectable to technical and operations audiences. The graph owns trigger/replay, Calendar/Web HTTP reads, Mailtrap adapter invocation, aggregation, normalization/deduplication/verification calls, discrepancy branching and the response. Python retains reusable tested parsing and authoritative rules because these are easier to reason about and test as code than in long visual expressions. There is deliberately no `run_entire_pipeline` Python endpoint.

Visual automation becomes harder to maintain when expressions duplicate business logic, branching becomes deeply nested, workflow diffs become opaque, or tenant/job state expands. Generated credential-free JSON and narrow contracts make review/reproduction manageable here. A queue-heavy long-running system could favor code-first orchestration again.

## Retrieval units and vectors

An event, policy or participant row is a complete business fact. Arbitrary character chunks could split the identifier from the associated rule or status. Stable row IDs support exact provenance, authoritative verification and citations. FastEmbed BGE-small avoids an external embedding bill and fits a small knowledge base. A normalized NumPy cosine index is sufficient for 19 rows; pgvector would add operations without meaningful retrieval benefit at this scale.

A content/model fingerprint prevents stale vectors from being accepted with changed records. Query transformation resolves event variants and follow-up context before semantic ranking, reducing unrelated event matches. Global policies remain eligible under event filters.

## Gemini selection and model boundaries

Default: `gemini-3.5-flash-lite`, listed as stable and free-tier eligible in Google's current model/pricing pages, checked 20 October 2026. The same Flash-class model was actually exercised in RAG and through n8n's compatible Gemini Chat Model integration. Configure another compatible Flash model explicitly if account availability changes; no silent provider or paid-model fallback exists.

Sources: [Google model catalog](https://ai.google.dev/gemini-api/docs/models), [pricing](https://ai.google.dev/gemini-api/docs/pricing), [n8n Gemini Chat Model](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatgooglegemini/). A free-tier-eligible model does not establish the account's billing tier or guarantee quota availability.

RAG uses a simple bounded REST call rather than a framework. The optional investigation assistant uses the actual n8n AI Agent node and Gemini Chat Model; the model chooses among tools and interprets evidence. A conventional source-processing graph is called deterministic automation. The two claims have separate evidence.

## Trust and uncertainty

Email claims cannot establish identity by themselves. Exact normalized directory matches, active status and event registration remain authoritative. LLM explanations are advisory. Ambiguous extraction is flagged; this implementation does not guess missing identity information. Deduplication retains every source and conflicting value rather than selecting whichever input arrived first as truth.

Prompt instructions alone are insufficient security. Tool implementations have no write/network capability and expose a bounded run snapshot, input lengths and output schemas are enforced, arbitrary URL fetching is blocked, and deterministic verification is reapplied at persistence. The demonstration additionally rejects unlabelled or non-example.com email evidence before agent execution.

## Operational trade-offs

Synchronous webhooks simplify local demonstration and preserve a real execution ID, but a proxy/worker restart can leave delivery uncertain. Atomic request IDs prevent accidental duplicate work. There is no false progress bar or automatic non-idempotent retry. A production version should use a durable queued execution/reconciliation API.

SQLite minimizes local setup. A separate PostgreSQL configuration supports durable hosted histories, but it must be explicitly provisioned; an ephemeral cloud filesystem is never advertised as durable. Model/index cache rebuilds are acceptable; lost audit histories are not.

The implemented workspace key is a high-entropy access capability suitable for an isolated synthetic demonstration. It is not a replacement for commercial authentication, tenant authorization or audit retention. The process-wide index cache contains public synthetic references only.
