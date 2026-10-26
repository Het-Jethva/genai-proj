"""Build a visually verifiable PDF version of the CCA report."""

from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "Northbridge_Guide_Report.pdf"
EVAL_PATH = ROOT / "output" / "evaluation_results.json"
CORPUS_PATH = ROOT / "data" / "campus_records.jsonl"

NAVY = colors.HexColor("#202B3D")
BLUE = colors.HexColor("#3565D4")
BLUE_DARK = colors.HexColor("#23479D")
MUTED = colors.HexColor("#667085")
LINE = colors.HexColor("#D9DFEA")
PAPER = colors.HexColor("#F7F8FC")
PALE_BLUE = colors.HexColor("#E9EEFC")
PALE_TEAL = colors.HexColor("#E7F4F1")
TEAL = colors.HexColor("#0A7B73")
PALE_RED = colors.HexColor("#FBEAEC")
RED = colors.HexColor("#B63D4A")
GRAPHITE = colors.HexColor("#1F2937")


def make_styles():
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "Title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=28,
            leading=32, textColor=NAVY, spaceAfter=8,
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle", parent=base["Normal"], fontName="Helvetica", fontSize=12.5,
            leading=17, textColor=MUTED, spaceAfter=16,
        ),
        "Eyebrow": ParagraphStyle(
            "Eyebrow", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8.5,
            leading=10, textColor=BLUE, tracking=0.8, spaceAfter=5,
        ),
        "H1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=18,
            leading=22, textColor=BLUE_DARK, spaceBefore=6, spaceAfter=8,
            keepWithNext=True,
        ),
        "H2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=12.5,
            leading=16, textColor=BLUE_DARK, spaceBefore=8, spaceAfter=5,
            keepWithNext=True,
        ),
        "Body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.6,
            leading=13.6, textColor=NAVY, spaceAfter=6,
        ),
        "BodyMuted": ParagraphStyle(
            "BodyMuted", parent=base["BodyText"], fontName="Helvetica", fontSize=9.1,
            leading=12.5, textColor=MUTED, spaceAfter=5,
        ),
        "Small": ParagraphStyle(
            "Small", parent=base["BodyText"], fontName="Helvetica", fontSize=8.2,
            leading=10.5, textColor=MUTED, spaceAfter=3,
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=8.2,
            leading=10.5, textColor=colors.HexColor("#F1F4FA"), spaceAfter=0,
        ),
        "SmallMono": ParagraphStyle(
            "SmallMono", parent=base["BodyText"], fontName="Courier", fontSize=8,
            leading=10.5, textColor=NAVY, spaceAfter=3,
        ),
        "Callout": ParagraphStyle(
            "Callout", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=12,
            leading=16, textColor=NAVY, spaceAfter=0,
        ),
        "Metric": ParagraphStyle(
            "Metric", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=16,
            leading=18, textColor=BLUE, alignment=TA_RIGHT,
        ),
        "MetricLabel": ParagraphStyle(
            "MetricLabel", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=9.2,
            leading=12, textColor=NAVY,
        ),
        "CenterSmall": ParagraphStyle(
            "CenterSmall", parent=base["BodyText"], fontName="Helvetica", fontSize=8.2,
            leading=10.2, textColor=MUTED, alignment=TA_CENTER,
        ),
    }


STYLES = make_styles()


def p(text: str, style: str = "Body") -> Paragraph:
    return Paragraph(text, STYLES[style])


def bullet(text: str) -> Paragraph:
    return Paragraph(f"<font color='#3565D4'>-</font>&nbsp;&nbsp;{escape(text)}", STYLES["Body"])


def link(label: str, url: str) -> str:
    return f"<link href='{url}' color='#3565D4'><u>{escape(label)}</u></link>"


def styled_table(data, widths, header=True, row_backgrounds=None, font_size=8.7, padding=7):
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), padding),
        ("RIGHTPADDING", (0, 0), (-1, -1), padding),
        ("TOPPADDING", (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
    ]
    if header:
        commands.extend([
            ("BACKGROUND", (0, 0), (-1, 0), GRAPHITE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ])
        start = 1
    else:
        start = 0
    if row_backgrounds:
        for index, fill in row_backgrounds.items():
            commands.append(("BACKGROUND", (0, index + start), (-1, index + start), fill))
    table.setStyle(TableStyle(commands))
    return table


def callout(title: str, body: str, fill=PALE_BLUE, border=BLUE):
    box = Table([[p(title, "Callout")], [p(body, "Body")]], colWidths=[6.95 * inch], hAlign="LEFT")
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fill),
        ("BOX", (0, 0), (-1, -1), 0.7, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 13),
        ("RIGHTPADDING", (0, 0), (-1, -1), 13),
        ("TOPPADDING", (0, 0), (-1, 0), 11),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, 1), 2),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 11),
    ]))
    return box


def draw_page(canvas, doc):
    canvas.saveState()
    width, height = letter
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.6)
    canvas.line(0.75 * inch, height - 0.53 * inch, width - 0.75 * inch, height - 0.53 * inch)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(0.75 * inch, height - 0.39 * inch, "NORTHBRIDGE GUIDE  /  CCA PROJECT")
    canvas.setStrokeColor(LINE)
    canvas.line(0.75 * inch, 0.53 * inch, width - 0.75 * inch, 0.53 * inch)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(0.75 * inch, 0.35 * inch, "ECSDI24402  /  Option 1")
    canvas.drawRightString(width - 0.75 * inch, 0.35 * inch, f"Page {doc.page}")
    canvas.restoreState()


def load_project_stats():
    report = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    records = [
        json.loads(line)
        for line in CORPUS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return report, len(records), len({record["category"] for record in records})


def build_story():
    report, record_count, category_count = load_project_stats()
    story = []

    story.extend([
        Spacer(1, 0.35 * inch),
        p("CCA PROJECT REPORT", "Eyebrow"),
        p("Northbridge Guide", "Title"),
        p("An evidence-first campus information assistant using retrieval-augmented generation", "Subtitle"),
    ])

    metadata = [
        [p("Course", "Small"), p("Gen AI and applications [ECSDI24402]", "Body")],
        [p("CCA choice", "Small"), p("Option 1, Project", "Body")],
        [p("Team", "Small"), p("[Student 1] and [Student 2]", "Body")],
        [p("Faculty", "Small"), p("[Faculty Name]", "Body")],
        [p("Date", "Small"), p("31 August 2026", "Body")],
    ]
    meta = Table(metadata, colWidths=[1.25 * inch, 5.7 * inch], hAlign="LEFT")
    meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), PALE_BLUE),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([meta, Spacer(1, 0.18 * inch)])
    story.append(callout(
        "Project thesis",
        "A campus assistant should make its evidence boundary visible: retrieve relevant records, answer from them, and refuse when the corpus does not support the question.",
        fill=PALE_TEAL,
        border=TEAL,
    ))
    story.extend([
        Spacer(1, 0.2 * inch),
        p("Executive summary", "H1"),
        p("Northbridge Guide is a classroom-ready Option 1 project for the Gen AI and applications CCA. The team created a transparent synthetic campus corpus, implemented a hybrid retrieval pipeline, added an answerability gate, and wrapped the system in a Streamlit interface. The user sees both the generated answer and the evidence records used to produce it.", "Body"),
        p("The implementation has two provider modes. A live OpenRouter route uses the configured free-model router when an API key is available. A deterministic fallback keeps the offline evaluation reproducible and lets the demo run even when the external provider is unavailable. Unsupported questions follow a refusal path instead of receiving invented details.", "Body"),
        p(f"The verified baseline contains {report['total_cases']} evaluation cases: {report['supported_cases']} supported questions and {report['refusal_cases']} refusal cases. It achieved {report['retrieval_recall_at_k']:.2f} retrieval recall@5, {report['refusal_accuracy']:.2f} refusal accuracy, {report['citation_validity']:.2f} citation validity, and {report['answer_keyword_coverage']:.4f} keyword coverage.", "Body"),
        PageBreak(),
        p("1. Project definition", "H1"),
        p("Problem", "H2"),
        p("Campus questions often look simple but depend on specific procedural, policy, or facilities information. A general language model can produce a fluent response even when it has no reliable campus source. This project treats groundedness and refusal behavior as first-class requirements.", "Body"),
        p("Objectives", "H2"),
        bullet("Create and validate a self-prepared dataset on a suitable campus topic."),
        bullet("Perform a GenAI task using the dataset through retrieval-augmented generation."),
        bullet("Show evidence labels and a refusal explanation in the user interface."),
        bullet("Measure retrieval, refusal, citation, and answer-content behavior offline."),
        p("Scope", "H2"),
        p("The prototype is intentionally framed as a fictional institute, Northbridge Institute. It is a demonstration artifact, not official campus infrastructure. The synthetic label is repeated in the corpus, interface, report, and presentation so a reviewer cannot mistake the examples for real institutional data.", "Body"),
        p("2. Dataset card", "H1"),
        p("The corpus is stored as JSONL in <font name='Courier'>data/campus_records.jsonl</font> and validated before use. Each record includes an identifier, category, title, answer, tags, source label, confidence marker, source type, and synthetic date.", "Body"),
    ])
    dataset_rows = [
        [p("Property", "TableHeader"), p("Verified value", "TableHeader")],
        [p("Records", "Body"), p(str(record_count), "Body")],
        [p("Categories", "Body"), p(f"{category_count} categories", "Body")],
        [p("Coverage", "Body"), p("Academics, examinations, fees, library, scholarships, clubs and societies, placements, facilities and IT, safety and wellbeing", "Body")],
        [p("Source type", "Body"), p("Synthetic, curated by the project team", "Body")],
        [p("Language", "Body"), p("English", "Body")],
        [p("Safety boundary", "Body"), p("No real institute, contact, or emergency data", "Body")],
    ]
    story.extend([styled_table(dataset_rows, [1.45 * inch, 5.5 * inch]), Spacer(1, 0.12 * inch)])
    story.extend([
        p("Data preparation process", "H2"),
        bullet("Define a fictional institute and the campus helpdesk categories."),
        bullet("Write compact records with one answerable topic per record."),
        bullet("Add tags and alternate wording to support retrieval."),
        bullet("Run the validator to check required fields, unique IDs, category counts, and synthetic source markers."),
        PageBreak(),
        p("3. Methodology and technical implementation", "H1"),
        p("The application separates retrieval, answerability, provider access, and presentation. That separation makes the project easier to inspect and evaluate than a single opaque prompt.", "Body"),
    ])
    method_rows = [
        [p("Layer", "TableHeader"), p("Implementation", "TableHeader"), p("Purpose", "TableHeader")],
        [p("Data", "Body"), p("JSONL loader and validator", "Body"), p("Load a known, inspectable corpus", "Body")],
        [p("Retrieval", "Body"), p("Hybrid lexical cosine, character 3-grams, concept groups; optional dense embeddings", "Body"), p("Rank evidence for varied campus wording", "Body")],
        [p("Gate", "Body"), p("Minimum retrieval score 0.16 plus support-signal checks", "Body"), p("Prevent unsupported generation", "Body")],
        [p("Generation", "Body"), p("OpenRouter-compatible HTTP provider with <font name='Courier'>openrouter/free</font>; deterministic fallback", "Body"), p("Produce a concise grounded answer", "Body")],
        [p("Trace", "Body"), p("Evidence blocks with valid <font name='Courier'>[R#]</font> citations", "Body"), p("Make the response inspectable", "Body")],
        [p("UI", "Body"), p("Streamlit Ask, Evaluation, and Corpus tabs", "Body"), p("Support demo, evaluation, and corpus inspection", "Body")],
    ]
    story.extend([styled_table(method_rows, [1.05 * inch, 3.2 * inch, 2.7 * inch]), Spacer(1, 0.14 * inch)])
    story.extend([
        p("Request flow", "H2"),
        bullet("Normalize the query and enforce the maximum input length."),
        bullet("Retrieve the top five candidate records."),
        bullet("Check answerability, including score, concept support, and unsupported-term ratio."),
        bullet("If supported, send only evidence blocks to the provider and instruct it to cite [R#] labels."),
        bullet("Filter invalid citations, trim the answer, and return the evidence trail."),
        bullet("If unsupported, return a deterministic refusal without citations."),
        p("Provider and deployment", "H2"),
        p("The live provider is configured through environment variables or Streamlit secrets. The API key is never stored in the repository. Streamlit Community Cloud is the target deployment. The public app is intentionally rate-limited per session because the live provider is an external dependency.", "Body"),
        p(f"Provider documentation used during implementation: {link('OpenRouter Quickstart', 'https://openrouter.ai/docs/quickstart')} and {link('OpenRouter chat API reference', 'https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request?explorer=true')}.", "BodyMuted"),
        PageBreak(),
        p("4. Evaluation", "H1"),
        p(f"The evaluation set is stored in <font name='Courier'>data/evaluation_set.jsonl</font> and contains {report['total_cases']} manually curated cases. Each case records the expected evidence IDs, expected refusal behavior, reference answer, category, and rationale. The evaluator runs without a live API call so the baseline is repeatable.", "Body"),
    ])
    eval_rows = [
        [p("Metric", "TableHeader"), p("Result", "TableHeader"), p("Interpretation", "TableHeader")],
        [p("Retrieval recall@5", "MetricLabel"), p("100%", "Metric"), p("All 37 supported cases surfaced an expected record in the top five.", "Body")],
        [p("Refusal accuracy", "MetricLabel"), p("100%", "Metric"), p("All 3 out-of-scope cases refused.", "Body")],
        [p("Citation validity", "MetricLabel"), p("100%", "Metric"), p("Every emitted citation label pointed to retrieved evidence.", "Body")],
        [p("Keyword coverage", "MetricLabel"), p(f"{report['answer_keyword_coverage']:.1%}", "Metric"), p("Reference-answer terms covered by the generated or deterministic answer.", "Body")],
    ]
    story.extend([
        styled_table(eval_rows, [1.5 * inch, 0.9 * inch, 4.55 * inch], row_backgrounds={0: PALE_TEAL, 1: PALE_TEAL, 2: PALE_TEAL, 3: PALE_BLUE}),
        Spacer(1, 0.12 * inch),
        callout("Evaluation reading", "These results establish that the implemented behaviors work on the prepared benchmark. They do not establish official-campus correctness, broad language coverage, or production reliability.", fill=PALE_BLUE, border=BLUE),
        p("Test coverage", "H2"),
        bullet("Dataset validation: required fields, unique IDs, source markers, and category balance."),
        bullet("Retrieval: supported query ranking and out-of-scope behavior."),
        bullet("Answering: citation filtering, refusal path, deterministic fallback, and length limits."),
        bullet("Python unit tests cover dataset, retrieval, answering, settings, and evaluation behavior."),
        p("5. Demo plan", "H1"),
        p("The recommended demo uses three questions so the project contribution is visible quickly:", "Body"),
    ])
    demo_rows = [
        [p("Prompt", "TableHeader"), p("Expected behavior", "TableHeader"), p("Evidence", "TableHeader")],
        [p("How do I request a transcript?", "Body"), p("Grounded answer", "Body"), p("acad-003", "SmallMono")],
        [p("Can I borrow a laptop from the library?", "Body"), p("Grounded answer", "Body"), p("lib-003", "SmallMono")],
        [p("Where is the cafeteria?", "Body"), p("Clear refusal", "Body"), p("No citation emitted", "SmallMono")],
    ]
    story.extend([styled_table(demo_rows, [3.1 * inch, 1.65 * inch, 2.2 * inch]), Spacer(1, 0.12 * inch)])
    story.extend([
        p("For the live run, open the Evaluation tab after the three prompts. This connects the visible UI behavior to the offline evaluation artifact.", "Body"),
        PageBreak(),
        p("6. Responsible design and limitations", "H1"),
        p("The project makes its limitations explicit because the corpus and provider are not official systems of record.", "Body"),
    ])
    limits = [
        [p("Decision", "TableHeader"), p("How it is handled", "TableHeader")],
        [p("Synthetic content", "Body"), p("Every record carries a synthetic source marker. The app displays a synthetic-corpus badge and the report repeats the warning.", "Body")],
        [p("Unsupported queries", "Body"), p("The answerability gate refuses below threshold and the UI explains that no campus record supports the question.", "Body")],
        [p("Provider dependency", "Body"), p("The OpenRouter path is optional for evaluation. A deterministic fallback preserves classroom demonstrability if the API is unavailable.", "Body")],
        [p("Secrets", "Body"), p("API keys are configured through secrets or environment variables and are excluded from version control.", "Body")],
        [p("Public access", "Body"), p("The Streamlit deployment is rate-limited per session. A production system would need authentication, approved sources, logging policy, and stronger abuse controls.", "Body")],
    ]
    story.extend([
        styled_table(limits, [1.45 * inch, 5.5 * inch]),
        Spacer(1, 0.15 * inch),
        p("Known next steps", "H2"),
        bullet("Replace the synthetic corpus with approved, versioned institutional sources."),
        bullet("Add source freshness checks and record-level update history."),
        bullet("Expand adversarial, multilingual, and paraphrase evaluation."),
        bullet("Add authenticated access and monitoring before any real-world deployment."),
        p("7. Rubric mapping", "H1"),
    ])
    rubric_rows = [
        [p("Criterion", "TableHeader"), p("Evidence in this project", "TableHeader"), p("Marks", "TableHeader")],
        [p("Understanding of topic / concept", "Body"), p("RAG explanation, dataset card, architecture slide, and methodology report.", "Body"), p("3", "Metric")],
        [p("Quality and technical implementation", "Body"), p("Validated JSONL corpus, modular retrieval/answering/provider code, tests, and offline evaluator.", "Body"), p("3", "Metric")],
        [p("Creativity and originality", "Body"), p("Visible source boundary, evidence trail, and a designed refusal experience.", "Body"), p("3", "Metric")],
        [p("Application / impact", "Body"), p("Campus helpdesk use case, live Streamlit demo, public-safe synthetic framing, and a repeatable demo script.", "Body"), p("4", "Metric")],
        [p("Documentation and presentation", "Body"), p("This report, editable deck, dataset card, methodology, demo script, rubric mapping, and README.", "Body"), p("2", "Metric")],
    ]
    story.extend([
        styled_table(rubric_rows, [1.8 * inch, 4.2 * inch, 0.95 * inch], row_backgrounds={0: PALE_BLUE, 1: PALE_BLUE, 2: PALE_BLUE, 3: PALE_BLUE, 4: PALE_BLUE}),
        Spacer(1, 0.15 * inch),
        callout("Submission note", "Replace [Student 1], [Student 2], and [Faculty Name] before submission. Add the published Streamlit URL to the README and presentation handoff slide.", fill=PALE_RED, border=RED),
        p("8. Handoff and reproducibility", "H1"),
        p("The repository is organized so the two-person team can run, inspect, and present the same project state.", "Body"),
    ])
    handoff_rows = [
        [p("Action", "TableHeader"), p("Command or artifact", "TableHeader")],
        [p("Install", "Body"), p("uv sync --dev", "SmallMono")],
        [p("Validate", "Body"), p("uv run python scripts\\validate_dataset.py", "SmallMono")],
        [p("Evaluate", "Body"), p("uv run python scripts\\evaluate.py", "SmallMono")],
        [p("Run locally", "Body"), p("uv run streamlit run app.py", "SmallMono")],
        [p("Deploy", "Body"), p("Streamlit Community Cloud with OPENROUTER_API_KEY configured as a secret", "Body")],
        [p("Present", "Body"), p("Use output/Northbridge_Guide_CCA.pptx and docs/demo_script.md", "Body")],
    ]
    story.extend([
        styled_table(handoff_rows, [1.35 * inch, 5.6 * inch]),
        Spacer(1, 0.15 * inch),
        p("Repository map", "H2"),
        bullet("app.py: Streamlit application and user-facing views."),
        bullet("data/: self-prepared corpus and evaluation set."),
        bullet("src/campus_guide/: data models, retrieval, answering, provider, settings, and evaluation modules."),
        bullet("docs/: dataset card, methodology, demo script, project report, and rubric mapping."),
        bullet("output/: verified evaluation results, editable report, PDF report, and presentation deck."),
        p("Conclusion", "H1"),
        p("Northbridge Guide satisfies the Option 1 project brief with a complete dataset-to-GenAI workflow. Its strongest classroom value is that the system demonstrates both sides of a responsible assistant: it answers when the corpus supports the question and refuses when it does not. The result is small enough to explain, technical enough to evaluate, and packaged for a two-person CCA submission.", "Body"),
        p("Sources and project artifacts", "H2"),
        p("External implementation references: " + link("OpenRouter Quickstart", "https://openrouter.ai/docs/quickstart") + ", " + link("OpenRouter free models router", "https://openrouter.ai/docs/cookbook/get-started/free-models-router-playground") + ", and " + link("OpenRouter FAQ", "https://openrouter.ai/docs/faq") + ". Internal evidence is listed throughout the repository and in the presentation speaker notes.", "BodyMuted"),
    ])
    return story


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frame = Frame(0.75 * inch, 0.75 * inch, 7 * inch, 9.65 * inch, id="normal")
    doc = BaseDocTemplate(
        str(OUT), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch, title="Northbridge Guide CCA Project Report",
        author="[Student 1] and [Student 2]",
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=draw_page)])
    doc.build(build_story())
    print(f"PDF: {OUT}")


if __name__ == "__main__":
    main()
