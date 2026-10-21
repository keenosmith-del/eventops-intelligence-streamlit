"""Protected structured additions scoped to a workspace; never authoritative identity data."""

import csv
import io
import json
import re

from eventops.config import setting
from eventops.knowledge import fingerprint, load_documents


def validate_upload(filename, content, mapping=None):
    if len(content) > 200_000 or not re.fullmatch(r"[\w.-]{1,80}\.(csv|json)", filename):
        raise ValueError("Use a bounded CSV/JSON document with a simple filename")
    if filename.endswith(".csv"):
        if not mapping or not {"id", "kind", "scope", "content"} <= set(mapping):
            raise ValueError("CSV requires explicit id/kind/scope/content column mapping")
        raw = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
        rows = [{key: row.get(column) for key, column in mapping.items()} for row in raw]
        document = {"schema_version": 1, "document_id": filename[:-4], "version": "1", "records": rows}
    else:
        document = json.loads(content)
    if (
        not isinstance(document, dict)
        or document.get("schema_version") != 1
        or not isinstance(document.get("document_id"), str)
        or not re.fullmatch(r"[\w-]{1,50}", document.get("document_id", ""))
        or not str(document.get("version", ""))
    ):
        raise ValueError("Expected schema_version 1, stable document_id and version")
    rows = document.get("records")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 50:
        raise ValueError("Provide 1–50 records")
    result = []
    seen = set()
    known = {r["id"] for r in load_documents() if r["kind"] == "event"} | {"ALL"}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each record must be a structured object")
        rid = str(row.get("id", ""))
        scope = row.get("scope", [])
        if isinstance(scope, str):
            scope = [s.strip() for s in scope.split(",")]
        if (
            not re.fullmatch(r"[\w-]{1,60}", rid)
            or rid in seen
            or row.get("kind") not in ("event", "policy", "participant")
            or not isinstance(scope, list)
            or not scope
            or not all(isinstance(item, str) for item in scope)
            or not set(scope) <= known
            or not isinstance(row.get("content"), str)
            or not 1 <= len(row["content"]) <= 5000
        ):
            raise ValueError("Invalid/duplicate record ID, kind, scope or bounded content")
        seen.add(rid)
        result.append(
            {
                "id": f"USR-{document['document_id']}-{rid}",
                "kind": row["kind"],
                "scope": scope,
                "content": row["content"],
                "fields": {},
                "source": f"{filename}#id={rid}",
                "document_version": str(document["version"]),
                "trust": "workspace supplemental knowledge; not verification authority",
            }
        )
    return {
        "document_id": document["document_id"],
        "version": str(document["version"]),
        "records": result,
        "fingerprint": fingerprint(result),
        "filename": filename,
    }


def put_document(store, owner, filename, content, mapping=None):
    if setting("KNOWLEDGE_ADMIN_ENABLED") != "true":
        raise PermissionError("Knowledge administration is disabled")
    doc = validate_upload(filename, content, mapping)
    import hashlib

    key = "document-" + hashlib.sha256((owner + doc["document_id"]).encode()).hexdigest()
    current = store.get(owner, key)
    if current and current["payload"]["fingerprint"] == doc["fingerprint"]:
        return {"changed": False, **doc}
    doc["active"] = True
    if current:
        store.save(owner, "document_audit", current["payload"])
        store.replace(owner, key, doc)
    else:
        store.save(owner, "document", doc, key)
    return {"changed": True, **doc}


def workspace_records(store, owner):
    return load_documents() + [
        r
        for item in store.list(owner, "document", 100)
        if item["payload"].get("active")
        for r in item["payload"]["records"]
    ]


def remove_document(store, owner, key):
    if setting("KNOWLEDGE_ADMIN_ENABLED") != "true":
        raise PermissionError("Knowledge administration is disabled")
    current = store.get(owner, key)
    if not current or current["kind"] != "document":
        raise KeyError("Document not found")
    store.save(owner, "document_audit", current["payload"])
    store.mutate(owner, key, lambda p: {**p, "active": False})
