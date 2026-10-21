"""Release boundaries: private origins, TLS, rate bounds and safe failures."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import URL
from sqlalchemy.exc import OperationalError

from deploy.check import SECRETS, validate_values
from eventops import client, service
from eventops.operations import WindowLimiter, emit, private_origin, reserve_run_capacity, validate_database
from eventops.scenarios import configuration


def test_hosted_database_requires_verified_tls(monkeypatch):
    monkeypatch.delenv("RELEASE_REHEARSAL", raising=False)
    for url in (
        "sqlite:///local.db",
        "postgresql+psycopg://db.example/demo?sslmode=require",
        "postgresql+psycopg://database/demo?sslmode=verify-full",
    ):
        with pytest.raises(ValueError):
            validate_database(url, production=True)
    assert (
        validate_database("postgresql+psycopg://db.example/demo?sslmode=verify-full", production=True).host
        == "db.example"
    )


def test_exact_private_webhook_origin_does_not_allow_other_hosts(monkeypatch):
    monkeypatch.setenv("PRIVATE_N8N_ORIGIN", "http://n8n:5678")
    monkeypatch.setenv("PUBLIC_DEMO", "true")
    monkeypatch.setenv("EVENTOPS_LOCAL_COMPOSE", "false")
    monkeypatch.setenv("N8N_WEBHOOK_URL", "http://n8n:5678/webhook/eventops-verify")
    assert client.webhook_url().startswith("http://n8n:")
    for url in (
        "http://n8n.attacker:5678/webhook/eventops-verify",
        "http://n8n:5679/webhook/eventops-verify",
        "http://n8n:5678@evil.test/webhook/eventops-verify",
    ):
        monkeypatch.setenv("N8N_WEBHOOK_URL", url)
        with pytest.raises(ValueError):
            client.webhook_url()
    assert not private_origin("http://n8n:5678/", "UNCONFIGURED_PRIVATE_ORIGIN")


def test_private_fixture_keeps_laptop_and_arbitrary_urls_disabled(monkeypatch):
    monkeypatch.setenv("ENABLE_LOCAL_SCENARIO", "false")
    monkeypatch.setenv("PRIVATE_SOURCE_ORIGIN", "http://scenario:8090")
    monkeypatch.setenv("ASSESSMENT_SOURCE_BASE_URL", "http://scenario:8090")
    assert not configuration("assessment_event")["configuration_errors"]
    for base in ("http://host.docker.internal:8090", "http://scenario:8091", "http://scenario:8090/private"):
        monkeypatch.setenv("ASSESSMENT_SOURCE_BASE_URL", base)
        assert configuration("assessment_event")["configuration_errors"]


def test_login_attempt_throttle_expires_without_retaining_passwords(monkeypatch):
    monkeypatch.setattr("eventops.operations.time.monotonic", lambda: 60)
    limiter = WindowLimiter(limit=2)
    assert limiter.allow() and limiter.allow() and not limiter.allow()
    monkeypatch.setattr("eventops.operations.time.monotonic", lambda: 120)
    assert limiter.allow()


def test_database_rate_limit_is_global_and_durable(store, monkeypatch):
    monkeypatch.setenv("PRODUCTION_MODE", "true")
    monkeypatch.setenv("RUNS_PER_HOUR", "2")
    monkeypatch.setenv("RUNS_PER_WORKSPACE_HOUR", "1")
    assert reserve_run_capacity(store, "owner-one")
    assert not reserve_run_capacity(store, "owner-one")
    assert reserve_run_capacity(store, "owner-two")
    assert not reserve_run_capacity(store, "owner-three")


def test_replay_does_not_consume_additional_run_capacity(store, monkeypatch):
    monkeypatch.setattr(service, "Store", lambda: store)
    monkeypatch.setenv("EVENTOPS_SERVICE_TOKEN", "x" * 40)
    monkeypatch.setenv("PRODUCTION_MODE", "true")
    monkeypatch.setenv("RUNS_PER_HOUR", "1")
    monkeypatch.setenv("RUNS_PER_WORKSPACE_HOUR", "1")
    c = TestClient(service.app)
    headers = {"X-EventOps-Token": "x" * 40}
    data = {"owner": "owner-" + "a" * 20, "request_id": "request-" + "a" * 20, "event_id": "EVT-101"}
    assert c.post("/runs/begin", json=data, headers=headers).status_code == 200
    assert c.post("/runs/begin", json=data, headers=headers).json()["replayed"]
    data["request_id"] = "request-" + "b" * 20
    assert c.post("/runs/begin", json=data, headers=headers).status_code == 429


def test_database_readiness_failure_is_sanitized(monkeypatch):
    monkeypatch.setenv("EVENTOPS_SERVICE_TOKEN", "x" * 40)

    def fail():
        raise OperationalError("private-database-password", None, Exception("private-provider-token"))

    monkeypatch.setattr(service, "Store", fail)
    c = TestClient(service.app)
    assert c.get("/readyz").status_code == 401
    result = c.get("/readyz", headers={"X-EventOps-Token": "x" * 40})
    assert result.status_code == 503
    assert "private" not in result.text and "Persistence" in result.text


def test_operational_logs_drop_payload_and_secret_fields(monkeypatch):
    recorded = []
    monkeypatch.setattr("eventops.operations.LOGGER.info", recorded.append)
    emit(
        "stage",
        run_id="run-test",
        status="failed",
        password="NEVER-LOG",
        body="PRIVATE-BODY",
        owner="PRIVATE-CAPABILITY",
    )
    text = recorded[0]
    assert json.loads(text)["run_id"] == "run-test"
    assert not any(secret in text for secret in ("NEVER-LOG", "PRIVATE-BODY", "PRIVATE-CAPABILITY"))


def test_release_preflight_rejects_shared_secrets_and_insecure_database():
    values = {key: "same-secret" * 4 for key in SECRETS}
    values.update(
        APP_SITE="http://localhost",
        EVENTOPS_DATABASE_URL=URL.create(
            "postgresql+psycopg",
            username="companion",
            password="synthetic",
            host="db.example",
            database="companion",
            query={"sslmode": "require"},
        ).render_as_string(hide_password=False),
    )
    errors = validate_values(values)
    assert any("distinct" in e for e in errors)
    assert any("HTTPS" in e for e in errors)
    assert any("verified TLS" in e for e in errors)


def test_older_release_refuses_newer_database_schema(store):
    from sqlalchemy import text

    from eventops.migrations import upgrade

    with store.engine.begin() as c:
        c.execute(text("INSERT INTO companion_schema_versions VALUES (99,'future release')"))
    with pytest.raises(RuntimeError, match="newer"):
        upgrade(store.engine, store.objects.metadata)
    with store.engine.connect() as c:
        assert (
            c.execute(text("SELECT count(*) FROM companion_schema_versions WHERE version=99")).scalar() == 1
        )


def test_explicit_release_environment_beats_loaded_developer_environment(tmp_path, monkeypatch):
    from deploy.check import compose_environment

    monkeypatch.setenv("N8N_ENCRYPTION_KEY", "old-development-key")
    path = tmp_path / "release.env"
    path.write_text("N8N_ENCRYPTION_KEY=independent-release-key\n")
    result = compose_environment(path)
    assert result["N8N_ENCRYPTION_KEY"] == "independent-release-key"
    assert result["HOME"] == __import__("os").environ["HOME"]


def test_model_calls_are_blocked_until_free_tier_is_confirmed(store, monkeypatch):
    from eventops.gemini import grounded_answer

    monkeypatch.setenv("PRODUCTION_MODE", "true")
    monkeypatch.setenv("GEMINI_ENABLED", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("GEMINI_FREE_TIER_CONFIRMED", "false")
    result = grounded_answer("Where?", [{"id": "EVT-101", "content": "Synthetic venue"}], store)
    assert result["status"] == "unavailable" and result["reason"] == "free_tier_not_confirmed"
    assert not store.list("budget", "reservation")
