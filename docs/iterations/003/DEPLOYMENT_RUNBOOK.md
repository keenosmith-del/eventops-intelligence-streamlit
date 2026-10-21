# Authoritative release runbook — preparation only

**Do not execute cloud setup now.** The owner set a strict R0/$0 budget and explicitly withheld deployment, account/resource creation and DNS changes. This runbook is the next-iteration procedure after approval, not evidence of a hosted app. Commits/pushes of reviewed preparation are authorized. Primary/fallback and current free quotas are in [hosting options](HOSTING_OPTIONS.md).

## Owner eligibility gates

1. Obtain an available Oracle **Always Free-only** ARM host in the home region, within the currently documented allocation; no PAYG upgrade, promotional-only shape, paid image/disk/load balancer or excess networking. Check actual console resource/IP/storage labels and reject any nonzero estimate. If free capacity is unavailable, stop: no paid substitution.
2. Obtain a **new Neon Free project**, PostgreSQL17 and a dedicated least-privilege role. Do not reuse any original database/project, secret or app service. Confirm account-wide quota headroom and keep the plan on Free.
3. For a provider URL, use an eligible Tailscale Personal account and a newly approved host identity/Funnel. No application account is created by these scripts. Account/terms/identity setup is owner-operated. Alternatively approve the optional existing-domain DNS change later; no purchase is necessary.
4. Gemini stays disabled until the owner can confirm billing-disabled Free. Do not upgrade/enable billing for acceptance. Confirm the existing Mailtrap sandbox's Free plan/API-read quota. Approve the shared reviewer gate and n8n execution retention.

## Host and release preparation

Use an independent Linux ARM64 host, for example a reviewed Ubuntu image with Python3.12 and current Docker Compose (`!override` support). Install through official OS/vendor repositories after account approval. Allow restricted SSH only; keep all app ports closed in Funnel mode. Permit required outbound HTTPS and Neon5432. Docker creates its own forwarding rules; use the provider firewall and verify published bindings instead of relying solely on a host firewall's defaults. Maintain OS/Docker updates and disk/log/backup monitoring.

On that host, clone the public repository and check out the exact approved release commit. No registry push is needed: build locally from that revision. From the repository root:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
# Use the actual owner-approved provider URL, without a path or secret.
.venv/bin/python -m deploy.prepare_environment --site https://APPROVED-HOST.TAILNET.ts.net
```

The generator refuses an existing file or dirty source and creates independent secrets privately. Add the **new** database URI and approved Mailtrap inputs to ignored `deploy/production.env` through a secure editor. Existing approved companion provider inputs may be copied only by explicitly passing `--approved-provider-env`; database/encryption settings are never copied. Keep `GEMINI_ENABLED=false` and `GEMINI_FREE_TIER_CONFIRMED=false` while billing is unknown. Never print the file or rendered secret-bearing Compose output.

```bash
.venv/bin/python -m deploy.check --env-file deploy/production.env --funnel
.venv/bin/pytest -q
.venv/bin/ruff check app.py eventops scripts tests deploy
.venv/bin/python scripts/build_workflows.py --check
.venv/bin/python -m deploy.release_manifest --output deploy/.local/release-manifest.json
mkdir -p deploy/.local/workflows
docker compose --env-file deploy/production.env -f deploy/compose.hosted.yaml -f deploy/compose.funnel.yaml build
```

Preflight checks values, verified-TLS database configuration, bounds, distinct secrets and topology; it does not verify DNS, account cost or provider reachability. Review the new role/project identity separately.

## Migrate and start privately

Follow [database procedures](DATABASE_AND_BACKUPS.md) to check, migrate and verify. Those one-off processor commands use `--no-deps`, so no gateway is started. Take a backup before every upgrade. Then:

```bash
docker compose --env-file deploy/production.env -f deploy/compose.hosted.yaml -f deploy/compose.funnel.yaml up -d app processor scenario n8n runners
.venv/bin/python -m deploy.publish --env-file deploy/production.env --publish
docker compose --env-file deploy/production.env -f deploy/compose.hosted.yaml -f deploy/compose.funnel.yaml ps
```

Verify private webhook/service auth and controlled source processing as in [smoke tests](SMOKE_TESTS.md). Confirm the fixture is labelled synthetic, Mailtrap is read-only, exports match persistence and history/reviews recover. Keep the editor/broker/processor private. Observe runner registration and actual Code-node execution, not just container existence.

## Expose only the reviewed app — requires deployment approval

After private acceptance, start the loopback gateway:

```bash
docker compose --env-file deploy/production.env -f deploy/compose.hosted.yaml -f deploy/compose.funnel.yaml up -d gateway
```

The owner installs/authenticates the official Tailscale daemon on the **new** host and approves MagicDNS/HTTPS/Funnel for that host. The following command is prepared from current official CLI documentation; it has **not** been executed:

```bash
tailscale funnel --bg 8505
tailscale funnel status
```

This publishes the guarded loopback gateway at the host's provider-issued HTTPS name. Do not publish5678,5679,8766,8090,5432 or any whole private subnet. Confirm the resulting public name matches `APP_SITE`. Funnel is beta and bandwidth-limited; approval of its public node attribute is a deliberate security change. No tunnel is opened by the local rehearsal.

```bash
.venv/bin/python -m deploy.smoke --url https://APPROVED-HOST.TAILNET.ts.net --output deploy/.local/public-smoke.json
```

Use a real browser for password rejection/acceptance, workspace isolation/recovery, websocket operation, exports and source results. Verify actual TLS, firewall bindings, provider quotas and restart persistence. Only after free-tier/billing confirmation deliberately enable both Gemini flags, recreate app/processor and run one grounded answer plus one analyst with observed citations/tools. If not confirmed, model functions remain unavailable and the public AI assessment is not fully accepted.

For the optional future `eventops-streamlit.kailor.co.za`, obtain explicit DNS approval and point only the new subdomain at the new host. Use `compose.hosted.yaml` without the Funnel overlay, set `APP_SITE` to that HTTPS origin, allow80/443 and validate Caddy ACME/renewal. Do not run two TLS ingress systems for the same listener and do not modify other DNS records.

## Handover and recurring operation

Record source/image/workflow hashes, actual URL, cloud plan/limits, account owner, public smoke, reviewer access instructions and backup/restore evidence. Save workspace capabilities privately. Stop for any quota exhaustion/nonzero price instead of upgrading. Use the incident procedures in [smoke/operations](SMOKE_TESTS.md) and [rollback](ROLLBACK.md). No automatic deploy-on-push exists.
