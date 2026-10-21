# Interview questions and defensible answers

**What changed in Iteration 002?** Relevant event HTTP scenarios, measurable RAG/ambiguity behavior, additive migrations and concurrency controls, source failure isolation/checkpoints/reconciliation, reusable evidence-validated investigations, a practical review interface, full Linux/PostgreSQL validation and offline CI preparation.

**Why not a larger vector database?** The corpus is small and structured-row retrieval is measurable. Local FastEmbed vectors preserve complete facts/IDs with little infrastructure. Scale and measured query behavior, not appearance, should justify another store.

**What does the evaluation prove?** Recall@5/MRR on curated expected sources, plus separate clarification/no-answer and curated fact/citation checks. It does not prove every generated statement is entailed or every unseen query works. Similarity is not confidence.

**How is context safer?** Explicit event IDs/titles are resolved first. A vague pronoun alone is insufficient; multiple possible contexts or unsupported references clarify without a generation call.

**Are the event integrations real?** n8n makes actual HTTP requests to a separately served controlled synthetic Calendar/Web service and genuine Mailtrap GET APIs. That is real transport and processing, but not a fabricated external event API. Public holiday connectors remain distinct.

**Is the agent genuine?** Yes: actual n8n AI Agent/Gemini Chat Model executions contain model-selected reference/findings/evidence calls. The deterministic verification workflow is never relabelled as an LLM agent.

**Can it override verification?** No. Tools expose bounded snapshots only; there is no write, sending, arbitrary browsing, SQL or executable-code parameter. Suggested actions are advisory. Reviews/corrections are separate audit records, not mutations of source truth.

**What about hallucination or injection?** Prompts are only one layer. Tool capability restrictions, input/output bounds, permitted snapshot equality, observed citations and independent deterministic decisions enforce real boundaries. A live model invented a shortened record ID and the explanation was rejected. Citation validation still does not prove full entailment.

**Why reuse investigations?** An atomic owner/run/intent/evidence-hash claim prevents concurrent duplicate model spending. Changed evidence invalidates reuse. A crashed/incomplete reservation is not automatically re-executed; cost safety is preferred over pretending recovery exists.

**What happens after a timeout?** Distinguish a definite HTTP rejection from uncertain delivery. Reconcile the original request ID with persisted checkpoints/final state and optional n8n metadata. Missing reservation is not proof of nondelivery; stale state requires intervention. No blind replay or queue recovery is claimed.

**Why retain JSON snapshots?** The app restores small whole executions. Revisions, transactional reviews and unique claim keys provide justified constraints. Add normalized result/tenant tables only when reporting/authorization requirements need them, through further additive migrations.

**What was actually container-tested?** Clean Linux installation, non-root app/processor/source, private networking, separate PostgreSQL, source scenarios, protected n8n workflows and persistent records. Managed-host TLS, backups and public acceptance remain separate.

**Is CI green?** The workflow is implemented and its constituent checks run locally. No hosted GitHub Actions success is claimed without an observed run; this iteration does not push.

**Is it production-ready?** It is substantially better prepared and locally validated. Public hosting is deliberately pending. Commercial identities/tenancy, retention/backups, queues/recovery, external runners and target-platform acceptance remain necessary before real multi-user operations.

**Which architecture would you recommend to a client?** A small internal tool may favor Streamlit/n8n; a bespoke branded product may favor a custom frontend/code graph. Ask about users, workflow complexity, long jobs, governance, hosting and maintenance ownership before choosing.
