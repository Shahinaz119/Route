
"""Tests the agent tools without an LLM, API key, or real embedding model."""
import numpy as np
import json

import pytest

from agent_tools import Session, build_tools


@pytest.fixture
def mock_embeddings(monkeypatch):
    """Prevent loading the real SentenceTransformer model during tests."""
    monkeypatch.setattr(
        Session,
        "load_embeddings_once",
        lambda self: None,
    )


def _tools_by_name(session: Session) -> dict:
    return {tool.name: tool for tool in build_tools(session)}


def test_tool_flow_without_llm(tmp_path, mock_embeddings):
    cv = tmp_path / "cv.txt"
    cv.write_text(
        "Skills: Python. Built a REST API with Flask.",
        encoding="utf-8",
    )

    roles = tmp_path / "roles.json"
    roles.write_text(json.dumps([{
        "role_id": "r",
        "title": "R",
        "requirements": [
            {
                "skill": "python",
                "min_level": "beginner",
                "mandatory": True,
            },
            {
                "skill": "sql",
                "min_level": "beginner",
                "mandatory": True,
            },
        ],
    }]), encoding="utf-8")

    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps([{
        "slug": "py-1",
        "title_en": "Python 1",
        "delivery_type": "recorded",
        "status": "published",
    }]), encoding="utf-8")

    session = Session(
        roles_path=roles,
        catalog_path=catalog,
        cv_path=cv,
    )
    tools = _tools_by_name(session)

    assert "Selected" in tools["select_role"].invoke({"role_id": "r"})

    tools["read_cv"].invoke({})

    profile = {
        "skills": [{
            "name": "Python",
            "claimed_level": "beginner",
            "evidence": "listed",
            "source_quote": "Python",
        }]
    }

    result = tools["submit_candidate_profile"].invoke({
        "profile_json": json.dumps(profile),
    })
    assert "Accepted" in result

    gaps = json.loads(tools["analyze_skill_gaps"].invoke({}))

    assert len(gaps) == 2
    assert {gap["skill"] for gap in gaps} == {"python", "sql"}

    # A listed skill without task evidence is unverified.
    # A skill absent from the CV is a potential gap.
    statuses = {gap["skill"]: gap["status"] for gap in gaps}
    assert statuses["python"] == "unverified"
    assert statuses["sql"] == "missing"

    result = tools["finalize_report"].invoke({
        "roadmap_json": "[]",
        "summary": "Test report",
    })

    assert session.report is not None
    assert session.report["roadmap"] == []
    assert session.report["summary"] == "Test report"


def test_invalid_profile_returns_error_not_exception(
    tmp_path,
    mock_embeddings,
):
    cv = tmp_path / "cv.txt"
    cv.write_text("Python", encoding="utf-8")

    session = Session(
        roles_path=tmp_path / "roles.json",
        catalog_path=tmp_path / "catalog.json",
        cv_path=cv,
    )

    tools = _tools_by_name(session)
    tools["read_cv"].invoke({})

    result = tools["submit_candidate_profile"].invoke({
        "profile_json": "{not json",
    })

    assert result.startswith("ERROR")

def test_search_catalog_uses_preloaded_embeddings(tmp_path, mock_embeddings, monkeypatch):
    import agent_tools

    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps([
    {
        "Slug": "python-course",
        "Title (EN)": "Python Programming",
        "Title (AR)": "برمجة بايثون",
        "Short Description (EN)": "Learn Python basics",
        "Delivery Type": "recorded",
        "Status": "published",
    },
    {
        "Slug": "sql-course",
        "Title (EN)": "SQL Fundamentals",
        "Title (AR)": "أساسيات SQL",
        "Short Description (EN)": "Learn SQL databases",
        "Delivery Type": "live",
        "Status": "published",
    },
]), encoding="utf-8")

    session = Session(
        roles_path=tmp_path / "roles.json",
        catalog_path=catalog,
    )

    # Fake the preloaded embedding data.
    session._emb_slugs = ["python-course", "sql-course"]
    session._emb_vectors = np.array([[1.0, 0.0], [0.0, 1.0]])
    session._emb_model = object()

    def fake_search_courses(query, courses_by_slug, **kwargs):
        assert query == "python"
        assert kwargs["preloaded_slugs"] == session._emb_slugs
        assert kwargs["preloaded_model"] is session._emb_model
        return [(courses_by_slug["python-course"], 0.91)]

    monkeypatch.setattr(agent_tools, "search_courses", fake_search_courses)

    tools = _tools_by_name(session)
    result = json.loads(tools["search_catalog"].invoke({"query": "python"}))

    assert len(result["courses"]) == 1
    assert result["courses"][0]["slug"] == "python-course"
    assert result["courses"][0]["score"] == 0.91



def test_search_catalog_rejects_semantic_match_without_evidence(
    tmp_path,
    mock_embeddings,
    monkeypatch,
):
    import agent_tools

    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps([
        {
            "Slug": "communication",
            "Title (EN)": "Communication Skills",
            "Short Description (EN)": "Improve workplace communication",
            "Delivery Type": "recorded",
            "Status": "published",
        },
        {
            "Slug": "llm-course",
            "Title (EN)": "Large Language Models",
            "Short Description (EN)": "Learn transformer models and LLM applications",
            "Delivery Type": "recorded",
            "Status": "published",
        },
    ]), encoding="utf-8")

    session = Session(
        roles_path=tmp_path / "roles.json",
        catalog_path=catalog,
    )
    session._emb_slugs = ["communication", "llm-course"]
    session._emb_vectors = np.array([[1.0, 0.0], [0.9, 0.1]])
    session._emb_model = object()

    def fake_search_courses(query, courses_by_slug, **kwargs):
        return [
            (courses_by_slug["communication"], 0.95),
            (courses_by_slug["llm-course"], 0.90),
        ]

    monkeypatch.setattr(agent_tools, "search_courses", fake_search_courses)

    tools = _tools_by_name(session)
    result = json.loads(
        tools["search_catalog"].invoke({"query": "large language models"})
    )

    assert [item["slug"] for item in result["courses"]] == ["llm-course"]


def test_unreviewed_tags_are_not_evidence(
    tmp_path,
    mock_embeddings,
    monkeypatch,
):
    import agent_tools

    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps([
        {
            "Slug": "communication",
            "Title (EN)": "Communication Skills",
            "Short Description (EN)": "Improve workplace communication",
            "Delivery Type": "recorded",
            "Status": "published",
        },
    ]), encoding="utf-8")

    tags = tmp_path / "course_skill_tags.json"
    tags.write_text(json.dumps({
        "communication": {
            "skills": ["large language models"],
            "reviewed": False,
        }
    }), encoding="utf-8")

    session = Session(
        roles_path=tmp_path / "roles.json",
        catalog_path=catalog,
        tags_path=tags,
    )
    session._emb_slugs = ["communication"]
    session._emb_vectors = np.array([[1.0, 0.0]])
    session._emb_model = object()

    monkeypatch.setattr(
        agent_tools,
        "search_courses",
        lambda query, courses_by_slug, **kwargs: [
            (courses_by_slug["communication"], 0.99)
        ],
    )

    tools = _tools_by_name(session)
    result = json.loads(
        tools["search_catalog"].invoke({
            "query": "large language models"
        })
    )

    assert result["courses"] == []



def test_finalize_report_rejects_unsupported_course_coverage(
    tmp_path,
    mock_embeddings,
):
    cv = tmp_path / "cv.txt"
    cv.write_text(
        "Built a simple website using HTML and CSS.",
        encoding="utf-8",
    )

    roles = tmp_path / "roles.json"
    roles.write_text(json.dumps([{
        "role_id": "r",
        "title": "R",
        "requirements": [
            {
                "skill": "python",
                "min_level": "beginner",
                "mandatory": True,
            }
        ],
    }]), encoding="utf-8")

    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps([{
        "Slug": "communication",
        "Title (EN)": "Communication Skills",
        "Short Description (EN)": "Improve workplace communication",
        "Delivery Type": "recorded",
        "Status": "published",
    }]), encoding="utf-8")

    session = Session(
        roles_path=roles,
        catalog_path=catalog,
        cv_path=cv,
    )
    tools = _tools_by_name(session)

    tools["select_role"].invoke({"role_id": "r"})
    tools["read_cv"].invoke({})

    profile = {"skills": []}

    tools["submit_candidate_profile"].invoke({
        "profile_json": json.dumps(profile),
    })
    tools["analyze_skill_gaps"].invoke({})

    result = tools["finalize_report"].invoke({
        "roadmap_json": json.dumps([{
            "slug": "communication",
            "covers": ["python"],
            "reason": "High similarity",
        }]),
        "summary": "Test",
    })

    assert result.startswith("ERROR:")
    assert "no verified evidence" in result
    assert session.report is None
