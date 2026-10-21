# Iteration 002 baseline

Starting revision: `be2aed8` (clean main). Repository publication is user-confirmed; public application deployment remains pending. No original v.01 files or infrastructure are in scope.

Observed baseline: Python 3.12.15, Streamlit 1.66.0, FastEmbed 0.7.4, isolated n8n 2.42.6. Regression: 111 passed / 0 failed / 0 skipped in 2.12 seconds, one Starlette test-client deprecation warning. Ruff and source compilation pass. Current local n8n container is the companion only.

Historical Iteration 001 artifacts contain actual Gemini provider responses and n8n executions 3/8/12 (agent), 4/6/9 (three-source processing). Those establish the old implementation only. SQLite local records, reviews, execution history and access capabilities must be preserved.

Confirmed risks: substring/pronoun context inheritance, no curated retrieval metrics, only citation-membership grounding checks, generic object updates without concurrency control, no migration ledger, no reconciliation after client timeout, inconsistent per-source service errors, HTTP source buffering, broad n8n environment access, no protected structured-knowledge administration, no CI, and unexecuted full Linux topology. Tracked historical evidence unnecessarily includes provider account/inbox identifiers; audit and redact current artifacts without rewriting history.

Plan: additive versioned migrations and compare-and-swap updates; explicit scenario catalog and independently served controlled event inputs; checkpoint/reconciliation lifecycle; strict source outcomes and error isolation; versioned RAG evaluation/ambiguity planning; protected workspace document management; evidence-bound reusable investigations; practical review queue; native operator UI improvements; pinned clean Linux build and isolated full-compose acceptance; offline CI and honest live/hosted status.
