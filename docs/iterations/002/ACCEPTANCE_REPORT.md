# Iteration 002 completion and acceptance report

Starting revision **be2aed8**; local branch **iteration/002-production-readiness**. Final revision is the local commit containing this report (`git rev-parse HEAD`). No push or public deployment was performed. The source repository was already public before this iteration; original v.01 remains untouched and clean.

## Significant changes and justification

1. **Persistence:** additive migration ledger, revision-based atomic updates, SQLite WAL/busy timeout, PostgreSQL advisory migration lock and pooled connections preserve history while preventing lost reviews/checkpoints. Investigation reservations prevent concurrent duplicate model calls. The 19 baseline SQLite object payloads survived unchanged.
2. **RAG:** explicit event references outrank inherited context; ambiguous pronouns/multiple references clarify; cross-document queries retain relevant policies. Real FastEmbed cosine retrieval remains local. Workspace supplements use separate indexes and protected mapped CSV/versioned JSON administration, stable IDs, fingerprints and audits; they cannot replace authoritative records. A versioned 30-case evaluation makes behavior measurable: 25 ranked cases, Recall@5 1.0, MRR 1.0, behavior 30/30 against 19 records. Citation/numeric checks and curated fact aliases are separate from retrieval metrics and are not a full entailment proof.
3. **n8n orchestration:** 31-node verification definition with bounded source configuration, source-isolated errors, explicit checkpoints and execution binding. HTTP client rejection differs from uncertain delivery; owner-bound reconciliation exposes processing/stale/final states without guessing or silently replaying. Final runs are immutable through the authoritative lifecycle. A real concurrency experiment discovered missing run IDs in in-progress replays; the contract was corrected and verified with simultaneous requests.
4. **Gemini agent:** 11-node workflow uses the real AI Agent, compatible Gemini Chat Model and three read-only tools. Intent, findings, conflicts, evidence IDs, actions and limitations are structured. Tool results must match the permitted evidence snapshot; nested citations must have been observed. Cache keys include workspace/run/intent/evidence hash. No write tool or verification authority is available. Execution 24's fabricated shortened citation was rejected and retained; exact-ID prompt refinement and focused execution 25 passed. This is a demonstrated model limitation, not a hidden success claim.
5. **Event integrations:** backend-selected assessment, reference and unavailable scenarios. Independent HTTP Calendar/Web synthetic event records reconcile real time/location/registration discrepancies alongside read-only Mailtrap synthetic emails. Strict trusted hosts prevent arbitrary URL fetches. Office Holidays/Nager.Date remain distinct external connectivity providers. The fixture is not represented as an external live event authority.
6. **Operator experience:** plain-language priorities/actions, searchable unresolved queue, source outcomes, raw/normalized fields with provenance, duplicate evidence, reason/action review notes, persisted history/reconciliation and separate model explanation/tool/evidence views. Reviews can propose corrections but cannot promote deterministic status. Desktop and narrow mobile checks completed. Fresh-session recovery restored the results, review audit entry and saved agent explanation after the full stack restart.
7. **Security/reliability:** streamed request size bound, explicit readonly tool permissions and iteration limits, injection-resistant data boundaries, no node environment access, service-scoped credentials, public evidence redaction and history audit. Non-root Python containers, health dependencies, separate volumes and restart preservation were exercised. Current evidence no longer exposes provider account/inbox IDs; old Git blobs still contain IDs, with no credential found. No history rewrite occurred.
8. **Build/release preparation:** pinned clean Linux build, complete isolated Compose topology with PostgreSQL, offline CI configuration, workflow drift checks, prepared HTTPS gateway/private service override and updated technical/interview documentation. These close reproducibility gaps without claiming a public deployment.

## Actual acceptance

**135 tests pass** on host and Linux ARM64; Ruff/compile/workflow validation/pip compatibility pass. Nine real controlled n8n failure branches pass. Actual event execution 5 and browser 23 produce eight records: three verified (two event observations, one participant), two review-required, two rejected and one incomplete; two duplicates merged. Real generated RAG responses cite EVT-101 and POL-003. Real agent execution 9 and focused browser 25 use the three permitted tools; cached replay skips the model. Exports match persistence. Five services are healthy after restart; all 44 object payloads and the review survive unchanged.

The execution manifest retains intermediate errors, including diagnostic execution 30 interrupted during container recreation. Successful settled-stack reruns provide acceptance evidence; intermediate errors are not erased. See [test results](TEST_RESULTS.md), [evidence](evidence/), [limitations](KNOWN_LIMITATIONS.md), [implementation](IMPLEMENTATION.md) and [architecture decisions](ARCHITECTURE_DECISIONS.md).

## Repeatable startup and acceptance

From the repository root, with Python 3.12 and Docker available:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python scripts/configure_local.py
# Configure independent companion provider credentials in ignored .env.
docker compose --env-file .env up -d --build
./scripts/setup_n8n.sh
.venv/bin/pytest -q
.venv/bin/ruff check app.py eventops scripts tests
.venv/bin/python scripts/build_workflows.py --check
.venv/bin/python scripts/validate_workflows.py
.venv/bin/python scripts/evaluate_rag.py
.venv/bin/python scripts/security_audit.py
.venv/bin/python scripts/acceptance002.py
```

Open http://127.0.0.1:8502. Explicitly enabled Gemini plus `acceptance002.py --models` performs bounded real model calls with controlled synthetic inputs; it is not required by offline tests. `runtime_checks002.py` exercises simultaneous webhooks; `container_checks002.py` restarts only this stack and checks persistence. To repeat failure diagnostics, generate `scripts/build_failure_probe.py`, import/publish its ignored workflow into local n8n, restart n8n, then run `scripts/acceptance_failure_probe.py`. See [n8n instructions](../../../n8n/README.md). Never delete volumes to initialize.

## Remaining status and recommendation

Hosted CI has not run because no push was authorized. Public deployment remains pending by instruction; no 100% assessment/public deployment claim is made. Actual n8n metadata API credentials, managed PostgreSQL TLS/backup recovery, public HTTPS source/gateway acceptance and hosted amd64 execution remain unverified. Empty inbox and selected lower-level failure cases have contract tests rather than fabricated live provider results. Synchronous processing has conservative stale detection, not automatic worker recovery or a durable queue. Knowledge administration is a protected development capability, disabled for public mode.

Recommend one provider/private network plus dedicated PostgreSQL, or a reviewed private host matching the tested stack. Approvals, secrets, domains, paid capacity, backups, retention, proper access controls and target-environment acceptance remain deployment prerequisites. [Deployment readiness](DEPLOYMENT_READINESS.md) records current evidence and boundaries.

Six-minute interview: grounded venue/policy question and follow-up; event trigger and n8n checkpoints; verified/duplicate/conflict/incomplete evidence and review; genuine Gemini tools and the rejected-citation example; evaluation limits, migration preservation and the deployment decision. [Talking points](INTERVIEW_TALKING_POINTS.md).
