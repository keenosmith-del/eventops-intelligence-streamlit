import os
import re
import threading
import uuid
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding

from eventops.config import ROOT, setting
from eventops.knowledge import fingerprint, load_documents

MODEL = "BAAI/bge-small-en-v1.5"


class SemanticIndex:
    def __init__(self, path=None, records=None):
        self.path = Path(path or ROOT / "storage/index.npz")
        self.records = records if records is not None else load_documents()
        self.model = TextEmbedding(
            model_name=MODEL,
            cache_dir=setting("FASTEMBED_CACHE_PATH", str(ROOT / "storage/models")),
            threads=1,
        )
        self.lock = threading.Lock()
        self.signature = fingerprint(self.records) + ":" + MODEL + ":passage-v1"
        self.vectors = None
        if self.path.exists():
            try:
                with np.load(self.path, allow_pickle=False) as saved:
                    if str(saved["signature"]) == self.signature:
                        self.vectors = saved["vectors"]
                        self._validate(self.vectors)
            except (ValueError, KeyError, OSError):
                self.vectors = None
        if self.vectors is None:
            self.vectors = np.asarray(
                list(self.model.passage_embed([r["content"] for r in self.records], batch_size=4)),
                dtype=np.float32,
            )
            self._validate(self.vectors)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.path.with_suffix(f".{os.getpid()}.{uuid.uuid4().hex}.tmp.npz")
            np.savez_compressed(temp, vectors=self.vectors, signature=self.signature)
            os.replace(temp, self.path)

    def _validate(self, vectors):
        if (
            vectors.shape != (len(self.records), 384)
            or not np.isfinite(vectors).all()
            or np.any(np.linalg.norm(vectors, axis=1) == 0)
        ):
            raise ValueError("Invalid embedding matrix")

    def search(self, plan, depth=5):
        if not 1 <= depth <= 10:
            raise ValueError("Retrieval depth must be 1–10")
        if plan.get("needs_clarification"):
            return []
        with self.lock:
            vector = np.asarray(
                list(self.model.query_embed(plan["normalized_query"]))[0],
                dtype=np.float32,
            )
        scores = self.vectors @ vector / (np.linalg.norm(self.vectors, axis=1) * np.linalg.norm(vector))
        eligible = []
        for i, record in enumerate(self.records):
            if plan["event_id"] and plan["event_id"] not in record["scope"] and "ALL" not in record["scope"]:
                continue
            if plan["kind"] and record["kind"] != plan["kind"]:
                continue
            if plan.get("category") and record["fields"].get("category") != plan["category"]:
                continue
            if float(scores[i]) >= 0.30:
                eligible.append({**record, "similarity": round(float(scores[i]), 4)})
        return sorted(eligible, key=lambda x: x["similarity"], reverse=True)[:depth]


def interpret(question, previous_event=None):
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 1000:
        raise ValueError("Question must contain 1–1000 characters")
    query = " ".join(question.split())
    query = re.sub(r"\bevt[\s_-]?(\d{3})\b", lambda m: "EVT-" + m[1], query, flags=re.I)
    explicit = set(re.findall(r"EVT-\d{3}", query))
    for record in load_documents():
        if record["kind"] == "event":
            title = record["fields"]["title"]
            aliases = [title, " ".join(title.split()[:-1]), title.split()[-1]]
            if any(
                re.search(r"\b" + re.escape(alias) + r"\b", query, re.I)
                for alias in aliases
                if len(alias) > 4
            ):
                explicit.add(record["id"])
    if len(explicit) > 1:
        raise ValueError("Clarify which one of the mentioned events you want to investigate")
    event_id = next(iter(explicit), None)
    inherited = False
    lower = query.casefold()
    policy = bool(
        re.search(
            r"polic|check[ -]?in|cancel|transfer|recording|eligib|identification|rules|photo.*id", lower
        )
    )
    participant = bool(
        re.search(
            r"participant|attendee|directory|registered|active|mensah|daniels|mokoena|patel|botha|petersen|dlamini",
            lower,
        )
    )
    schedule = bool(re.search(r"where|when|venue|capacity|start|schedule|location", lower))
    kind = (
        "policy"
        if policy and not schedule and not participant
        else "participant"
        if participant and not policy and not schedule
        else "event"
        if schedule and not policy and not participant
        else None
    )
    context = [previous_event] if isinstance(previous_event, str) else list(previous_event or [])
    context = list(dict.fromkeys(e for e in context if isinstance(e, str)))
    follow = bool(
        re.search(r"^(and\b|what about\b)|\b(its|it|that event|this event|there|she|he|they)\b", lower)
    )
    ambiguous = False
    if not event_id and follow:
        if (
            len(context) == 1
            and (policy or schedule)
            and not re.search(r"\b(other|another|different|she|he|they)\b", lower)
        ):
            event_id, inherited = context[0], True
        else:
            ambiguous = True
    category = (
        next(
            (
                v
                for pattern, v in [
                    ("check[ -]?in", "check_in"),
                    ("cancel", "cancellation"),
                    ("transfer", "transfers"),
                    ("recording", "recording"),
                ]
                if re.search(pattern, lower)
            ),
            None,
        )
        if kind == "policy"
        else None
    )
    return {
        "question": question,
        "normalized_query": query + (f" Event {event_id}" if inherited else ""),
        "event_id": event_id,
        "kind": kind,
        "category": category,
        "inherited_context": inherited,
        "needs_clarification": ambiguous,
        "clarification": "Which event and subject do you mean?" if ambiguous else None,
        "interpretation": "deterministic query transformation v2; explicit references precede follow-up context",
    }


def ask(index, store, owner, question, previous_event=None, depth=5, generate=False):
    from eventops.gemini import grounded_answer

    try:
        plan = interpret(question, previous_event)
    except ValueError as exc:
        if not str(exc).startswith("Clarify"):
            raise
        plan = {
            "question": question,
            "normalized_query": question,
            "event_id": None,
            "kind": None,
            "category": None,
            "inherited_context": False,
            "needs_clarification": True,
            "clarification": str(exc),
        }
    hits = index.search(plan, depth)
    answer = (
        grounded_answer(plan["normalized_query"], hits, store)
        if generate and not plan.get("needs_clarification")
        else {
            "status": "evidence_only",
            "answer": "Retrieved source records are shown below. Model generation was not requested.",
            "citation_ids": [],
        }
    )
    if plan.get("needs_clarification"):
        answer = {"status": "clarification_required", "answer": plan["clarification"], "citation_ids": []}
    result = {
        "plan": plan,
        "evidence": hits,
        "response": answer,
        "retrieval": "FastEmbed cosine semantic search",
    }
    result["id"] = store.save(owner, "question", result)
    return result
