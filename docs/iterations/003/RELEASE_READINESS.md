# Iteration 003 release readiness

**Verdict:** local deterministic release rehearsal passed. The project is prepared to begin controlled, owner-approved free infrastructure setup and hosted acceptance. It is **not publicly deployed**, and full public AI assessment acceptance remains blocked while Gemini is disabled. A real-browser release check is pending because the browser tool refused the local target.

Starting implementation baseline: `a0f41bfc99c9a991879e3047beb3739f98d8ad6c` (initial stale local main was `be2aed8`). Work is on `iteration/003-deployment-readiness`; no merge into main or infrastructure creation is implied. Source/rehearsal hashes accompany the evidence, and Git identifies the delivered commit. Necessary commits/pushes were subsequently authorized by the owner. Implementation commit: `4f926f46d3d19421354e67b7f70a0b798ce99840`; this report is updated in a subsequent documentation-only commit.

| Area | Conclusion | Evidence / condition |
| --- | --- | --- |
| Application implementation | Ready for controlled provisioning |147 regression tests pass; new model execution disabled/pending |
| Docker build | Verified locally | Linux ARM64 image runs; non-root/read-only release stack exercised |
| Production configuration | Validated; actual account inputs pending | Standalone six-service and optional Funnel topology checks; dummy values are not connectivity proof |
| n8n workflows | Prepared and executed locally | Real publication, durable state, actual deterministic Code/source execution and external runner; agent graph prepared but no new Gemini invocation |
| Secrets inventory | Complete | Separate five boundary secrets, provider/database inventory, ignored private files; no keys in evidence |
| Database migrations | Tested locally | Additive ledger1/2, permission/rollback probe, newer-schema refusal tests; separate Neon project pending |
| Persistent storage | Tested locally / hosted pending | DB/n8n/model volumes; review/claim/object preservation, stopped n8n state backup |
| Authentication boundaries | Reviewed | Strong gate, private service tokens, owner capabilities, replay/rate bounds; enterprise identity is out of scope |
| HTTPS gateway | Configuration validated / live pending | Caddy validation and loopback routing; no public TLS certificate/Funnel route tested |
| CI | Verified | Baseline39546325285 and release39552175515 both completed successfully; release run checks exact implementation commit `4f926f46d3d19421354e67b7f70a0b798ce99840` |
| Monitoring | Prepared | Startup SQL, liveness, manual authenticated readiness, bounded redacted logs and incident runbook; no hosted alert service provisioned |
| Backup and restore | Tested locally / hosted pending | Real PG archive restored into a new empty destination; exact payload/claim equality; off-host/n8n replacement restore pending |
| Full release rehearsal | Partial overall; deterministic path passed | Model functions intentionally not revalidated; actual browser check blocked; all8 services healthy after restart |
| Real hosted deployment | Not performed | Owner explicitly withheld authorization |
| Public hosted acceptance | Pending | Free host capacity, new Neon, ingress/TLS, browser and model gates unresolved |

## Delivered implementation

- `eventops/operations.py` supplies production input checks, exact private origins, sanitized operational metadata, login throttle and durable source-run budgets. API startup/readiness/errors, client trust, source validation and workflow revision tracking use these controls.
- Gemini generation requires both explicit enablement and confirmed free-tier status in production. The release rehearsal has both disabled. Deterministic verification retains authority; AI interpretations never promote records to verified.
- Migration code refuses a future schema version. Configuration validates dedicated PostgreSQL with verified TLS; local rehearsal alone permits its isolated unencrypted database.
- Standalone `deploy/compose.hosted.yaml` retains Streamlit, FastEmbed, protected Python, real n8n and an external runner. A private fixture serves labelled synthetic HTTP independently. Durable n8n encrypted credentials/history and FastEmbed caches remain on the host; application records/reviews use PostgreSQL.
- `compose.funnel.yaml` binds the gateway only to loopback for future approved ingress. `compose.rehearsal.yaml` adds two isolated local PostgreSQL services, never a public database. Caddy is non-root with read-only filesystem, dropped capabilities and internal routes blocked.
- New configuration, preparation, preflight, database, publication, health, smoke, rehearsal and source-manifest scripts provide repeatable release operations. Gateway image, SQL init, ignored secret paths, versioned workflows, expanded tests and CI checks accompany them.

## Architecture, price and capacity decision

The conditional primary is **Oracle Always Free ARM + a new Neon Free PostgreSQL17 project + eligible Tailscale Personal Funnel** using a free provider HTTPS hostname. No domain purchase or DNS change is needed. Start around2OCPU/6GB within the current documented free allocation; use persistent host volumes for n8n/cache and a separate Neon database for the companion. No paid host, expiring credit or automatic upgrade is acceptable.

The intended recurring total is **$0 only if those exact ongoing-free entitlements and capacity are available**. Oracle free capacity/idle reclamation, Neon quotas/sleep, Funnel beta/bandwidth and Mailtrap plan/API quota remain explicit limitations. Account-level cost and future pricing cannot be guaranteed from documentation. Gemini billing is unknown and remains disabled. Full price/limit sources and alternatives are in [hosting options](HOSTING_OPTIONS.md).

Fallback: the same full stack on separately owned always-on hardware with Neon Free and provider ingress. This retains genuine n8n, embeddings and processing but loses independent cloud availability. If an Always Free persistent host cannot be obtained, no complete independent $0 alternative has been verified among the assessed managed hosts. Report that blocker instead of paying or removing functionality.

## Operations and handover

[Deployment runbook](DEPLOYMENT_RUNBOOK.md) contains exact host build, preflight, database migration, workflow publication, private acceptance, optional ingress and public smoke commands. No deploy-on-push is configured. [Database and backups](DATABASE_AND_BACKUPS.md) covers the new role, verified TLS, transactional migrations, private archives and empty-target restore. [n8n guide](N8N_DEPLOYMENT.md) covers stable IDs, hashed revisions, credential rebinding, bounded tools and actual execution checks.

Rollback preserves volumes and matching n8n encryption keys, reselects a reviewed application/workflow revision and runs private acceptance. Database recovery restores to a new empty destination before a deliberate cutover; it never downgrades or overwrites live tables. In-flight requests are reconciled rather than blindly replayed. See [rollback](ROLLBACK.md), [security review](SECURITY_REVIEW.md), [observed tests](TEST_RESULTS.md) and [interview explanation](INTERVIEW_TALKING_POINTS.md).

## Remaining release blockers

1. Owner-approved actual free host eligibility/capacity and zero-cost resource labels, separate Neon Free project/role, free Mailtrap API entitlement and eligible Personal Funnel host identity. No resources exist from this iteration.
2. Explicit approval to expose the new guarded app and its provider-generated URL. Real firewall, TLS, remote database permissions, cold starts, backups and public browser/websocket acceptance must then pass.
3. Gemini remains disabled per owner instruction. Billing-disabled Free confirmation is necessary before a new grounded model response and actual n8n Gemini/tool execution can be accepted. Historical agent evidence is not a replacement for hosted acceptance.
4. Off-host backup destination/access and an operating owner must be confirmed. Free availability remains best-effort; quota exhaustion results in unavailability rather than paid fallback.

The existing domain preference and R0 budget are already known. No purchase, existing DNS modification, paid upgrade, original application change, volume deletion or history rewrite is part of this release.
