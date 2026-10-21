# Database, migrations, backups and restoration

Use a **new Neon Free project** and PostgreSQL17, separate from every original EventOps database/role. Keep the account on Free; never upgrade for quota or use an expiring database trial. Confirm spare account-wide limits without modifying existing projects. Use verified TLS over the new public endpoint; Neon private networking is not assumed on Free.

## Provisioning preparation — owner-operated next iteration

Create the new project/database through the owner console after approval. Create a dedicated app role with no superuser/CREATEDB/CREATEROLE rights. In this **new** database only, an owner can prepare:

```sql
CREATE ROLE eventops_streamlit LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
GRANT CONNECT ON DATABASE neondb TO eventops_streamlit;
GRANT USAGE, CREATE ON SCHEMA public TO eventops_streamlit;
```

Set its password through the new project's secure role controls or interactive `psql` `\password eventops_streamlit`; do not put the password in a shell argument or tracked SQL. Use the actual new database name if it differs from `neondb`. The app role owns its application tables so additive migrations work, but has no reason to administer other databases. `EVENTOPS_DATABASE_URL` must use `postgresql+psycopg` and `sslmode=verify-full&sslrootcert=system`. Never paste the URI into chat, logs or a public command.

The release preflight checks role flags, encrypted connection, PostgreSQL major, migration versions, required tables/indexes and read/write permissions. The rolled-back permission probe leaves no audit/test row. The supported backup client is PostgreSQL17.9; choosing a newer database major requires a reviewed matching client and another restore test.

## Exact operational commands

After the clean release/environment preparation in the runbook, from the repository root:

```bash
# Read connectivity/current versions without applying migrations.
docker compose --env-file deploy/production.env -f deploy/compose.hosted.yaml run --rm --no-deps processor python -m deploy.database check
# Transactional, additive migration and version verification.
docker compose --env-file deploy/production.env -f deploy/compose.hosted.yaml run --rm --no-deps processor python -m deploy.database migrate
# Required tables/indexes, safe read/write probe, least-privilege/TLS checks.
docker compose --env-file deploy/production.env -f deploy/compose.hosted.yaml run --rm --no-deps processor python -m deploy.database verify
# New exclusive mode0600 custom-format dump; refuses an existing output file.
.venv/bin/python -m deploy.database backup --env-file deploy/production.env --file deploy/.local/pre-release.dump
```

Use the Funnel overlay for service startup; DB operation containers need no ingress. `--no-deps` avoids accidentally publishing a gateway or starting unrelated services. Migrations use a transaction-scoped PostgreSQL advisory lock and preserve existing IDs/payloads. Application startup applies the same additive migrations; preflight is still required so failures happen before public exposure. A ledger newer than the running release is rejected. There is no destructive downgrade/reset/reseed command.

The backup helper passes libpq settings by environment-variable names to a disposable official PostgreSQL client. It never places the secret URI/password in argv. Custom archives are consistent `pg_dump` snapshots; the role needs read access to its own tables. Backups contain private workspace capabilities and synthetic evidence: mode0600 is necessary, but encrypt and copy them off-host as well.

## Explicit empty-destination restore

Use a separately prepared private restore environment file pointing to a **new empty** database. Never point it at the live DB. The command requires the exact destination name and refuses any non-system table:

```bash
.venv/bin/python -m deploy.database restore --env-file deploy/restore.env --file deploy/.local/pre-release.dump --confirm-empty-database NEW_EMPTY_DATABASE_NAME
```

`restore.env` is Git-ignored; its URL also requires verified TLS. Restore is transactional and stops on the first error. Inspect the restored schema and compare row/payload hashes before any approved traffic cutover. Do not overwrite production to test recovery. Recovery to an earlier backup can lose newer changes and needs an explicit owner decision.

## n8n state and encryption key

n8n uses its own durable SQLite/state volume on the free host. Do **not** move a continuously polling n8n database onto Neon Free without measuring its compute cost. Stop n8n and the runner for a consistent state backup; copy the complete `.n8n` directory, including SQLite WAL/SHM and configuration, plus the matching private environment/encryption key. Workflow JSON alone does not preserve execution history or decrypt credentials. Restrict the copied folder to0700. Store encrypted off-host copies and a recovery copy of the exact application/workflow manifests.

The local rehearsal takes a stopped-state backup, restarts n8n with the same key, and exercises a token-authenticated workflow again. Full hosted n8n-volume restoration into a replacement host remains a next-phase acceptance check; no production volume is overwritten here.

## Observed restoration and free-tier operation

Actual isolated PostgreSQL17 rehearsal restored a real custom archive into a new empty database; object payloads, review entries and investigation claims matched by hash. The app role was non-superuser and permission probing rolled back. Existing Iteration 002 volumes were not touched. Local PostgreSQL transport was private HTTP-hosted-network TCP without TLS; **remote Neon TLS/backup restoration is pending**, not inferred from that test.

Neon Free currently scales down after five inactive minutes and caps compute/storage/transfer. Scheduled database health queries can keep it awake and consume the monthly budget, so recurring Docker health is liveness only; `/readyz` is authenticated/on-demand, with one DB check at process startup. Observe actual usage; do not add synthetic keepalive traffic. DB quota/unavailability returns a sanitized failure and requires reconciliation before replay. Companion histories/reviews are retained; no automatic silent deletion policy was introduced.
