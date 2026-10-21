"""Validate production input and rendered topology without revealing secrets."""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
SECRETS = (
    "APP_PASSWORD",
    "N8N_WEBHOOK_TOKEN",
    "EVENTOPS_SERVICE_TOKEN",
    "N8N_ENCRYPTION_KEY",
    "N8N_RUNNERS_AUTH_TOKEN",
)


def compose_environment(env_file):
    """An explicit release file wins over developer .env values loaded by Python."""
    env = dict(os.environ)
    for key, value in dotenv_values(env_file).items():
        if key not in {"HOME", "PATH", "CODEX_HOME"} and value is not None:
            env[key] = value
    return env


def run_compose(command, **kwargs):
    env_file = command[command.index("--env-file") + 1]
    return subprocess.run(command, env=compose_environment(env_file), **kwargs)


def validate_values(values, rehearsal=False):
    errors = []
    for name in SECRETS:
        if len(values.get(name) or "") < 32:
            errors.append(name + " must contain at least 32 characters")
    if len({values.get(name) for name in SECRETS}) != len(SECRETS):
        errors.append("Independent security boundaries require distinct secrets")
    site = urlsplit(values.get("APP_SITE", ""))
    if (
        not site.hostname
        or site.username
        or site.password
        or site.path not in ("", "/")
        or site.query
        or site.fragment
    ):
        errors.append("APP_SITE must be an application origin")
    if not rehearsal and (
        site.scheme != "https"
        or site.port not in (None, 443)
        or site.hostname in ("localhost", "127.0.0.1")
        or (site.hostname or "").endswith(".invalid")
    ):
        errors.append("APP_SITE must be the approved public HTTPS domain")
    if rehearsal and (site.scheme != "http" or site.hostname != "localhost" or site.port != 8080):
        errors.append("Rehearsal must use the fixed localhost HTTP origin")
    try:
        u = make_url(values.get("EVENTOPS_DATABASE_URL", ""))
        if u.drivername != "postgresql+psycopg" or not u.password or not u.database:
            raise ValueError()
        if not rehearsal and (
            u.query.get("sslmode") != "verify-full"
            or u.query.get("sslrootcert") != "system"
            or u.host in ("localhost", "127.0.0.1", "database", "host.docker.internal")
        ):
            raise ValueError()
        if rehearsal and (u.host != "database" or u.database != "companion003"):
            raise ValueError()
    except Exception:
        errors.append(
            "Set the dedicated PostgreSQL URL with verified TLS (or the isolated rehearsal database)"
        )
    for name in ("RELEASE_REVISION", "RELEASE_TAG"):
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}", values.get(name, "")):
            errors.append(name + " must be a bounded release identifier")
    for name, high in (
        ("GEMINI_DAILY_LIMIT", 20),
        ("AGENT_DAILY_LIMIT", 5),
        ("RUNS_PER_HOUR", 100),
        ("RUNS_PER_WORKSPACE_HOUR", 20),
        ("EXECUTIONS_DATA_MAX_AGE", 720),
    ):
        try:
            if not 1 <= int(values.get(name, "0")) <= high:
                raise ValueError()
        except ValueError:
            errors.append(name + " is outside the reviewed bounds")
    if values.get("GEMINI_ENABLED") not in ("true", "false"):
        errors.append("GEMINI_ENABLED must be explicit")
    if values.get("GEMINI_ENABLED") == "true" and not values.get("GEMINI_API_KEY"):
        errors.append("Enabled Gemini requires an approved key")
    if values.get("GEMINI_ENABLED") == "true" and values.get("GEMINI_FREE_TIER_CONFIRMED") != "true":
        errors.append("Enabled Gemini requires owner-confirmed free tier with billing disabled")
    if not re.fullmatch(r"gemini-[\w.-]*flash[\w.-]*", values.get("GEMINI_MODEL", "")):
        errors.append("Use a compatible Flash model")
    if not all(values.get(n) for n in ("MAILTRAP_API_TOKEN", "MAILTRAP_ACCOUNT_ID", "MAILTRAP_INBOX_ID")):
        errors.append("Mailtrap sandbox configuration is required for release acceptance")
    return errors


def compose_command(env_file, rehearsal=False, funnel=False):
    args = ["docker", "compose", "--env-file", str(env_file), "-f", str(ROOT / "deploy/compose.hosted.yaml")]
    if rehearsal:
        args += ["-f", str(ROOT / "deploy/compose.rehearsal.yaml")]
    if funnel:
        args += ["-f", str(ROOT / "deploy/compose.funnel.yaml")]
    return args


def validate_topology(config, rehearsal=False, funnel=False):
    services = config["services"]
    expected = {"app", "processor", "n8n", "runners", "scenario", "gateway"}
    assert set(services) == expected | ({"database", "restore"} if rehearsal else set())
    for name in expected - {"gateway"}:
        if not rehearsal:
            assert not services[name].get("ports"), "Internal services must have no published ports"
    assert services["n8n"]["environment"]["N8N_RUNNERS_MODE"] == "external"
    assert services["app"]["environment"]["PRIVATE_N8N_ORIGIN"] == "http://n8n:5678"
    assert "MAILTRAP_API_TOKEN" not in services["app"]["environment"]
    assert "GEMINI_API_KEY" not in services["processor"]["environment"]
    assert "EVENTOPS_DATABASE_URL" not in services["n8n"]["environment"]
    assert config["networks"]["runner"]["internal"]
    assert config["networks"]["sources"]["internal"]
    assert set(services["runners"]["networks"]) == {"runner"}
    assert set(services["scenario"]["networks"]) == {"sources"}
    ports = services["gateway"].get("ports", [])
    if rehearsal or funnel:
        assert len(ports) == 1 and ports[0].get("host_ip") == "127.0.0.1"
        assert str(ports[0]["published"]) == ("8503" if rehearsal else "8505")
    else:
        assert {str(p["published"]) for p in ports} == {"80", "443"}
    for service in services.values():
        assert not service.get("privileged")
        for port in service.get("ports", []):
            if rehearsal:
                assert port.get("host_ip") == "127.0.0.1"
    return {
        "service_count": len(services),
        "private_services": sorted(expected - {"gateway"}),
        "rehearsal": rehearsal,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--rehearsal", action="store_true")
    parser.add_argument("--funnel", action="store_true")
    args = parser.parse_args()
    values = dotenv_values(args.env_file)
    errors = validate_values(values, args.rehearsal)
    if args.funnel and not (urlsplit(values.get("APP_SITE", "")).hostname or "").endswith(".ts.net"):
        errors.append("Funnel requires the approved provider-issued ts.net HTTPS name")
    if errors:
        print(json.dumps({"status": "invalid", "errors": errors}, indent=2))
        raise SystemExit(1)
    # Rendered config contains secrets: capture in memory, never print it.
    rendered = subprocess.check_output(
        compose_command(args.env_file, args.rehearsal, args.funnel) + ["config", "--format", "json"],
        text=True,
        env=compose_environment(args.env_file),
    )
    result = validate_topology(json.loads(rendered), args.rehearsal, args.funnel)
    print(json.dumps({"status": "validated", **result, "public_deployment": "not_performed"}, indent=2))


if __name__ == "__main__":
    main()
