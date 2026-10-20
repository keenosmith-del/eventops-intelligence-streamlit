"""Owner-scoped JSON persistence, atomic idempotency and daily budgets."""

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    select,
    update,
)
from sqlalchemy.exc import IntegrityError

from eventops.config import ROOT, database_url


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, url=None):
        (ROOT / "storage").mkdir(exist_ok=True)
        self.engine = create_engine(
            url or database_url(),
            **(
                {"connect_args": {"check_same_thread": False}}
                if (url or database_url()).startswith("sqlite:")
                else {}
            ),
        )
        metadata = MetaData()
        self.objects = Table(
            "companion_objects",
            metadata,
            Column("id", String(160), primary_key=True),
            Column("owner", String(80), nullable=False, index=True),
            Column("kind", String(30), nullable=False),
            Column("created_at", String(40), nullable=False),
            Column("payload", Text, nullable=False),
        )
        metadata.create_all(self.engine)

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
                .values(payload=json.dumps(payload))
            )
            if result.rowcount != 1:
                raise KeyError("Record not found for this workspace")

    def get(self, owner, object_id):
        with self.engine.connect() as conn:
            row = (
                conn.execute(
                    select(self.objects).where(
                        self.objects.c.id == object_id, self.objects.c.owner == owner
                    )
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
