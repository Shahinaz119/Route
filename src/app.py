"""EYOUTH Career Path Agent - Professional Streamlit UI"""
import base64
import json
import os
import sys
import tempfile
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
import config  # noqa: F401

from pipeline import load_roles

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=" ROUTE:EYOUTH Career Path Agent",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Load logo ─────────────────────────────────────────────────────────────────
LOGO_PATH = Path("assets/Eyouth_logo.png")


def get_logo_base64() -> str:
    if LOGO_PATH.exists():
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


logo_b64 = get_logo_base64()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * {{ font-family: 'Inter', sans-serif; }}

    .stApp {{
        background: #F0F4F8;
    }}

    /* Hide Streamlit default elements */
    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{
        padding-top: 0 !important;
        max-width: 1100px;
    }}

    /* ── Navbar ── */
    .navbar {{
        background: #FFFFFF;
        padding: 14px 40px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 32px;
        border-radius: 0 0 16px 16px;
    }}
    .navbar-logo img {{
        height: 36px;
    }}
    .navbar-title {{
        color: #1A3C6E;
        font-size: 1rem;
        font-weight: 600;
        letter-spacing: 0.3px;
    }}

    /* ── Hero section ── */
    .hero {{
        background: linear-gradient(135deg, #1A3C6E 0%, #2563EB 100%);
        border-radius: 20px;
        padding: 48px 56px;
        color: white;
        margin-bottom: 32px;
        position: relative;
        overflow: hidden;
    }}
    .hero::before {{
        content: '';
        position: absolute;
        top: -50px; right: -50px;
        width: 250px; height: 250px;
        background: rgba(255,255,255,0.05);
        border-radius: 50%;
    }}
    .hero::after {{
        content: '';
        position: absolute;
        bottom: -80px; left: -30px;
        width: 300px; height: 300px;
        background: rgba(255,255,255,0.04);
        border-radius: 50%;
    }}
    .hero h1 {{
        font-size: 2rem;
        font-weight: 700;
        margin: 0 0 8px 0;
        line-height: 1.3;
    }}
    .hero p {{
        font-size: 1rem;
        opacity: 0.85;
        margin: 0;
        font-weight: 300;
    }}

    /* ── Step cards ── */
    .step-card {{
        background: white;
        border-radius: 16px;
        padding: 28px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        margin-bottom: 20px;
        border: 1px solid #E8EDF2;
        transition: box-shadow 0.2s;
    }}
    .step-card:hover {{
        box-shadow: 0 4px 20px rgba(26,60,110,0.12);
    }}
    .step-number {{
        background: linear-gradient(135deg, #1A3C6E, #2563EB);
        color: white;
        width: 32px; height: 32px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.9rem;
        margin-bottom: 12px;
    }}
    .step-title {{
        color: #1A3C6E;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 4px;
    }}
    .step-subtitle {{
        color: #64748B;
        font-size: 0.85rem;
        margin-bottom: 16px;
        direction: rtl;
        text-align: right;
    }}

    /* ── Analyze button ── */
    .stButton > button {{
        background: linear-gradient(135deg, #1A3C6E, #2563EB) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 14px 32px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        width: 100% !important;
        transition: all 0.2s !important;
        box-shadow: 0 4px 14px rgba(37,99,235,0.35) !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(37,99,235,0.45) !important;
    }}

    /* ── Results section ── */
    .results-header {{
        background: white;
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 20px;
        border-left: 5px solid #2563EB;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }}
    .results-title {{
        color: #1A3C6E;
        font-size: 1.3rem;
        font-weight: 700;
        margin: 0;
    }}

    /* ── Summary box ── */
    .summary-box {{
        background: linear-gradient(135deg, #EFF6FF, #DBEAFE);
        border-radius: 16px;
        padding: 24px 28px;
        border: 1px solid #BFDBFE;
        direction: rtl;
        text-align: right;
        font-size: 1rem;
        line-height: 2;
        color: #1E3A5F;
        margin-bottom: 24px;
    }}

    /* ── Section title ── */
    .section-title {{
        color: #1A3C6E;
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }}

    /* ── Badges ── */
    .badge-demonstrated {{
        display: inline-block;
        background: #D1FAE5;
        color: #065F46;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.82rem;
        font-weight: 500;
        margin: 3px;
        border: 1px solid #A7F3D0;
    }}
    .badge-listed {{
        display: inline-block;
        background: #DBEAFE;
        color: #1E40AF;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.82rem;
        font-weight: 500;
        margin: 3px;
        border: 1px solid #BFDBFE;
    }}
    .badge-gap {{
        display: inline-block;
        background: #FEF3C7;
        color: #92400E;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.82rem;
        font-weight: 500;
        margin: 3px;
        border: 1px solid #FDE68A;
    }}
    .badge-missing {{
        display: inline-block;
        background: #FEE2E2;
        color: #991B1B;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.82rem;
        font-weight: 500;
        margin: 3px;
        border: 1px solid #FECACA;
    }}
    .badge-unverified {{
        display: inline-block;
        background: #F3F4F6;
        color: #374151;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.82rem;
        font-weight: 500;
        margin: 3px;
        border: 1px solid #D1D5DB;
    }}

    /* ── Course card ── */
    .course-card {{
        background: white;
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 14px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 6px rgba(0,0,0,0.05);
        transition: box-shadow 0.2s;
    }}
    .course-card:hover {{
        box-shadow: 0 4px 16px rgba(26,60,110,0.1);
    }}
    .course-number {{
        background: #1A3C6E;
        color: white;
        width: 26px; height: 26px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        font-weight: 700;
        margin-right: 10px;
    }}
    .course-title-en {{
        color: #1A3C6E;
        font-size: 0.95rem;
        font-weight: 600;
    }}
    .course-title-ar {{
        color: #64748B;
        font-size: 0.88rem;
        direction: rtl;
        text-align: right;
        margin-top: 4px;
    }}
    .course-meta {{
        display: flex;
        gap: 10px;
        margin-top: 10px;
        flex-wrap: wrap;
    }}
    .meta-chip {{
        background: #F1F5F9;
        color: #475569;
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.78rem;
        font-weight: 500;
    }}
    .meta-chip-live {{
        background: #FEE2E2;
        color: #991B1B;
    }}
    .meta-chip-recorded {{
        background: #D1FAE5;
        color: #065F46;
    }}
    .meta-chip-hybrid {{
        background: #DBEAFE;
        color: #1E40AF;
    }}
    .score-bar-bg {{
        background: #E2E8F0;
        border-radius: 10px;
        height: 6px;
        margin-top: 10px;
        overflow: hidden;
    }}
    .score-bar-fill {{
        height: 100%;
        border-radius: 10px;
        background: linear-gradient(90deg, #2563EB, #1A3C6E);
    }}

    /* ── Stats row ── */
    .stat-box {{
        background: white;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #E8EDF2;
    }}
    .stat-number {{
        font-size: 2rem;
        font-weight: 700;
        color: #1A3C6E;
        line-height: 1;
    }}
    .stat-label {{
        font-size: 0.8rem;
        color: #64748B;
        margin-top: 4px;
    }}

    /* ── Download button ── */
    .stDownloadButton > button {{
        background: white !important;
        color: #1A3C6E !important;
        border: 2px solid #1A3C6E !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }}
    .stDownloadButton > button:hover {{
        background: #1A3C6E !important;
        color: white !important;
    }}

    /* ── Selectbox and file uploader ── */
    .stSelectbox > div > div {{
        border-radius: 10px !important;
        border: 1.5px solid #CBD5E1 !important;
    }}
    .stFileUploader > div {{
        border-radius: 10px !important;
        border: 2px dashed #CBD5E1 !important;
    }}
</style>
""", unsafe_allow_html=True)

# ── Navbar ────────────────────────────────────────────────────────────────────
logo_html = (
    f'<img src="data:image/png;base64,{logo_b64}" style="height:36px;">'
    if logo_b64 else
    '<span style="font-size:1.4rem;font-weight:700;color:#1A3C6E;">EYOUTH</span>'
)

st.markdown(f"""
<div class="navbar">
    <div class="navbar-logo">{logo_html}</div>
    <div class="navbar-title">🎯 Career Path Agent</div>
</div>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>Smart Career Path & Skill Gap Agent</h1>
    <p>Upload your CV, choose your target role, and get a personalized learning roadmap powered by AI</p>
    <p style="margin-top:6px; font-size:0.88rem; opacity:0.7;">
        احصل على تحليل شامل لمهاراتك وخارطة طريق مخصصة من كورسات EYOUTH
    </p>
</div>
""", unsafe_allow_html=True)

# ── Paths ─────────────────────────────────────────────────────────────────────
ROLES_PATH = Path("data/roles_sample.json")
CATALOG_PATH = Path("data/courses.xlsx")

# ── Load roles ────────────────────────────────────────────────────────────────
try:
    roles = load_roles(ROLES_PATH)
    role_options = {rid: role.title for rid, role in roles.items()}
except Exception as exc:
    st.error(f"Could not load roles: {exc}")
    st.stop()

# ── Three steps ───────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 1, 1], gap="medium")

with col1:
    st.markdown("""
    <div class="step-card">
        <div class="step-number">1</div>
        <div class="step-title">Choose Your Target Role</div>
        <div class="step-subtitle">اختر الوظيفة التي تريد العمل بها</div>
    </div>
    """, unsafe_allow_html=True)
    selected_role_id = st.selectbox(
        "Role",
        options=list(role_options.keys()),
        format_func=lambda rid: role_options[rid],
        label_visibility="collapsed",
    )

with col2:
    st.markdown("""
    <div class="step-card">
        <div class="step-number">2</div>
        <div class="step-title">Upload Your CV</div>
        <div class="step-subtitle">ارفع سيرتك الذاتية بصيغة PDF أو Word</div>
    </div>
    """, unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "CV",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed",
    )

with col3:
    st.markdown("""
    <div class="step-card">
        <div class="step-number">3</div>
        <div class="step-title">Get Your Roadmap</div>
        <div class="step-subtitle">احصل على خارطة طريق التعلم المخصصة</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
    run_button = st.button("🚀 Analyze my CV", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── Run agent ─────────────────────────────────────────────────────────────────
if run_button:
    if uploaded_file is None:
        st.warning("⚠️ Please upload your CV first. / من فضلك ارفع سيرتك الذاتية أولاً")
        st.stop()

    with st.spinner("🔍 Analyzing your CV... قد يستغرق هذا دقيقة أو دقيقتين"):
        from deep_agent import AgentError, run_agent

        model_name = os.getenv("AGENT_MODEL", "google_genai:gemini-3.8-flash")

        suffix = "." + uploaded_file.name.split(".")[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = Path(tmp.name)

        try:
            report, summary = run_agent(
                role_id=selected_role_id,
                cv_path=tmp_path,
                roles_path=ROLES_PATH,
                catalog_path=CATALOG_PATH,
                model_name=model_name,
            )
        except AgentError as exc:
            st.error(f"❌ Agent error: {exc}")
            st.stop()
        except Exception as exc:
            st.error(f"❌ Unexpected error: {exc}")
            st.stop()
        finally:
            tmp_path.unlink(missing_ok=True)

    st.success("✅ Analysis complete! / اكتمل التحليل")
    st.divider()

    # ── Stats row ─────────────────────────────────────────────────────────────
    skills = report.get("candidate_skills", [])
    gaps = report.get("gaps", [])
    roadmap = report.get("roadmap", [])
    uncovered = report.get("uncovered_gaps", [])
    unverified = report.get("unverified", [])

    demonstrated = [s for s in skills if s["evidence"] == "demonstrated"]
    listed_only = [s for s in skills if s["evidence"] == "listed"]
    actionable_gaps = [g for g in gaps if g["status"] in {"missing", "underdeveloped"}]

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number" style="color:#065F46;">{len(demonstrated)}</div>
            <div class="stat-label">✅ Demonstrated Skills</div>
        </div>""", unsafe_allow_html=True)
    with s2:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number" style="color:#1E40AF;">{len(listed_only)}</div>
            <div class="stat-label">📝 Listed Skills</div>
        </div>""", unsafe_allow_html=True)
    with s3:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number" style="color:#92400E;">{len(actionable_gaps)}</div>
            <div class="stat-label">⚠️ Skill Gaps</div>
        </div>""", unsafe_allow_html=True)
    with s4:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number" style="color:#1A3C6E;">{len(roadmap)}</div>
            <div class="stat-label">🎓 Courses Recommended</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:24px;'>", unsafe_allow_html=True)

    # ── Two columns layout ────────────────────────────────────────────────────
    left_col, right_col = st.columns([1, 1], gap="large")

    with left_col:
        # Summary
        st.markdown('<div class="section-title">📋 ملخصك الشخصي / Your Summary</div>',
                    unsafe_allow_html=True)
        if report.get("summary"):
            st.markdown(
                f'<div class="summary-box">{report["summary"]}</div>',
                unsafe_allow_html=True,
            )

        # Skills
        st.markdown('<div class="section-title">💼 مهاراتك / Your Skills</div>',
                    unsafe_allow_html=True)

        if demonstrated:
            st.markdown("**✅ Demonstrated / موثّقة بأدلة:**")
            badges = " ".join(
                f'<span class="badge-demonstrated">{s["name"]}</span>'
                for s in demonstrated
            )
            st.markdown(badges, unsafe_allow_html=True)

        if listed_only:
            st.markdown("**📝 Listed only / مذكورة فقط:**")
            badges = " ".join(
                f'<span class="badge-listed">{s["name"]}</span>'
                for s in listed_only
            )
            st.markdown(badges, unsafe_allow_html=True)

        if not demonstrated and not listed_only:
            st.info("No skills found in CV.")

        # Gaps
        st.markdown('<div class="section-title" style="margin-top:20px;">⚠️ فجوات المهارات / Skill Gaps</div>',
                    unsafe_allow_html=True)

        missing_gaps = [g for g in gaps if g["status"] == "missing"]
        under_gaps = [g for g in gaps if g["status"] == "underdeveloped"]

        if missing_gaps:
            st.markdown("**❌ Missing / غائبة:**")
            badges = " ".join(
                f'<span class="badge-missing">{g["skill"]}</span>'
                for g in missing_gaps
            )
            st.markdown(badges, unsafe_allow_html=True)

        if under_gaps:
            st.markdown("**⬆️ Underdeveloped / تحتاج تطوير:**")
            badges = " ".join(
                f'<span class="badge-gap">{g["skill"]}</span>'
                for g in under_gaps
            )
            st.markdown(badges, unsafe_allow_html=True)

        if unverified:
            st.markdown("**🔍 To verify / تحتاج إثبات:**")
            badges = " ".join(
                f'<span class="badge-unverified">{s}</span>'
                for s in unverified
            )
            st.markdown(badges, unsafe_allow_html=True)

        if not actionable_gaps and not unverified:
            st.success("🎉 No major skill gaps found!")

    with right_col:
        # Roadmap
        st.markdown('<div class="section-title">🗺️ خارطة طريق التعلم / Learning Roadmap</div>',
                    unsafe_allow_html=True)

        if roadmap:
            for i, course in enumerate(roadmap, start=1):
                delivery = course.get("delivery_type", "")
                if delivery == "live":
                    chip_class = "meta-chip meta-chip-live"
                    delivery_label = "🔴 Live"
                elif delivery == "recorded":
                    chip_class = "meta-chip meta-chip-recorded"
                    delivery_label = "🟢 Recorded"
                else:
                    chip_class = "meta-chip meta-chip-hybrid"
                    delivery_label = "🔵 Hybrid"

                covers = ", ".join(course.get("covers", []))
                score = course.get("score", 0)
                score_pct = int(score * 100)
                score_color = (
                    "#16A34A" if score >= 0.6
                    else "#D97706" if score >= 0.4
                    else "#DC2626"
                )

                st.markdown(f"""
<div class="course-card">
    <div style="display:flex; align-items:center;">
        <span class="course-number">{i}</span>
        <span class="course-title-en">{course.get("title", "")}</span>
    </div>
    <div class="course-title-ar">{course.get("title_ar", "")}</div>
    <div class="course-meta">
        <span class="{chip_class}">{delivery_label}</span>
        <span class="meta-chip">🎯 {covers}</span>
        <span class="meta-chip" style="color:{score_color}; font-weight:600;">
            Match: {score_pct}%
        </span>
    </div>
    <div class="score-bar-bg">
        <div class="score-bar-fill" style="width:{score_pct}%; background: {'#16A34A' if score >= 0.6 else '#D97706' if score >= 0.4 else '#DC2626'};"></div>
    </div>
</div>
""", unsafe_allow_html=True)
        else:
            st.info("No courses matched from the current catalog.")

        if uncovered:
            st.markdown("**⚠️ Gaps not covered by current catalog:**")
            for skill in uncovered:
                st.markdown(
                    f'<span class="badge-missing">❌ {skill}</span>',
                    unsafe_allow_html=True,
                )

    st.markdown("</div>", unsafe_allow_html=True)
    st.divider()

    # ── Download ──────────────────────────────────────────────────────────────
    dl_col1, dl_col2, dl_col3 = st.columns([1, 2, 1])
    with dl_col2:
        st.download_button(
            label="📥 Download Full Report / تحميل التقرير الكامل",
            data=json.dumps(report, ensure_ascii=False, indent=2),
            file_name=f"eyouth_career_report_{selected_role_id}.json",
            mime="application/json",
            use_container_width=True,
        )

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown(f"""
<div style="text-align:center; margin-top:32px; padding:20px;
     color:#94A3B8; font-size:0.82rem; border-top:1px solid #E2E8F0;">
    {logo_html.replace('height:36px', 'height:24px')}
    <span style="margin-left:10px;">
        © 2025 EYOUTH · Smart Career Path Agent · Powered by AI
    </span>
</div>
""", unsafe_allow_html=True)