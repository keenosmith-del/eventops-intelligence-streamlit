# Deployment readiness

The repository is publicly available on GitHub. Iteration 001 acceptance occurred locally before publication. Iteration 002 develops and validates local deployment preparation only: **no public deployment or push was performed**.

## Tested local architecture

Root `compose.yaml`: Streamlit at 8502, protected processor at loopback 8767, n8n editor/webhooks at loopback 5680, internal PostgreSQL and independent controlled HTTP source. Python image is built from pinned dependencies under Python 3.12.15; app/processor/source run as UID 1000. Health checks and dependencies enforce readiness; memory limits are explicit. Separate `iteration002_*` volumes preserve old companion data.

Use README's setup sequence and `scripts/setup_n8n.sh`. Generation remains opt-in; provider keys belong only to the services that need them. Workflows embed a trusted processor address instead of reading environment variables; node environment access is blocked. Local HTTP/cookie settings are for loopback development only.

Migrations are additive and versioned (`python -m scripts.migrate`). SQLite uses WAL/busy timeout and serialized migration initialization; PostgreSQL uses transaction-scoped advisory locking. Back up before upgrading. Never reset/reseed old data or reuse the original assessment's database. Histories/reviews are retained; approve retention/backups before real deployment.

## Hosting options

| Option | Benefit | Operational cost/constraint |
| --- | --- | --- |
| Community Cloud + separately hosted n8n/processor/PostgreSQL | Easy Streamlit release flow | Three-service integration, cross-provider reachability, model cold starts, durable DB still required |
| One container provider, separate app/processor/n8n services + managed DB | Shared region/private networking, simpler secret/operations ownership | Multiple service allocations; persistent n8n data and realistic compute budget |
| Private container host running the full stack + managed DB | Closest to tested Compose topology, precise network/gateway control | Host patching/backups/TLS/monitoring become your responsibility |
| App + processor in one supervised container, separate n8n/DB | Fewer Python compute allocations | Requires a supported private secondary listener and reviewed process supervisor; not assumed from a free web tier |

Recommendation: one container provider/private network with dedicated PostgreSQL, or a reviewed private container host matching Compose. Prefer predictable capacity over a fragile chain of unrelated free services. Consolidating Python processes can be evaluated later if platform port/process guarantees and operating budget justify it; it was not needed to validate this iteration.

Current official references checked for preparation:

- [Streamlit deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) and [secrets](https://docs.streamlit.io/deploy/concepts/secrets): configure app entrypoint/dependencies and server secrets. Community Cloud does not host companion n8n.
- [Render private networking](https://render.com/docs/private-network): same-region services can communicate privately; free web services cannot receive private requests. Do not assume an arbitrary second private listener works on a free app.
- [Render persistent disks](https://render.com/docs/disks): persistent disks require an eligible paid service. Review the [pricing page](https://render.com/pricing) for actual compute/storage allocations.
- [n8n security settings](https://docs.n8n.io/hosting/configuration/environment-variables/security/): node environment access can be blocked, and production cookies require HTTPS.

Exact current prices/account entitlements could not be established reliably from the accessible pricing content, so no monthly total or free entitlement is invented. Budget app memory, processor, n8n, DB/storage, backups, egress and domain costs separately, using the recorded local sample as a sizing observation rather than a hosted guarantee.

## Precise next-phase checklist — do not execute yet

1. Approve provider, region, services, domain and spending limit; review access to synthetic versus real data.
2. Publish the reviewed iteration only after push approval. No existing Render service should be touched.
3. Provision a **new** dedicated managed PostgreSQL role/database with TLS. Apply additive migrations and test backup restoration.
4. Host app, processor and n8n with private networking. Keep processor and n8n editor inaccessible publicly; use SSH/VPN for editor administration.
5. Configure demo access password or proper identity/tenant controls, independent tokens/encryption key, provider budgets and retention.
6. Generate workflows with the approved processor URL. Import/publish through the protected editor/CLI; delete temporary plaintext credential imports.
7. Configure publicly reachable HTTPS production webhooks. The prepared gateway permits only those two paths; never expose the editor through it.
8. Provide an approved controlled HTTPS event source if required. Do not relabel the local synthetic service as a hosted third-party source.
9. Validate model cold start, memory, source bounds, auth, all scenarios, agent citations/tools, exports, reviews/history and restart/reconciliation in the target environment.
10. Record actual deployment revision/URL and observed hosted CI run. Until then label hosted status pending.

`deploy/compose.hosted.yaml`, `deploy/Caddyfile` and `deploy/README.md` are prepared configuration, not hosted-verified artifacts. Commercial operation additionally needs proper identities/tenancy, monitored recovery/queues, external n8n runners, tested backups and retention policy.
