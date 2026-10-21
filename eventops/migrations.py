"""Additive, versioned SQLAlchemy migrations. No destructive bootstrap/downgrade."""

from sqlalchemy import Column, Integer, MetaData, String, Table, inspect, select, text

VERSION = 2


def upgrade(engine, metadata):
    with engine.begin() as conn:
        if engine.dialect.name == "sqlite":
            conn.exec_driver_sql("BEGIN IMMEDIATE")
        if engine.dialect.name == "postgresql":
            conn.execute(text("SELECT pg_advisory_xact_lock(73592002)"))
        ledger = Table(
            "companion_schema_versions",
            MetaData(),
            Column("version", Integer, primary_key=True),
            Column("description", String(200), nullable=False),
        )
        ledger.create(conn, checkfirst=True)
        applied = set(conn.execute(select(ledger.c.version)).scalars())
        metadata.create_all(conn)
        if 1 not in applied:
            conn.execute(
                ledger.insert().values(version=1, description="Existing companion objects retained unchanged")
            )
        if 2 not in applied:
            columns = {c["name"] for c in inspect(conn).get_columns("companion_objects")}
            if "revision" not in columns:
                conn.execute(
                    text("ALTER TABLE companion_objects ADD COLUMN revision INTEGER NOT NULL DEFAULT 0")
                )
            conn.execute(
                ledger.insert().values(
                    version=2, description="Optimistic object revisions and investigation claims"
                )
            )
