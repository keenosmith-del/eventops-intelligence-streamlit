"""Conservative deterministic operations; never trust an LLM verification verdict."""

import csv
import hashlib
import io
import json
import re
import unicodedata
from copy import deepcopy
from datetime import date, datetime, timezone
from html.parser import HTMLParser

from icalendar import Calendar

from eventops.knowledge import load_documents

FIELDS = ("event_id", "participant_id", "full_name", "email", "title", "starts_at", "venue")
EMAIL = re.compile(r"[^\s@;<>]+@[^\s@;<>]+\.[A-Za-z]{2,}")


def clean(value):
    return " ".join(unicodedata.normalize("NFKC", str(value or "")).split()).strip()


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.hidden = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1
        if tag in ("br", "p", "div", "li"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden = max(0, self.hidden - 1)
        if tag in ("p", "div", "li"):
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def extract_claim(body):
    if "<" in body:
        parser = VisibleText()
        parser.feed(body)
        body = "".join(parser.parts)
    values = {k: "" for k in FIELDS}
    issues = []
    ids = sorted(set("EVT-" + x for x in re.findall(r"\bEVT[\s-]?(\d{3})\b", body, re.I)))
    emails = sorted(set(x.casefold() for x in EMAIL.findall(body)))
    values["event_id"] = ids[0] if len(ids) == 1 else ""
    values["email"] = emails[0] if len(emails) == 1 else ""
    if len(ids) > 1:
        issues.append("ambiguous_event_id")
    if len(emails) > 1:
        issues.append("ambiguous_email")
    labels = {
        "full_name": r"(?:full[ _]?name|participant name|name)",
        "participant_id": r"participant[ _]?id",
        "title": r"(?:event[ _]?title|title)",
        "starts_at": r"(?:starts_at|event[ _]?date|date[ /]?time)",
        "venue": r"(?:location|venue)",
    }
    for field, label in labels.items():
        matches = re.findall(r"(?:^|[\n;])\s*" + label + r"\s*:\s*([^\n;]+)", body, re.I)
        if len(set(clean(x) for x in matches)) > 1:
            issues.append("ambiguous_" + field)
        elif matches:
            values[field] = matches[0]
    return {**values, "issues": issues, "extraction_method": "deterministic"}


def extract(payload, limit=3):
    source = payload["source"]
    if payload.get("status") != "completed":
        return []
    body = payload.get("body", "")
    if not isinstance(body, str) or len(body.encode()) > 512_000:
        raise ValueError("Source payload exceeds bounds")
    records = []

    def add(raw, rid, excerpt, reference=None):
        records.append(
            {
                **{k: raw.get(k, "") for k in FIELDS},
                "issues": raw.get("issues", []),
                "extraction_method": raw.get("extraction_method", "deterministic"),
                "source": source,
                "source_record_id": str(rid),
                "raw": deepcopy(raw),
                "evidence": [
                    {
                        "source": source,
                        "source_record_id": str(rid),
                        "reference": reference or payload.get("reference", ""),
                        "excerpt": excerpt[:12000],
                    }
                ],
            }
        )

    if source == "email":
        if not isinstance(payload.get("messages"), list):
            raise ValueError("Missing email messages array")
        for message in payload["messages"][:limit]:
            text = message["subject"] + "\n" + message["body"]
            add(extract_claim(text), message["id"], text, message["reference"])
    elif source == "calendar":
        if "BEGIN:VCALENDAR" not in body:
            raise ValueError("Expected iCalendar document")
        for component in Calendar.from_ical(body).walk("VEVENT")[:limit]:
            summary = str(component.get("SUMMARY", ""))
            description = str(component.get("DESCRIPTION", ""))
            start = component.get("DTSTART")
            raw = extract_claim(summary + "\n" + description)
            raw.update(
                title=summary,
                venue=str(component.get("LOCATION", "")),
                starts_at=start.dt.isoformat() if start else "",
            )
            add(
                raw,
                str(component.get("UID", "")) or hashlib.sha256(str(component).encode()).hexdigest()[:16],
                component.to_ical().decode(),
            )
    elif source == "web":
        items = json.loads(body)
        if isinstance(items, dict):
            items = items.get("records", [items])
        if not isinstance(items, list) or any(not isinstance(x, dict) for x in items):
            raise ValueError("Expected web JSON records")
        for i, item in enumerate(items[:limit]):
            raw = {k: item.get(k, "") for k in FIELDS}
            raw["title"] = raw["title"] or item.get("name", item.get("localName", ""))
            raw["starts_at"] = raw["starts_at"] or item.get("date", "")
            add(raw, item.get("id", i), json.dumps(item))
    else:
        raise ValueError("Unsupported source")
    return records


def normalize(records):
    output = []
    for source in records:
        r = deepcopy(source)
        for field in FIELDS:
            r[field] = clean(r.get(field))[:500]
        r["email"] = r["email"].casefold()
        r["event_id"] = re.sub(r"^EVT[\s-]?(\d{3})$", r"EVT-\1", r["event_id"], flags=re.I).upper()
        r["participant_id"] = r["participant_id"].upper()
        r["issues"] = list(r.get("issues", []))
        if r["email"] and not EMAIL.fullmatch(r["email"]):
            r["issues"].append("invalid_email")
        if r["event_id"] and not re.fullmatch(r"EVT-\d{3}", r["event_id"]):
            r["issues"].append("invalid_event_id")
        if r["starts_at"]:
            try:
                dt = datetime.fromisoformat(r["starts_at"].replace("Z", "+00:00"))
                if len(r["starts_at"]) > 10:
                    if dt.utcoffset() is None:
                        r["issues"].append("missing_timezone")
                    else:
                        r["starts_at"] = dt.astimezone(timezone.utc).isoformat()
                else:
                    r["starts_at"] = date.fromisoformat(r["starts_at"]).isoformat()
            except ValueError:
                r["issues"].append("invalid_timestamp")
        output.append(r)
    return output


def deduplicate(records):
    groups = {}
    for record in records:
        key = (
            (record["event_id"], record["email"])
            if record["email"] and record["event_id"]
            else (record["source"], record["source_record_id"])
        )
        if key not in groups:
            groups[key] = {
                **deepcopy(record),
                "inputs": [deepcopy(record)],
                "duplicate_count": 0,
                "conflicts": {},
            }
        else:
            existing = groups[key]
            existing["inputs"].append(deepcopy(record))
            existing["duplicate_count"] += 1
            existing["evidence"].extend(record["evidence"])
            existing["issues"].extend(record["issues"])
            for field in FIELDS:
                a, b = existing[field], record[field]
                if a and b and a.casefold() != b.casefold():
                    existing["conflicts"].setdefault(field, [a])
                    existing["conflicts"][field].append(b)
                    existing["issues"].append("conflicting_" + field)
                elif not a:
                    existing[field] = b
    result = []
    for key, r in groups.items():
        r["id"] = hashlib.sha256(json.dumps(key).encode()).hexdigest()[:20]
        r["issues"] = sorted(set(r["issues"]))
        r["duplicate_type"] = (
            "conflicting"
            if r["conflicts"]
            else "exact_or_complementary"
            if r["duplicate_count"]
            else "unique"
        )
        r["potentially_related"] = [
            v["source_record_id"]
            for v in records
            if v["source_record_id"] != r["source_record_id"]
            and v["full_name"]
            and v["full_name"].casefold() == r["full_name"].casefold()
            and v["email"] != r["email"]
        ]
        result.append(r)
    return result


def verify(records, target_event, references=None):
    refs = references if references is not None else load_documents()
    events = {r["id"]: r for r in refs if r["kind"] == "event"}
    people = {r["fields"]["email"]: r for r in refs if r["kind"] == "participant"}
    result = []
    for source in records:
        r = deepcopy(source)
        r["checks"], r["matches"] = [], []
        source_issues = list(r.get("input_issues", r.get("issues", [])))
        r["input_issues"] = source_issues
        issues = list(source_issues)

        def check(rule, field, actual, expected, passed):
            r["checks"].append(
                {
                    "rule": rule,
                    "field": field,
                    "actual": actual,
                    "reference": expected,
                    "status": "passed" if passed else "failed",
                    "authority": "deterministic",
                }
            )
            if not passed:
                issues.append(rule)

        event = events.get(r["event_id"])
        check("event_exists", "event_id", r["event_id"], sorted(events), bool(event))
        check("target_event_matches", "event_id", r["event_id"], target_event, r["event_id"] == target_event)
        participant = people.get(r["email"])
        is_registration = bool(r["email"] or r["participant_id"] or r["source"] == "email")
        if event:
            r["matches"].append(event)
            for field in ("title", "starts_at", "venue"):
                actual, expected = r[field], event["fields"][field]
                if actual or not is_registration:
                    passed = clean(actual).casefold() == clean(expected).casefold()
                    if field == "starts_at" and actual:
                        try:
                            passed = datetime.fromisoformat(actual) == datetime.fromisoformat(expected)
                        except ValueError:
                            passed = False
                    check(field + "_matches", field, actual, expected, bool(actual) and passed)
        if is_registration:
            check(
                "directory_identity",
                "email",
                r["email"],
                participant["fields"]["email"] if participant else None,
                bool(participant),
            )
            if participant:
                r["matches"].append(participant)
                pf = participant["fields"]
                check("active_participant", "status", pf["status"], "active", pf["status"] == "active")
                check(
                    "registered_for_event",
                    "event_id",
                    r["event_id"],
                    pf["registered_events"],
                    r["event_id"] in pf["registered_events"],
                )
                check(
                    "name_matches",
                    "full_name",
                    r["full_name"],
                    pf["full_name"],
                    bool(r["full_name"]) and r["full_name"].casefold() == pf["full_name"].casefold(),
                )
                if r["participant_id"]:
                    check(
                        "participant_id_matches",
                        "participant_id",
                        r["participant_id"],
                        pf["participant_id"],
                        r["participant_id"] == pf["participant_id"],
                    )
        for issue in source_issues:
            r["checks"].append(
                {
                    "rule": issue,
                    "field": "source",
                    "actual": issue,
                    "reference": None,
                    "status": "failed",
                    "authority": "deterministic",
                }
            )
        missing = not r["event_id"] or (is_registration and (not r["email"] or not r["full_name"]))
        rejected = bool(r["event_id"] and not event) or any(
            x in issues
            for x in ("active_participant", "registered_for_event", "invalid_email", "invalid_event_id")
        )
        r["status"] = (
            "incomplete"
            if missing
            else "rejected"
            if rejected
            else "review_required"
            if issues
            else "verified"
        )
        r["issues"] = sorted(set(issues))
        r["record_type"] = "registration" if is_registration else "event_observation"
        r["review_status"] = "unreviewed"
        result.append(r)
    return result


def summary(records):
    return {
        "total": len(records),
        **{
            s: sum(r["status"] == s for r in records)
            for s in ("verified", "review_required", "rejected", "incomplete")
        },
        "duplicates_merged": sum(r.get("duplicate_count", 0) for r in records),
    }


def export_csv(records, verified_only=False):
    output = io.StringIO()
    fields = [
        "id",
        *FIELDS,
        "record_type",
        "status",
        "review_status",
        "duplicate_count",
        "issues",
        "conflicts",
        "evidence",
    ]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for r in records:
        if verified_only and r["status"] != "verified":
            continue
        row = {
            k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in r.items()
        }
        # Prevent spreadsheet formula injection in exported external values.
        row = {
            k: "'" + str(v) if str(v).lstrip().startswith(("=", "+", "-", "@")) else v for k, v in row.items()
        }
        writer.writerow(row)
    return output.getvalue()
