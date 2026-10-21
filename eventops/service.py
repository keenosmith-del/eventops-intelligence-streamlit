"""Narrow, authenticated primitives for the n8n graph; no whole-pipeline endpoint."""

import hashlib
import hmac
import json
import re
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from eventops import pipeline, providers
from eventops.config import setting
from eventops.knowledge import fingerprint, load_documents
from eventops.scenarios import configuration
from eventops.store import Store, now

app = FastAPI(
    title="EventOps companion primitives",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.middleware("http")
async def bounded_body(request: Request, call_next):
    from starlette.responses import JSONResponse

    if not request.headers.get("content-length", "0").isdigit():
        return JSONResponse({"detail": "Invalid content length"}, status_code=400)
    if int(request.headers.get("content-length", "0")) > 2_000_000:
        return JSONResponse({"detail": "Payload too large"}, status_code=413)
    chunks = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > 2_000_000:
            return JSONResponse({"detail": "Payload too large"}, status_code=413)
        chunks.append(chunk)
    body = b"".join(chunks)
    request._body = body
    if len(body) > 2_000_000:
        return JSONResponse({"detail": "Payload too large"}, status_code=413)
    return await call_next(request)


def authorize(x_eventops_token: str = Header(default="")):
    expected = setting("EVENTOPS_SERVICE_TOKEN")
    if len(expected) < 32 or not hmac.compare_digest(expected, x_eventops_token):
        raise HTTPException(401, "Invalid service credential")


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RunInput(Contract):
    owner: str = Field(pattern=r"^[a-zA-Z0-9-]{16,80}$")
    request_id: str = Field(pattern=r"^[a-zA-Z0-9-]{16,80}$")
    event_id: str = Field(pattern=r"^EVT-\d{3}$")
    limit: int = Field(default=3, ge=1, le=5)
    scenario: Literal["external_reference", "assessment_event", "provider_unavailable"] = "external_reference"
    execution_id: str | None = Field(default=None, max_length=80)


class Stage(Contract):
    records: list[dict] = Field(max_length=30)


class ExtractInput(Contract):
    source: Literal["calendar", "email", "web"]
    payload: dict
    limit: int = Field(default=3, ge=1, le=5)


class VerificationInput(Stage):
    event_id: str = Field(pattern=r"^EVT-\d{3}$")


class Finish(RunInput):
    run_id: str
    execution_id: str
    outcomes: list[dict] = Field(min_length=3, max_length=3)
    records: list[dict] = Field(max_length=30)


@app.get("/health")
def health():
    return {"status": "ok", "application": "eventops-streamlit-companion"}


@app.post("/runs/begin", dependencies=[Depends(authorize)])
def begin(data: RunInput):
    if data.event_id not in {r["id"] for r in load_documents() if r["kind"] == "event"}:
        raise HTTPException(422, "Unknown target event")
    store = Store()
    run_id = data.request_id
    existing = store.get(data.owner, run_id)
    if existing:
        if any(
            existing["payload"].get(k, "external_reference" if k == "scenario" else None) != getattr(data, k)
            for k in ("event_id", "limit", "scenario")
        ):
            raise HTTPException(409, "Request ID is already bound to different inputs")
        return {"replayed": True, "run_id": run_id, "run": {"run_id": run_id, **existing["payload"]}}
    try:
        store.save(
            data.owner,
            "run",
            {
                **data.model_dump(),
                "run_id": run_id,
                "status": "running",
                "started_at": now(),
                "heartbeat_at": now(),
                "stages": [],
                "records": [],
                "outcomes": [],
            },
            run_id,
        )
    except Exception as exc:
        from sqlalchemy.exc import IntegrityError

        if isinstance(exc, IntegrityError):
            existing = store.get(data.owner, run_id)
            if existing:
                if any(
                    existing["payload"].get(k, "external_reference" if k == "scenario" else None)
                    != getattr(data, k)
                    for k in ("event_id", "limit", "scenario")
                ):
                    raise HTTPException(409, "Request ID is already bound to different inputs")
                return {"replayed": True, "run_id": run_id, "run": {"run_id": run_id, **existing["payload"]}}
            raise HTTPException(409, "Execution ID already reserved") from exc
        raise
    return {"replayed": False, "run_id": run_id, **data.model_dump()}


@app.get("/sources/email", dependencies=[Depends(authorize)])
def email(limit: int = 3):
    if not 1 <= limit <= 5:
        raise HTTPException(422, "Limit must be 1–5")
    try:
        return providers.read_source("email", limit)
    except providers.SourceError as exc:
        return {
            "source": "email",
            "status": "timed_out" if "timed out" in str(exc) else "failed",
            "error": str(exc),
            "messages": [],
        }


@app.get("/sources/config", dependencies=[Depends(authorize)])
def source_config(scenario: str = "external_reference"):
    try:
        return configuration(scenario)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/stages/extract", dependencies=[Depends(authorize)])
def extraction(data: ExtractInput):
    payload = {**data.payload, "source": data.source}
    try:
        records = pipeline.extract(payload, data.limit)
        return {
            "records": records,
            "outcome": {
                "source": data.source,
                "status": ("completed_empty" if not records else "completed")
                if payload.get("status") == "completed"
                else payload.get("status", "failed"),
                "reference": payload.get("reference"),
                "count": len(records),
                "error": payload.get("error"),
                "observed_at": now(),
            },
        }
    except (ValueError, KeyError, TypeError, AttributeError):
        return {
            "records": [],
            "outcome": {
                "source": data.source,
                "status": "failed",
                "count": 0,
                "error": "Unexpected source response schema",
                "observed_at": now(),
            },
        }


@app.post("/stages/normalize", dependencies=[Depends(authorize)])
def normalization(data: Stage):
    return {"records": pipeline.normalize(data.records)}


@app.post("/stages/deduplicate", dependencies=[Depends(authorize)])
def deduplication(data: Stage):
    return {"records": pipeline.deduplicate(data.records)}


@app.post("/stages/verify", dependencies=[Depends(authorize)])
def verification(data: VerificationInput):
    return {"records": pipeline.verify(data.records, data.event_id)}


@app.post("/runs/finish", dependencies=[Depends(authorize)])
def finish(data: Finish):
    store = Store()
    current = store.get(data.owner, data.run_id)
    if not current or current["payload"].get("request_id") != data.request_id:
        raise HTTPException(404, "Execution not found")
    if any(
        current["payload"].get(k, "external_reference" if k == "scenario" else None) != getattr(data, k)
        for k in ("event_id", "scenario", "limit")
    ):
        raise HTTPException(409, "Finalization inputs differ from reserved request")
    if current["payload"]["status"] != "running":
        return current["payload"]
    if {x.get("source") for x in data.outcomes} != {"calendar", "email", "web"}:
        raise HTTPException(422, "All three source outcomes required")
    allowed = {"completed", "completed_empty", "failed", "unavailable", "timed_out", "partially_processed"}
    if any(o.get("status") not in allowed for o in data.outcomes):
        raise HTTPException(422, "Invalid source outcome status")
    # Reapply authoritative verification even if an intermediate node is altered.
    records = pipeline.verify(data.records, data.event_id)
    completed = sum(o["status"] in ("completed", "completed_empty") for o in data.outcomes)
    result = {
        **current["payload"],
        "run_id": data.run_id,
        "execution_id": data.execution_id,
        "orchestrator": "n8n",
        "status": ("completed" if completed == 3 else "partial" if completed else "failed"),
        "finished_at": now(),
        "records": records,
        "outcomes": data.outcomes,
        "summary": pipeline.summary(records),
        "agent": {"status": "not_requested"},
    }

    def finalize(existing):
        if existing["status"] != "running":
            return existing
        return {**existing, **result, "stages": existing.get("stages", [])}

    return store.mutate(data.owner, data.run_id, finalize)


class Checkpoint(Contract):
    owner: str = Field(pattern=r"^[a-zA-Z0-9-]{16,80}$")
    run_id: str = Field(pattern=r"^[a-zA-Z0-9-]{16,80}$")
    execution_id: str = Field(max_length=80)
    stage: str = Field(min_length=1, max_length=100)
    outcome: dict | None = None


@app.post("/runs/checkpoint", dependencies=[Depends(authorize)])
def checkpoint(data: Checkpoint):
    def change(run):
        if run["status"] != "running":
            return run
        stages = run.get("stages", [])
        if not any(s["stage"] == data.stage for s in stages):
            stages.append({"stage": data.stage, "at": now(), "outcome": data.outcome})
        return {**run, "stages": stages, "heartbeat_at": now(), "execution_id": data.execution_id}

    try:
        return Store().mutate(data.owner, data.run_id, change)
    except KeyError as exc:
        raise HTTPException(404, "Run not found") from exc


@app.get("/runs/{run_id}/reconcile", dependencies=[Depends(authorize)])
def reconcile_run(run_id: str, x_workspace_key: str = Header(default="")):
    from eventops.lifecycle import reconcile

    return reconcile(Store(), x_workspace_key, run_id)


def snapshot(payload):
    return {
        "references": [
            r for r in load_documents() if payload["event_id"] in r["scope"] or "ALL" in r["scope"]
        ],
        "findings": [
            {"id": r["id"], "status": r["status"], "issues": r["issues"], "checks": r["checks"]}
            for r in payload["records"]
        ],
        "evidence": [{"id": r["id"], "evidence": r["evidence"]} for r in payload["records"]],
    }


def snapshot_hash(payload):
    return fingerprint(
        [
            snapshot(payload),
            {
                "outcomes": payload["outcomes"],
                "review_states": [(r["id"], r.get("review_status")) for r in payload["records"]],
            },
        ]
    )


class AgentInput(Contract):
    owner: str = Field(pattern=r"^[a-zA-Z0-9-]{16,80}$")
    run_id: str = Field(pattern=r"^[a-zA-Z0-9-]{16,80}$")
    intent: str = Field(min_length=1, max_length=1000)


@app.post("/agent/context", dependencies=[Depends(authorize)])
def agent_context(data: AgentInput):
    store = Store()
    run = store.get(data.owner, data.run_id)
    if not run or run["kind"] != "run" or run["payload"]["status"] == "running":
        raise HTTPException(404, "Finished execution not found")
    if setting("GEMINI_ENABLED") != "true" or not setting("GEMINI_API_KEY"):
        raise HTTPException(503, "Gemini is not configured")
    payload = run["payload"]
    # This demonstration sends only explicitly controlled synthetic sandbox messages to Gemini.
    for record in payload["records"]:
        for evidence in record.get("evidence", []):
            if evidence.get("source") == "email":
                excerpt = evidence.get("excerpt", "")
                emails = re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", excerpt)
                if "CONTROLLED SYNTHETIC ASSESSMENT REGISTRATION" not in excerpt or any(
                    not email.casefold().endswith("@example.com") for email in emails
                ):
                    raise HTTPException(
                        422,
                        "Only labelled synthetic example.com sandbox messages may be sent to the demonstration agent",
                    )
    digest = snapshot_hash(payload)
    key = hashlib.sha256((data.owner + data.run_id + data.intent.strip() + digest).encode()).hexdigest()
    claim = store.claim_investigation(data.owner, key)
    if not claim["claimed"]:
        return {
            "replayed": True,
            "agent": claim["result"]
            or {
                "status": claim["state"],
                "note": "Identical investigation already reserved; no second model execution.",
            },
        }
    if not store.budget("n8n-agent", 5):
        result = {"status": "unavailable", "reason": "daily_budget_exhausted"}
        store.finish_investigation(data.owner, key, result)
        raise HTTPException(429, "Daily agent execution budget exhausted")
    return {
        **data.model_dump(),
        "event_id": payload["event_id"],
        "replayed": False,
        "investigation_id": key,
        "snapshot_hash": digest,
        **snapshot(payload),
    }


class EvidenceFinding(Contract):
    description: str = Field(max_length=1500)
    evidence_ids: list[str] = Field(min_length=1, max_length=10)


class AgentAnswer(Contract):
    summary: str = Field(max_length=6000)
    intent: str = Field(max_length=1000)
    evidence_ids: list[str] = Field(max_length=30)
    limitations: list[str] = Field(max_length=10)
    findings: list[EvidenceFinding] = Field(default_factory=list, max_length=10)
    conflicts: list[EvidenceFinding] = Field(default_factory=list, max_length=10)
    suggested_review_actions: list[str] = Field(default_factory=list, max_length=10)
    uncertainties: list[str] = Field(default_factory=list, max_length=10)


class AgentFinish(AgentInput):
    execution_id: str
    output: str = Field(max_length=12000)
    intermediate_steps: list[dict] = Field(max_length=20)
    error: bool = False
    investigation_id: str | None = Field(default=None, max_length=64)
    snapshot_hash: str | None = Field(default=None, max_length=64)


@app.post("/agent/finish", dependencies=[Depends(authorize)])
def agent_finish(data: AgentFinish):
    store = Store()
    run = store.get(data.owner, data.run_id)
    if not run or run["kind"] != "run":
        raise HTTPException(404, "Run not found")
    payload = run["payload"]
    if data.snapshot_hash and data.snapshot_hash != snapshot_hash(payload):
        raise HTTPException(409, "Run evidence changed during investigation")
    agent = {
        "status": "unavailable",
        "execution_id": data.execution_id,
        "model": "gemini-3.5-flash-lite",
        "tool_calls": [],
        "note": "No validated model-assisted result available.",
    }
    calls = []
    rejection_code = "invalid_schema"
    try:
        answer = AgentAnswer.model_validate_json(re.sub(r"^```(?:json)?\s*|\s*```$", "", data.output.strip()))
        calls = []
        observed_ids = set()
        allowed = {"reference_lookup", "inspect_findings", "inspect_evidence"}
        for step in data.intermediate_steps:
            action = step.get("action", {})
            if action.get("tool") not in allowed:
                raise ValueError("Unapproved tool")
            # Citations must occur in actual tool results, not merely exist somewhere in the dataset.
            observation = step.get("observation", "")
            observed = json.loads(observation) if isinstance(observation, str) else observation
            # n8n Code Tools wrap string results as [{"response": "<JSON>"}].
            if isinstance(observed, list) and len(observed) == 1 and isinstance(observed[0], dict):
                observed = json.loads(observed[0].get("response", ""))
            if not isinstance(observed, dict) or not isinstance(observed.get("records"), list):
                raise ValueError("Invalid tool observation")
            field = {
                "reference_lookup": "references",
                "inspect_findings": "findings",
                "inspect_evidence": "evidence",
            }[action["tool"]]
            expected = {r["id"]: r for r in snapshot(payload)[field]}
            if any(not isinstance(r, dict) or expected.get(r.get("id")) != r for r in observed["records"]):
                raise ValueError("Tool observation differs from permitted evidence")
            observed_ids.update(r["id"] for r in observed["records"] if isinstance(r, dict) and "id" in r)
            # Store observable tool calls and results; omit internal agent logs/thoughts.
            calls.append(
                {
                    "tool": action["tool"],
                    "input": action.get("toolInput"),
                    "observation": str(step.get("observation", ""))[:16000],
                }
            )
        cited = set(answer.evidence_ids) | {
            rid for item in answer.findings + answer.conflicts for rid in item.evidence_ids
        }
        ids = observed_ids & ({r["id"] for r in payload["records"]} | {r["id"] for r in load_documents()})
        if data.error or not calls or not answer.summary or not answer.evidence_ids or not cited <= ids:
            raise ValueError("Missing model execution evidence or invalid citations")
        agent = {
            **agent,
            "status": "completed",
            "note": "Model explanation; deterministic record statuses remain authoritative.",
            "result": answer.model_dump(),
            "tool_calls": calls,
        }
    except (ValueError, TypeError, KeyError):
        agent = {
            **agent,
            "reason": rejection_code,
            "model_execution_observed": bool(calls),
            "tool_calls": calls,
            "note": "Model output rejected by evidence validation; deterministic results remain available.",
        }

    def save_agent(current):
        if data.snapshot_hash and data.snapshot_hash != snapshot_hash(current):
            raise HTTPException(409, "Evidence changed before saving investigation")
        return {**current, "agent": agent}

    store.mutate(data.owner, data.run_id, save_agent)
    if data.investigation_id:
        store.finish_investigation(data.owner, data.investigation_id, agent)
    store.save(data.owner, "agent", {"run_id": data.run_id, **agent})
    return agent
