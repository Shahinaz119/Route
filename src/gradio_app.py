
"""EYOUTH Career Path Agent - Gradio UI"""

import os
import sys
import tempfile
from pathlib import Path
from html import escape

import gradio as gr

# Make src imports available
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent

sys.path.insert(0, str(SRC_DIR))

import config  # noqa: F401

from pipeline import load_roles
from deep_agent import AgentError, run_agent
from pdf_report import generate_pdf_report


ROLES_PATH = PROJECT_ROOT / "data" / "roles_sample.json"
CATALOG_PATH = PROJECT_ROOT / "data" / "courses.xlsx"
LOGO_PATH = PROJECT_ROOT / "assets" / "Eyouth_logo.png"


# Load roles
roles = load_roles(ROLES_PATH)
role_options = [
    (role.title, role_id)
    for role_id, role in roles.items()
]

if not role_options:
    raise RuntimeError("No target roles were found in roles_sample.json")


def build_results(report, summary):
    """Build readable Markdown results from the agent report."""

    skills = report.get("candidate_skills", [])
    gaps = report.get("gaps", [])
    roadmap = report.get("roadmap", [])
    uncovered = report.get("uncovered_gaps", [])
    unverified = report.get("unverified", [])

    demonstrated = [
        s for s in skills
        if isinstance(s, dict) and s.get("evidence") == "demonstrated"
    ]

    listed = [
        s for s in skills
        if isinstance(s, dict) and s.get("evidence") == "listed"
    ]

    actionable_gaps = [
        g for g in gaps
        if isinstance(g, dict)
        and g.get("status") in {"missing", "underdeveloped"}
    ]

    lines = [
        "## 📊 Analysis Overview",
        "",
        f"- **Demonstrated skills:** {len(demonstrated)}",
        f"- **Listed skills:** {len(listed)}",
        f"- **Actionable skill gaps:** {len(actionable_gaps)}",
        f"- **Recommended courses:** {len(roadmap)}",
        "",
        "## 📋 Your Summary",
        "",
        summary or "No summary available.",
        "",
        "## 💼 Your Skills",
        "",
        "### Demonstrated Skills",
    ]

    if demonstrated:
        lines.extend(
            f"- {s.get('name', 'Unnamed skill')}"
            for s in demonstrated
        )
    else:
        lines.append("- No demonstrated skills recorded.")

    lines.extend(["", "### Listed Skills"])

    if listed:
        lines.extend(
            f"- {s.get('name', 'Unnamed skill')}"
            for s in listed
        )
    else:
        lines.append("- No listed-only skills recorded.")

    lines.extend(["", "## ⚠️ Skill Gaps", ""])

    if actionable_gaps:
        for gap in actionable_gaps:
            lines.append(
                f"- **{gap.get('skill', 'Unknown')}** — "
                f"{gap.get('status', 'Not specified')}"
            )
    else:
        lines.append("No actionable skill gaps recorded.")

    lines.extend(["", "## 🔍 Skills Requiring Verification", ""])

    if unverified:
        lines.extend(f"- {skill}" for skill in unverified)
    else:
        lines.append("No unverified skills recorded.")

    lines.extend(["", "## 🗺️ Personalized Learning Roadmap", ""])

    if roadmap:
        for index, course in enumerate(roadmap, start=1):
            title = course.get("title", "Course")
            title_ar = course.get("title_ar", "")
            delivery = course.get("delivery_type", "Not specified")
            covers = ", ".join(course.get("covers", []))
            reason = course.get("reason", "")

            lines.extend([
                f"### {index}. {title}",
                "",
            ])

            if title_ar:
                lines.extend([f"**Arabic title:** {title_ar}", ""])

            lines.extend([
                f"- **Delivery:** {delivery}",
                f"- **Skills covered:** {covers or 'Not specified'}",
                f"- **Why recommended:** {reason or 'Not specified'}",
                "",
            ])
    else:
        lines.append("No supported course recommendations found.")

    lines.extend(["", "## Remaining Skill Gaps", ""])

    if uncovered:
        lines.extend(f"- {skill}" for skill in uncovered)
    else:
        lines.append("No uncovered gaps recorded.")

    return "\n".join(lines)


def analyze_cv(cv_file, selected_role_id):
    """Run the agent and generate the final PDF."""

    if cv_file is None:
        raise gr.Error("Please upload your CV first.")

    if not selected_role_id:
        raise gr.Error("Please select your target role.")

    model_name = os.getenv("AGENT_MODEL", "").strip()

    if not model_name:
        raise gr.Error(
            "AGENT_MODEL is missing. Please check your .env file."
        )

    cv_path = Path(cv_file)

    if cv_path.suffix.lower() not in {".pdf", ".docx", ".txt"}:
        raise gr.Error("Supported CV formats are PDF, DOCX, and TXT.")

    temporary_cv = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=cv_path.suffix.lower(),
        ) as tmp:
            temporary_cv = Path(tmp.name)
            tmp.write(cv_path.read_bytes())

        report, summary = run_agent(
            role_id=selected_role_id,
            cv_path=temporary_cv,
            roles_path=ROLES_PATH,
            catalog_path=CATALOG_PATH,
            model_name=model_name,
        )

        results_markdown = build_results(report, summary)

        role_label = roles[selected_role_id].title
        safe_role = "".join(
            char if char.isalnum() or char in "-_" else "_"
            for char in role_label
        )

        output_dir = PROJECT_ROOT / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        pdf_path = output_dir / f"eyouth_report_{safe_role}.pdf"

        generate_pdf_report(report, pdf_path)

        return (
            f"## ✅ Analysis completed\n\n"
            f"**Target role:** {role_label}",
            results_markdown,
            str(pdf_path),
        )

    except AgentError as exc:
        raise gr.Error(f"Agent error: {exc}") from exc

    except Exception as exc:
        raise gr.Error(f"Unexpected error: {exc}") from exc

    finally:
        if temporary_cv and temporary_cv.exists():
            temporary_cv.unlink()


# Interface styling
CUSTOM_CSS = """
.gradio-container {
    max-width: 1100px !important;
    margin: auto !important;
}

#hero {
    background: linear-gradient(135deg, #1A3C6E, #2563EB);
    color: white;
    padding: 30px;
    border-radius: 18px;
    margin-bottom: 18px;
}

#hero h1 {
    color: white;
    font-size: 30px;
}

#hero p {
    color: #EAF2FF;
    font-size: 15px;
}

.primary-button {
    background: linear-gradient(135deg, #1A3C6E, #2563EB) !important;
    color: white !important;
    border: none !important;
}
"""


with gr.Blocks(
    theme=gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="slate",
        neutral_hue="slate",
    ),
    css=CUSTOM_CSS,
    title="EYOUTH Career Path Agent",
) as demo:

    with gr.Row():
        if LOGO_PATH.exists():
            gr.Image(
                value=str(LOGO_PATH),
                show_label=False,
                show_download_button=False,
                container=False,
                height=65,
                width=150,
            )
        else:
            gr.Markdown("# EYOUTH")

    gr.HTML("""
    <div id="hero">
        <h1>Smart Career Path & Skill Gap Agent</h1>
        <p>
            Upload your CV, choose your target role, and get
            a personalized learning roadmap powered by AI.
        </p>
        <p dir="rtl">
            ارفع سيرتك الذاتية، اختر الوظيفة المستهدفة،
            واحصل على خارطة طريق تعليمية مخصصة.
        </p>
    </div>
    """)

    gr.Markdown("## Start Your Career Analysis")

    with gr.Row():
        with gr.Column():
            selected_role = gr.Dropdown(
                choices=role_options,
                value=role_options[0][1],
                label="1. Choose Your Target Role",
                info="اختر الوظيفة التي تريد العمل بها",
            )

        with gr.Column():
            cv_upload = gr.File(
                label="2. Upload Your CV",
                file_types=[".pdf", ".docx", ".txt"],
                type="filepath",
            )

    analyze_button = gr.Button(
        "Analyze My CV",
        variant="primary",
        elem_classes=["primary-button"],
    )

    status_output = gr.Markdown()

    results_output = gr.Markdown(
        label="Career Analysis Results",
    )

    pdf_output = gr.File(
        label="Download Your Professional PDF Report",
        interactive=False,
    )

    analyze_button.click(
        fn=analyze_cv,
        inputs=[cv_upload, selected_role],
        outputs=[status_output, results_output, pdf_output],
    )

    gr.Markdown(
        """
        ---
        <center>
        **EYOUTH · Smart Career Path Agent**  
        Powered by AI
        </center>
        """
    )


if __name__ == "__main__":
    output_dir = PROJECT_ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    demo.launch(
        allowed_paths=[str(output_dir.resolve())]
    )
