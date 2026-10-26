import json
import tempfile
import unittest
from pathlib import Path

from src.campus_guide.data import (
    DatasetValidationError,
    category_counts,
    load_evaluation_cases,
    load_records,
)

ROOT = Path(__file__).resolve().parents[1]


class DatasetTests(unittest.TestCase):
    def test_records_are_curated_and_broad(self):
        records = load_records(ROOT / "data" / "campus_records.jsonl")
        self.assertEqual(len(records), 54)
        self.assertEqual(len(category_counts(records)), 9)
        self.assertTrue(all(record.source_type == "synthetic" for record in records))
        self.assertEqual(len({record.id for record in records}), len(records))

    def test_evaluation_references_existing_records(self):
        records = load_records(ROOT / "data" / "campus_records.jsonl")
        cases = load_evaluation_cases(ROOT / "data" / "evaluation_set.jsonl")
        ids = {record.id for record in records}
        self.assertEqual(len(cases), 40)
        self.assertTrue(all(item in ids for case in cases for item in case.expected_record_ids))
        self.assertEqual(sum(case.expected_refusal for case in cases), 3)

    def test_record_schema_rejects_wrong_types_and_dates(self):
        invalid_record = {
            "id": "bad-001",
            "category": "Test",
            "title": "Bad record",
            "content": "Content",
            "source": "Synthetic source",
            "effective_date": "not-a-date",
            "tags": "wifi",
            "confidence": "curated-synthetic",
            "source_type": "synthetic",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.jsonl"
            path.write_text(json.dumps(invalid_record) + "\n", encoding="utf-8")
            with self.assertRaises(DatasetValidationError):
                load_records(path)

    def test_evaluation_schema_rejects_string_boolean_and_ids(self):
        invalid_case = {
            "id": "bad-001",
            "question": "A question",
            "expected_record_ids": "fee-001",
            "expected_refusal": "false",
            "reference_answer": "An answer",
            "category": "Fees",
            "rationale": "A reason",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evaluation.jsonl"
            path.write_text(json.dumps(invalid_case) + "\n", encoding="utf-8")
            with self.assertRaises(DatasetValidationError):
                load_evaluation_cases(path)


if __name__ == "__main__":
    unittest.main()
