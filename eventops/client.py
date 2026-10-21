"""Protected n8n production-webhook client, with recoverable persisted requests."""

import uuid
from urllib.parse import urlsplit

import httpx

from eventops.config import setting
from eventops.store import now


def webhook_url(agent=False):
    url = setting("N8N_AGENT_URL" if agent else "N8N_WEBHOOK_URL")
    p = urlsplit(url)
    if (
        not p.hostname
        or p.username
        or p.password
        or p.query
        or p.fragment
        or not p.path.startswith("/webhook/")
    ):
        raise ValueError("Configure a production n8n webhook URL")
    if p.scheme != "https" and not (
        p.scheme == "http"
        and (
            p.hostname in ("127.0.0.1", "localhost")
            or (setting("EVENTOPS_LOCAL_COMPOSE") == "true" and p.hostname == "n8n")
        )
    ):
        raise ValueError("Remote n8n webhooks require HTTPS")
    if setting("PUBLIC_DEMO") == "true" and p.hostname in ("localhost", "127.0.0.1"):
        raise ValueError("Hosted mode cannot use a localhost webhook")
    return url


def trigger(store, owner, event_id, limit=3, request_id=None, transport=None, scenario="external_reference"):
    request_id = request_id or str(uuid.uuid4())
    payload = {
        "owner": owner,
        "event_id": event_id,
        "limit": limit,
        "request_id": request_id,
        "scenario": scenario,
    }
    try:
        with httpx.Client(timeout=120, follow_redirects=False, transport=transport) as client:
            response = client.post(
                webhook_url(),
                headers={"X-EventOps-Webhook": setting("N8N_WEBHOOK_TOKEN")},
                json=payload,
            )
        if response.status_code in (400, 401, 403, 409, 422):
            result = {
                **payload,
                "run_id": request_id,
                "status": "request_rejected",
                "http_status": response.status_code,
                "records": [],
                "outcomes": [],
                "error": "Webhook rejected this request. Correct authentication or input before a deliberate retry.",
            }
            key = "request-" + request_id
            if not store.get(owner, key):
                store.save(owner, "request", result, key)
            return result
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict) or result.get("run_id") != request_id or "status" not in result:
            raise ValueError("Invalid n8n response")
        return result
    except (httpx.HTTPError, ValueError):
        # Retain uncertain delivery. Never rerun automatically after a timeout.
        existing = store.get(owner, request_id)
        if existing:
            return existing["payload"]
        result = {
            **payload,
            "run_id": request_id,
            "status": "delivery_unknown",
            "started_at": now(),
            "records": [],
            "outcomes": [],
            "error": "Webhook unavailable, rejected, or interrupted. Check n8n before retrying this request ID.",
        }
        if not store.get(owner, "request-" + request_id):
            store.save(owner, "request", result, "request-" + request_id)
        return result


def explain(owner, run_id, intent):
    with httpx.Client(timeout=120, follow_redirects=False) as client:
        response = client.post(
            webhook_url(True),
            headers={"X-EventOps-Webhook": setting("N8N_WEBHOOK_TOKEN")},
            json={"owner": owner, "run_id": run_id, "intent": intent},
        )
    response.raise_for_status()
    return response.json()


def reconcile_request(store, owner, request_id):
    from eventops.lifecycle import reconcile

    return reconcile(store, owner, request_id)
