"""Repeatable offline evaluation for retrieval, refusals, and citations."""

from __future__ import annotations

import re
from collections.abc import Iterable

from .answering import AnswerService
from .models import EvaluationCase

TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {"a", "an", "and", "are", "for", "from", "how", "in", "is", "of", "on", "the", "to", "what", "when", "where", "with"}
ANSWER_QUALITY_THRESHOLD = 0.75


def _keywords(text: str) -> set[str]:
    return {token for token in TOKEN_RE.findall(text.lower()) if token not in STOPWORDS and len(token) > 2}


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def evaluate_cases(
    service: AnswerService,
    cases: Iterable[EvaluationCase],
    top_k: int = 5,
) -> dict:
    rows: list[dict] = []
    retrieval_hits: list[float] = []
    refusal_hits: list[float] = []
    citation_validity: list[float] = []
    keyword_coverage: list[float] = []

    for case in cases:
        hits = service.index.search(case.question, k=top_k)
        retrieved_ids = [hit.record.id for hit in hits]
        found_expected = bool(set(case.expected_record_ids) & set(retrieved_ids))
        result = service.answer(case.question)
        refusal_correct = result.refused == case.expected_refusal
        valid_citations = bool(result.cited_record_ids) and all(
            cited_id in {hit.record.id for hit in result.hits}
            for cited_id in result.cited_record_ids
        )
        expected_terms = _keywords(case.reference_answer)
        answer_terms = _keywords(result.answer)
        coverage = len(expected_terms & answer_terms) / max(1, len(expected_terms))
        retrieval_pass = case.expected_refusal or found_expected
        answer_quality_pass = case.expected_refusal or coverage >= ANSWER_QUALITY_THRESHOLD
        citation_pass = case.expected_refusal or (result.supported and valid_citations)
        overall_pass = refusal_correct and retrieval_pass and citation_pass and answer_quality_pass

        if not case.expected_refusal:
            retrieval_hits.append(1.0 if found_expected else 0.0)
            keyword_coverage.append(coverage)
            citation_validity.append(1.0 if valid_citations and bool(result.cited_record_ids) else 0.0)
        refusal_hits.append(1.0 if refusal_correct else 0.0)
        rows.append(
            {
                "id": case.id,
                "category": case.category,
                "expected_refusal": case.expected_refusal,
                "refused": result.refused,
                "retrieval_hit": found_expected,
                "retrieval_pass": retrieval_pass,
                "refusal_pass": refusal_correct,
                "top_score": round(result.top_score, 4),
                "citation_valid": valid_citations,
                "answer_quality_pass": answer_quality_pass,
                "keyword_coverage": round(coverage, 4),
                "status": "PASS" if overall_pass else "CHECK",
                "top_record": retrieved_ids[0] if retrieved_ids else "-",
            }
        )

    return {
        "total_cases": len(rows),
        "supported_cases": sum(1 for row in rows if not row["expected_refusal"]),
        "refusal_cases": sum(1 for row in rows if row["expected_refusal"]),
        "retrieval_recall_at_k": _mean(retrieval_hits),
        "refusal_accuracy": _mean(refusal_hits),
        "citation_validity": _mean(citation_validity),
        "answer_keyword_coverage": _mean(keyword_coverage),
        "answer_quality_threshold": ANSWER_QUALITY_THRESHOLD,
        "top_k": top_k,
        "cases": rows,
    }


def category_evaluation(rows: Iterable[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["category"], []).append(row)
    output = []
    for category, category_rows in sorted(grouped.items()):
        supported_rows = [row for row in category_rows if not row["expected_refusal"]]
        output.append(
            {
                "category": category,
                "cases": len(category_rows),
                "pass_rate": _mean([1.0 if row["status"] == "PASS" else 0.0 for row in category_rows]),
                "retrieval_recall": _mean([1.0 if row["retrieval_pass"] else 0.0 for row in supported_rows])
                if supported_rows
                else None,
                "citation_validity": _mean(
                    [1.0 if row["citation_valid"] else 0.0 for row in supported_rows]
                )
                if supported_rows
                else None,
                "answer_quality": _mean(
                    [1.0 if row["answer_quality_pass"] else 0.0 for row in supported_rows]
                )
                if supported_rows
                else None,
            }
        )
    return output
