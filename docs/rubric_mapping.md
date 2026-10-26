# CCA rubric mapping

The project is designed for the 15-mark evaluation supplied in the class brief.

| Criterion | Evidence in this project | How to show it |
|---|---|---|
| Understanding of topic / concept - 3 | RAG pipeline, evidence-first prompt, retrieval scores, refusal policy, and dataset card | Explain the pipeline from JSONL record to cited answer. |
| Quality and technical implementation - 3 | Schema validation, hybrid index, provider adapter, deterministic fallback, citation checking, tests, and evaluation command | Run validation, unit tests, and the Evaluation tab. |
| Creativity and originality - 3 | Fictional Northbridge corpus, evidence trail, explicit out-of-scope behavior, and Corpus inspection view | Show the supported question followed by the cafeteria-menu refusal. |
| Application / impact - 4 | Campus-helpdesk workflow covers academic, financial, library, career, facilities, club, scholarship, and wellbeing queries | Explain how a student gets a next step without searching several records manually. |
| Documentation and presentation - 2 | Report, dataset card, methodology, demo script, rubric map, README, and PPTX deck | Use the deck narrative and keep the synthetic-data limitation visible. |

## Submission checklist

- [ ] Replace `[Student 1]`, `[Student 2]`, `[Faculty Name]`, and cover placeholders.
- [ ] Keep the fictional institute and data disclaimer in the report, deck, and app.
- [ ] Run `uv run python scripts\validate_dataset.py`.
- [ ] Run `uv run python -m unittest discover -s tests -v`.
- [ ] Run `uv run python scripts\evaluate.py` and keep the generated result file with the submission.
- [ ] Test one supported question and one refusal on the machine used for the presentation.
- [ ] If deploying publicly, add the OpenRouter key through host secrets only.
