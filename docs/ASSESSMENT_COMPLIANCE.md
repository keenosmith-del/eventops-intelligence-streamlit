# Assessment requirements and evidence

This maps the user-supplied assessment requirements to observed companion behavior. A standalone original assessor rubric was not supplied; no external score or unconditional 100% compliance is asserted.

| Requirement | Current evidence / status |
| --- | --- |
| Independently operating Python low-code interface | Native Streamlit; real n8n; own processor and dedicated persistence; local Docker acceptance |
| Three structured indexed documents | Event catalog, participant directory, operational policies; 19 real FastEmbed vectors |
| Semantic RAG and grounded responses | Actual cosine retrieval + generated Gemini venue/policy citations; 30-case curated evaluation; grounding limits documented |
| Calendar, Email, Web | Real n8n HTTP source orchestration; existing Office Holidays/Nager.Date connectivity retained; controlled event Calendar/Web HTTP plus actual Mailtrap reads demonstrated |
| Autonomous end-to-end processing | One trigger performs source ingestion, extraction, normalization, merging, verification, persistence and returns results without per-stage interaction |
| Accurate extraction, normalization and deduplication | Raw/normalized provenance, duplicate/conflict evidence, source isolation and validation; representative verified/rejected/review/incomplete records |
| Authoritative verification | Deterministic Python checks against reference identities/event fields; AI cannot promote records |
| Traceable evidence and results | Stable record/source IDs, actual n8n execution IDs/checkpoints, evidence-bound citations, both CSV exports matched to persisted state |
| Error handling and reliability | 135 passing tests; nine actual controlled failure probes; concurrent replay; additive migrations; restart preservation |
| Polished deployable interface | Desktop/mobile review, practical review/history/search workflow; clean Linux image/full local topology accepted |
| Public independently deployed application | **Pending by explicit instruction**; GitHub publication alone does not satisfy this requirement |
| Additional Gemini AI Agent capability | Actual n8n AI Agent + Gemini Chat Model and three readonly tools, structured result validation/cache; invalid citation rejected and retained |

[Completion report](iterations/002/ACCEPTANCE_REPORT.md) · [Observed tests](iterations/002/TEST_RESULTS.md) · [Deployment prerequisites](iterations/002/DEPLOYMENT_READINESS.md).
