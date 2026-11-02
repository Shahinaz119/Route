"""Tests for deterministic logic and the grounding guard. No network access needed."""
import json

import pytest

from course_matcher import match_courses
from cv_extractor import extract_profile
from gap_analyzer import analyze_gaps
from models import (
    CandidateSkill,
    CatalogCourse,
    CourseTags,
    CVProfile,
    Evidence,
    Level,
    RoleProfile,
    RoleRequirement,
    SkillGap,
)


def role(*reqs: RoleRequirement) -> RoleProfile:
    return RoleProfile(role_id="r", title="Test role", requirements=list(reqs))


def req(skill: str, level: Level, mandatory: bool = True) -> RoleRequirement:
    return RoleRequirement(skill=skill, min_level=level, mandatory=mandatory)


def cand(name: str, level: Level, evidence: Evidence, quote: str = "") -> CandidateSkill:
    return CandidateSkill(name=name, claimed_level=level, evidence=evidence, source_quote=quote)


def course(slug: str) -> CatalogCourse:
    return CatalogCourse(slug=slug, title_en=slug, delivery_type="recorded", status="published")


def gap(skill: str, status: str = "missing", priority: int = 1) -> SkillGap:
    return SkillGap(
        skill=skill,
        required_level=Level.BEGINNER,
        current_level=Level.NONE,
        evidence=Evidence.NONE,
        mandatory=True,
        status=status,
        priority=priority,
    )


# ---------- gap analysis ----------

def test_absent_skill_is_missing():
    cv = CVProfile(skills=[cand("python", Level.INTERMEDIATE, Evidence.DEMONSTRATED, "Python")])
    gaps = analyze_gaps(cv, role(req("sql", Level.BEGINNER)))
    assert [(g.skill, g.status) for g in gaps] == [("sql", "missing")]


def test_listed_skill_meeting_level_is_unverified():
    cv = CVProfile(skills=[cand("python", Level.ADVANCED, Evidence.LISTED, "Python")])
    gaps = analyze_gaps(cv, role(req("python", Level.INTERMEDIATE)))
    assert [g.status for g in gaps] == ["unverified"]


def test_demonstrated_skill_meeting_level_is_not_a_gap():
    cv = CVProfile(skills=[cand("python", Level.ADVANCED, Evidence.DEMONSTRATED, "Python")])
    assert analyze_gaps(cv, role(req("python", Level.INTERMEDIATE))) == []


# ---------- course matching ----------

def test_greedy_picks_course_covering_most_gaps():
    courses = [course("A"), course("B")]
    tags = {
        "A": CourseTags(skills=["python", "sql"], reviewed=True),
        "B": CourseTags(skills=["sql"], reviewed=True),
    }
    gaps = [gap("python", priority=1), gap("sql", priority=2)]
    recs, uncovered, _ = match_courses(gaps, courses, tags)
    assert [r.slug for r in recs] == ["A"]
    assert recs[0].covers == ["python", "sql"]
    assert uncovered == []


def test_unverified_skill_does_not_trigger_recommendation():
    tags = {"A": CourseTags(skills=["python"], reviewed=True)}
    recs, uncovered, _ = match_courses([gap("python", status="unverified")], [course("A")], tags)
    assert recs == [] and uncovered == []


def test_unpublished_course_tags_are_ignored():
    # "X" has tags but is not in the published course list.
    tags = {"X": CourseTags(skills=["sql"], reviewed=True)}
    recs, uncovered, _ = match_courses([gap("sql")], [course("A")], tags)
    assert recs == []
    assert [g.skill for g in uncovered] == ["sql"]


def test_untagged_catalog_produces_warning():
    recs, uncovered, warnings = match_courses([gap("python")], [course("A")], {})
    assert recs == []
    assert [g.skill for g in uncovered] == ["python"]
    assert any("no skill tags" in w for w in warnings)


# ---------- grounding guard in extraction ----------

class FakeLLM:
    def __init__(self, responses: list[str]):
        self.responses = list(responses)

    def complete(self, system: str, user: str) -> str:
        return self.responses.pop(0)


def test_ungrounded_skill_is_dropped():
    cv_text = "Projects: built a REST API with Flask."
    payload = {
        "skills": [
            {"name": "Flask", "claimed_level": "beginner", "evidence": "demonstrated",
             "source_quote": "built a REST API with Flask"},
            {"name": "Kubernetes", "claimed_level": "advanced", "evidence": "listed",
             "source_quote": "Kubernetes expert"},
        ],
    }
    profile = extract_profile(cv_text, FakeLLM([json.dumps(payload)]))
    assert [s.name for s in profile.skills] == ["flask"]


def test_invalid_llm_output_raises_after_retries():
    with pytest.raises(RuntimeError):
        extract_profile("some cv text", FakeLLM(["not json", "still not json"]))