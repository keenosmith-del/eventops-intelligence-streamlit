"""Safe DB preflight/migration/probe and explicit backup/empty-target restore."""

import argparse
import hashlib
import json
import os
import subprocess
import uuid
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from eventops.migrations import VERSION
from eventops.operations import validate_database
from eventops.store import Store

TABLES = {"companion_objects", "companion_schema_versions", "companion_investigations"}


def inspect_database(url, apply=False, probe=False, rehearsal=False):
    validate_database(url, production=not rehearsal)
    engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
    with engine.connect() as c:
        c.execute(text("SELECT 1"))
        server_version = int(c.execute(text("SHOW server_version_num")).scalar())
        if not 170000 <= server_version < 180000:
            raise ValueError("This release rehearses PostgreSQL 17 and its matching backup client")
        role = c.execute(
            text("SELECT rolsuper,rolcreatedb,rolcreaterole FROM pg_roles WHERE rolname=current_user")
        ).one()
        if any(role):
            raise ValueError("The application role must not be superuser/CREATEDB/CREATEROLE")
        tls = c.execute(text("SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()")).scalar()
        if not rehearsal and not tls:
            raise ValueError("The hosted database connection is not encrypted")
    if apply:
        Store(url)
    with engine.connect() as c:
        tables = set(inspect(c).get_table_names())
        versions = (
            list(c.execute(text("SELECT version FROM companion_schema_versions ORDER BY version")).scalars())
            if "companion_schema_versions" in tables
            else []
        )
        indexes = inspect(c).get_indexes("companion_objects") if "companion_objects" in tables else []
        counts = {
            table: c.execute(text("SELECT count(*) FROM " + table)).scalar()
            for table in sorted(TABLES & tables)
        }
    if probe:
        if not TABLES <= tables or versions != list(range(1, VERSION + 1)):
            raise ValueError("Apply required additive migrations before permission probing")
        with engine.connect() as c:
            tx = c.begin()
            key = "release-probe-" + uuid.uuid4().hex
            c.execute(
                text(
                    "INSERT INTO companion_objects(id,owner,kind,created_at,payload) VALUES(:id,'release-preflight','probe','release','{}')"
                ),
                {"id": key},
            )
            assert (
                c.execute(text("SELECT id FROM companion_objects WHERE id=:id"), {"id": key}).scalar() == key
            )
            tx.rollback()
    engine.dispose()
    return {
        "connected": True,
        "postgres_major": server_version // 10000,
        "encrypted": bool(tls),
        "least_privilege_role": True,
        "schema_versions": versions,
        "schema_current": versions == list(range(1, VERSION + 1)),
        "required_tables_present": TABLES <= tables,
        "object_indexes": [i["name"] for i in indexes],
        "row_counts": counts,
        "write_probe_rolled_back": probe,
    }


def archive(url, output, network, restore=False, confirmation=None):
    u = make_url(url)
    if restore:
        if confirmation != u.database:
            raise ValueError("Restore requires the exact destination database name as confirmation")
    env = dict(os.environ)
    pairs = {
        "PGHOST": u.host,
        "PGPORT": str(u.port or 5432),
        "PGUSER": u.username,
        "PGPASSWORD": u.password,
        "PGDATABASE": u.database,
        "PGSSLMODE": u.query.get("sslmode", "prefer"),
    }
    if u.query.get("sslrootcert"):
        pairs["PGSSLROOTCERT"] = u.query["sslrootcert"]
    env.update({k: str(v) for k, v in pairs.items() if v})
    command = ["docker", "run", "--rm", "-i", "--network", network]
    for key in pairs:
        command += ["-e", key]
    command += ["postgres:17.9-alpine"]
    if restore:
        query = "SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')"
        count = subprocess.check_output(
            command + ["psql", "-Atc", query], env=env, stderr=subprocess.PIPE, text=True
        ).strip()
        if count != "0":
            raise ValueError("Restore refuses a nonempty destination; never overwrite a live database")
    command += ["pg_restore" if restore else "pg_dump"]
    command += ["--no-owner", "--no-acl"]
    if restore:
        command += ["--exit-on-error", "--single-transaction", "--dbname", u.database]
        with output.open("rb") as source:
            subprocess.run(
                command, stdin=source, env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
            )
    else:
        command += ["--format=custom"]
        output.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "wb") as target:
                subprocess.run(command, stdout=target, stderr=subprocess.PIPE, env=env, check=True)
        except Exception:
            output.unlink(missing_ok=True)
            raise
    return {
        "operation": "restored_empty_destination" if restore else "backup_created",
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "bytes": output.stat().st_size,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("check", "migrate", "verify", "backup", "restore"))
    p.add_argument("--env-file", type=Path)
    p.add_argument("--rehearsal", action="store_true")
    p.add_argument("--file", type=Path)
    p.add_argument("--network", default="bridge")
    p.add_argument("--confirm-empty-database")
    args = p.parse_args()
    values = dotenv_values(args.env_file) if args.env_file else os.environ
    url = values.get("EVENTOPS_DATABASE_URL")
    try:
        if args.action in ("backup", "restore"):
            if not args.file:
                p.error("Backup/restore requires --file")
            validate_database(url, production=not args.rehearsal)
            result = archive(
                url, args.file, args.network, args.action == "restore", args.confirm_empty_database
            )
        else:
            result = inspect_database(url, args.action == "migrate", args.action == "verify", args.rehearsal)
        print(json.dumps(result, indent=2))
        if args.action in ("migrate", "verify") and not result["schema_current"]:
            raise SystemExit(1)
    except Exception as exc:
        # Driver errors can contain credentials/URLs. Class is sufficient for operator triage.
        print(json.dumps({"status": "failed", "error_category": type(exc).__name__, "action": args.action}))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
