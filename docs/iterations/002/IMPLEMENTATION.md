# Implementation — Iteration 002

Starting from `be2aed8`, retained the existing Streamlit app, reference documents, FastEmbed model, Gemini provider and n8n tool architecture.

## Data and retrieval

Added backend-owned assessment/reference/unavailable scenarios and an independently served Calendar/Web source. Representative inputs cover correct schedules, duplicate registrations, inactive participants, mismatched names, unknown events, venue/time discrepancies and incomplete identity. Existing Mailtrap messages are only read; the application never sends new messages. Raw email casing is now retained alongside normalized values, field provenance and source relevance.

The query planner resolves explicit event titles/IDs first, narrows only justified policy/type filters, supports cross-document questions, and flags vague or multiple contexts. A 30-case versioned corpus and deterministic supported/unsupported answer checks separate retrieval quality from generation reliability. A supplementary numeric/source and prohibited-action guard rejects evident grounded-answer violations without extra model calls.

Protected workspace knowledge ingestion supports bounded mapped CSV/schema-versioned JSON, stable namespaced IDs, metadata/fingerprints, duplicate content detection, replacement history, removal from retrieval and isolated indexes. Supplemental content never becomes verification authority.

## State and automation

Added additive migrations, pooled engines, SQLite WAL/busy timeout, revision-based updates, immutable completed runs, atomic review audit writes and unique investigation claims. Request IDs are bound to owner/event/scenario/limits. Checkpoints expose genuine source progress. Reconciliation distinguishes absent evidence, processing, stale/uncertain, final state and optional n8n-confirmed pre-persistence failure.

The n8n graph isolates all source reads and parsing-service failures, saves three explicit outcomes, and records real checkpoints. Controlled diagnostic runs test HTTP errors, timeout, DNS, malformed input and processing-service failure. Environment access is blocked; URLs are administrator-generated configuration, not user input.

Gemini investigation outputs now include findings, conflicts, suggested actions and uncertainties. Actual returned tool records must equal the permitted evidence snapshot. Nested citations are validated. Identical investigations reuse saved results with evidence-hash invalidation. Agent output remains advisory.

## Operator experience

Removed numbered headings, added scenario selection, explicit data classifications, recorded checkpoint inspection, record search/status/review filtering, attention-first ordering, plain-language discrepancy explanations, concise raw/normalized tables, expandable authoritative matches, practical review reasons/actions, enriched history and request reconciliation. The original restrained cream/charcoal theme and native Streamlit controls remain.

## Build and release preparation

Added meaningful offline GitHub Actions, clean pinned Linux builds, health checks, non-root Python containers, separate PostgreSQL and model/n8n volumes, private networking and bounded memory. Added hosted gateway/configuration preparation, exact startup/import/acceptance procedures, security/history scans and sanitized public evidence. No push, public deployment, paid provisioning or original app modification is performed in this iteration.
