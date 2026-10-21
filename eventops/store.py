"""Owner-scoped JSON persistence, atomic idempotency and daily budgets."""

import json
import threading
import uuid
from datetime import datetime, timezone
from functools import lru_cache

from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    event,
    select,
    update,
)
from sqlalchemy.exc import IntegrityError

from eventops.config import ROOT, database_url


def now():
    return datetime.now(timezone.utc).isoformat()


_initialization_lock = threading.RLock()


@lru_cache(maxsize=64)
def connection(url):
    with _initialization_lock:
        engine = create_engine(
            url,
            pool_pre_ping=True,
            **(
                {"connect_args": {"check_same_thread": False, "timeout": 15}}
                if url.startswith("sqlite:")
                else {"pool_size": 3, "max_overflow": 2, "connect_args": {"connect_timeout": 5}}
            ),
        )
        if url.startswith("sqlite:"):

            @event.listens_for(engine, "connect")
            def configure_sqlite(dbapi_connection, record):
                dbapi_connection.execute("PRAGMA busy_timeout=15000")
                dbapi_connection.execute("PRAGMA journal_mode=WAL")

        metadata = MetaData()
        objects = Table(
            "companion_objects",
            metadata,
            Column("id", String(160), primary_key=True),
            Column("owner", String(80), nullable=False, index=True),
            Column("kind", String(30), nullable=False, index=True),
            Column("created_at", String(40), nullable=False),
            Column("payload", Text, nullable=False),
            Column("revision", Integer, nullable=False, server_default="0"),
        )
        claims = Table(
            "companion_investigations",
            metadata,
            Column("id", String(64), primary_key=True),
            Column("owner", String(80), nullable=False),
            Column("state", String(30), nullable=False),
            Column("created_at", String(40), nullable=False),
            Column("payload", Text, nullable=False),
        )
        from eventops.migrations import upgrade

        upgrade(engine, metadata)
        return engine, objects, claims


class Store:
    def __init__(self, url=None):
        (ROOT / "storage").mkdir(exist_ok=True)
        self.engine, self.objects, self.claims = connection(url or database_url())

    def save(self, owner, kind, payload, object_id=None):
        object_id = object_id or str(uuid.uuid4())
        with self.engine.begin() as conn:
            conn.execute(
                self.objects.insert().values(
                    id=object_id,
                    owner=owner,
                    kind=kind,
                    created_at=now(),
                    payload=json.dumps(payload),
                )
            )
        return object_id

    def replace(self, owner, object_id, payload):
        with self.engine.begin() as conn:
            result = conn.execute(
                update(self.objects)
                .where(self.objects.c.id == object_id, self.objects.c.owner == owner)
                .values(payload=json.dumps(payload), revision=self.objects.c.revision + 1)
            )
            if result.rowcount != 1:
                raise KeyError("Record not found for this workspace")

    def get(self, owner, object_id):
        with self.engine.connect() as conn:
            row = (
                conn.execute(
                    select(self.objects).where(self.objects.c.id == object_id, self.objects.c.owner == owner)
                )
                .mappings()
                .first()
            )
        return {**dict(row), "payload": json.loads(row["payload"])} if row else None

    def list(self, owner, kind, limit=50):
        with self.engine.connect() as conn:
            rows = (
                conn.execute(
                    select(self.objects)
                    .where(self.objects.c.owner == owner, self.objects.c.kind == kind)
                    .order_by(self.objects.c.created_at.desc())
                    .limit(limit)
                )
                .mappings()
                .all()
            )
        return [{**dict(r), "payload": json.loads(r["payload"])} for r in rows]

    def reserve(self, namespace, key, payload):
        try:
            self.save(namespace, "reservation", payload, f"{namespace}:{key}")
            return True
        except IntegrityError:
            return False

    def budget(self, namespace, limit):
        day = now()[:10]
        for slot in range(limit):
            if self.reserve("budget", f"{namespace}:{day}:{slot}", {}):
                return True
        return False

    def mutate(self, owner, object_id, transform, attempts=12):
        """Compare-and-swap prevents stale writers from losing newer evidence."""
        for _ in range(attempts):
            current = self.get(owner, object_id)
            if not current:
                raise KeyError("Record not found for this workspace")
            payload = transform(current["payload"])
            with self.engine.begin() as conn:
                result = conn.execute(
                    update(self.objects)
                    .where(
                        self.objects.c.id == object_id,
                        self.objects.c.owner == owner,
                        self.objects.c.revision == current["revision"],
                    )
                    .values(payload=json.dumps(payload), revision=current["revision"] + 1)
                )
                if result.rowcount == 1:
                    return payload
        raise RuntimeError("Concurrent update; retry this operation")

    def review(self, owner, run_id, record_id, status, note, reason, next_action="", correction=None):
        if (
            status not in ("unreviewed", "investigating", "resolved_with_note")
            or not note.strip()
            or not reason.strip()
        ):
            raise ValueError("Review needs an allowed status, a note and a reason")
        entry = {
            "run_id": run_id,
            "record_id": record_id,
            "review_status": status,
            "note": note[:2000],
            "reason": reason[:1000],
            "next_action": next_action[:1000],
            "correction": correction or {},
            "resolved": status == "resolved_with_note",
            "at": now(),
            "reviewer": "workspace capability holder; not an authenticated employee",
        }
        for _ in range(12):
            current = self.get(owner, run_id)
            if not current or current["kind"] != "run":
                raise KeyError("Run not found")
            payload = current["payload"]
            record = next((r for r in payload["records"] if r["id"] == record_id), None)
            if not record:
                raise KeyError("Record not found")
            record["review_status"] = status
            with self.engine.begin() as conn:
                result = conn.execute(
                    update(self.objects)
                    .where(
                        self.objects.c.id == run_id,
                        self.objects.c.owner == owner,
                        self.objects.c.revision == current["revision"],
                    )
                    .values(payload=json.dumps(payload), revision=current["revision"] + 1)
                )
                if result.rowcount:
                    conn.execute(
                        self.objects.insert().values(
                            id=str(uuid.uuid4()),
                            owner=owner,
                            kind="review",
                            created_at=entry["at"],
                            payload=json.dumps(entry),
                        )
                    )
                    return entry
        raise RuntimeError("Concurrent review; retry")

    def claim_investigation(self, owner, key):
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    self.claims.insert().values(
                        id=key, owner=owner, state="running", created_at=now(), payload="{}"
                    )
                )
            return {"claimed": True}
        except IntegrityError:
            with self.engine.connect() as conn:
                row = (
                    conn.execute(
                        select(self.claims).where(self.claims.c.id == key, self.claims.c.owner == owner)
                    )
                    .mappings()
                    .first()
                )
            return {
                "claimed": False,
                "state": row["state"] if row else "unavailable",
                "result": json.loads(row["payload"]) if row else {},
            }

    def finish_investigation(self, owner, key, result):
        with self.engine.begin() as conn:
            conn.execute(
                update(self.claims)
                .where(
                    self.claims.c.id == key, self.claims.c.owner == owner, self.claims.c.state == "running"
                )
                .values(state=result["status"], payload=json.dumps(result))
            )
