"""Read-only reconciliation. Age is uncertainty, never proof of failure or completion."""

from datetime import datetime, timezone

import httpx

from eventops.config import setting


def reconcile(store, owner, request_id, transport=None):
    row = store.get(owner, request_id)
    pending = store.get(owner, "request-" + request_id)
    if not row:
        return {
            "state": "delivery_unknown" if pending else "not_observed",
            "request_id": request_id,
            "note": "No reservation observed. This does not prove the webhook never reached n8n.",
        }
    run = row["payload"]
    status = run["status"]
    result = {
        "request_id": request_id,
        "state": status,
        "run": run,
        "metadata_source": "persisted companion run",
    }
    if status != "running":
        return result
    last = run.get("heartbeat_at", run["started_at"])
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds()
    result["state"] = (
        "intervention_required" if age > int(setting("STALE_RUN_SECONDS", "180")) else "processing"
    )
    result["age_seconds"] = round(age, 1)
    result["note"] = "Stale checkpoint is not proof of failure. No automatic replay or recovery is performed."
    # Optional read-only n8n public API metadata; only the execution already bound to this owner/run.
    base = setting("N8N_METADATA_URL")
    key = setting("N8N_API_KEY")
    eid = run.get("execution_id")
    if base and key and eid and str(eid).isdigit():
        from urllib.parse import urlsplit

        p = urlsplit(base)
        if p.scheme == "https" or (
            setting("EVENTOPS_LOCAL_COMPOSE") == "true" and p.scheme == "http" and p.hostname == "n8n"
        ):
            try:
                with httpx.Client(timeout=5, transport=transport, follow_redirects=False) as client:
                    response = client.get(
                        base.rstrip("/") + "/api/v1/executions/" + str(eid),
                        headers={"X-N8N-API-KEY": key},
                        params={"includeData": "false"},
                    )
                response.raise_for_status()
                metadata = response.json()
                if metadata.get("workflowId") != "EventOpsVerify01" or str(metadata.get("id")) != str(eid):
                    raise ValueError("Execution metadata mismatch")
                result["n8n_status"] = metadata.get("status")
                if metadata.get("status") in ("error", "crashed", "canceled"):
                    result["state"] = "failed_before_persistence"
                elif metadata.get("status") == "success":
                    result["state"] = "intervention_required"
                    result["note"] = (
                        "n8n finished without authoritative persisted results. Reconcile manually; not complete."
                    )
            except (httpx.HTTPError, ValueError, KeyError):
                result["metadata_error"] = "n8n metadata unavailable"
    return result
