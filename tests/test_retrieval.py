import unittest
from pathlib import Path

from src.campus_guide.data import load_records
from src.campus_guide.retrieval import RetrievalIndex

ROOT = Path(__file__).resolve().parents[1]


class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = RetrievalIndex(load_records(ROOT / "data" / "campus_records.jsonl"))

    def test_exact_question_retrieves_expected_record(self):
        hits = self.index.search("When are Term 1 fees due?", k=3)
        self.assertGreaterEqual(len(hits), 1)
        self.assertEqual(hits[0].record.id, "fee-001")

    def test_paraphrase_retrieves_expected_record(self):
        hits = self.index.search("How many books can I check out as an undergraduate?", k=3)
        self.assertEqual(hits[0].record.id, "lib-002")

    def test_unknown_query_has_low_confidence(self):
        hits = self.index.search("Who is the current rector?", k=3)
        self.assertGreaterEqual(len(hits), 1)
        self.assertLess(hits[0].score, 0.16)

    def test_zero_top_k_returns_no_hits(self):
        self.assertEqual(self.index.search("library hours", k=0), [])


if __name__ == "__main__":
    unittest.main()
