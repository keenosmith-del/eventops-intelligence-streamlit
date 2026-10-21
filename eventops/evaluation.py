"""Reproducible retrieval metrics and curated answer checks, never an LLM judge."""

import re
import time

from eventops.rag import interpret


def evaluate_answer(case, answer, hits):
    ids = {r["id"] for r in hits}
    citations = answer.get("citation_ids", [])
    citation_valid = bool(citations) and set(citations) <= ids
    text = answer.get("answer", "").casefold()
    facts = all(
        any(alias.casefold() in text for alias in aliases)
        for aliases in case.get("supported_fact_aliases", [])
    )
    forbidden = [
        claim for claim in case.get("unsupported_claim_patterns", []) if re.search(claim, text, re.I)
    ]
    expected = case.get("expected_behavior", "answer")
    abstained = answer.get("status") in ("insufficient_evidence", "clarification_required")
    return {
        "citation_valid": citation_valid,
        "expected_facts_present": facts,
        "unsupported_claims_detected": forbidden,
        "supported_behavior": (
            abstained
            if expected != "answer"
            else answer.get("status") == "generated" and citation_valid and facts and not forbidden
        ),
        "method": "curated deterministic fact aliases and forbidden claims; not complete entailment proof",
    }


def evaluate(index, cases, k=5):
    results = []
    recalls = []
    rr = []
    for case in cases:
        started = time.perf_counter()
        try:
            plan = interpret(case["query"], case.get("prior_context"))
            hits = index.search(plan, k)
        except ValueError:
            plan = {"needs_clarification": True}
            hits = []
        ranked = [r["id"] for r in hits]
        expected = set(case["expected_source_ids"])
        recall = len(set(ranked) & expected) / len(expected) if expected else None
        reciprocal = (
            next((1 / (i + 1) for i, r in enumerate(ranked) if r in expected), 0) if expected else None
        )
        if expected:
            recalls.append(recall)
            rr.append(reciprocal)
        behavior = (
            bool(plan.get("needs_clarification"))
            if case["expected_behavior"] == "clarify"
            else not hits
            if case["expected_behavior"] == "abstain"
            else bool(expected & set(ranked))
        )
        results.append(
            {
                "id": case["id"],
                "query": case["query"],
                "prior_context": case.get("prior_context"),
                "expected_source_ids": case["expected_source_ids"],
                "supported_fact_aliases": case.get("supported_fact_aliases", []),
                "expected_behavior": case["expected_behavior"],
                "ranked_source_ids": ranked,
                "recall_at_k": recall,
                "reciprocal_rank": reciprocal,
                "behavior_passed": behavior,
                "retrieval_ms": round((time.perf_counter() - started) * 1000, 3),
            }
        )
    return {
        "dataset_version": 2,
        "k": k,
        "cases": results,
        "metrics": {
            "recall_at_k": sum(recalls) / len(recalls),
            "mrr": sum(rr) / len(rr),
            "retrieval_case_count": len(recalls),
            "behavior_passed": sum(r["behavior_passed"] for r in results),
            "total_cases": len(results),
        },
        "grounding_note": "Retrieval metrics are separate from generated-answer factual evaluation; cosine is not confidence.",
    }
