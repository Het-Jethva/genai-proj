"""Load and validate the human-readable JSONL artifacts."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import date
from pathlib import Path

from .models import CampusRecord, EvaluationCase

REQUIRED_RECORD_FIELDS = {
    "id",
    "category",
    "title",
    "content",
    "source",
    "effective_date",
    "tags",
    "confidence",
    "source_type",
}


class DatasetValidationError(ValueError):
    """Raised when a dataset record is incomplete or inconsistent."""


def _read_jsonl(path: Path) -> Iterable[tuple[int, dict]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                continue
            try:
                value = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise DatasetValidationError(f"{path}:{line_number} is not valid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise DatasetValidationError(f"{path}:{line_number} must contain a JSON object")
            yield line_number, value


def load_records(path: str | Path) -> list[CampusRecord]:
    path = Path(path)
    records: list[CampusRecord] = []
    seen_ids: set[str] = set()
    for line_number, value in _read_jsonl(path):
        missing = REQUIRED_RECORD_FIELDS - set(value)
        if missing:
            raise DatasetValidationError(f"{path}:{line_number} missing fields: {sorted(missing)}")
        try:
            record = CampusRecord.from_dict(value)
        except (KeyError, TypeError, ValueError) as exc:
            raise DatasetValidationError(f"{path}:{line_number} has invalid record fields: {exc}") from exc
        try:
            date.fromisoformat(record.effective_date)
        except ValueError as exc:
            raise DatasetValidationError(
                f"{path}:{line_number} effective_date must be an ISO date (YYYY-MM-DD)"
            ) from exc
        if record.id in seen_ids:
            raise DatasetValidationError(f"{path}:{line_number} repeats record id {record.id}")
        if record.source_type != "synthetic":
            raise DatasetValidationError(f"{path}:{line_number} must stay marked synthetic")
        if not record.tags:
            raise DatasetValidationError(f"{path}:{line_number} needs at least one retrieval tag")
        seen_ids.add(record.id)
        records.append(record)
    if not records:
        raise DatasetValidationError(f"{path} has no records")
    return records


def load_evaluation_cases(path: str | Path) -> list[EvaluationCase]:
    path = Path(path)
    cases: list[EvaluationCase] = []
    seen_ids: set[str] = set()
    for line_number, value in _read_jsonl(path):
        required = {"id", "question", "expected_record_ids", "expected_refusal", "reference_answer", "category", "rationale"}
        missing = required - set(value)
        if missing:
            raise DatasetValidationError(f"{path}:{line_number} missing fields: {sorted(missing)}")
        try:
            case = EvaluationCase.from_dict(value)
        except (KeyError, TypeError, ValueError) as exc:
            raise DatasetValidationError(f"{path}:{line_number} has invalid evaluation fields: {exc}") from exc
        if case.id in seen_ids:
            raise DatasetValidationError(f"{path}:{line_number} repeats case id {case.id}")
        if case.expected_refusal and case.expected_record_ids:
            raise DatasetValidationError(
                f"{path}:{line_number} refusal case {case.id} cannot name supporting records"
            )
        if not case.expected_refusal and not case.expected_record_ids:
            raise DatasetValidationError(
                f"{path}:{line_number} supported case {case.id} must name at least one supporting record"
            )
        if len(set(case.expected_record_ids)) != len(case.expected_record_ids):
            raise DatasetValidationError(
                f"{path}:{line_number} repeats an expected record id in case {case.id}"
            )
        seen_ids.add(case.id)
        cases.append(case)
    if not cases:
        raise DatasetValidationError(f"{path} has no evaluation cases")
    return cases


def category_counts(records: Iterable[CampusRecord]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        counts[record.category] = counts.get(record.category, 0) + 1
    return dict(sorted(counts.items()))
