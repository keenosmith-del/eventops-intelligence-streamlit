"""Validated structured rows with stable, record-level provenance."""

import csv
import hashlib
import json
import re
from datetime import datetime

from eventops.config import ROOT


def load_documents(directory=None):
    directory = directory or ROOT / "data/structured"
    events = list(csv.DictReader((directory / "events.csv").open()))
    policies = list(csv.DictReader((directory / "policies.csv").open()))
    doc = json.loads((directory / "directory.json").read_text())
    if doc.get("schema_version") != 1:
        raise ValueError("Unsupported directory schema")
    people = doc["participants"]
    records = []
    ids = set()
    event_ids = {e["event_id"] for e in events}
    for filename, kind, rows, id_key in [
        ("events.csv", "event", events, "event_id"),
        ("policies.csv", "policy", policies, "policy_id"),
        ("directory.json", "participant", people, "participant_id"),
    ]:
        for row in rows:
            row = {k: v.strip() if isinstance(v, str) else v for k, v in row.items()}
            rid = row[id_key]
            if rid in ids or not rid:
                raise ValueError("Duplicate or missing source identifier")
            ids.add(rid)
            if kind == "event":
                if (
                    not re.fullmatch(r"EVT-\d{3}", rid)
                    or not row["title"]
                    or not row["venue"]
                ):
                    raise ValueError("Malformed event")
                start, end = [
                    datetime.fromisoformat(row[k]) for k in ("starts_at", "ends_at")
                ]
                if (
                    start.utcoffset() is None
                    or end.utcoffset() is None
                    or end <= start
                    or int(row["capacity"]) < 1
                ):
                    raise ValueError("Invalid event schedule or capacity")
                scope = [rid]
                content = f"Event {rid}: {row['title']}. Starts at: {row['starts_at']}. Ends at: {row['ends_at']}. Venue: {row['venue']}. Capacity: {row['capacity']}."
            elif kind == "policy":
                if (
                    row["event_id"] not in event_ids | {"ALL"}
                    or not row["rule_text"]
                    or not row["category"]
                ):
                    raise ValueError("Invalid policy")
                scope = [row["event_id"]]
                content = f"Policy {rid}. Applies to {row['event_id']}. Category {row['category']}. {row['rule_text']}"
            else:
                row["email"] = row["email"].casefold()
                if (
                    not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", row["email"])
                    or row["status"] not in ("active", "inactive")
                    or not row["full_name"]
                ):
                    raise ValueError("Invalid directory identity")
                if any(e not in event_ids for e in row["registered_events"]):
                    raise ValueError("Unknown registration event")
                scope = row["registered_events"]
                content = f"Participant {rid}: {row['full_name']}. Email: {row['email']}. Organization: {row['organization']}. Directory status: {row['status']}. Registered events: {', '.join(scope)}."
            records.append(
                {
                    "id": rid,
                    "kind": kind,
                    "scope": scope,
                    "content": content,
                    "fields": row,
                    "source": f"{filename}#{id_key}={rid}",
                }
            )
    if len(
        {r["fields"]["email"] for r in records if r["kind"] == "participant"}
    ) != len(people):
        raise ValueError("Duplicate directory email")
    return records


def fingerprint(records):
    return hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
