"""Deterministic skill gap analysis. No LLM involved, so results are reproducible."""
from __future__ import annotations

from models import LEVEL_ORDER, CVProfile, Evidence, Level, RoleProfile, SkillGap
from skills import normalize_skill

_STATUS_ORDER = {"missing": 0, "underdeveloped": 1, "unverified": 2}


def _rank(level: Level) -> int:
    return LEVEL_ORDER.index(level)


def analyze_gaps(cv: CVProfile, role: RoleProfile) -> list[SkillGap]:
    """Compare a candidate profile with a role's requirements.

    Status rules:
      missing        -> the skill does not appear in the CV.
      underdeveloped -> the skill appears, but the claimed level is below the requirement.
      unverified     -> the level meets the requirement, but evidence is only a listing.
      (no gap)       -> the level meets the requirement and the skill is demonstrated.
    """
    candidate = {skill.name: skill for skill in cv.skills}
    gaps: list[SkillGap] = []
    seen: set[str] = set()

    for req in role.requirements:
        name = normalize_skill(req.skill)
        if name in seen:
            continue
        seen.add(name)

        have = candidate.get(name)
        if have is None:
            status, current, evidence = "missing", Level.NONE, Evidence.NONE
        elif _rank(have.claimed_level) < _rank(req.min_level):
            status, current, evidence = "underdeveloped", have.claimed_level, have.evidence
        elif have.evidence == Evidence.DEMONSTRATED:
            continue  # requirement met with evidence: not a gap
        else:
            status, current, evidence = "unverified", have.claimed_level, have.evidence

        gaps.append(
            SkillGap(
                skill=name,
                required_level=req.min_level,
                current_level=current,
                evidence=evidence,
                mandatory=req.mandatory,
                status=status,
            )
        )
    return _prioritize(gaps)


def _prioritize(gaps: list[SkillGap]) -> list[SkillGap]:
    """Mandatory first, then missing > underdeveloped > unverified, then higher required level."""
    ordered = sorted(
        gaps,
        key=lambda g: (not g.mandatory, _STATUS_ORDER[g.status], -_rank(g.required_level), g.skill),
    )
    return [gap.model_copy(update={"priority": i}) for i, gap in enumerate(ordered, start=1)]
