# Interview questions and defensible answers

**Why build this version?** To demonstrate engineering selection rather than allegiance to one framework. The same business rules and evidence requirements can be delivered through a custom product or a smaller internal tool.

**Why Streamlit?** It provides native chat, forms, tables, navigation and exports in Python. It is effective when operational usefulness matters more than highly customized frontend interactions. It is less appropriate for a complex branded multi-tenant product experience.

**Why n8n instead of LangGraph here?** Visual source connections and branches are easy to inspect in a small operations workflow. LangGraph remains attractive when state machines, testing, code review and developer ownership dominate. The companion uses real n8n execution records rather than a decorative exported graph.

**How do we know the RAG is semantic?** FastEmbed produced actual 19×384 passage vectors and query vectors. Cosine ranking finds the expected paraphrased cancellation and ID policies. Model/index fingerprints and stored hits make retrieval reproducible; there is no hard-coded question-to-answer mapping or lexical fallback pretending to be embeddings.

**Why row chunks?** Each row preserves one complete business fact plus its identifier and event scope. Arbitrary character splitting could separate a policy from its event or a participant from their active status. A much larger mixed-document corpus would need another chunking strategy and retrieval evaluation.

**Why Gemini Flash-Lite?** It is a currently documented Flash-class model with free-tier availability and low-cost suitability. It actually answered this RAG demonstration and ran through n8n's compatible chat model node. Account quotas/billing must still be checked; there is no paid fallback.

**Is this truly an agent?** Only the optional Gemini workflow is called an LLM-powered agent. The real AI Agent node chose `reference_lookup`, `inspect_findings` and `inspect_evidence`; the saved execution contains those calls and the model's structured response. The verification graph is deterministic automation and is labelled accordingly.

**Does the agent's explanation verify identity?** No. Exact normalized directory matching, active status and registration are authoritative deterministic checks. Agent output cannot mutate those decisions. A review note is a separate human annotation.

**Why use Python alongside a low-code tool?** Parsing ICS/email/JSON and comparing identity fields needs careful tests, schema boundaries and reusable rules. n8n orchestrates these narrow primitives and owns the source/branch graph. Putting all rules into visual expressions would obscure correctness; hiding the complete workflow behind one Python endpoint would obscure orchestration.

**What prevents prompt injection?** Untrusted input is delimited as data, tools expose only bounded read-only snapshots, no tool accepts executable instructions or URLs, output and citations/tool names are validated, and deterministic verification is reapplied. The demo refuses unlabelled or non-example.com email evidence before model analysis. Prompts alone are not a complete defense.

**What if the LLM hallucinates with valid citations?** Citation membership validation catches invented IDs, not all unsupported claims. The UI preserves source text and labels generated explanations. Claim-level entailment evaluation and adversarial testing would be necessary for higher-assurance production use.

**What if the inbox is empty?** A successful read can produce zero records. That is recorded as zero, not fabricated extraction. Source success, workflow completion and record verification remain separate.

**How are conflicts handled?** Event/email duplicates retain all inputs and evidence. Distinct supplied names, locations, titles or dates produce explicit conflicting values and prevent verification. Similar names with different emails are not silently merged.

**Why are holiday records incomplete?** They are genuine external observations with no authoritative assessment event or participant identity. Their presence proves the read, not attendance eligibility. Only the labelled synthetic registration messages support this sample participant verification.

**What happens after a webhook timeout?** Delivery is uncertain. The app preserves the request ID and any already-persisted run. The same ID returns saved state rather than re-running sources. There is no automatic recovery/cancellation; investigate the real n8n execution before retrying.

**How durable is the app?** SQLite on local persistent disk preserves records. The hosted filesystem can be ephemeral. A separate PostgreSQL connection is implemented for durable hosting, but no managed database has been provisioned or validated in this delivery.

**What is not yet production-ready?** Public hosting, managed database acceptance, real user identity/tenant permissions, durable queued execution/reconciliation, commercial data governance/retention, and platform-specific memory/cold-start testing. The current synthetic workspace key/password model is deliberately described as a demonstration boundary.

**How were tests separated from live evidence?** The automated suite uses controlled transports for failure paths and actual local embeddings for retrieval tests. Separate files record real Gemini provider IDs, n8n executions, actual source counts and browser interactions. A mock provider response never establishes a live integration claim.
