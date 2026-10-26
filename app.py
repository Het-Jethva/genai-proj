"""Northbridge Guide Streamlit application."""

from __future__ import annotations

import hashlib
import html
from pathlib import Path

try:
    import streamlit as st
except ImportError as exc:  # pragma: no cover - exercised only before installation
    raise SystemExit("Install the project dependencies first: uv sync --dev") from exc

from src.campus_guide.answering import AnswerService
from src.campus_guide.data import category_counts, load_evaluation_cases
from src.campus_guide.evaluation import category_evaluation, evaluate_cases
from src.campus_guide.providers import build_provider
from src.campus_guide.retrieval import RetrievalIndex
from src.campus_guide.settings import SettingsError, get_settings

ROOT = Path(__file__).resolve().parent
RECORDS_PATH = ROOT / "data" / "campus_records.jsonl"
EVALUATION_PATH = ROOT / "data" / "evaluation_set.jsonl"
CSS_PATH = ROOT / "src" / "campus_guide" / "ui.css"

SAMPLE_QUESTIONS = [
    "When are Term 1 fees due?",
    "How many books can an undergraduate borrow?",
    "What should I do when a building alarm sounds?",
    "How do I request a resume clinic?",
]


@st.cache_resource(show_spinner=False)
def get_index(enable_dense: bool, records_fingerprint: str) -> RetrievalIndex:
    return RetrievalIndex.from_path(RECORDS_PATH, enable_dense=enable_dense)


@st.cache_data(show_spinner=False)
def get_cases(evaluation_fingerprint: str):
    return load_evaluation_cases(EVALUATION_PATH)


def file_fingerprint(path: Path) -> str:
    """Return a content fingerprint so Streamlit caches follow data edits."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _secret_or_empty(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value)
    except FileNotFoundError:
        pass
    return ""


def get_app_settings():
    secret_names = (
        "OPENROUTER_API_KEY",
        "OPENROUTER_MODEL",
        "OPENROUTER_BASE_URL",
        "OPENROUTER_SITE_URL",
        "OPENROUTER_APP_NAME",
        "ENABLE_DENSE_EMBEDDINGS",
        "MIN_RETRIEVAL_SCORE",
        "MAX_REQUESTS_PER_SESSION",
    )
    overrides = {name: _secret_or_empty(name) for name in secret_names}
    overrides = {name: value for name, value in overrides.items() if value}
    return get_settings(overrides)


def inject_styles() -> None:
    st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def render_header(index: RetrievalIndex, settings) -> None:
    mode = "hosted answers" if settings.api_configured else "keyless grounded fallback"
    st.markdown(
        """
        <header class="app-header">
          <div>
            <p class="app-kicker">GEN AI / CCA PROJECT / 2026</p>
            <h1 class="app-wordmark">Northbridge Guide</h1>
            <p class="app-lede">A fictional campus helpdesk that answers from a prepared corpus, names the record it used, and stops when the evidence runs out.</p>
          </div>
          <div class="header-search"><strong>⌘K</strong><span>SEARCH / EVIDENCE</span></div>
        </header>
        """,
        unsafe_allow_html=True,
    )
    counts = category_counts(index.records)
    st.markdown(
        f"""
        <div class="trust-strip">
          <span><strong>{len(index.records)}</strong> curated records</span>
          <span><strong>{len(counts)}</strong> campus areas</span>
          <span><strong>{index.stats()['retrieval_mode']}</strong></span>
          <span><strong>{html.escape(mode)}</strong></span>
          <span>fictional data / no official policy</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_heading(kicker: str, title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="section-heading">
          <p class="section-kicker">{html.escape(kicker)}</p>
          <h2>{html.escape(title)}</h2>
          <p>{html.escape(description)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_strip(metrics: list[tuple[str, str, str]]) -> None:
    cells = []
    for label, value, note in metrics:
        cells.append(
            f"<div class='metric-cell'><div class='metric-label'>{html.escape(label)}</div>"
            f"<div class='metric-value'>{html.escape(value)}</div><div class='metric-note'>{html.escape(note)}</div></div>"
        )
    st.markdown(f"<div class='metric-strip'>{''.join(cells)}</div>", unsafe_allow_html=True)


def render_result(result) -> None:
    shell_key = "answer_shell_refusal" if result.refused else "answer_shell_grounded"
    chip_class = "status-chip is-refused" if result.refused else "status-chip is-grounded"
    chip_text = "EVIDENCE NOT FOUND" if result.refused else "GROUNDED ANSWER"
    score = f"{result.top_score:.2f}" if result.hits else "-"
    with st.container(key=shell_key):
        st.markdown(
            f"<div class='answer-title'><h3>Response</h3><span class='{chip_class}'>{chip_text}</span></div>",
            unsafe_allow_html=True,
        )
        with st.container(key=f"{shell_key}_copy"):
            st.markdown(result.answer, unsafe_allow_html=False)
        st.markdown(
            f"""
            <div class="answer-meta">
              <span>retrieval score / {score}</span>
              <span>provider / {html.escape(result.provider)}</span>
              <span>latency / {result.latency_ms} ms</span>
              <span>mode / {html.escape(result.retrieval_mode)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    if result.provider_error and result.provider_error != "query_too_long":
        st.caption("Hosted generation was unavailable for this request. The answer shown uses the grounded fallback path.")
    if not result.hits:
        return

    st.markdown("<h3 class='evidence-title'>Evidence trail</h3>", unsafe_allow_html=True)
    for position, hit in enumerate(result.hits):
        record = hit.record
        label = f"R{position + 1}"
        st.markdown(
            f"""
            <article class="evidence-card">
              <div class="evidence-card__head"><span class="evidence-card__label">[{label}] / {html.escape(record.id)}</span><span class="evidence-card__score">{hit.score:.2f}</span></div>
              <h4>{html.escape(record.title)}</h4>
              <p>{html.escape(record.content)}</p>
              <p class="evidence-card__meta">{html.escape(record.source)} / effective {html.escape(record.effective_date)}</p>
            </article>
            """,
            unsafe_allow_html=True,
        )


def render_ask_tab(index: RetrievalIndex, settings) -> None:
    render_section_heading(
        "Ask the corpus",
        "One question. Named evidence.",
        "Northbridge Guide retrieves the nearest records before it writes. Try a supported question, then test the refusal path with a topic the corpus does not cover.",
    )
    render_metric_strip(
        [
            ("Records", str(len(index.records)), "prepared JSONL units"),
            ("Areas", str(len(index.categories)), "campus helpdesk scope"),
            ("Context", str(settings.max_context_records), "records sent to the model"),
            ("Session", f"{st.session_state.get('request_count', 0)} / {settings.max_requests_per_session}", "open demo request cap"),
        ]
    )

    if "pending_question" in st.session_state:
        st.session_state["question_input"] = st.session_state.pop("pending_question")

    left, right = st.columns([1.42, 0.58], gap="large")
    with left, st.container(key="query_panel"), st.form("ask_form", clear_on_submit=False):
        question = st.text_area(
            "Question",
            key="question_input",
            height=124,
            placeholder="Example: How many books can an undergraduate borrow?",
            help="Ask one campus question in 800 characters or fewer.",
        )
        st.caption("The assistant will refuse questions that do not clear the evidence threshold.")
        submitted = st.form_submit_button("Answer with evidence", width="stretch")

    with right, st.container(key="sample_panel"):
        st.markdown(
            "<h3>Try a prepared query</h3><p class='sample-copy'>These prompts map to records in the evaluation set.</p>",
            unsafe_allow_html=True,
        )
        for idx, sample in enumerate(SAMPLE_QUESTIONS):
            if st.button(sample, key=f"sample_{idx}", width="stretch"):
                st.session_state["pending_question"] = sample
                st.rerun()

    if submitted:
        request_count = int(st.session_state.get("request_count", 0))
        if request_count >= settings.max_requests_per_session:
            st.error("This demo session reached its request cap. Start a new session to continue testing.")
        else:
            st.session_state["request_count"] = request_count + 1
            provider = build_provider(settings)
            service = AnswerService(index, settings, provider=provider)
            with st.spinner("Retrieving evidence and writing the answer..."):
                result = service.answer(question)
            st.session_state["latest_result"] = result
            history = st.session_state.setdefault("history", [])
            history.insert(0, {"question": question, "refused": result.refused, "score": result.top_score})
            del history[5:]

    latest = st.session_state.get("latest_result")
    if latest is not None:
        render_result(latest)
    else:
        st.markdown(
            """
            <div class="answer-shell">
              <div class="answer-title"><h3>Waiting for a question</h3><span class="status-chip">READY</span></div>
              <div class="answer-copy"><p>The first answer will show the generated response, the retrieval score, the provider path, and every record sent as evidence.</p></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    history = st.session_state.get("history", [])
    if history:
        st.markdown("<h3 class='evidence-title'>Recent queries</h3>", unsafe_allow_html=True)
        for item in history:
            state = "refused" if item["refused"] else "answered"
            st.markdown(
                f"<div class='corpus-row'><p>{html.escape(item['question'])}</p><p class='corpus-row__meta'>{state} / top score {item['score']:.2f}</p></div>",
                unsafe_allow_html=True,
            )


def render_evaluation_tab(index: RetrievalIndex, settings) -> None:
    render_section_heading(
        "Offline evaluation",
        "Measure the retrieval before you trust the answer.",
        "The 40-case suite contains supported questions across the corpus and three deliberately out-of-scope prompts. It runs without an API key so the reported numbers are repeatable.",
    )
    cases = get_cases(file_fingerprint(EVALUATION_PATH))
    render_metric_strip(
        [
            ("Test cases", str(len(cases)), "curated ground truth"),
            ("Supported", str(sum(not case.expected_refusal for case in cases)), "answerable prompts"),
            ("Refusals", str(sum(case.expected_refusal for case in cases)), "out-of-scope prompts"),
            ("Top-k", "5", "retrieval recall window"),
        ]
    )
    if st.button("Run offline evaluation", key="run_evaluation", width="content"):
        evaluation_service = AnswerService(index, settings, provider=None)
        with st.spinner("Running the 40-case evaluation..."):
            st.session_state["evaluation_report"] = evaluate_cases(evaluation_service, cases, top_k=5)

    report = st.session_state.get("evaluation_report")
    if not report:
        st.markdown(
            "<div class='answer-shell'><div class='answer-title'><h3>Evaluation is ready</h3><span class='status-chip'>OFFLINE</span></div><div class='answer-copy'><p>Run the suite to inspect recall, refusal accuracy, citation validity, and answer keyword coverage.</p></div></div>",
            unsafe_allow_html=True,
        )
        return

    render_metric_strip(
        [
            ("Recall @ 5", f"{report['retrieval_recall_at_k']:.0%}", "supported cases"),
            ("Refusal accuracy", f"{report['refusal_accuracy']:.0%}", "all cases"),
            ("Citations", f"{report['citation_validity']:.0%}", "valid supported answers"),
            ("Keyword coverage", f"{report['answer_keyword_coverage']:.0%}", "fallback answer text"),
        ]
    )
    st.caption("These values use the deterministic grounded fallback. Hosted model output can vary, so the same suite remains the baseline check.")
    st.dataframe(report["cases"], width="stretch", hide_index=True)
    st.markdown("<h3 class='evidence-title'>Category view</h3>", unsafe_allow_html=True)
    st.caption(
        f"Case status requires correct refusal behavior, expected retrieval, a valid citation, and at least {report['answer_quality_threshold']:.0%} keyword coverage for supported cases."
    )
    st.dataframe(category_evaluation(report["cases"]), width="stretch", hide_index=True)


def render_corpus_tab(index: RetrievalIndex) -> None:
    render_section_heading(
        "Prepared corpus",
        "Read the records the model can use.",
        "Every record is fictional, hand-curated for this project, and stored as an inspectable JSONL line with a source label, effective date, tags, and confidence marker.",
    )
    category = st.selectbox("Filter by campus area", ["All areas", *index.categories], key="corpus_category")
    query = st.text_input("Filter records", key="corpus_filter", placeholder="Search titles, tags, and content")
    normalized = query.lower().strip()
    records = [
        record
        for record in index.records
        if (category == "All areas" or record.category == category)
        and (not normalized or normalized in record.as_search_text().lower())
    ]
    st.caption(f"Showing {len(records)} of {len(index.records)} records")
    for record in records:
        st.markdown(
            f"""
            <article class="corpus-row">
              <h3>{html.escape(record.title)}</h3>
              <p>{html.escape(record.content)}</p>
              <p class="corpus-row__meta">{html.escape(record.id)} / {html.escape(record.category)} / {html.escape(record.source)} / effective {html.escape(record.effective_date)}</p>
            </article>
            """,
            unsafe_allow_html=True,
        )


def render_sidebar(index: RetrievalIndex, settings) -> bool:
    st.sidebar.markdown("## Northbridge Guide")
    st.sidebar.caption("CCA submission prototype")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Runtime")
    if settings.api_configured:
        st.sidebar.success("OpenRouter key configured")
    else:
        st.sidebar.info("Keyless grounded fallback")
    st.sidebar.caption("The app never displays or stores the API key.")
    dense = st.sidebar.checkbox(
        "Enable dense retrieval",
        value=settings.enable_dense_embeddings,
        help="Uses sentence-transformers only when the optional package is installed. The default index stays keyless and lightweight.",
    )
    st.sidebar.markdown("### Corpus")
    st.sidebar.caption(f"{len(index.records)} records / {len(index.categories)} areas")
    st.sidebar.caption("All records are fictional and must not be presented as official university policy.")
    return dense


def main() -> None:
    st.set_page_config(page_title="Northbridge Guide", page_icon="N", layout="wide", initial_sidebar_state="collapsed")
    inject_styles()
    try:
        settings = get_app_settings()
    except SettingsError as exc:
        st.error(f"Configuration error: {exc}")
        st.stop()
    records_fingerprint = file_fingerprint(RECORDS_PATH)
    index = get_index(settings.enable_dense_embeddings, records_fingerprint)
    dense_choice = render_sidebar(index, settings)
    if dense_choice != settings.enable_dense_embeddings:
        index = get_index(dense_choice, records_fingerprint)

    if "request_count" not in st.session_state:
        st.session_state["request_count"] = 0
    if "history" not in st.session_state:
        st.session_state["history"] = []

    render_header(index, settings)
    ask_tab, evaluation_tab, corpus_tab = st.tabs(["Ask", "Evaluation", "Corpus"])
    with ask_tab:
        render_ask_tab(index, settings)
    with evaluation_tab:
        render_evaluation_tab(index, settings)
    with corpus_tab:
        render_corpus_tab(index)

    st.markdown(
        "<footer class='footer-rule'><p class='footer-copy'>Northbridge Guide / fictional dataset / evidence-first RAG / CCA component project / replace the placeholders in the report before submission.</p></footer>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
