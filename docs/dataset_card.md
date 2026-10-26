# Dataset card: Northbridge campus records

## Summary

`data/campus_records.jsonl` contains 54 hand-curated fictional knowledge records for the Northbridge Guide project. The records cover academics, examinations, fees, library, scholarships, clubs and societies, placements and careers, facilities and IT, and safety and wellbeing.

Each line contains:

- `id`: stable identifier used for citations and evaluation.
- `category`: campus area.
- `title`: short retrieval label.
- `content`: one coherent policy or service record.
- `source`: a fictional document section label.
- `effective_date`: synthetic date used to demonstrate date-aware grounding.
- `tags`: retrieval terms and paraphrase anchors.
- `confidence`: `curated-synthetic`.
- `source_type`: `synthetic`.

## Collection and preparation

The records were authored for this project, then organized into comparable knowledge units. Each record carries one subject, a source label, a date, and tags that support exact and paraphrased questions. Repeated broad claims were avoided. The corpus includes explicit limits, exception paths, and privacy reminders so the RAG prompt has concrete details to cite.

## Intended use

Use this dataset to demonstrate retrieval-augmented generation, citation display, refusal behavior, corpus inspection, and offline evaluation in a classroom setting.

## Out of scope

The corpus is not an official policy source. It must not be used to make real decisions about fees, examinations, safety, wellbeing, scholarships, placements, or student eligibility. The emergency number is fictional and must never be dialled.

## Bias and limitations

The dataset reflects the project authors' chosen campus categories and phrasing. It does not represent the needs of every student, language, disability, or campus process. All records are in English. A real deployment would need approved source documents, ownership review, expiry checks, privacy review, multilingual testing, and a named content owner.

## Maintenance

Run `uv run python scripts\validate_dataset.py` after changing either JSONL file. Update the evaluation set when a record is added or materially changed. Do not silently change an answerable policy without changing its source label or effective date.
