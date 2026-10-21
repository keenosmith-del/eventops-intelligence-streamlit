"""Credential-free deployment artifact checks. Does not start any service."""

import json
import secrets
import subprocess
import tempfile
from pathlib import Path

from sqlalchemy.engine import URL

from deploy.check import ROOT, SECRETS, compose_command, validate_topology, validate_values

values = {name: secrets.token_urlsafe(36) for name in SECRETS}
values.update(
    APP_SITE="https://assessment.example.test",
    RELEASE_TAG="ci",
    RELEASE_REVISION="ci-artifact-check",
    GEMINI_ENABLED="false",
    GEMINI_FREE_TIER_CONFIRMED="false",
    GEMINI_MODEL="gemini-3.5-flash-lite",
    GEMINI_DAILY_LIMIT="8",
    AGENT_DAILY_LIMIT="3",
    RUNS_PER_HOUR="30",
    RUNS_PER_WORKSPACE_HOUR="6",
    EXECUTIONS_DATA_MAX_AGE="168",
    MAILTRAP_API_TOKEN="dummy-ci-only",
    MAILTRAP_ACCOUNT_ID="dummy",
    MAILTRAP_INBOX_ID="dummy",
)
values["EVENTOPS_DATABASE_URL"] = URL.create(
    "postgresql+psycopg",
    username="companion",
    password=secrets.token_urlsafe(32),
    host="database.example.test",
    database="companion",
    query={"sslmode": "verify-full", "sslrootcert": "system"},
).render_as_string(hide_password=False)
assert not validate_values(values)
with tempfile.TemporaryDirectory(prefix="eventops-deploy-check-") as folder:
    path = Path(folder) / "ci.env"
    path.write_text("\n".join(k + "=" + v for k, v in values.items()))
    path.chmod(0o600)
    config = json.loads(
        subprocess.check_output(compose_command(path) + ["config", "--format", "json"], text=True)
    )
    summary = validate_topology(config)
    funnel_config = json.loads(
        subprocess.check_output(compose_command(path, funnel=True) + ["config", "--format", "json"], text=True)
    )
    validate_topology(funnel_config, funnel=True)
    summary["funnel_overlay_validated"] = True
    template = (ROOT / "deploy/production.env.example").read_text()
    from dotenv import dotenv_values

    declared = set(dotenv_values(ROOT / "deploy/production.env.example"))
    assert declared == set(values) | {"GEMINI_API_KEY"}, "Environment inventory/template drift"
    assert "/webhook/" not in (ROOT / "deploy/Caddyfile").read_text().replace("/webhook/*", "")
print(
    json.dumps(
        {
            "status": "validated",
            "configuration": "dummy values only; no account/DNS/connectivity inferred",
            **summary,
        },
        indent=2,
    )
)
