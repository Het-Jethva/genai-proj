"""Small, inspectable hybrid retrieval index.

The default index has no model download. It combines weighted word overlap,
character n-grams, and a curated concept-expansion layer. If the optional
sentence-transformers package is installed and enabled, a dense cosine score
joins the same ranking formula.
"""

from __future__ import annotations

import math
import os
import re
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from .data import load_records
from .models import CampusRecord, RetrievalHit

TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "could", "did", "do", "does",
    "for", "from", "have", "how", "i", "if", "in", "is", "it", "me", "many", "may", "much",
    "my", "of", "on", "or", "please", "should", "than", "the", "then", "to", "was", "what",
    "when", "where", "which", "who", "will", "with", "would", "your",
}

# These groups let the keyless index recognize common student phrasing without
# pretending that a synonym table is a language model.
CONCEPT_GROUPS = (
    {"exam", "examination", "assessment", "test", "midterm", "final", "paper", "timetable", "schedule"},
    {"fee", "fees", "payment", "pay", "tuition", "charges", "late", "invoice", "installment", "installments", "instalment", "instalments"},
    {"borrow", "borrowed", "loan", "checkout", "renew", "renewal", "library", "book"},
    {"scholarship", "grant", "aid", "financial", "income", "support", "award"},
    {"club", "clubs", "society", "societies", "student", "committee", "event"},
    {"placement", "placements", "internship", "internships", "career", "recruiter", "job"},
    {"attendance", "present", "absence", "absent", "medical", "illness", "miss", "missed", "missing", "presence"},
    {"registration", "register", "enrolment", "enrollment", "enrol", "add", "drop"},
    {"lab", "laboratory", "room", "facility", "facilities", "maker", "workshop"},
    {"safety", "security", "emergency", "incident", "guard", "health", "fire"},
    {"wifi", "network", "internet", "wireless", "connectivity"},
    {"counselling", "counseling", "wellbeing", "wellness", "support", "mental"},
    {"hour", "hours", "open", "opening", "close", "closed", "weekday", "weekdays", "saturday", "sunday"},
)

# These terms carry identity, freshness, or answer-shape meaning. A related
# record is not enough when one of these terms is absent from the evidence.
PRECISION_ALIASES = (
    {"amount"},
    {"appeal"},
    {"cafeteria"},
    {"current", "currently"},
    {"health"},
    {"international"},
    {"last", "latest"},
    {"menu"},
    {"mental"},
    {"next"},
    {"number"},
    {"outcome"},
    {"package"},
    {"password"},
    {"phone"},
    {"rector"},
    {"refund"},
    {"this"},
    {"today"},
    {"tomorrow"},
    {"timetable", "schedule"},
    {"class", "classes", "course", "courses"},
    {"exam", "examination", "assessment", "test", "midterm", "final", "paper"},
    {"installment", "installments", "instalment", "instalments"},
    {"yesterday"},
)

AMBIGUOUS_CONCEPT_TERMS = frozenset({"close", "closed", "event", "open", "student", "support"})


def _normalize_phrases(text: str) -> str:
    normalized = text.lower()
    for phrase, replacement in (
        (r"\bchecked\s+out\b", "checkout"),
        (r"\bcheck\s+out\b", "checkout"),
        (r"\bsign\s+in\b", "signin"),
        (r"\blog\s+in\b", "login"),
    ):
        normalized = re.sub(phrase, replacement, normalized)
    return normalized


def tokenize(text: str) -> list[str]:
    return [token for token in TOKEN_RE.findall(_normalize_phrases(text)) if token not in STOPWORDS]


def _char_ngrams(text: str, n: int = 3) -> Counter[str]:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    return Counter(normalized[index : index + n] for index in range(max(0, len(normalized) - n + 1)))


def _cosine(left: Counter[str] | dict[str, float], right: Counter[str] | dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(value * right.get(key, 0.0) for key, value in left.items())
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return max(0.0, min(1.0, dot / (left_norm * right_norm)))


class RetrievalIndex:
    """Rank records with transparent component scores."""

    def __init__(self, records: Iterable[CampusRecord], enable_dense: bool = False) -> None:
        self.records = list(records)
        if not self.records:
            raise ValueError("RetrievalIndex needs at least one record")
        self._token_lists = [tokenize(record.as_search_text()) for record in self.records]
        self._token_sets = [set(tokens) for tokens in self._token_lists]
        self._char_vectors = [_char_ngrams(record.as_search_text()) for record in self.records]
        self._idf = self._build_idf(self._token_lists)
        self._weighted_vectors = [self._weighted_vector(tokens) for tokens in self._token_lists]
        self._dense_model = None
        self._dense_vectors = None
        self.dense_enabled = False
        if enable_dense:
            self._try_enable_dense()

    @classmethod
    def from_path(cls, path: str | Path, enable_dense: bool = False) -> RetrievalIndex:
        return cls(load_records(path), enable_dense=enable_dense)

    @staticmethod
    def _build_idf(token_lists: list[list[str]]) -> dict[str, float]:
        document_count = len(token_lists)
        document_frequency: Counter[str] = Counter()
        for tokens in token_lists:
            document_frequency.update(set(tokens))
        return {
            token: math.log((document_count + 1) / (count + 1)) + 1
            for token, count in document_frequency.items()
        }

    def _weighted_vector(self, tokens: list[str]) -> dict[str, float]:
        counts = Counter(tokens)
        total = max(1, len(tokens))
        return {
            token: (count / total) * self._idf.get(token, 1.0)
            for token, count in counts.items()
        }

    def _try_enable_dense(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except (ImportError, OSError, RuntimeError):
            return
        try:
            model_name = os.getenv("DENSE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            model = SentenceTransformer(model_name)
            vectors = model.encode(
                [record.as_search_text() for record in self.records],
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        except (OSError, RuntimeError, ValueError):
            return
        self._dense_model = model
        self._dense_vectors = vectors
        self.dense_enabled = True

    def _dense_scores(self, query: str) -> list[float | None]:
        if not self.dense_enabled or self._dense_model is None or self._dense_vectors is None:
            return [None] * len(self.records)
        try:
            query_vector = self._dense_model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
            return [max(0.0, min(1.0, float(sum(a * b for a, b in zip(query_vector, vector))))) for vector in self._dense_vectors]
        except (OSError, RuntimeError, ValueError):
            return [None] * len(self.records)

    @staticmethod
    def _concept_terms(tokens: list[str]) -> set[str]:
        expanded = set(tokens)
        for group in CONCEPT_GROUPS:
            if set(tokens) & group:
                expanded.update(group)
        return expanded

    @staticmethod
    def _matched_groups(tokens: set[str]) -> list[set[str]]:
        return [
            group
            for group in CONCEPT_GROUPS
            if (tokens & group) - AMBIGUOUS_CONCEPT_TERMS
        ]

    @staticmethod
    def _group_coverage(query_groups: list[set[str]], record_tokens: set[str]) -> float:
        if not query_groups:
            return 1.0
        return sum(bool(group & record_tokens) for group in query_groups) / len(query_groups)

    def search(self, query: str, k: int = 5) -> list[RetrievalHit]:
        query = query.strip()
        if not query or k <= 0:
            return []
        query_tokens = tokenize(query)
        if not query_tokens:
            return []
        query_vector = self._weighted_vector(query_tokens)
        query_chars = _char_ngrams(query)
        expanded_query = self._concept_terms(query_tokens)
        dense_scores = self._dense_scores(query)
        hits: list[RetrievalHit] = []
        query_token_set = set(query_tokens)
        query_groups = self._matched_groups(query_token_set)
        record_tokens_by_id = {
            record.id: token_sets for record, token_sets in zip(self.records, self._token_sets)
        }

        for index, record in enumerate(self.records):
            lexical_score = _cosine(query_vector, self._weighted_vectors[index])
            char_score = _cosine(query_chars, self._char_vectors[index])
            concept_score = len(expanded_query & self._token_sets[index]) / math.sqrt(
                max(1, len(expanded_query)) * max(1, len(self._token_sets[index]))
            )
            dense_score = dense_scores[index]
            if dense_score is None:
                score = 0.52 * lexical_score + 0.23 * concept_score + 0.25 * char_score
            else:
                score = 0.40 * lexical_score + 0.18 * concept_score + 0.17 * char_score + 0.25 * dense_score
            hits.append(
                RetrievalHit(
                    record=record,
                    score=score,
                    lexical_score=lexical_score,
                    concept_score=concept_score,
                    dense_score=dense_score,
                )
            )
        hits.sort(key=lambda hit: (-hit.score, hit.record.id))
        top_record_tokens = record_tokens_by_id[hits[0].record.id]
        top_is_compatible = (
            not self.missing_precision_terms(query, hits[0].record)
            and self._group_coverage(query_groups, top_record_tokens) >= 1.0
        )
        if not top_is_compatible:
            compatible_hits = [
                hit
                for hit in hits
                if not self.missing_precision_terms(query, hit.record)
                and self._group_coverage(query_groups, record_tokens_by_id[hit.record.id]) >= 1.0
            ]
            if compatible_hits:
                promoted = max(compatible_hits, key=lambda hit: (hit.score, hit.record.id))
                hits.remove(promoted)
                hits.insert(0, promoted)
        return hits[:k]

    def support_signal(self, query: str, record: CampusRecord) -> tuple[float, float]:
        """Return direct-token and concept-group coverage for answerability."""

        query_tokens = set(tokenize(query))
        record_tokens = set(tokenize(record.as_search_text()))
        direct_coverage = len(query_tokens & record_tokens) / max(1, len(query_tokens))
        matched_groups = self._matched_groups(query_tokens)
        if not matched_groups:
            return direct_coverage, 1.0 if direct_coverage else 0.0
        group_coverage = sum(bool(group & record_tokens) for group in matched_groups) / len(matched_groups)
        return direct_coverage, group_coverage

    @staticmethod
    def missing_precision_terms(query: str, record: CampusRecord) -> set[str]:
        query_tokens = set(tokenize(query))
        record_tokens = set(tokenize(record.as_search_text()))
        missing: set[str] = set()
        for alias_group in PRECISION_ALIASES:
            queried = query_tokens & alias_group
            if queried and not record_tokens & alias_group:
                missing.update(queried)
        return missing

    @staticmethod
    def unsupported_term_ratio(query: str, record: CampusRecord) -> float:
        """Estimate how much of a query names a topic absent from a record."""

        query_tokens = set(tokenize(query))
        record_tokens = set(tokenize(record.as_search_text()))
        recognized = query_tokens & record_tokens
        for group in RetrievalIndex._matched_groups(query_tokens):
            if query_tokens & group and record_tokens & group:
                recognized.update(query_tokens & group)
        return len(query_tokens - recognized) / max(1, len(query_tokens))

    @property
    def categories(self) -> list[str]:
        return sorted({record.category for record in self.records})

    def stats(self) -> dict[str, int | str]:
        return {
            "records": len(self.records),
            "categories": len(self.categories),
            "retrieval_mode": "dense semantic + lexical" if self.dense_enabled else "lexical + concept proxy",
        }
