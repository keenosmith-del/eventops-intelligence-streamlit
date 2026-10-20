import os
import re
import threading
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding

from eventops.config import ROOT, setting
from eventops.knowledge import fingerprint, load_documents

MODEL = "BAAI/bge-small-en-v1.5"


class SemanticIndex:
    def __init__(self, path=None):
        self.path = Path(path or ROOT / "storage/index.npz")
        self.records = load_documents()
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
            temp = self.path.with_suffix(f".{os.getpid()}.tmp.npz")
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
        with self.lock:
            vector = np.asarray(list(self.model.query_embed(plan["normalized_query"]))[0], dtype=np.float32)
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
    query = re.sub(r"\bevt[\s-]?(\d{3})\b", lambda m: "EVT-" + m[1], query, flags=re.I)
    events = sorted(set(re.findall(r"EVT-\d{3}", query)))
    if len(events) > 1:
        raise ValueError("Ask about one event at a time")
    event_id = events[0] if events else None
    inherited = False
    if (
        not event_id
        and previous_event
        and re.search(r"\b(it|its|that|this|there|what about|and)\b", query, re.I)
    ):
        event_id, inherited = previous_event, True
    if not event_id:
        for r in load_documents():
            if r["kind"] == "event" and (
                r["fields"]["title"].casefold() in query.casefold()
                or re.search(r"\b" + re.escape(r["fields"]["title"].split()[-1]) + r"\b", query, re.I)
            ):
                event_id = r["id"]
                break
    lower = query.casefold()
    kind = (
        "policy"
        if re.search(r"polic|check.in|cancel|transfer|recording|eligib|identification|rules", lower)
        else "participant"
        if re.search(r"participant|attendee|directory|registered|active", lower)
        else "event"
        if re.search(r"where|when|venue|capacity|start|schedule", lower)
        else None
    )
    category = (
        next(
            (
                v
                for k, v in [
                    ("check.in", "check_in"),
                    ("cancel", "cancellation"),
                    ("transfer", "transfers"),
                    ("recording", "recording"),
                ]
                if re.search(k, lower)
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
        "interpretation": "deterministic query transformation",
    }


def ask(index, store, owner, question, previous_event=None, depth=5, generate=False):
    from eventops.gemini import grounded_answer

    plan = interpret(question, previous_event)
    hits = index.search(plan, depth)
    answer = (
        grounded_answer(plan["normalized_query"], hits, store)
        if generate
        else {
            "status": "evidence_only",
            "answer": "Retrieved source records are shown below. Model generation was not requested.",
            "citation_ids": [],
        }
    )
    result = {
        "plan": plan,
        "evidence": hits,
        "response": answer,
        "retrieval": "FastEmbed cosine semantic search",
    }
    result["id"] = store.save(owner, "question", result)
    return result
