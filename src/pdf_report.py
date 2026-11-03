
from pathlib import Path
from datetime import datetime
from xml.sax.saxutils import escape

import arabic_reshaper
from bidi.algorithm import get_display

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


NAVY = colors.HexColor("#142D4E")
BLUE = colors.HexColor("#2878B8")
LIGHT_GRAY = colors.HexColor("#F3F5F7")
DARK = colors.HexColor("#263445")
MUTED = colors.HexColor("#68788A")
WHITE = colors.white


def shape_arabic(text):
    """Prepare Arabic text for ReportLab."""
    text = str(text or "")
    if not text:
        return ""

    return get_display(arabic_reshaper.reshape(text))


def register_arabic_font():
    """Register the Arabic font using a project-relative path."""

    project_root = Path(__file__).resolve().parent.parent

    candidates = [
        project_root / "assets" / "fonts" / "Amiri-Regular.ttf",
        project_root / "assets" / "fonts" / "NotoNaskhArabic-Regular.ttf",
        project_root / "assets" / "Amiri-Regular.ttf",
        project_root / "assets" / "NotoNaskhArabic-Regular.ttf",
    ]

    for font_path in candidates:
        if font_path.exists():
            if "ArabicFont" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(
                    TTFont("ArabicFont", str(font_path))
                )
            return "ArabicFont"

    raise FileNotFoundError(
        "Arabic font not found. Add Amiri-Regular.ttf "
        "inside assets/fonts/."
    )


def safe_text(value):
    return escape(str(value or ""))


def make_styles(font_name):
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ReportTitle",
        fontName="Helvetica-Bold",
        fontSize=23,
        leading=30,
        textColor=WHITE,
        alignment=TA_LEFT,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        name="SectionTitle",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=19,
        textColor=NAVY,
        alignment=TA_LEFT,
        spaceBefore=12,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        name="BodyEnglish",
        fontName="Helvetica",
        fontSize=9,
        leading=14,
        textColor=DARK,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name="BodyArabic",
        fontName=font_name,
        fontSize=10,
        leading=17,
        textColor=DARK,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name="SmallText",
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=MUTED,
    ))

    return styles


def paragraph(text, styles, arabic=False):
    """Create a paragraph using the selected language font."""

    if arabic:
        return Paragraph(
            shape_arabic(text),
            styles["BodyArabic"],
        )

    return Paragraph(
        safe_text(text),
        styles["BodyEnglish"],
    )


def section_title(number, title, styles):
    return Paragraph(
        f"{number:02d}  |  {safe_text(title)}",
        styles["SectionTitle"],
    )


def make_table(rows, widths=None):
    table = Table(
        rows,
        colWidths=widths,
        repeatRows=1,
        hAlign="LEFT",
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 12),
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_GRAY),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9E0E7")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    return table


def add_page_number(canvas, document):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)

    canvas.drawString(
        18 * mm,
        10 * mm,
        "EYOUTH | Smart Career Path Agent",
    )

    canvas.drawRightString(
        A4[0] - 18 * mm,
        10 * mm,
        f"Page {document.page}",
    )

    canvas.restoreState()


def generate_pdf_report(report, output_path):
    """
    Generate a professional PDF from the finalized agent report.
    """

    if not isinstance(report, dict):
        raise ValueError("Report must be a dictionary.")

    required_fields = {
        "role",
        "candidate_skills",
        "gaps",
        "roadmap",
        "summary",
    }

    missing = required_fields - report.keys()

    if missing:
        raise ValueError(
            f"Report is missing fields: {sorted(missing)}"
        )

    font_name = register_arabic_font()
    styles = make_styles(font_name)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title="EYOUTH Career Development Report",
        author="EYOUTH Smart Career Agent",
    )

    story = []

    # Report header
    header = Table(
        [[
            Paragraph(
                "<b>EYOUTH</b><br/>"
                "<font size='9'>CAREER INTELLIGENCE REPORT</font>",
                ParagraphStyle(
                    "Brand",
                    fontName="Helvetica-Bold",
                    fontSize=18,
                    leading=25,
                    textColor=WHITE,
                ),
            )
        ]],
        colWidths=[174 * mm],
    )

    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("BOX", (0, 0), (-1, -1), 0, NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 15),
        ("RIGHTPADDING", (0, 0), (-1, -1), 15),
        ("TOPPADDING", (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
    ]))

    story.append(header)
    story.append(Spacer(1, 12 * mm))

    story.append(Paragraph(
        "Career Development Report",
        styles["ReportTitle"],
    ))

    story.append(Paragraph(
        safe_text(report["role"]),
        ParagraphStyle(
            "Role",
            fontName="Helvetica-Bold",
            fontSize=15,
            textColor=BLUE,
            spaceAfter=12,
        ),
    ))

    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d')}",
        styles["SmallText"],
    ))

    story.append(Spacer(1, 8 * mm))

    # 01 Executive Summary
    story.append(section_title(1, "Executive Summary", styles))

    story.append(
        paragraph(report["summary"], styles, arabic=True)
    )

    story.append(Spacer(1, 5 * mm))

    # 02 Candidate Skills Profile
    story.append(section_title(2, "Candidate Skills Profile", styles))

    skill_rows = [[
        "Skill",
        "Claimed Level",
        "Evidence",
    ]]

    for skill in report.get("candidate_skills", []):
        if not isinstance(skill, dict):
            continue

        skill_rows.append([
            safe_text(skill.get("name", "")),
            safe_text(skill.get("claimed_level", "")),
            safe_text(skill.get("evidence", "")),
        ])

    if len(skill_rows) == 1:
        skill_rows.append(["No skills recorded", "-", "-"])

    story.append(make_table(
        skill_rows,
        [65 * mm, 45 * mm, 64 * mm],
    ))

    story.append(Spacer(1, 5 * mm))

    # 03 Skill Gap Analysis
    story.append(section_title(3, "Skill Gap Analysis", styles))

    gap_rows = [[
        "Required Skill",
        "Status",
        "Candidate Level",
        "Required Level",
    ]]

    for gap in report.get("gaps", []):
        if not isinstance(gap, dict):
            continue

        gap_rows.append([
            safe_text(gap.get("skill", "")),
            safe_text(gap.get("status", "")),
            safe_text(gap.get("candidate_level", "")),
            safe_text(gap.get("required_level", "")),
        ])

    if len(gap_rows) == 1:
        gap_rows.append(["No gaps recorded", "-", "-", "-"])

    story.append(make_table(
        gap_rows,
        [52 * mm, 35 * mm, 43 * mm, 44 * mm],
    ))

    story.append(Spacer(1, 5 * mm))

    # 04 Skills Requiring Verification
    story.append(section_title(
        4,
        "Skills Requiring Verification",
        styles,
    ))

    unverified = report.get("unverified", [])

    if unverified:
        for skill in unverified:
            if isinstance(skill, dict):
                skill_name = skill.get("skill", skill.get("name", ""))
                reason = skill.get("reason", "")

                text = str(skill_name)

                if reason:
                    text += f" — {reason}"
            else:
                text = str(skill)

            story.append(
                paragraph(f"• {text}", styles)
            )
    else:
        story.append(paragraph(
            "No unverified skills were recorded.",
            styles,
        ))

    story.append(Spacer(1, 5 * mm))

    # 05 Personalized Learning Roadmap
    story.append(section_title(
        5,
        "Personalized Learning Roadmap",
        styles,
    ))

    roadmap = report.get("roadmap", [])

    if roadmap:
        for index, course in enumerate(roadmap, start=1):
            if not isinstance(course, dict):
                continue

            course_content = [
                Paragraph(
                    f"{index}. {safe_text(course.get('title', 'Course'))}",
                    ParagraphStyle(
                        f"Course{index}",
                        fontName="Helvetica-Bold",
                        fontSize=10,
                        textColor=BLUE,
                        spaceAfter=5,
                    ),
                ),
                paragraph(
                    f"Delivery: {course.get('delivery_type', 'Not specified')}",
                    styles,
                ),
                paragraph(
                    "Skills covered: "
                    + ", ".join(course.get("covers", [])),
                    styles,
                ),
                paragraph(
                    "Evidence: " + str(course.get("reason", "")),
                    styles,
                ),
                Spacer(1, 4 * mm),
            ]

            story.append(KeepTogether(course_content))
    else:
        story.append(paragraph(
            "No supported course recommendations were found.",
            styles,
        ))

    story.append(Spacer(1, 5 * mm))

    # 06 Remaining Skill Gaps
    story.append(section_title(6, "Remaining Skill Gaps", styles))

    uncovered = report.get("uncovered_gaps", [])

    if uncovered:
        for skill in uncovered:
            story.append(
                paragraph(f"• {skill}", styles)
            )
    else:
        story.append(paragraph(
            "All actionable gaps have supported course recommendations.",
            styles,
        ))

    # 07 Methodology & Limitations
    # Start this section on a new page so its heading and content
    # are always visible together.
    story.append(PageBreak())

    methodology_content = [
        section_title(7, "Methodology & Limitations", styles)
    ]

    limitations = report.get("limitations", [])

    if limitations:
        for limitation in limitations:
            methodology_content.append(
                paragraph(f"• {limitation}", styles)
            )
    else:
        methodology_content.append(
            paragraph(
                "No additional limitations were recorded.",
                styles,
            )
        )

    story.append(KeepTogether(methodology_content))

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    return output_path


if __name__ == "__main__":
    sample_report = {
        "role": "Data Analyst",

        "candidate_skills": [
            {
                "name": "Python",
                "claimed_level": "intermediate",
                "evidence": "demonstrated",
            },
            {
                "name": "SQL",
                "claimed_level": "beginner",
                "evidence": "listed",
            },
        ],

        "gaps": [
            {
                "skill": "Power BI",
                "status": "missing",
                "candidate_level": "none",
                "required_level": "intermediate",
            },
        ],

        "unverified": ["Machine Learning"],

        "roadmap": [],

        "uncovered_gaps": ["Advanced SQL"],

        "catalog": [],

        "summary": "The candidate has a foundation in Python and SQL.",

        "trace": [],

        "limitations": [],
    }

    output_file = "test_career_report.pdf"

    generate_pdf_report(sample_report, output_file)

    print(f"PDF created: {output_file}")
