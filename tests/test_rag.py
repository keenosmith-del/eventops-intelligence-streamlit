import json

import httpx
import numpy as np
import pytest

from eventops.gemini import grounded_answer
from eventops.knowledge import fingerprint, load_documents
from eventops.rag import SemanticIndex, ask, interpret


@pytest.fixture(scope="module")
def index():
    return SemanticIndex()


def test_three_documents():
    docs = load_documents()
    assert len(docs) == 19
    assert {k: sum(r["kind"] == k for r in docs) for k in ["event", "policy", "participant"]} == {
        "event": 3,
        "policy": 9,
        "participant": 7,
    }
    assert len(set(r["source"].split("#")[0] for r in docs)) == 3
    assert len(set(r["id"] for r in docs)) == 19


def test_real_embeddings(index):
    assert index.vectors.shape == (19, 384)
    assert np.isfinite(index.vectors).all()
    assert not np.allclose(index.vectors[0], index.vectors[1])


@pytest.mark.parametrize(
    "question,expected",
    [
        ("What are the check-in rules for EVT-101?", "POL-003"),
        ("Where is EVT-102 held?", "EVT-102"),
        ("How soon must I cancel my registration?", "POL-002"),
        ("What photographic identification do attendees need?", "POL-001"),
        ("Is Lindi Mokoena active?", "P-003"),
    ],
)
def test_semantic_search(index, question, expected):
    assert index.search(interpret(question))[0]["id"] == expected


def test_context():
    plan = interpret("And what are its check-in rules?", "EVT-101")
    assert plan["event_id"] == "EVT-101" and plan["inherited_context"]
    assert plan["category"] == "check_in"
    assert "EVT-101" in plan["normalized_query"]


def test_normalization():
    assert interpret(" Where is evt 102 held? ")["event_id"] == "EVT-102"
    assert interpret("Where is the Sustainable Retail Forum?")["event_id"] == "EVT-102"


def test_context_not_blindly_inherited():
    assert interpret("Where is EVT-103?", "EVT-101")["event_id"] == "EVT-103"
    assert interpret("Tell me about catering", "EVT-101")["event_id"] is None


@pytest.mark.parametrize("question", ["", " " * 10, "x" * 1001, "Compare EVT-101 and EVT-102"])
def test_invalid_query(question):
    with pytest.raises(ValueError):
        interpret(question)


def test_global_policy_scope(index):
    hits = index.search(interpret("Cancellation policy for EVT-103"))
    assert hits[0]["id"] == "POL-002"


def test_unknown_event_not_fabricated(index):
    assert index.search(interpret("Where is EVT-999?")) == []


def test_persistence_and_followup(index, store, monkeypatch):
    monkeypatch.setenv("GEMINI_ENABLED", "false")
    first = ask(index, store, "owner-a", "Where is EVT-101 held?", generate=True)
    second = ask(
        index,
        store,
        "owner-a",
        "And what are its check-in rules?",
        first["plan"]["event_id"],
    )
    assert second["evidence"][0]["id"] == "POL-003"
    assert store.get("owner-a", first["id"])["payload"]["response"]["status"] == "unavailable"
    assert len(store.list("owner-a", "question")) == 2
    assert not store.get("owner-b", first["id"])


def test_reproducible_index(index, tmp_path):
    path = tmp_path / "index.npz"
    np.savez_compressed(path, vectors=index.vectors, signature=index.signature)
    rebuilt = SemanticIndex(path)
    assert np.array_equal(rebuilt.vectors, index.vectors)


def test_corrupt_index_rebuilt(tmp_path):
    path = tmp_path / "broken.npz"
    path.write_text("bad")
    rebuilt = SemanticIndex(path)
    assert rebuilt.vectors.shape == (19, 384)


def test_source_fingerprint_changes():
    docs = load_documents()
    before = fingerprint(docs)
    docs[0]["fields"]["title"] = "Changed"
    assert fingerprint(docs) != before


@pytest.fixture
def generation(monkeypatch):
    monkeypatch.setenv("GEMINI_ENABLED", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "test-only")
    return [{"id": "POL-003", "content": "Check-in closes at 08:45."}]


def transport_answer(answer):
    return httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "finishReason": "STOP",
                        "content": {"parts": [{"text": json.dumps(answer)}]},
                    }
                ],
                "responseId": "test-response",
            },
        )
    )


def test_grounding_contract(generation, store):
    def handler(request):
        body = json.loads(request.content)
        assert "POL-003" in body["contents"][0]["parts"][0]["text"]
        assert "untrusted" in body["systemInstruction"]["parts"][0]["text"]
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "finishReason": "STOP",
                        "content": {
                            "parts": [
                                {"text": '{"answer":"Check-in closes at 08:45.","citation_ids":["POL-003"]}'}
                            ]
                        },
                    }
                ]
            },
        )

    result = grounded_answer("When does check-in close?", generation, store, httpx.MockTransport(handler))
    assert result["status"] == "generated"


@pytest.mark.parametrize(
    "answer",
    [
        {"answer": "Invented", "citation_ids": ["FAKE"]},
        {"answer": "No citations", "citation_ids": []},
        {"answer": "Bad", "citation_ids": ["POL-003", "POL-003"]},
        {"answer": "Bad", "citation_ids": ["POL-003"], "extra": "forbidden"},
    ],
)
def test_bad_citations_rejected(generation, store, answer):
    assert grounded_answer("question", generation, store, transport_answer(answer))["status"] == "unavailable"


def test_insufficient_evidence(generation, store):
    result = grounded_answer(
        "question",
        generation,
        store,
        transport_answer({"answer": "", "citation_ids": []}),
    )
    assert result["status"] == "insufficient_evidence"
    assert grounded_answer("question", [], store)["status"] == "insufficient_evidence"


@pytest.mark.parametrize("status", [401, 429, 500])
def test_gemini_failures(generation, store, status):
    result = grounded_answer(
        "question",
        generation,
        store,
        httpx.MockTransport(lambda request: httpx.Response(status)),
    )
    assert result["status"] == "unavailable" and result["reason"] == f"provider_http_{status}"


def test_gemini_budget(generation, store, monkeypatch):
    monkeypatch.setenv("GEMINI_DAILY_LIMIT", "0")
    assert grounded_answer("question", generation, store)["reason"] == "daily_budget_exhausted"
