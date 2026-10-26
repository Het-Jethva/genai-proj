# Demo script

## Before the demo

Replace the student and faculty placeholders in the report and deck. Run the validation command and the unit tests. If using OpenRouter, put the key in the local environment or host secrets panel. Do not show the key on screen.

## Demo sequence

1. Open the Ask tab and point to the visible fictional-data notice.
2. Ask, "When are Term 1 fees due?" Show the answer, the retrieval score, the provider path, and the `[R1]` evidence record.
3. Ask, "How many books can an undergraduate borrow?" Point out that the answer includes the six-book limit and fourteen-day loan period from the library record.
4. Ask, "What is tomorrow's cafeteria menu?" Show the refusal. Explain that the assistant does not fill missing evidence with a guess.
5. Open the Corpus tab. Filter by Scholarships or Placements and show the source label, effective date, tags, and fictional marker.
6. Open the Evaluation tab and run the 40-case suite. Explain recall@5, refusal accuracy, citation validity, and keyword coverage in plain language.
7. Close with the limitation: this is a classroom prototype over synthetic data. A real campus deployment needs approved documents, content ownership, expiry monitoring, privacy review, and user testing.

## Questions to expect

**Why use synthetic data?**

The project needed a self-prepared dataset without exposing real student or institutional records. Synthetic records make the pipeline reproducible and let the demo show dates, limits, source labels, and refusal cases. They are not a substitute for approved university data.

**What happens without an API key?**

The retrieval and evaluation still run. The service uses a deterministic grounded fallback that cites the selected record. Hosted generation is an optional presentation layer.

**How do you reduce hallucination?**

The system retrieves evidence first, sends only that evidence to the hosted model, requires citations, validates citation labels, and refuses low-coverage queries. The fallback path remains available when the model or network fails.

**What would you improve next?**

Replace the fictional corpus with approved documents, add a content expiry workflow, enable dense embeddings after measuring their benefit, and collect human ratings for correctness, helpfulness, and refusal quality.

