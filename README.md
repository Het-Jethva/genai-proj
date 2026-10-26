# Northbridge Guide

Northbridge Guide is a submission-ready GenAI project for ECSDI24402, Gen AI and applications. It is a Streamlit campus-helpdesk prototype backed by a self-prepared fictional dataset. The assistant retrieves evidence first, cites the records it uses, and refuses questions that fall outside the corpus.

## What this project demonstrates

- A curated JSONL dataset with 54 records across 9 campus areas.
- Hybrid retrieval using weighted lexical similarity, character n-grams, and a transparent concept-expansion layer.
- Optional dense retrieval with `sentence-transformers` when the optional dependency is installed and enabled.
- OpenRouter chat generation with `openrouter/free` when a key is available.
- A deterministic grounded fallback so the demo and evaluation still run without a key.
- Source labels, effective dates, refusal behavior, query-length limits, and a per-session request cap.
- A 40-question offline evaluation set with 37 supported cases and 3 refusal cases.
- A Streamlit interface with Ask, Evaluation, and Corpus views, including safely rendered Markdown answers.

The institute, policy records, contact number, dates, and amounts are fictional. Do not present them as official university information. Replace the corpus with approved local material before using the idea outside this submission.

## Project structure

```text
app.py                         Streamlit application
data/campus_records.jsonl      self-prepared fictional knowledge corpus
data/evaluation_set.jsonl     40-case ground-truth evaluation set
src/campus_guide/              loading, retrieval, answering, provider, evaluation
scripts/                       dataset validation and offline evaluation commands
tests/                         standard-library unit tests
docs/                          dataset card, methodology, demo script, rubric map
pyproject.toml                 project metadata and dependencies
uv.lock                        locked dependency resolution for uv
```

## Run it locally

Use Python 3.10 or newer. The verified setup uses `uv`:

```powershell
uv sync --dev
uv run python scripts\validate_dataset.py
uv run python -m unittest discover -s tests -v
uv run python scripts\evaluate.py
uv run streamlit run app.py
uv run ruff check app.py src scripts tests
```

If you prefer standard tooling, `python -m venv .venv` followed by `python -m pip install -r requirements.txt` also works.

The app works without an API key. In that mode it uses the deterministic grounded fallback and labels the provider path in the interface.

To enable hosted generation for a local run, set the key only in your shell or a local secrets file:

```powershell
$env:OPENROUTER_API_KEY = "your-key"
$env:OPENROUTER_MODEL = "openrouter/free"
uv run streamlit run app.py
```

Never commit a real key. `.env.example` and `.streamlit/secrets.toml.example` show the supported configuration shape.
For local convenience, the app also loads a project-local `.env` file when present. Keep that file private and untracked.

OpenRouter exposes an OpenAI-compatible chat-completions endpoint and documents `openrouter/free` as its free-model router. Check its current limits and model availability before the live demo: [OpenRouter quickstart](https://openrouter.ai/docs/quickstart), [free models router](https://openrouter.ai/docs/cookbook/get-started/free-models-router-playground).

## Optional dense retrieval

The default deployment stays light and keyless. To add a local dense semantic score, install the optional package and enable it:

```powershell
uv sync --extra dense
$env:ENABLE_DENSE_EMBEDDINGS = "1"
uv run streamlit run app.py
```

The first run downloads the configured embedding model. If the package or model is unavailable, the app returns to its deterministic hybrid lexical/concept index.

## Rebuild project artifacts

The report builders use the `docs` extra so a fresh uv environment can reproduce the editable report and PDF:

```powershell
uv run --extra docs python scripts\build_report.py
uv run --extra docs python scripts\build_report_pdf.py
```

## Streamlit Community Cloud

1. Push this repository to a Git provider without any secrets.
2. Create a Streamlit app with `app.py` as the main file.
3. Keep `requirements.txt` as the dependency file.
4. Add `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `OPENROUTER_SITE_URL`, and `OPENROUTER_APP_NAME` in the app's Secrets panel.
5. Open the public URL and test one supported question and one out-of-scope question.

The app keeps chat open to visitors but limits each browser session to 30 requests and caps each question at 800 characters. This does not replace host-level quota controls. If the live key is unavailable, the public app remains usable through the grounded fallback.

## Evaluation

The offline command does not call the hosted model. It measures the repeatable baseline:

- Recall@5 for supported questions.
- Refusal accuracy across supported and out-of-scope questions.
- Citation validity for grounded answers.
- Keyword coverage against the curated reference answers.

The current run produced 100% retrieval recall@5, 100% refusal accuracy, 100% citation validity, and 91.4% answer keyword coverage. Supported-case status also requires at least 75% keyword coverage; these are baseline results for the prepared fictional corpus, not claims about a real university service.

## Presentation handoff

- `docs/project_report.md` is the report source.
- `docs/demo_script.md` is the speaking and demo sequence.
- `docs/rubric_mapping.md` ties project evidence to the 15-mark evaluation.
- `output/Northbridge_Guide_CCA.pptx` is the presentation deck.
- `output/Northbridge_Guide_Report.docx` is the formatted report.
- `output/Northbridge_Guide_Report.pdf` is the visually verified PDF report.

Before submission, replace `[Student 1]`, `[Student 2]`, `[Faculty Name]`, and any course-specific cover fields in the report and deck. Keep the fictional-data disclaimer visible.
