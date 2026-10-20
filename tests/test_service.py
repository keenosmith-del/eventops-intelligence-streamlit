import json
import uuid

import pytest
from fastapi.testclient import TestClient

from eventops.service import app
from eventops.store import Store


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("EVENTOPS_DATABASE_URL", "sqlite:///" + str(tmp_path / "service.db"))
    monkeypatch.setenv("EVENTOPS_SERVICE_TOKEN", "a" * 40)
    with TestClient(app) as c:
        c.headers["X-EventOps-Token"] = "a" * 40
        yield c


def run_input():
    return {"owner": "a" * 48, "request_id": str(uuid.uuid4()), "event_id": "EVT-101", "limit": 3}


def test_auth(client):
    assert client.get("/health").status_code == 200
    assert client.get("/sources/config", headers={"X-EventOps-Token": "bad"}).status_code == 401


def test_invalid_request(client):
    data = run_input()
    data["event_id"] = "EVT-999"
    assert client.post("/runs/begin", json=data).status_code == 422
    data["event_id"] = "EVT-101"
    data["url"] = "https://evil.com"
    assert client.post("/runs/begin", json=data).status_code == 422


def test_replay_owner_isolation(client):
    data = run_input()
    first = client.post("/runs/begin", json=data).json()
    second = client.post("/runs/begin", json=data).json()
    assert not first["replayed"] and second["replayed"]
    data["owner"] = "b" * 48
    assert client.post("/runs/begin", json=data).status_code == 409


@pytest.mark.parametrize(
    "statuses,expected",
    [
        (["completed"] * 3, "completed"),
        (["completed", "failed", "completed"], "partial"),
        (["failed"] * 3, "failed"),
        (["completed", "unavailable", "completed"], "partial"),
    ],
)
def test_finish_partial(client, processed, statuses, expected):
    data = run_input()
    first = client.post("/runs/begin", json=data).json()
    result = client.post(
        "/runs/finish",
        json={
            **data,
            "run_id": first["run_id"],
            "execution_id": "test-1",
            "outcomes": [
                {"source": s, "status": status} for s, status in zip(["calendar", "email", "web"], statuses)
            ],
            "records": processed,
        },
    )
    assert result.status_code == 200
    assert result.json()["status"] == expected
    assert result.json()["summary"]["verified"] == 1


def test_failed_extraction_continues(client):
    response = client.post(
        "/stages/extract", json={"source": "web", "payload": {"status": "completed", "body": "invalid"}}
    )
    assert response.json()["outcome"]["status"] == "failed"
    assert response.json()["records"] == []


def test_missing_run(client):
    assert (
        client.post(
            "/agent/context", json={"owner": "x" * 48, "run_id": str(uuid.uuid4()), "intent": "Explain"}
        ).status_code
        == 404
    )


def test_record_state_not_overridden_by_agent(client, processed):
    data = run_input()
    client.post("/runs/begin", json=data)
    client.post(
        "/runs/finish",
        json={
            **data,
            "run_id": data["request_id"],
            "execution_id": "1",
            "outcomes": [{"source": s, "status": "completed"} for s in ["calendar", "email", "web"]],
            "records": processed,
        },
    )
    body = {
        "owner": data["owner"],
        "run_id": data["request_id"],
        "intent": "Explain",
        "execution_id": "2",
        "output": json.dumps(
            {
                "intent": "explain",
                "summary": "Check passed",
                "evidence_ids": [processed[0]["id"]],
                "limitations": [],
            }
        ),
        "intermediate_steps": [],
    }
    result = client.post("/agent/finish", json=body)
    assert result.json()["status"] == "unavailable"  # No tool evidence: never claim a genuine agent.
    body["intermediate_steps"] = [
        {
            "action": {"tool": "inspect_findings", "toolInput": "all"},
            "observation": json.dumps([{"response": json.dumps({"records": [{"id": processed[0]["id"]}]})}]),
        }
    ]
    assert client.post("/agent/finish", json=body).json()["status"] == "completed"
    saved = Store().get(data["owner"], data["request_id"])["payload"]
    assert saved["records"][0]["status"] == "verified"
    body["intermediate_steps"][0]["action"]["tool"] = "send_email"
    assert client.post("/agent/finish", json=body).json()["status"] == "unavailable"


def test_budget_atomic(store):
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=4) as pool:
        result = list(pool.map(lambda _: store.reserve("test", "same", {}), range(8)))
    assert sum(result) == 1


def test_owner_scope(store):
    rid = store.save("a", "run", {"test": True})
    assert store.get("a", rid)
    assert store.get("b", rid) is None
    with pytest.raises(KeyError):
        store.replace("b", rid, {})


def test_client_uncertain_delivery(store, monkeypatch):
    import httpx

    from eventops.client import trigger

    monkeypatch.setenv("N8N_WEBHOOK_URL", "http://127.0.0.1:5679/webhook/eventops-verify")
    rid = str(uuid.uuid4())
    result = trigger(
        store,
        "x" * 48,
        "EVT-101",
        request_id=rid,
        transport=httpx.MockTransport(lambda request: httpx.Response(401)),
    )
    assert result["status"] == "delivery_unknown"
    assert store.get("x" * 48, "request-" + rid)


def test_agent_rejects_unlabelled_email(client, processed, monkeypatch):
    monkeypatch.setenv("GEMINI_ENABLED", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    data = run_input()
    client.post("/runs/begin", json=data)
    client.post(
        "/runs/finish",
        json={
            **data,
            "run_id": data["request_id"],
            "execution_id": "1",
            "outcomes": [{"source": s, "status": "completed"} for s in ["calendar", "email", "web"]],
            "records": processed,
        },
    )
    response = client.post(
        "/agent/context", json={"owner": data["owner"], "run_id": data["request_id"], "intent": "Explain"}
    )
    assert response.status_code == 422
    assert "synthetic" in response.json()["detail"]


def test_client_repeated_failed_delivery_is_saved_once(store, monkeypatch):
    import httpx

    from eventops.client import trigger

    monkeypatch.setenv("N8N_WEBHOOK_URL", "http://127.0.0.1:5679/webhook/eventops-verify")
    rid = str(uuid.uuid4())
    transport = httpx.MockTransport(lambda request: httpx.Response(401))
    for _ in range(2):
        assert (
            trigger(store, "x" * 48, "EVT-101", request_id=rid, transport=transport)["status"]
            == "delivery_unknown"
        )
    assert len(store.list("x" * 48, "request")) == 1


@pytest.mark.parametrize("url", ["", "https://127.0.0.1/private"])
def test_bad_source_configuration_does_not_hide_other_sources(client, monkeypatch, url):
    monkeypatch.setenv("CALENDAR_FEED_URL", url)
    response = client.get("/sources/config")
    assert response.status_code == 200
    result = response.json()
    assert result["calendar"] == "" and "calendar" in result["configuration_errors"]
    assert result["web"].startswith("https://date.nager.at/")
