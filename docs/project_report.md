# Northbridge Guide

## An evidence-first campus information assistant using retrieval-augmented generation

**Course:** Gen AI and applications [ECSDI24402]  
**CCA choice:** Option 1, Project  
**Team:** [Student 1] and [Student 2]  
**Faculty:** [Faculty Name]  
**Date:** 31 August 2026

## Abstract

Northbridge Guide is a Streamlit prototype that answers campus-helpdesk questions from a self-prepared fictional dataset. The project demonstrates a complete retrieval-augmented generation pipeline. It validates JSONL records, retrieves relevant evidence, sends only that evidence to an OpenRouter-compatible model when configured, checks citations, and refuses questions that the corpus cannot support. A deterministic fallback keeps the demo and evaluation usable without a hosted key.

The corpus contains 54 records across 9 campus areas. The offline evaluation contains 40 cases, including 3 out-of-scope questions. The current baseline achieved 100% retrieval recall@5, 100% refusal accuracy, 100% citation validity, and 91.4% answer keyword coverage. Supported-case status also requires at least 75% keyword coverage. These values describe this fictional corpus and should not be read as claims about a real university service.

## 1. Problem statement

Students often need small answers with exact details: a fee deadline, a borrowing limit, a form, a room-booking rule, or the next office to contact. A generic chatbot can answer quickly but may invent a date or policy when it lacks a source. This project tests a narrower design. The assistant should answer only when the prepared corpus provides enough evidence, show the records it used, and say when it cannot answer.

## 2. Objectives

1. Prepare an original, inspectable dataset for a fictional campus.
2. Build a working RAG application with a browser interface.
3. Ground generated responses in retrieved records and display citations.
4. Measure retrieval and refusal behavior with a repeatable test set.
5. Document limitations and safe deployment practices.

## 3. Dataset preparation

The team prepared 54 fictional records in `data/campus_records.jsonl`. The corpus covers academics, examinations, fees, library, scholarships, clubs and societies, placements and careers, facilities and IT, and safety and wellbeing. Each record has a stable ID, category, title, content, fictional source label, synthetic effective date, retrieval tags, confidence marker, and `source_type` value.

The dataset uses short, coherent records instead of long unstructured files. This makes each retrieved unit easy to inspect and cite. Records include both direct answers and boundaries. For example, the attendance record says that each course outline sets its own participation rule rather than inventing one institute-wide percentage. The emergency record includes a warning that its phone number is fictional.

The full data card is in `docs/dataset_card.md`. It states the intended classroom use, out-of-scope decisions, maintenance steps, and limitations.

## 4. System design

```text
User question
    |
    v
Validation and length limit
    |
    v
Hybrid retrieval: word score + character score + concept score
    |
    v
Answerability check and top-k evidence
    |                         \\
    |                          \\
    v                           v
OpenRouter/free generation      Deterministic grounded fallback
    |                           /
    v                          /
Citation validation and refusal guard
    |
    v
Answer, evidence trail, score, provider status
```

### Retrieval

The default index uses weighted word similarity, character n-gram similarity, and a small concept-expansion table. Word similarity handles direct terms. Character n-grams help with spelling variation and exact fragments. Concept groups connect phrases such as `exam` and `examination`, or `fee` and `installment`. The optional `sentence-transformers` path adds dense cosine similarity when explicitly enabled.

### Generation

The hosted path sends a system instruction and an evidence block to the `/api/v1/chat/completions` endpoint. The configured model defaults to `openrouter/free`. The prompt asks the model to answer only from the evidence, avoid invented facts, cite labels such as `[R1]`, and keep the response short. The provider adapter reads the API key from environment configuration and never writes it to the repository.

When no key is present or the request fails, the service returns the strongest retrieved record as a deterministic answer with a valid citation. The UI labels this provider path so the evaluator knows whether the hosted model ran.

### Guardrails

- The app rejects blank questions and questions longer than 800 characters.
- The answer service checks the retrieval score, direct query coverage, concept-group coverage, and unsupported-term ratio.
- Low-evidence questions receive a refusal and do not cite unrelated records.
- Model citations are limited to the retrieved evidence labels.
- The public demo remains open to visitors but limits each browser session to 30 requests.
- The app and report repeat the fictional-data disclaimer.

## 5. User interface

The Streamlit app has three views:

- **Ask:** question form, prepared prompts, answer, retrieval metadata, and evidence trail.
- **Evaluation:** repeatable offline metrics and per-case results.
- **Corpus:** filters and readable source records.

The interface uses a cool near-white surface, a single cobalt signal color, technical typography, and a graphite evidence surface. It keeps the main action left aligned and uses borders instead of decorative gradients or card stacks. The full CSS includes responsive rules for narrow screens and visible focus states.

## 6. Evaluation

The test set contains 40 cases. Thirty-seven are expected to be answerable, and three are expected to be refused because the corpus has no current rector record, cafeteria menu, or placement-package outcome data.

| Metric | Result | Meaning |
|---|---:|---|
| Retrieval recall@5 | 100% | Every supported case names at least one expected record in the top five. |
| Refusal accuracy | 100% | Supported and out-of-scope cases received the expected answer/refusal decision. |
| Citation validity | 100% | Every supported fallback answer cites a record present in its evidence list. |
| Answer keyword coverage | 91.4% | The fallback answer contains most keywords in each curated reference answer. |

The command writes the machine-readable result to `output/evaluation_results.json`. The evaluation intentionally runs without the hosted model. Model answers can vary with provider availability, so the offline baseline provides a stable reference point.

## 7. Responsible use and limitations

This is a classroom prototype over fictional data. It is not an official university information system. The synthetic dates, charges, contact number, and rules must not guide real student decisions. A real version would require approved source documents, a content owner for each policy area, expiry monitoring, privacy review, access controls, multilingual testing, and human review for high-impact answers.

The hosted free-model route also depends on external availability and quota. Public deployment must keep the key in the host secrets manager. The request cap lowers risk but does not make a public key unlimited or abuse-proof.

## 8. Reproduction steps

```powershell
uv sync --dev
uv run python scripts\validate_dataset.py
uv run python -m unittest discover -s tests -v
uv run python scripts\evaluate.py
uv run streamlit run app.py
```

For hosted generation, set `OPENROUTER_API_KEY` and keep `OPENROUTER_MODEL=openrouter/free`. Without a key, the app runs through the grounded fallback.

## 9. Conclusion

Northbridge Guide shows the whole GenAI workflow in a small project: prepare data, retrieve evidence, generate a response, show citations, refuse unsupported questions, and measure the result. Its most important design choice is the refusal path. The prototype does not pretend that a language model can answer every campus question. It makes the boundary visible, testable, and easy to explain during the CCA presentation.

## References

1. OpenRouter, "Quickstart Guide," [https://openrouter.ai/docs/quickstart](https://openrouter.ai/docs/quickstart).
2. OpenRouter, "Free Models Router," [https://openrouter.ai/docs/cookbook/get-started/free-models-router-playground](https://openrouter.ai/docs/cookbook/get-started/free-models-router-playground).
