"""Actual HTTP acceptance for the full isolated stack. No sends or provider mocks."""

import argparse
import csv
import io
import json
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx

from eventops.config import setting
from eventops.pipeline import export_csv
from eventops.public_evidence import sanitize
from eventops.store import Store, now

parser = argparse.ArgumentParser()
parser.add_argument(
    "--models",
    action="store_true",
    help="Opt in to bounded real Gemini requests using controlled synthetic inputs only",
)
parser.add_argument("--base", default="http://127.0.0.1:5680")
args = parser.parse_args()
folder = Path("docs/iterations/002/evidence")
folder.mkdir(parents=True, exist_ok=True)
key = Path("storage/iteration002-workspace.txt")
owner = key.read_text().strip() if key.exists() else uuid.uuid4().hex + uuid.uuid4().hex[:16]
key.write_text(owner)
key.chmod(0o600)
headers = {"X-EventOps-Webhook": setting("N8N_WEBHOOK_TOKEN")}
service_headers = {"X-EventOps-Token": setting("EVENTOPS_SERVICE_TOKEN"), "X-Workspace-Key": owner}
report = {
    "observed_at": now(),
    "environment": "isolated full Docker Linux ARM64 topology, PostgreSQL; controlled HTTP scenario + real Mailtrap",
    "runs": [],
    "checks": [],
}
with httpx.Client(timeout=130, follow_redirects=False) as client:
    for scenario in ["assessment_event", "provider_unavailable"]:
        payload = {
            "owner": owner,
            "request_id": str(uuid.uuid4()),
            "event_id": "EVT-101",
            "limit": 5,
            "scenario": scenario,
        }
        started = time.perf_counter()
        response = client.post(args.base + "/webhook/eventops-verify", headers=headers, json=payload)
        response.raise_for_status()
        run = response.json()
        assert run.get("execution_id"), f"No persisted execution: {str(run)[:200]}"
        assert run["status"] == ("partial" if scenario == "provider_unavailable" else "completed")
        assert {o["source"] for o in run["outcomes"]} == {"calendar", "email", "web"}
        assert run["summary"]["verified"] >= 1 and run["summary"]["duplicates_merged"] >= 1
        assert run["summary"]["rejected"] >= 1
        if scenario == "assessment_event":
            assert any("venue_matches" in r["issues"] for r in run["records"])
            assert any(r["status"] == "incomplete" for r in run["records"])
        else:
            assert next(o for o in run["outcomes"] if o["source"] == "web")["status"] == "failed"
        replay = client.post(args.base + "/webhook/eventops-verify", headers=headers, json=payload).json()
        assert replay["execution_id"] == run["execution_id"]
        state = client.get(
            "http://127.0.0.1:8767/runs/" + run["run_id"] + "/reconcile", headers=service_headers
        ).json()
        assert state["state"] == run["status"] and state["run"]["records"] == run["records"]
        all_csv = export_csv(run["records"])
        verified_csv = export_csv(run["records"], True)
        assert len(list(csv.DictReader(io.StringIO(all_csv)))) == len(run["records"])
        assert len(list(csv.DictReader(io.StringIO(verified_csv)))) == run["summary"]["verified"]
        report["runs"].append(
            {
                "scenario": scenario,
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "run": run,
                "checks": {
                    "replay": "passed",
                    "reconciliation": "passed",
                    "all_csv": "passed",
                    "verified_csv": "passed",
                },
            }
        )
        if scenario == "assessment_event":
            folder.joinpath("assessment-all.csv").write_text(export_csv(sanitize(run)["records"]))
            folder.joinpath("assessment-verified.csv").write_text(export_csv(sanitize(run)["records"], True))
    for header, label in [({}, "missing_auth"), ({"X-EventOps-Webhook": "wrong"}, "wrong_auth")]:
        response = client.post(args.base + "/webhook/eventops-verify", headers=header, json={})
        assert response.status_code in (401, 403)
        report["checks"].append({"check": label, "http_status": response.status_code, "status": "passed"})
    if args.models:
        run = report["runs"][0]["run"]
        for r in run["records"]:
            for e in r["evidence"]:
                if e["source"] == "email":
                    assert "CONTROLLED SYNTHETIC ASSESSMENT REGISTRATION" in e["excerpt"]
                    assert r["email"].endswith("@example.com")
        request = {
            "owner": owner,
            "run_id": run["run_id"],
            "intent": "Explain successful and rejected registrations, merged duplicates, source conflicts and missing information. Inspect findings, references and evidence. Propose human review actions without modifying any statuses.",
        }
        start = time.perf_counter()
        response = client.post(args.base + "/webhook/eventops-agent", headers=headers, json=request)
        response.raise_for_status()
        agent = response.json()
        report["agent"] = {"elapsed_seconds": time.perf_counter() - start, "result": agent}
        assert agent["status"] == "completed", str(agent)[:200]
        again = client.post(args.base + "/webhook/eventops-agent", headers=headers, json=request).json()
        assert again.get("execution_id") == agent["execution_id"]
        report["agent"]["repeat_reused_same_result"] = True
        from eventops.rag import SemanticIndex, ask

        idx = SemanticIndex()
        local = Store("sqlite:///storage/iteration002-models.db")
        answers = []
        for query, previous in [
            ("Where is EVT-101 held?", None),
            ("And what are its check-in rules?", "EVT-101"),
        ]:
            start = time.perf_counter()
            answer = ask(idx, local, owner, query, previous, generate=True)
            answers.append({"elapsed_seconds": time.perf_counter() - start, **answer})
            assert answer["response"]["status"] == "generated"
        report["rag"] = answers
folder.joinpath("full-stack-acceptance.json").write_text(json.dumps(sanitize(report), indent=2))
print(
    json.dumps(
        {
            "runs": [
                {
                    "scenario": r["scenario"],
                    "execution_id": r["run"]["execution_id"],
                    "status": r["run"]["status"],
                    "summary": r["run"]["summary"],
                }
                for r in report["runs"]
            ],
            "agent": report.get("agent", {}).get("result", {}).get("status"),
            "artifact": str(folder / "full-stack-acceptance.json"),
        },
        indent=2,
    )
)
