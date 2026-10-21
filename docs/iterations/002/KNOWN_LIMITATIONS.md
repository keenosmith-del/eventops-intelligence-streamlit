# Known limitations — Iteration 002

- Public application deployment remains pending by explicit instruction. A public GitHub repository is not a publicly hosted application. No hosted CI success or managed PostgreSQL account acceptance is inferred from local tests.
- Controlled event Calendar/Web data uses a separately served local HTTP fixture. Its transport and reconciliation are real; it is synthetic and not a live external event authority. Mailtrap and historical/public reference providers remain distinct.
- The 30-case RAG evaluation is curated against a 19-record corpus. High Recall/MRR does not establish arbitrary-query quality. Fact-alias, forbidden-claim and numeric checks detect selected unsupported answers; they do not prove full factual entailment or eliminate hallucination.
- Supplemental knowledge administration is a protected development feature. Public mode should leave it disabled. Original reference data remains authoritative and unmodified.
- Workspace bearer capabilities and a demonstration password are not employee identity, tenant authorization or commercial review accountability. Reviewers are explicitly described as capability holders.
- Synchronous webhooks can still be interrupted. Checkpoints/stale detection/reconciliation expose uncertainty, but there is no durable distributed queue, automatic replay, cancellation or worker recovery.
- Read-only n8n metadata reconciliation requires separately configured credentials. Without them, a stale run cannot be proven crashed and is labelled intervention required. Absence of a reservation does not prove a request never reached n8n.
- A crashed reserved investigation is not automatically repeated. Completed investigations are reused by evidence hash; unavailable/in-progress reservations require deliberate investigation, protecting costs over automatic recovery.
- Local PostgreSQL container validation is not a managed-host TLS, backup or disaster recovery acceptance test. Histories are retained; no destructive cleanup policy was introduced. Establish approved retention and tested backups before real operations.
- Calendar/Web n8n HTTP nodes buffer fixed, configured source responses before bounded parsing. Arbitrary URLs are blocked, but production deployment should add egress/response-size enforcement at the network boundary.
- n8n uses its local internal runner in this demonstration. External runners and tighter host isolation remain a commercial hosting prerequisite.
- Public evidence account/inbox identifiers were redacted from current files. Earlier Git history still contains those identifiers; no actual API credential exposure was found and history was not rewritten.
