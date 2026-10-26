"""Run the offline CCA evaluation suite and write a JSON report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.campus_guide.answering import AnswerService
from src.campus_guide.data import load_evaluation_cases, load_records
from src.campus_guide.evaluation import evaluate_cases
from src.campus_guide.retrieval import RetrievalIndex
from src.campus_guide.settings import get_settings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "output" / "evaluation_results.json")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    records = load_records(ROOT / "data" / "campus_records.jsonl")
    cases = load_evaluation_cases(ROOT / "data" / "evaluation_set.jsonl")
    settings = get_settings()
    service = AnswerService(RetrievalIndex(records), settings, provider=None)
    report = evaluate_cases(service, cases, top_k=args.top_k)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "cases"}, indent=2))
    print(f"Evaluation JSON: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
