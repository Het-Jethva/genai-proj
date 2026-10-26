import unittest

from src.campus_guide.evaluation import category_evaluation, evaluate_cases
from src.campus_guide.models import AnswerResult, CampusRecord, EvaluationCase, RetrievalHit


class EvaluationTests(unittest.TestCase):
    def test_status_requires_grounding_and_answer_quality(self):
        record = CampusRecord(
            id="test-001",
            category="Test",
            title="Test record",
            content="A short answer",
            source="Synthetic source",
            effective_date="2026-01-01",
            tags=("test",),
            confidence="curated-synthetic",
            source_type="synthetic",
        )
        hit = RetrievalHit(record=record, score=0.9, lexical_score=0.9, concept_score=0.9)

        class StubIndex:
            def search(self, question, k=5):
                return [hit]

        class StubService:
            index = StubIndex()

            def answer(self, question):
                return AnswerResult(
                    query=question,
                    answer="wrong answer",
                    hits=[hit],
                    cited_record_ids=[],
                    supported=True,
                    refused=False,
                )

        case = EvaluationCase(
            id="case-001",
            question="What is the answer?",
            expected_record_ids=("test-001",),
            expected_refusal=False,
            reference_answer="The answer contains a specific policy detail.",
            category="Test",
            rationale="Checks quality gates.",
        )
        report = evaluate_cases(StubService(), [case])

        self.assertEqual(report["cases"][0]["status"], "CHECK")
        self.assertEqual(category_evaluation(report["cases"])[0]["pass_rate"], 0.0)
