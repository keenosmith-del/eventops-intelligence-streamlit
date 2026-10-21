# Design decisions

Iteration 002 continues the existing independent product rather than replacing it. The GitHub repository is public; deployment remains pending. [Detailed iteration decisions](iterations/002/ARCHITECTURE_DECISIONS.md) preserve the rationale.

- **Streamlit:** supported native navigation, forms, conversation, tables and downloads reduce frontend ownership for an internal tool. Custom React remains attractive for complex branded/multi-user experiences.
- **n8n plus focused Python:** visual connections/branches/checkpoints are inspectable; reusable parsing/business rules stay in testable Python primitives. Neither a decorative graph nor a giant backend workflow endpoint meets this boundary.
- **Structured rows and FastEmbed:** complete domain facts and stable IDs are natural retrieval units. The small measured corpus does not justify a heavyweight vector database. Fingerprints and curated metrics make the lightweight choice defensible.
- **Explicit ambiguity:** titles/IDs override old context. Unclear pronouns and multiple targets request clarification. This is safer than retrieving confidently for a silently inherited event.
- **Separate grounding evaluation:** Recall/MRR concern retrieval. Citation checks, curated fact/unsupported-claim evaluation and conservative runtime guards concern generation. None proves complete factual entailment; no expensive judge is silently added to ordinary traffic.
- **Realistic controlled data:** an independent HTTP scenario demonstrates relevant event reconciliation without fabricating public APIs. Real Mailtrap reads are distinguished from local synthetic Calendar/Web transport; public holiday connectors remain available.
- **Deterministic authority:** directory identity/active/registration checks, supplied event details and conflict rules decide status. AI explanation and human review do not promote records. Known invalid identities take precedence over missing secondary fields; missing event identity alone stays incomplete.
- **Small additive persistence:** existing bounded JSON snapshots remain useful. Revision counters, a migration ledger and unique investigation claims add real constraints without destructive table replacement. A tested dedicated local PostgreSQL topology prepares durability beyond SQLite.
- **Conservative lifecycle:** checkpoints, atomic replay and reconciliation expose uncertainty after timeout. Staleness is not proof of failure and there is no distributed recovery claim.
- **Evidence-bound read-only agents:** tool observations must match the permitted snapshot; all nested citations must be observed. Investigation reuse avoids redundant model work. Real citation rejection is retained as a failure observation, not relabelled a successful answer.
- **Protected supplemental knowledge:** bounded schemas/field mapping, versions, fingerprints, removals and workspace isolation are practical; public administration stays disabled. Supplements never become identity authority.
- **One operational hosting boundary:** local containers actually run. Prefer a private container provider/network and dedicated PostgreSQL over an assumed chain of free services. Exact hosted capacity/cost requires approval and measurement.

Gemini remains the configured Flash-class provider; no model/provider/billing fallback is enabled. The model was selected against official availability/pricing documentation during the baseline and invoked for fresh iteration evidence. Account quotas/tier are not inferred from model eligibility.
