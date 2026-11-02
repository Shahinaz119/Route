from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Level(str, Enum):
    NONE = "none"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


LEVEL_ORDER: list[Level] = [Level.NONE, Level.BEGINNER, Level.INTERMEDIATE, Level.ADVANCED]


class Evidence(str, Enum):
    DEMONSTRATED = "demonstrated"  # used in a project or job with a described task
    LISTED = "listed"              # appears only in a skills list
    NONE = "none"


class CandidateSkill(BaseModel):
    name: str
    claimed_level: Level
    evidence: Evidence
    source_quote: str = Field(default="", max_length=300)


class CVProfile(BaseModel):
    skills: list[CandidateSkill] = Field(default_factory=list)
    years_experience: float | None = None
    education: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)


class RoleRequirement(BaseModel):
    skill: str
    min_level: Level
    mandatory: bool = True


class RoleProfile(BaseModel):
    role_id: str
    title: str
    requirements: list[RoleRequirement]
    source: str = "UNSOURCED"


class SkillGap(BaseModel):
    skill: str
    required_level: Level
    current_level: Level
    evidence: Evidence
    mandatory: bool
    status: Literal["missing", "underdeveloped", "unverified"]
    priority: int = 0


class CatalogCourse(BaseModel):
    """A published EYOUTH course, containing only the fields the pipeline uses."""

    slug: str
    title_en: str
    title_ar: str = ""
    short_description_en: str = ""
    overview_en: str = ""
    instructor_en: str = ""
    category: str = ""
    delivery_type: Literal["hybrid", "live", "recorded"]
    status: str
    stage: str | None = None
    duration: str | float | None = None
    certificate_hours: float | None = None
    quiz_type: str | None = None

    @field_validator("delivery_type", "status", mode="before")
    @classmethod
    def _normalize_case(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value


class CourseTags(BaseModel):
    """Skills generated for a course. Stays unreviewed until a human checks it."""

    skills: list[str] = Field(default_factory=list)
    reviewed: bool = False


class Recommendation(BaseModel):
    slug: str
    title: str
    delivery_type: Literal["hybrid", "live", "recorded"]
    covers: list[str]
    reason: str