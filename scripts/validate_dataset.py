"""Validate the two JSONL artifacts before a demo or a submission."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.campus_guide.data import category_counts, load_evaluation_cases, load_records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, default=ROOT / "data" / "campus_records.jsonl")
    parser.add_argument("--evaluation", type=Path, default=ROOT / "data" / "evaluation_set.jsonl")
    args = parser.parse_args()
    records = load_records(args.records)
    cases = load_evaluation_cases(args.evaluation)
    record_ids = {record.id for record in records}
    missing = sorted({item for case in cases for item in case.expected_record_ids} - record_ids)
    if missing:
        raise SystemExit(f"Evaluation references unknown record ids: {missing}")
    print(f"Records: {len(records)}")
    print(f"Categories: {len(category_counts(records))}")
    print(f"Evaluation cases: {len(cases)} ({sum(case.expected_refusal for case in cases)} refusal cases)")
    for category, count in category_counts(records).items():
        print(f"  {category}: {count}")
    print("Dataset validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
