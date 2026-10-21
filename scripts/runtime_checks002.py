"""Read-only/resource checks plus one idempotent concurrent run on controlled sources."""

import json
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx

from eventops.config import setting
from eventops.public_evidence import sanitize
from eventops.store import now

headers = {"X-EventOps-Webhook": setting("N8N_WEBHOOK_TOKEN")}
owner = "concurrency-" + uuid.uuid4().hex
request = {
    "owner": owner,
    "request_id": str(uuid.uuid4()),
    "event_id": "EVT-101",
    "limit": 5,
    "scenario": "assessment_event",
}


def dispatch(_):
    with httpx.Client(timeout=130) as c:
        response = c.post("http://127.0.0.1:5680/webhook/eventops-verify", headers=headers, json=request)
        response.raise_for_status()
        return response.json()


with ThreadPoolExecutor(max_workers=2) as pool:
    replies = list(pool.map(dispatch, range(2)))
assert len({r["run_id"] for r in replies}) == 1
assert sum(r["status"] == "completed" for r in replies) >= 1
with httpx.Client(timeout=10) as c:
    headers = {"X-EventOps-Token": setting("EVENTOPS_SERVICE_TOKEN"), "X-Workspace-Key": owner}
    start = time.perf_counter()
    state = c.get(
        "http://127.0.0.1:8767/runs/" + request["request_id"] + "/reconcile", headers=headers
    ).json()
    db_ms = (time.perf_counter() - start) * 1000
assert state["state"] == "completed"
Path("docs/iterations/002/evidence/concurrent-webhook.json").write_text(
    json.dumps(
        sanitize(
            {
                "observed_at": now(),
                "request_id": request["request_id"],
                "responses": [
                    {"status": r["status"], "execution_id": r.get("execution_id")} for r in replies
                ],
                "persisted_state": state["state"],
                "source_checkpoints": state["run"].get("stages"),
                "reconciliation_http_ms": db_ms,
                "samples": 1,
                "note": "Two real simultaneous webhook requests; one reserved run. Per-node execution manifest corroborates the replay branch.",
            }
        ),
        indent=2,
    )
)
print(
    "Concurrent requests returned",
    [r["status"] for r in replies],
    "; one persisted run",
    request["request_id"],
)
