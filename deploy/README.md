# Release preparation — no deployment performed

The authoritative instructions are [Iteration 003 deployment runbook](../docs/iterations/003/DEPLOYMENT_RUNBOOK.md). The owner's budget is **R0/$0 ongoing**, with no paid upgrade, trial-credit dependence, account/resource creation or DNS change in this iteration.

Primary conditional hosting: Oracle Always Free ARM + new Neon Free project + optional Personal Funnel provider HTTPS hostname. Eligibility/capacity and Gemini free-tier billing status are unverified; Gemini remains disabled. [Verified hosting comparison](../docs/iterations/003/HOSTING_OPTIONS.md).

- `compose.hosted.yaml`: standalone six-service production definition, dedicated external verified-TLS PostgreSQL, no public backend/editor/webhook ports.
- `compose.funnel.yaml`: only a loopback app gateway for a separately owner-approved free provider tunnel; does not start a tunnel/account.
- `compose.rehearsal.yaml`: local-only new PostgreSQL/restore services and loopback ports; never use on a public host.
- `production.env.example`, `prepare_environment.py`, `check.py`: private configuration/inventory/topology checks; no cloud provisioning.
- `database.py`: connectivity/schema/role/TLS/migrations, transactional permission probe and explicit backup/empty-target restore.
- `publish.py`: repeatable encrypted credential binding, workflow manifests/import/publication and deliberate restart; no automatic replay.
- `smoke.py`, `rehearse.py`, `release_manifest.py`: actual local acceptance/public read-only checks/traceable source hashes.

Quick local validation: `python -m deploy.ci_check`. Full rehearsal commands, safety boundaries, backups, rollback, monitoring and exact future deployment steps are in the runbook and linked documents. Existing local `compose.yaml` remains development-only. Never remove volumes to initialize or reuse the original application's environment/database/services.
