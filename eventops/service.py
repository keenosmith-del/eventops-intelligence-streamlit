"""Narrow, authenticated primitives for the n8n graph; no whole-pipeline endpoint."""

import hmac
import json
import re
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from eventops import pipeline, providers
from eventops.config import setting
from eventops.knowledge import load_documents
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

    if int(request.headers.get("content-length", "0")) > 2_000_000:
        return JSONResponse({"detail": "Payload too large"}, status_code=413)
    body = await request.body()
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
        return {"replayed": True, "run_id": run_id, "run": existing["payload"]}
    try:
        store.save(
            data.owner,
            "run",
            {
                **data.model_dump(),
                "status": "running",
                "started_at": now(),
                "records": [],
                "outcomes": [],
            },
            run_id,
        )
    except Exception as exc:
        from sqlalchemy.exc import IntegrityError

        if isinstance(exc, IntegrityError):
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
            "status": "failed",
            "error": str(exc),
            "messages": [],
        }


@app.get("/sources/config", dependencies=[Depends(authorize)])
def source_config():
    urls = {
        "calendar": setting("CALENDAR_FEED_URL", providers.DEFAULT_CALENDAR),
        "web": setting("WEB_SOURCE_URL", providers.DEFAULT_WEB),
    }
    errors = {}
    for source, url in urls.items():
        try:
            # Network/DNS failures belong to each n8n source read, not global configuration.
            providers.validate_url(url, resolve=False)
        except providers.SourceError as exc:
            errors[source] = str(exc)
            urls[source] = ""
    return {**urls, "configuration_errors": errors}


@app.post("/stages/extract", dependencies=[Depends(authorize)])
def extraction(data: ExtractInput):
    payload = {**data.payload, "source": data.source}
    try:
        records = pipeline.extract(payload, data.limit)
        return {
            "records": records,
            "outcome": {
                "source": data.source,
                "status": payload.get("status", "failed"),
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
    if current["payload"]["status"] != "running":
        return current["payload"]
    if {x.get("source") for x in data.outcomes} != {"calendar", "email", "web"}:
        raise HTTPException(422, "All three source outcomes required")
    # Reapply authoritative verification even if an intermediate node is altered.
    records = pipeline.verify(data.records, data.event_id)
    completed = sum(o["status"] == "completed" for o in data.outcomes)
    result = {
        **current["payload"],
        "run_id": data.run_id,
        "execution_id": data.execution_id,
        "orchestrator": "n8n",
        "status": (
            "completed" if completed == 3 else "partial" if completed else "failed"
        ),
        "finished_at": now(),
        "records": records,
        "outcomes": data.outcomes,
        "summary": pipeline.summary(records),
        "agent": {"status": "not_requested"},
    }
    store.replace(data.owner, data.run_id, result)
    return result


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
                if (
                    "CONTROLLED SYNTHETIC ASSESSMENT REGISTRATION" not in excerpt
                    or any(
                        not email.casefold().endswith("@example.com")
                        for email in emails
                    )
                ):
                    raise HTTPException(
                        422,
                        "Only labelled synthetic example.com sandbox messages may be sent to the demonstration agent",
                    )
    if not store.budget("n8n-agent", 5):
        raise HTTPException(429, "Daily agent execution budget exhausted")
    return {
        **data.model_dump(),
        "event_id": payload["event_id"],
        "references": [
            r
            for r in load_documents()
            if payload["event_id"] in r["scope"] or "ALL" in r["scope"]
        ],
        "findings": [
            {
                "id": r["id"],
                "status": r["status"],
                "issues": r["issues"],
                "checks": r["checks"],
            }
            for r in payload["records"]
        ],
        "evidence": [
            {"id": r["id"], "evidence": r["evidence"]} for r in payload["records"]
        ],
    }


class AgentAnswer(Contract):
    summary: str = Field(max_length=6000)
    intent: str = Field(max_length=1000)
    evidence_ids: list[str] = Field(max_length=30)
    limitations: list[str] = Field(max_length=10)


class AgentFinish(AgentInput):
    execution_id: str
    output: str = Field(max_length=12000)
    intermediate_steps: list[dict] = Field(max_length=20)
    error: bool = False


@app.post("/agent/finish", dependencies=[Depends(authorize)])
def agent_finish(data: AgentFinish):
    store = Store()
    run = store.get(data.owner, data.run_id)
    if not run or run["kind"] != "run":
        raise HTTPException(404, "Run not found")
    payload = run["payload"]
    agent = {
        "status": "unavailable",
        "execution_id": data.execution_id,
        "model": "gemini-3.5-flash-lite",
        "tool_calls": [],
        "note": "No validated model-assisted result available.",
    }
    try:
        answer = AgentAnswer.model_validate_json(
            re.sub(r"^```(?:json)?\s*|\s*```$", "", data.output.strip())
        )
        calls = []
        observed_ids = set()
        allowed = {"reference_lookup", "inspect_findings", "inspect_evidence"}
        for step in data.intermediate_steps:
            action = step.get("action", {})
            if action.get("tool") not in allowed:
                raise ValueError("Unapproved tool")
            # Citations must occur in actual tool results, not merely exist somewhere in the dataset.
            observation = step.get("observation", "")
            observed = (
                json.loads(observation) if isinstance(observation, str) else observation
            )
            # n8n Code Tools wrap string results as [{"response": "<JSON>"}].
            if (
                isinstance(observed, list)
                and len(observed) == 1
                and isinstance(observed[0], dict)
            ):
                observed = json.loads(observed[0].get("response", ""))
            if not isinstance(observed, dict) or not isinstance(
                observed.get("records"), list
            ):
                raise ValueError("Invalid tool observation")
            observed_ids.update(
                r["id"]
                for r in observed["records"]
                if isinstance(r, dict) and "id" in r
            )
            # Store observable tool calls and results; omit internal agent logs/thoughts.
            calls.append(
                {
                    "tool": action["tool"],
                    "input": action.get("toolInput"),
                    "observation": str(step.get("observation", ""))[:16000],
                }
            )
        ids = observed_ids & (
            {r["id"] for r in payload["records"]} | {r["id"] for r in load_documents()}
        )
        if (
            data.error
            or not calls
            or not answer.summary
            or not answer.evidence_ids
            or not set(answer.evidence_ids) <= ids
        ):
            raise ValueError("Missing model execution evidence or invalid citations")
        agent = {
            **agent,
            "status": "completed",
            "note": "Model explanation; deterministic record statuses remain authoritative.",
            "result": answer.model_dump(),
            "tool_calls": calls,
        }
    except (ValueError, TypeError, KeyError):
        pass
    payload["agent"] = agent
    store.replace(data.owner, data.run_id, payload)
    store.save(data.owner, "agent", {"run_id": data.run_id, **agent})
    return agent
