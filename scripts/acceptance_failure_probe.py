"""Actual n8n HTTP error branches against the independent controlled server."""

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx

from eventops.config import setting
from eventops.public_evidence import sanitize

report = []
with httpx.Client(timeout=130) as client:
    for probe in [
        "http401",
        "http403",
        "http429",
        "http500",
        "timeout",
        "malformed",
        "dns",
        "processing_unavailable",
        "invalid_calendar",
    ]:
        response = client.post(
            "http://127.0.0.1:5680/webhook/eventops-failure-probe",
            headers={"X-EventOps-Webhook": setting("N8N_WEBHOOK_TOKEN")},
            json={"owner": "diagnostic-" + uuid.uuid4().hex, "request_id": str(uuid.uuid4()), "probe": probe},
        )
        response.raise_for_status()
        run = response.json()
        target = "calendar" if probe == "invalid_calendar" else "web"
        web = next(o for o in run["outcomes"] if o["source"] == target)
        assert run["status"] == "partial" and web["status"] in ("failed", "timed_out")
        assert next(o for o in run["outcomes"] if o["source"] == "email")["status"] == "completed"
        if probe == "timeout":
            assert web["status"] == "timed_out"
        report.append(
            {
                "probe": probe,
                "execution_id": run["execution_id"],
                "status": "passed",
                "workflow_status": run["status"],
                "outcomes": run["outcomes"],
            }
        )
Path("docs/iterations/002/evidence/n8n-failure-probes.json").write_text(
    json.dumps(
        sanitize(
            {
                "classification": "Actual n8n requests to controlled HTTP test routes; not real external provider outages",
                "checks": report,
            }
        ),
        indent=2,
    )
)
print([(r["probe"], r["status"]) for r in report])
