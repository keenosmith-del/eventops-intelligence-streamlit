# Iteration 002 — observed tests

Observed locally 20–21 October 2026. Baseline `be2aed8`: 111 tests passed. Final suite: **135 passed, zero failed/skipped**, host Python 3.12.15 and Linux ARM64 container. Both emit one Starlette/httpx TestClient deprecation warning. Ruff, compileall, generated-workflow drift/contract checks and Linux `pip check` passed. The first sandboxed host run could not bind a loopback socket; the same complete suite passed with local network permission. A container restart overlapped an exploratory diagnostic batch and caused execution 30 to fail; the settled-stack nine-case batch passed. These intermediate failures are not counted as acceptance passes.

| Verification | Observation / evidence |
| --- | --- |
| Semantic retrieval | Real FastEmbed BAAI/bge-small-en-v1.5; 19 corpus records; 30 curated cases, 25 ranked-source cases; Recall@5 1.0, MRR 1.0, behavior 30/30. `evidence/rag-evaluation.json` |
| Generated RAG | Actual Gemini venue/policy responses with valid citations, plus ambiguous-context clarification. `evidence/full-stack-acceptance.json` |
| Event workflow | Actual n8n execution 5 and browser execution 23; independent Calendar/Web HTTP fixture, real synthetic Mailtrap read. Eight merged records: 3 verified, 2 review-required, 2 rejected, 1 incomplete, 2 duplicates merged. Three verified records include two event observations and one participant. |
| Failure isolation | Nine actual diagnostic webhook runs: HTTP 401/403/429/500, timeout, malformed Web, DNS, processing-service unavailability, invalid Calendar. Healthy email processing survives; workflow partial. `evidence/n8n-failure-probes.json` |
| Agent | Actual AI Agent/Gemini Chat Model + reference, findings and raw-evidence tools. Execution 9 passed; cached replay 10 did not rerun the model. Browser 24 produced an invalid citation and was rejected; focused browser 25 passed. Workflow success alone does not imply output acceptance. |
| Idempotency | Two simultaneous real webhook requests returned completed/running for one persisted run. Replay branch skipped source processing. `evidence/concurrent-webhook.json` |
| Reconciliation | Owner-scoped final state/checkpoints exercised over HTTP; stale/intervention and metadata contracts tested. Actual credentialed n8n metadata lookup remains unconfigured. |
| Persistence | Additive SQLite upgrade retained all 19 baseline payloads; final Docker restart retained all 44 object payloads and one review byte-for-byte. `evidence/preservation.json`, `evidence/container-runtime.json` |
| Exports | All/verified exports compared to persisted records; CSV formula protection retained. Both UI download buttons exercised. `assessment-all.csv`, `assessment-verified.csv` |
| Browser | Explicit venue question/follow-up; event trigger; result inspection; duplicates; reason/action review; history reopen and fresh-session capability recovery after restart; participant filter; actual agent; desktop and 390×844 mobile screenshots. |
| Build | Clean Linux dependency installation/build, UID1000, imports, five healthy services, restart persistence and `pip check`. Hosted override parses using synthetic configuration without starting it. |
| Security | Current files and all available Git blobs scanned for known configured secrets and selected patterns. No actual credential found. Historical provider account/inbox IDs remain; current artifacts redacted. `security-review.json` |
| Original application | Read-only final Git status of sibling v.01 is clean. No original application/database/deployment changes made. |

Tests added cover migrations, concurrent compare-and-swap, reservation claims, review audit, stale reconciliation, exact-source binding, partial Mailtrap body failures, explicit/ambiguous query context, versioned evaluation, unsupported generated claims, admin isolation, real independent HTTP transport, SSRF boundaries, malformed sources and observed tool evidence.

CI is configured in `.github/workflows/quality.yml`; **no hosted run observed** because this iteration was not pushed. Ordinary CI has no Gemini/Mailtrap secrets; its first run needs the public embedding model download. Local clean Linux validation is ARM64; hosted amd64 execution remains pending. Perfect small-corpus retrieval metrics are not proof of general answer correctness.
