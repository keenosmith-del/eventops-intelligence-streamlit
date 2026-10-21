"""Scan current release files and all available Git history; never prints secret values."""

import argparse
import json
import re
import subprocess
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    re.compile(rb"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"postgres(?:ql)?(?:\+psycopg)?://[^\s:@]+:[^\s@${}]+@[^\s]+"),
]


def audit(history=True):
    configured = {}
    for path in [ROOT / ".env", ROOT / "deploy/production.env", ROOT / "deploy/.local/rehearsal.env"]:
        if path.exists():
            for key, value in dotenv_values(path).items():
                configured[str(path) + ":" + key] = value
    actual = [
        v.encode()
        for k, v in configured.items()
        if v and len(v) > 20 and any(p in k for p in ["TOKEN", "KEY", "PASSWORD"])
    ]
    paths = (
        subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT)
        .decode()
        .split("\0")
    )
    findings = []
    identifiers = []

    def check(label, body):
        if any(v in body for v in actual) or any(pattern.search(body) for pattern in PATTERNS):
            findings.append(label)
        if re.search(rb"mailtrap\.io/api/accounts/\d+/inboxes/\d+", body):
            identifiers.append(label)

    for name in set(filter(None, paths)):
        p = ROOT / name
        if p.is_file():
            check(name, p.read_bytes())
    history_objects = 0
    if history:
        rows = (
            subprocess.check_output(["git", "rev-list", "--objects", "--all"], cwd=ROOT).decode().splitlines()
        )
        for row in rows:
            oid, _, path = row.partition(" ")
            if not path:
                continue
            if subprocess.check_output(["git", "cat-file", "-t", oid], cwd=ROOT).strip() != b"blob":
                continue
            history_objects += 1
            check(
                "history:" + oid[:10] + ":" + path,
                subprocess.check_output(["git", "cat-file", "blob", oid], cwd=ROOT),
            )
    return {
        "actual_secrets_found": sorted(set(findings)),
        "unnecessary_provider_identifiers": sorted(set(identifiers)),
        "history_blobs_scanned": history_objects,
        "current_files_scanned": len(set(filter(None, paths))),
        "note": "Pattern/value scan is a safeguard, not proof that arbitrary unknown secrets cannot exist. History is read-only.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--current-only", action="store_true")
    args = parser.parse_args()
    result = audit(not args.current_only)
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result["actual_secrets_found"]))
