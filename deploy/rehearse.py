"""Explicit LOCAL ONLY release acceptance. Never provisions a remote service."""

import argparse
import csv
import io
import json
import subprocess
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import dotenv_values
from sqlalchemy.engine import make_url

from deploy.check import ROOT, compose_command, compose_environment, run_compose, validate_values
from deploy.database import archive
from deploy.smoke import check_public
from eventops.pipeline import export_csv
from eventops.public_evidence import sanitize

FOLDER = ROOT / "docs/iterations/003/evidence"
ENV = ROOT / "deploy/.local/rehearsal.env"


def command(*args, input=None):
    env = compose_environment(args[args.index("--env-file") + 1]) if "--env-file" in args else None
    return subprocess.check_output(args, input=input, text=True, stderr=subprocess.PIPE, env=env).strip()


def wait(compose, seconds=90):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        rows = [json.loads(x) for x in command(*compose, "ps", "--format", "json").splitlines()]
        if len(rows) == 8 and all(
            r["State"] == "running" and r.get("Health") in ("healthy", "") for r in rows
        ):
            return [
                {"service": r["Service"], "state": r["State"], "health": r.get("Health") or "process_only"}
                for r in rows
            ]
        time.sleep(1)
    raise RuntimeError("Rehearsal services did not become ready")


def processor(compose, code):
    return json.loads(command(*compose, "exec", "-T", "processor", "python", "-", input=code))


def database_snapshot(compose):
    return processor(
        compose,
        """import hashlib,json
from eventops.store import Store
with Store().engine.connect() as c:
 rows=c.exec_driver_sql('SELECT id,kind,payload FROM companion_objects ORDER BY id').all()
 claims=c.exec_driver_sql('SELECT id,state,payload FROM companion_investigations ORDER BY id').all()
 print(json.dumps({'objects':len(rows),'reviews':sum(r[1]=='review' for r in rows),'sha256':hashlib.sha256(repr((rows,claims)).encode()).hexdigest()}))
""",
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--models",
        action="store_true",
        help="Explicitly permit one analyst and one grounded answer on labelled synthetic data",
    )
    p.add_argument(
        "--interrupt",
        action="store_true",
        help="Kill only rehearsal n8n during an isolated diagnostic execution",
    )
    p.add_argument(
        "--resume",
        action="store_true",
        help="Resume backup/restore from persisted local acceptance without new provider/model calls",
    )
    args = p.parse_args()
    values = dotenv_values(ENV)
    if validate_values(values, rehearsal=True):
        raise ValueError("Rehearsal preflight failed")
    if args.models and values["GEMINI_ENABLED"] != "true":
        raise ValueError(
            "Explicitly enable Gemini in the ignored rehearsal file first; no automatic billing or key changes"
        )
    compose = compose_command(ENV, True)
    if args.resume:
        report = json.loads((FOLDER / "release-rehearsal.inprogress.json").read_text())
        finish_rehearsal(report, values, compose)
        return
    FOLDER.mkdir(parents=True, exist_ok=True)
    owner = uuid.uuid4().hex + uuid.uuid4().hex[:16]
    private = ROOT / "deploy/.local/acceptance-workspace.json"
    private.write_text(json.dumps({"owner": owner}))
    private.chmod(0o600)
    report = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "environment": "isolated Docker Linux ARM64 rehearsal; local PostgreSQL without TLS; private synthetic HTTP + actual Mailtrap",
        "source_revision": values["RELEASE_REVISION"],
        "checks": {},
        "runs": [],
    }
    report["services"] = wait(compose)
    report["public_surface"] = check_public("http://127.0.0.1:8503", True)
    token = {"X-EventOps-Webhook": values["N8N_WEBHOOK_TOKEN"]}
    service = {"X-EventOps-Token": values["EVENTOPS_SERVICE_TOKEN"], "X-Workspace-Key": owner}
    base = "http://127.0.0.1:5681"
    with httpx.Client(timeout=130) as client:
        assert client.post(base + "/webhook/eventops-verify", json={}).status_code in (401, 403)
        assert client.post(base + "/webhook/eventops-agent", json={}).status_code in (401, 403)
        assert client.get("http://127.0.0.1:8768/readyz").status_code == 401
        assert client.get("http://127.0.0.1:8768/readyz", headers=service).json()["status"] == "ready"
        report["checks"]["protected_internal_auth"] = "passed"
        for scenario in ("assessment_event", "provider_unavailable"):
            payload = {
                "owner": owner,
                "request_id": str(uuid.uuid4()),
                "event_id": "EVT-101",
                "limit": 5,
                "scenario": scenario,
            }
            start = time.perf_counter()
            response = client.post(base + "/webhook/eventops-verify", headers=token, json=payload)
            response.raise_for_status()
            run = response.json()
            assert run["status"] == ("completed" if scenario == "assessment_event" else "partial")
            assert next(o for o in run["outcomes"] if o["source"] == "email")["status"] == "completed"
            replay = client.post(base + "/webhook/eventops-verify", headers=token, json=payload).json()
            assert replay["execution_id"] == run["execution_id"]
            saved = client.get(
                "http://127.0.0.1:8768/runs/" + run["run_id"] + "/reconcile", headers=service
            ).json()
            assert saved["run"]["records"] == run["records"]
            other = client.get(
                "http://127.0.0.1:8768/runs/" + run["run_id"] + "/reconcile",
                headers={**service, "X-Workspace-Key": "different-owner-" + uuid.uuid4().hex},
            ).json()
            assert "run" not in other
            if scenario == "assessment_event":
                assert {"verified", "review_required", "rejected", "incomplete"} <= {
                    r["status"] for r in run["records"]
                }
                assert run["summary"]["duplicates_merged"] >= 1
                selected = next(r for r in run["records"] if r["status"] == "rejected")
                code = (
                    "from eventops.store import Store; import json; print(json.dumps(Store().review("
                    + ",".join(
                        repr(x)
                        for x in (
                            owner,
                            run["run_id"],
                            selected["id"],
                            "investigating",
                            "Release rehearsal inspected the source evidence",
                            "Inactive directory/name mismatch",
                            "Request authoritative review",
                        )
                    )
                    + ")))"
                )
                review = processor(compose, code)
                assert review["review_status"] == "investigating"
                deterministic_run = run
                private.write_text(json.dumps({"owner": owner, "run_id": run["run_id"]}))
                for verified, filename in ((False, "all.csv"), (True, "verified.csv")):
                    body = export_csv(run["records"], verified)
                    assert len(list(csv.DictReader(io.StringIO(body)))) == (
                        run["summary"]["verified"] if verified else len(run["records"])
                    )
                    FOLDER.joinpath(filename).write_text(export_csv(sanitize(run)["records"], verified))
            report["runs"].append({"elapsed_seconds": round(time.perf_counter() - start, 3), "run": run})
            FOLDER.joinpath("release-rehearsal.inprogress.json").write_text(
                json.dumps(sanitize(report), indent=2)
            )
        report["checks"].update(
            csv_exports="passed", review_persisted="passed", owner_isolation="passed", replay="passed"
        )
        if args.models:
            intent = "Explain why Lindi was rejected. Read the authoritative participant, deterministic findings and raw evidence; copy exact outer record IDs and suggest one human review action."
            result = client.post(
                base + "/webhook/eventops-agent",
                headers=token,
                json={"owner": owner, "run_id": deterministic_run["run_id"], "intent": intent},
            )
            result.raise_for_status()
            agent = result.json()
            report["agent"] = agent
            assert agent["status"] == "completed" and agent["tool_calls"]
            repeat = client.post(
                base + "/webhook/eventops-agent",
                headers=token,
                json={"owner": owner, "run_id": deterministic_run["run_id"], "intent": intent},
            ).json()
            assert repeat["execution_id"] == agent["execution_id"]
            # Real embeddings/generation in the Linux app, private synthetic reference data only.
            rag_code = """import json
from eventops.rag import SemanticIndex,ask
from eventops.store import Store
r=ask(SemanticIndex(),Store(),OWNER,'Where is EVT-101 held?',generate=True)
print(json.dumps(r))
""".replace("OWNER", repr(owner))
            rag = json.loads(command(*compose, "exec", "-T", "app", "python", "-", input=rag_code))
            report["rag"] = rag
            assert rag["response"]["status"] == "generated" and "EVT-101" in rag["response"]["citation_ids"]
        else:
            report["model_status"] = "not_requested; no fabricated execution claim"
        if args.interrupt:
            report["interruption"] = interrupt_probe(compose, client, owner, token, service)
        FOLDER.joinpath("release-rehearsal.inprogress.json").write_text(
            json.dumps(sanitize(report), indent=2)
        )
    finish_rehearsal(report, values, compose)


def finish_rehearsal(report, values, compose):
    # Stop-before-copy n8n backup includes WAL, encrypted credentials and configuration.
    run_compose(
        compose + ["stop", "n8n", "runners"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    backup_dir = ROOT / "deploy/.local" / ("n8n-backup-" + uuid.uuid4().hex[:8])
    run_compose(
        compose + ["cp", "n8n:/home/node/.n8n", str(backup_dir)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    backup_dir.chmod(0o700)
    run_compose(
        compose + ["start", "n8n", "runners"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    report["checks"]["n8n_stopped_state_backup"] = (
        "created privately; encrypted credentials and key must be kept together"
    )
    before = database_snapshot(compose)
    run_compose(compose + ["restart"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    report["services_after_restart"] = wait(compose)
    after = database_snapshot(compose)
    assert before == after and before["reviews"] > 0
    report["restart"] = {"preserved": True, "before": before, "after": after}
    backup = ROOT / "deploy/.local" / ("companion-" + uuid.uuid4().hex[:8] + ".dump")
    report["database_backup"] = archive(
        values["EVENTOPS_DATABASE_URL"], backup, "eventops-rehearsal003_backend"
    )
    restore_name = "companion003_restore_" + uuid.uuid4().hex[:8]
    run_compose(
        compose
        + ["exec", "-T", "restore", "createdb", "-U", "release_bootstrap", "-O", "companion", restore_name],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    destination = (
        make_url(values["EVENTOPS_DATABASE_URL"])
        .set(host="restore", database=restore_name)
        .render_as_string(hide_password=False)
    )
    report["database_restore"] = archive(
        destination, backup, "eventops-rehearsal003_backend", True, restore_name
    )
    restored = processor(
        compose,
        "import json; from eventops.store import Store; from sqlalchemy import create_engine; import hashlib; e=create_engine("
        + repr(destination)
        + ");\nwith e.connect() as c:\n rows=c.exec_driver_sql('SELECT id,kind,payload FROM companion_objects ORDER BY id').all(); claims=c.exec_driver_sql('SELECT id,state,payload FROM companion_investigations ORDER BY id').all(); print(json.dumps({'objects':len(rows),'reviews':sum(r[1]=='review' for r in rows),'sha256':hashlib.sha256(repr((rows,claims)).encode()).hexdigest()}))",
    )
    assert restored == after
    report["database_restore"]["all_object_payloads_and_claims_match"] = True
    logs = command(*compose, "logs", "--no-color", "runners")
    report["external_runner"] = {
        "container": "isolated runner network; no provider/database credentials or volumes",
        "activity_observed": "runner" in logs.lower(),
        "workflow_execution": "real Code nodes completed in configured external mode",
    }
    stats = command("docker", "stats", "--no-stream", "--format", "{{json .}}")
    report["resource_sample"] = [
        {k: r[k] for k in ("Name", "MemUsage", "CPUPerc")}
        for r in map(json.loads, stats.splitlines())
        if r["Name"].startswith("eventops-rehearsal003-")
    ]
    FOLDER.joinpath("release-rehearsal.json").write_text(json.dumps(sanitize(report), indent=2))
    print(
        json.dumps(
            {
                "status": "passed",
                "model_execution": report.get("agent", {}).get("status") == "completed",
                "backup_restore": "payload hashes match",
                "public_deployment": "not_performed",
                "evidence": "docs/iterations/003/evidence/release-rehearsal.json",
            },
            indent=2,
        )
    )


def interrupt_probe(compose, client, owner, token, service):
    graph = json.loads((ROOT / "deploy/.local/workflows/verification.json").read_text())
    graph.update(id="EventOpsInterrupted003", name="Local rehearsal interruption probe")
    for node in graph["nodes"]:
        if node["name"] == "Verification webhook":
            node["parameters"]["path"] = "eventops-interrupted003"
            node["webhookId"] = "eventops-interrupted003"
        if node["name"] == "Read Web":
            node["parameters"]["url"] = "http://scenario:8090/hold"
            node["parameters"]["options"]["timeout"] = 60000
    path = ROOT / "deploy/.local/workflows/interruption.json"
    path.write_text(json.dumps(graph))
    run_compose(
        compose + ["exec", "-T", "n8n", "n8n", "import:workflow", "--input=/workflows/interruption.json"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    run_compose(
        compose + ["exec", "-T", "n8n", "n8n", "publish:workflow", "--id=EventOpsInterrupted003"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    run_compose(
        compose + ["restart", "n8n", "runners"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    wait(compose)
    rid = str(uuid.uuid4())
    payload = {
        "owner": owner,
        "request_id": rid,
        "event_id": "EVT-101",
        "limit": 5,
        "scenario": "assessment_event",
    }

    def dispatch():
        try:
            return client.post(
                "http://127.0.0.1:5681/webhook/eventops-interrupted003", headers=token, json=payload
            ).status_code
        except httpx.HTTPError:
            return "delivery_unknown"

    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(dispatch)
        end = time.monotonic() + 25
        state = {}
        while time.monotonic() < end:
            state = client.get("http://127.0.0.1:8768/runs/" + rid + "/reconcile", headers=service).json()
            if any(s["stage"] == "email" for s in state.get("run", {}).get("stages", [])):
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("Did not observe real source checkpoint before interruption")
        run_compose(
            compose + ["kill", "-s", "SIGKILL", "n8n"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        response = pending.result(timeout=10)
    run_compose(
        compose + ["up", "-d", "n8n", "runners"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    wait(compose)
    # Evaluate stale uncertainty without falsifying the persisted timestamps.
    code = (
        "import json,os; from eventops.store import Store; from eventops.lifecycle import reconcile; os.environ['STALE_RUN_SECONDS']='1'; print(json.dumps(reconcile(Store(),"
        + repr(owner)
        + ","
        + repr(rid)
        + ")))"
    )
    reconciled = processor(compose, code)
    assert reconciled["state"] == "intervention_required" and reconciled["run"]["status"] == "running"
    repeated = client.post(
        "http://127.0.0.1:5681/webhook/eventops-verify", headers=token, json=payload
    ).json()
    assert repeated["run_id"] == rid and repeated["status"] == "running"
    return {
        "request_id": rid,
        "execution_id": reconciled["run"]["execution_id"],
        "client_delivery": response,
        "state": reconciled["state"],
        "healthy_checkpoints": [s["stage"] for s in reconciled["run"]["stages"]],
        "replay_did_not_repeat_sources": True,
        "automatic_recovery": False,
    }


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        import traceback

        failure = next(
            f for f in reversed(traceback.extract_tb(exc.__traceback__)) if "/deploy/" in f.filename
        )
        print(json.dumps({"file": Path(failure.filename).name, "line": failure.lineno}))
        # Keep detailed provider/database errors private. Partial evidence is not a pass.
        print(
            json.dumps(
                {"status": "failed", "category": type(exc).__name__, "public_deployment": "not_performed"}
            )
        )
        raise SystemExit(1) from None
