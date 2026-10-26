"""Typed data structures shared by loading, retrieval, answering, and evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CampusRecord:
    """One prepared knowledge unit from the synthetic campus corpus."""

    id: str
    category: str
    title: str
    content: str
    source: str
    effective_date: str
    tags: tuple[str, ...]
    confidence: str = "curated-synthetic"
    source_type: str = "synthetic"

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> CampusRecord:
        required_text_fields = ("id", "category", "title", "content", "source", "effective_date")
        for field_name in required_text_fields:
            field_value = value[field_name]
            if not isinstance(field_value, str) or not field_value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")

        raw_tags = value["tags"]
        if not isinstance(raw_tags, list) or any(
            not isinstance(tag, str) or not tag.strip() for tag in raw_tags
        ):
            raise ValueError("tags must be a list of non-empty strings")

        for field_name in ("confidence", "source_type"):
            field_value = value.get(field_name)
            if not isinstance(field_value, str) or not field_value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")

        return cls(
            id=value["id"],
            category=value["category"],
            title=value["title"],
            content=value["content"],
            source=value["source"],
            effective_date=value["effective_date"],
            tags=tuple(raw_tags),
            confidence=value["confidence"],
            source_type=value["source_type"],
        )

    def as_search_text(self) -> str:
        # Repeat the short descriptive fields once so exact titles, tags, and
        # category terms are not diluted by a longer policy paragraph.
        return " ".join((self.title, self.title, self.content, self.category, *self.tags, *self.tags))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "effective_date": self.effective_date,
            "tags": list(self.tags),
            "confidence": self.confidence,
            "source_type": self.source_type,
        }


@dataclass(frozen=True)
class RetrievalHit:
    record: CampusRecord
    score: float
    lexical_score: float
    concept_score: float
    dense_score: float | None = None

    @property
    def evidence_label(self) -> str:
        return self.record.id.upper()


@dataclass
class AnswerResult:
    query: str
    answer: str
    hits: list[RetrievalHit] = field(default_factory=list)
    cited_record_ids: list[str] = field(default_factory=list)
    supported: bool = False
    refused: bool = False
    provider: str = "deterministic fallback"
    provider_error: str | None = None
    latency_ms: int = 0

    @property
    def top_score(self) -> float:
        return self.hits[0].score if self.hits else 0.0

    @property
    def retrieval_mode(self) -> str:
        if any(hit.dense_score is not None for hit in self.hits):
            return "hybrid: dense semantic + lexical"
        return "hybrid: lexical + concept proxy"


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    question: str
    expected_record_ids: tuple[str, ...]
    expected_refusal: bool
    reference_answer: str
    category: str
    rationale: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> EvaluationCase:
        for field_name in ("id", "question", "reference_answer", "category", "rationale"):
            field_value = value[field_name]
            if not isinstance(field_value, str) or not field_value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")

        raw_record_ids = value["expected_record_ids"]
        if not isinstance(raw_record_ids, list) or any(
            not isinstance(record_id, str) or not record_id.strip() for record_id in raw_record_ids
        ):
            raise ValueError("expected_record_ids must be a list of non-empty strings")
        if not isinstance(value["expected_refusal"], bool):
            raise TypeError("expected_refusal must be a boolean")

        return cls(
            id=value["id"],
            question=value["question"],
            expected_record_ids=tuple(raw_record_ids),
            expected_refusal=value["expected_refusal"],
            reference_answer=value["reference_answer"],
            category=value["category"],
            rationale=value["rationale"],
        )
