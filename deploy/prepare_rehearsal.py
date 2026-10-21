"""Prepare fresh LOCAL ONLY configuration, preserving any existing rehearsal secrets."""

import hashlib
import json
import os
import secrets
import subprocess
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT / "deploy/.local"
folder.mkdir(exist_ok=True)
path = folder / "rehearsal.env"
if path.exists():
    print("Existing rehearsal environment preserved; encryption key unchanged.")
else:
    approved = dotenv_values(ROOT / ".env")
    v = {
        key: secrets.token_urlsafe(36)
        for key in (
            "APP_PASSWORD",
            "EVENTOPS_SERVICE_TOKEN",
            "N8N_WEBHOOK_TOKEN",
            "N8N_ENCRYPTION_KEY",
            "N8N_RUNNERS_AUTH_TOKEN",
            "BOOTSTRAP_PASSWORD",
            "COMPANION_DB_PASSWORD",
        )
    }
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    # Uncommitted rehearsal content is explicitly identified, not mislabeled as the clean baseline.
    source = hashlib.sha256()
    for glob in (
        "eventops/*.py",
        "deploy/*.py",
        "deploy/*.yaml",
        "deploy/Caddyfile",
        "scripts/build_workflows.py",
        "Dockerfile",
        "app.py",
    ):
        for item in sorted(ROOT.glob(glob)):
            source.update(str(item.relative_to(ROOT)).encode() + item.read_bytes())
    v.update(
        APP_SITE="http://localhost:8080",
        RELEASE_TAG="rehearsal003",
        RELEASE_REVISION=revision[:12] + "-worktree-" + source.hexdigest()[:12],
        GEMINI_ENABLED="false",
        GEMINI_FREE_TIER_CONFIRMED="false",
        GEMINI_MODEL=approved.get("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        GEMINI_DAILY_LIMIT="8",
        AGENT_DAILY_LIMIT="3",
        RUNS_PER_HOUR="30",
        RUNS_PER_WORKSPACE_HOUR="6",
        EXECUTIONS_DATA_MAX_AGE="168",
    )
    v["EVENTOPS_DATABASE_URL"] = URL.create(
        "postgresql+psycopg",
        username="companion",
        password=v["COMPANION_DB_PASSWORD"],
        host="database",
        database="companion003",
        query={"sslmode": "disable"},
    ).render_as_string(hide_password=False)
    for key in ("GEMINI_API_KEY", "MAILTRAP_API_TOKEN", "MAILTRAP_ACCOUNT_ID", "MAILTRAP_INBOX_ID"):
        v[key] = approved.get(key) or ""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        for key, value in v.items():
            f.write(key + "=" + json.dumps(value) + "\n")
    print("Fresh isolated rehearsal environment prepared; Gemini is disabled. No secrets printed.")

# Refresh traceability only; never rotate an existing credential or encryption key.
if "--refresh-revision" in __import__("sys").argv:
    values = dotenv_values(path)
    from deploy.release_manifest import manifest

    source = manifest()
    values["RELEASE_REVISION"] = source["revision"][:12] + "-worktree-" + source["source_sha256"][:12]
    path.write_text("\n".join(key + "=" + json.dumps(value) for key, value in values.items()) + "\n")
    path.chmod(0o600)
    print("Release source metadata refreshed; all credentials preserved.")
