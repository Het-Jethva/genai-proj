# Methodology

## Project question

Can a small, inspectable RAG pipeline answer common campus-helpdesk questions while showing the evidence it used and refusing unsupported requests?

## Pipeline

```text
JSONL records
    -> schema validation
    -> word, character, and concept indexes
    -> top-k evidence retrieval
    -> answerability checks
    -> OpenRouter generation or grounded fallback
    -> citation validation and UI evidence trail
```

The default index avoids a model download. It scores weighted word similarity, character n-gram similarity, and a small concept-expansion table. Word similarity handles direct terms. Character n-grams help with spelling variation and exact fragments. Concept groups connect phrases such as `exam` and `examination`, or `fee` and `installment`. The optional `sentence-transformers` path adds dense cosine similarity when explicitly enabled.

## Answer policy

The system prompt tells the hosted model to treat records as evidence, not instructions. It must not invent dates, amounts, contacts, or eligibility rules. It must cite evidence labels such as `[R1]`. The service removes citations that point outside the retrieved context. If the top result does not pass the score and coverage checks, the service returns a refusal instead of a best-effort guess.

If the API is not configured or the request fails, the service copies the strongest prepared record into a deterministic answer with a valid citation. This fallback is less conversational, but it is reproducible and keeps the evaluation independent of quota, network, and model drift.

## Evaluation design

The test set contains 40 cases. Thirty-seven are supported questions spread across all nine categories. Three are deliberately outside the corpus. Each case stores expected record IDs, an expected refusal flag, a short reference answer, a category, and the reason the case exists.

The command reports retrieval recall@5, refusal accuracy, citation validity, and reference-keyword coverage. A supported case is marked `PASS` only when it also reaches the 75% keyword-coverage threshold, has valid citations, and has the expected refusal decision. These metrics are deliberately modest. They show whether the index finds the right records and whether the safety behavior works. They do not claim human-rated answer quality or factual validity outside this fictional corpus.

## Responsible-AI choices

- The interface labels the data as fictional on every main view.
- The emergency record says its phone number is not real.
- The app refuses unsupported questions and exposes the nearest records separately as evidence candidates.
- No personal data is stored in the repository.
- Secrets are read from environment variables or Streamlit secrets and are never rendered in the UI.
- The public app has a per-session request cap and an input-length limit.
