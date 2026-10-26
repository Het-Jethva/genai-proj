import unittest
from pathlib import Path

from src.campus_guide.answering import AnswerService
from src.campus_guide.data import load_records
from src.campus_guide.providers import GenerationResponse
from src.campus_guide.retrieval import RetrievalIndex
from src.campus_guide.settings import get_settings

ROOT = Path(__file__).resolve().parents[1]


class AnsweringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        index = RetrievalIndex(load_records(ROOT / "data" / "campus_records.jsonl"))
        cls.service = AnswerService(index, get_settings(), provider=None)

    def test_supported_answer_contains_grounding_marker(self):
        result = self.service.answer("When are Term 1 fees due?")
        self.assertTrue(result.supported)
        self.assertFalse(result.refused)
        self.assertIn("[R1]", result.answer)
        self.assertIn("fee-001", result.cited_record_ids)

    def test_unsupported_answer_refuses(self):
        result = self.service.answer("What is tomorrow's cafeteria menu?")
        self.assertTrue(result.refused)
        self.assertFalse(result.supported)
        self.assertEqual(result.cited_record_ids, [])

    def test_unsupported_specific_detail_does_not_use_related_record(self):
        result = self.service.answer("What is the current rector phone number?")
        self.assertTrue(result.refused)
        self.assertFalse(result.supported)
        self.assertEqual(result.cited_record_ids, [])

    def test_multi_intent_question_does_not_return_a_partial_answer(self):
        result = self.service.answer("When are Term 1 fees due and what is the cafeteria menu?")
        self.assertTrue(result.refused)
        self.assertFalse(result.supported)
        self.assertEqual(result.cited_record_ids, [])

    def test_long_question_is_rejected_before_retrieval(self):
        result = self.service.answer("x" * 801)
        self.assertTrue(result.refused)
        self.assertEqual(result.provider_error, "query_too_long")

    def test_hosted_markdown_is_preserved_for_rendering(self):
        class StubProvider:
            def generate(self, system_prompt, user_prompt):
                return GenerationResponse("You may borrow **six books**. [R1]", "test-model")

        service = AnswerService(
            self.service.index,
            get_settings({"OPENROUTER_API_KEY": "test-key"}),
            provider=StubProvider(),
        )
        result = service.answer("How many books can an undergraduate borrow?")

        self.assertEqual(result.answer, "You may borrow **six books**. [R1]")
        self.assertTrue(result.supported)

    def test_empty_hosted_answer_falls_back(self):
        class StubProvider:
            def generate(self, system_prompt, user_prompt):
                return GenerationResponse("[R1]", "test-model")

        service = AnswerService(
            self.service.index,
            get_settings({"OPENROUTER_API_KEY": "test-key"}),
            provider=StubProvider(),
        )
        result = service.answer("How many books can an undergraduate borrow?")

        self.assertTrue(result.supported)
        self.assertEqual(result.provider, "deterministic grounded fallback")
        self.assertIn("six books", result.answer)


if __name__ == "__main__":
    unittest.main()
