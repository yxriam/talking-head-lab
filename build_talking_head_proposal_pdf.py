from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    FrameBreak,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


OUT = Path("output/pdf/talking_head_ai_project_two_page_proposal.pdf")
OUT.parent.mkdir(parents=True, exist_ok=True)

PAGE_W, PAGE_H = A4
MARGIN_X = 17 * mm
BOTTOM = 15 * mm
GAP = 6 * mm
COL_W = (PAGE_W - 2 * MARGIN_X - GAP) / 2


styles = {
    "title": ParagraphStyle(
        "title",
        fontName="Times-Bold",
        fontSize=16,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=4,
    ),
    "author": ParagraphStyle(
        "author",
        fontName="Times-Roman",
        fontSize=9,
        leading=10.5,
        alignment=TA_CENTER,
        spaceAfter=6,
    ),
    "abstract": ParagraphStyle(
        "abstract",
        fontName="Times-Roman",
        fontSize=8.2,
        leading=9.5,
        alignment=TA_JUSTIFY,
        firstLineIndent=0,
        spaceAfter=3,
    ),
    "section": ParagraphStyle(
        "section",
        fontName="Times-Bold",
        fontSize=9.1,
        leading=10.5,
        alignment=TA_CENTER,
        spaceBefore=4,
        spaceAfter=3,
    ),
    "body": ParagraphStyle(
        "body",
        fontName="Times-Roman",
        fontSize=8.3,
        leading=9.45,
        alignment=TA_JUSTIFY,
        firstLineIndent=8,
        spaceAfter=3,
    ),
    "body_noindent": ParagraphStyle(
        "body_noindent",
        fontName="Times-Roman",
        fontSize=8.3,
        leading=9.45,
        alignment=TA_JUSTIFY,
        firstLineIndent=0,
        spaceAfter=3,
    ),
    "caption": ParagraphStyle(
        "caption",
        fontName="Times-Roman",
        fontSize=7.1,
        leading=8.0,
        alignment=TA_CENTER,
        spaceBefore=2,
        spaceAfter=2,
    ),
    "table": ParagraphStyle(
        "table",
        fontName="Times-Roman",
        fontSize=6.95,
        leading=7.65,
    ),
    "ref": ParagraphStyle(
        "ref",
        fontName="Times-Roman",
        fontSize=6.8,
        leading=7.5,
        firstLineIndent=-8,
        leftIndent=8,
        spaceAfter=1.2,
    ),
}


def p(text, style="body"):
    return Paragraph(text, styles[style])


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 7)
    canvas.drawCentredString(PAGE_W / 2, 8.5 * mm, str(canvas.getPageNumber()))
    canvas.restoreState()


def make_doc():
    doc = BaseDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=14 * mm,
        bottomMargin=BOTTOM,
    )

    top_frame = Frame(
        MARGIN_X,
        PAGE_H - 74 * mm,
        PAGE_W - 2 * MARGIN_X,
        57 * mm,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="first_top",
    )
    first_left = Frame(
        MARGIN_X,
        BOTTOM + 3 * mm,
        COL_W,
        PAGE_H - 94 * mm,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="first_left",
    )
    first_right = Frame(
        MARGIN_X + COL_W + GAP,
        BOTTOM + 3 * mm,
        COL_W,
        PAGE_H - 94 * mm,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="first_right",
    )
    full_left = Frame(
        MARGIN_X,
        BOTTOM + 3 * mm,
        COL_W,
        PAGE_H - BOTTOM - 18 * mm,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="full_left",
    )
    full_right = Frame(
        MARGIN_X + COL_W + GAP,
        BOTTOM + 3 * mm,
        COL_W,
        PAGE_H - BOTTOM - 18 * mm,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="full_right",
    )

    doc.addPageTemplates(
        [
            PageTemplate(id="first", frames=[top_frame, first_left, first_right], onPage=on_page),
            PageTemplate(id="columns", frames=[full_left, full_right], onPage=on_page),
        ]
    )
    return doc


def evaluation_table():
    rows = [
        [p("<b>Dimension</b>", "table"), p("<b>Metric / Evidence</b>", "table")],
        [p("Lip synchronisation", "table"), p("SyncNet-style score where available; 1-5 human rating.", "table")],
        [p("Identity", "table"), p("ArcFace similarity between source image and generated frames.", "table")],
        [p("Voice", "table"), p("ECAPA-TDNN speaker similarity and human accent/naturalness ratings.", "table")],
        [p("Robustness", "table"), p("Failure cases by crop mode, image quality, prompt length, and backend.", "table")],
        [p("Safety/usability", "table"), p("Consent workflow, warning visibility, and user questionnaire.", "table")],
    ]
    table = Table(rows, colWidths=[29 * mm, COL_W - 29 * mm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.3, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return table


def timeline_table():
    rows = [
        [p("<b>Weeks</b>", "table"), p("<b>Milestone</b>", "table")],
        [p("1-4", "table"), p("Literature review, ethics/consent plan, dataset design.", "table")],
        [p("5-8", "table"), p("Improve WebUI, logging, crop modes, and settings.", "table")],
        [p("9-12", "table"), p("SadTalker/MuseTalk comparisons and preliminary metrics.", "table")],
        [p("13-18", "table"), p("Human evaluation of realism, lip sync, identity, and voice.", "table")],
        [p("19-22", "table"), p("Failure analysis and improvement strategies.", "table")],
        [p("23-26", "table"), p("Final experiments, report, presentation, and demo package.", "table")],
    ]
    table = Table(rows, colWidths=[18 * mm, COL_W - 18 * mm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.3, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
                ("TOPPADDING", (0, 0), (-1, -1), 1.8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
            ]
        )
    )
    return table


story = [
    p("Consent-Aware Personalized Talking-Head Video Generation with Voice Cloning", "title"),
    p("Xinran Yang<br/>AI Project Proposal Draft", "author"),
    p(
        "<b>Abstract-</b> This proposal describes a one-academic-year AI project on personalised talking-head video generation from a face image, a short audio/video voice reference, and a text prompt. The current prototype connects Chatterbox voice cloning with SadTalker and MuseTalk backends through a WebUI. The project will turn this prototype into a reproducible research system by comparing backend behaviour, evaluating lip synchronisation, identity preservation, speaker similarity, naturalness, and failure cases, and by studying interface-level consent and warning design for authorised use. The expected contribution is not a new foundation model, but an evaluated pipeline with clear evidence about when the system works, when it fails, and how users should configure it responsibly.",
        "abstract",
    ),
    p(
        "<b>Index Terms-</b> talking-head generation, voice cloning, lip synchronisation, synthetic media, responsible AI, human evaluation.",
        "abstract",
    ),
    FrameBreak(),
    p("I. INTRODUCTION", "section"),
    p(
        "Recent progress in text-to-speech, voice cloning, and audio-driven facial animation makes it possible to generate a talking-head video from very limited input: one face image, one short voice reference, and a text prompt. Such systems can support accessibility, education, language learning, remote presentation, and personalised communication.",
    ),
    p(
        "However, the same technical capability creates risks of impersonation, misleading endorsement, fraud, and non-consensual synthetic media. For this reason, a useful academic project should not only show that generation works, but also evaluate quality limits, failure modes, and responsible-use mechanisms.",
    ),
    p(
        "This project asks: <b>How can a personalised talking-head generation pipeline be designed and evaluated so that it is useful for authorised users while making quality limitations and synthetic-media risks visible?</b>",
        "body_noindent",
    ),
    p("II. RELATED WORK", "section"),
    p(
        "Lip-synchronisation methods such as Wav2Lip focus on matching mouth movement to speech in unconstrained video. MuseTalk improves real-time lip synchronisation through latent-space inpainting. These methods are suitable when mouth accuracy is the primary objective, but they may appear unnatural if the head and upper face remain static.",
    ),
    p(
        "Full-face animation approaches such as SadTalker predict 3D motion coefficients for expression and head pose, then render a talking face from a single image. They can produce richer facial motion, but may introduce artefacts when the source image has a strong smile, low resolution, occlusion, or unusual pose.",
    ),
    p(
        "Voice cloning introduces another source of variation. Chatterbox can synthesise speech from a short reference clip, but its quality depends on reference duration, background noise, accent, and text length. Speaker-verification methods such as ECAPA-TDNN and face-recognition embeddings such as ArcFace provide practical ways to quantify similarity. The project gap is a controlled, user-facing comparison of these components with explicit failure analysis.",
    ),
    FrameBreak(),
    p("III. SYSTEM DESIGN", "section"),
    p(
        "The prototype already implements a WebUI with three user inputs: a face image, a voice reference audio/video, and a text prompt. If the voice source is video, ffmpeg extracts a mono 24 kHz reference segment. Chatterbox then generates synthetic speech from the text and reference audio. The face image is preprocessed using full-image preservation, centre crop, or automatic face crop. Finally, SadTalker or MuseTalk renders the output video.",
    ),
    p(
        "The system exposes controlled parameters including reference start time, reference duration, crop mode, preprocess mode, pose style, expression scale, TTS temperature, and exaggeration. These controls are important because the project is not merely a demo: they allow repeatable experiments under fixed conditions.",
    ),
    p(
        "<b>Critical functionalities.</b> CF1: image, audio/video, and text input. CF2: automatic audio extraction. CF3: image preprocessing options. CF4: Chatterbox voice generation. CF5: SadTalker/MuseTalk backend comparison. CF6: visible synthetic-media warning layer. CF7: experiment logging for settings, runtime, and output paths.",
        "body_noindent",
    ),
    p("IV. RESEARCH QUESTIONS", "section"),
    p(
        "<b>RQ1.</b> How do backend choice and image preprocessing affect perceived realism, lip synchronisation, and identity preservation?<br/><b>RQ2.</b> How do voice-reference quality, duration, and accent affect generated speech similarity and naturalness?<br/><b>RQ3.</b> What warning and consent-interface choices reduce misuse risk while preserving usability for authorised educational or creative scenarios?",
        "body_noindent",
    ),
    NextPageTemplate("columns"),
    PageBreak(),
    p("V. EVALUATION PLAN", "section"),
    p(
        "The evaluation will use a small authorised dataset of 8-12 identities or public/consented samples. For each identity, the project will use one or more face images, short reference clips, and fixed English prompts. Outputs will be generated under paired conditions so that only one factor changes at a time: backend, crop mode, reference duration, or generation parameter.",
    ),
    p("TABLE I<br/>PLANNED EVALUATION MEASURES", "caption"),
    evaluation_table(),
    Spacer(1, 3),
    p(
        "Human evaluation will rate lip synchronisation, identity consistency, speech naturalness, accent retention, visual naturalness, and artefacts on a 1-5 scale. Automatic metrics will be used where feasible, but the report will not rely on a single metric because talking-head realism is perceptual and multi-factorial.",
    ),
    p("VI. COMPARISON AND FAILURE ANALYSIS", "section"),
    p(
        "The project will run three main comparison experiments. First, SadTalker will be compared with MuseTalk under the same identity, voice reference, and text. SadTalker is expected to provide more visible head and facial movement, while MuseTalk is expected to be stronger for lip precision. Second, full-image, centre-crop, and automatic face-crop modes will be compared to study identity preservation and mouth artefacts. Third, short voice prompts will be compared with longer clean references to test speaker similarity and accent retention.",
    ),
    p(
        "Failure cases will be reported as evidence rather than hidden. Expected failures include accurate lips with static head motion, natural head movement with weak mouth precision, distorted mouth shapes from smiling images, identity drift after aggressive cropping, noisy references reducing accent quality, and long text prompts producing unnatural speech rhythm. Each failure will be linked to an improvement strategy, such as changing backend, adjusting crop mode, lowering expression scale, using cleaner 20-30 second reference audio, warning when face detection fails, or splitting long text into shorter sentences.",
    ),
    p("VII. SCOPE AND TIMELINE", "section"),
    p(
        "The project will produce a runnable WebUI, reproducible logs, quantitative metrics, human evaluation results, failure-case analysis, and responsible-use recommendations. It will not train a new foundation model, generate non-consensual videos, remove warning mechanisms, or deploy the system as a public production service.",
    ),
    p("TABLE II<br/>ONE-ACADEMIC-YEAR PLAN", "caption"),
    timeline_table(),
    Spacer(1, 3),
    FrameBreak(),
    p("VIII. EXPECTED CONTRIBUTION", "section"),
    p(
        "The final contribution will be an end-to-end, consent-aware talking-head generation pipeline and a research report explaining which model/configuration works best under different input conditions. The project is suitable as an AI project because it includes system integration, controlled comparison experiments, quantitative and human-centred evaluation, failure analysis, and a responsible-AI design component.",
    ),
    p("REFERENCES", "section"),
    p('[1] K. R. Prajwal et al., "A Lip Sync Expert Is All You Need for Speech to Lip Generation In The Wild," arXiv:2008.10010, 2020.', "ref"),
    p('[2] Y. Zhang et al., "MuseTalk: Real-Time High Quality Lip Synchronization with Latent Space Inpainting," arXiv:2410.10122, 2024.', "ref"),
    p('[3] W. Zhang et al., "SadTalker: Learning Realistic 3D Motion Coefficients for Stylized Audio-Driven Single Image Talking Face Animation," arXiv:2211.12194, 2022.', "ref"),
    p('[4] Resemble AI, "Chatterbox TTS," GitHub repository, 2026.', "ref"),
    p('[5] B. Desplanques et al., "ECAPA-TDNN: Emphasized Channel Attention, Propagation and Aggregation in TDNN Based Speaker Verification," arXiv:2005.07143, 2020.', "ref"),
    p('[6] J. Deng et al., "ArcFace: Additive Angular Margin Loss for Deep Face Recognition," arXiv:1801.07698, 2018.', "ref"),
    p('[7] National Institute of Standards and Technology, "AI Risk Management Framework," 2023.', "ref"),
]


def main():
    doc = make_doc()
    doc.build(story)
    print(OUT)


if __name__ == "__main__":
    main()
