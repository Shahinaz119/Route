"""Match skill gaps to published courses with greedy set cover.

Each step picks the course that covers the most still-uncovered gaps.
Ties go to the course covering the highest-priority gap, then to slug order.
"""
from __future__ import annotations

from collections import defaultdict

from models import CatalogCourse, CourseTags, Recommendation, SkillGap

ACTIONABLE_STATUSES = {"missing", "underdeveloped"}


def match_courses(
    gaps: list[SkillGap],
    courses: list[CatalogCourse],
    tags: dict[str, CourseTags],
) -> tuple[list[Recommendation], list[SkillGap], list[str]]:
    """Return (recommendations ordered by gap priority, uncovered gaps, warnings)."""
    warnings: list[str] = []
    published = {course.slug: course for course in courses}

    # Tags for courses that are not published are ignored on purpose.
    skill_to_slugs: dict[str, set[str]] = defaultdict(set)
    for slug in published:
        entry = tags.get(slug)
        if entry is None:
            continue
        for skill in entry.skills:
            skill_to_slugs[skill].add(slug)

    untagged = [s for s in published if s not in tags or not tags[s].skills]
    unreviewed = [s for s in published if s in tags and tags[s].skills and not tags[s].reviewed]
    if untagged:
        warnings.append(f"{len(untagged)} published course(s) have no skill tags and cannot be matched")
    if unreviewed:
        warnings.append(f"{len(unreviewed)} course(s) use skill tags that a human has not reviewed yet")

    priority_of = {g.skill: g.priority for g in gaps}
    remaining = {g.skill: g for g in gaps if g.status in ACTIONABLE_STATUSES}
    selected: dict[str, list[str]] = {}

    while remaining:
        scores: dict[str, list[str]] = {}
        for slug in sorted(published):
            covered = sorted(skill for skill in remaining if slug in skill_to_slugs.get(skill, set()))
            if covered:
                scores[slug] = covered
        if not scores:
            break

        best = max(
            scores,
            key=lambda slug: (len(scores[slug]), -min(priority_of[s] for s in scores[slug])),
        )
        selected[best] = scores[best]
        for skill in scores[best]:
            del remaining[skill]

    uncovered = sorted(remaining.values(), key=lambda g: g.priority)

    ordered = sorted(
        selected.items(),
        key=lambda item: (min(priority_of[s] for s in item[1]), item[0]),
    )
    recommendations = [
        Recommendation(
            slug=slug,
            title=published[slug].title_en,
            delivery_type=published[slug].delivery_type,
            covers=skills,
            reason="Covers: " + ", ".join(skills),
        )
        for slug, skills in ordered
    ]
    return recommendations, uncovered, warnings