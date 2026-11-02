"""Load the EYOUTH catalog from an Excel sheet (.xlsx) or a JSON list.

CATALOG_KEYS maps internal field names to the exact column headers in the sheet.
Headers are matched exactly, including spaces, parentheses and capital letters.
"""
from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import ValidationError

from models import CatalogCourse, CourseTags

logger = logging.getLogger(__name__)

# internal field name -> exact column header in the Excel sheet (or key in JSON)
CATALOG_KEYS: dict[str, str] = {
    "slug": "Slug",
    "title_en": "Title (EN)",
    "title_ar": "Title (AR)",
    "short_description_en": "Short Description (EN)",
    "overview_en": "Overview (EN)",
    "instructor_en": "Instructor Name (EN)",
    "category": "Category",
    "delivery_type": "Delivery Type",
    "status": "Status",
    "stage": "Stage",
    "duration": "Duration",
    "certificate_hours": "Certificate Hours",
    "quiz_type": "Quiz Type",
}

# Columns the pipeline cannot work without.
REQUIRED_KEYS = ["slug", "title_en", "delivery_type", "status"]


def _read_rows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Return (rows, column headers). Only the first sheet is read."""
    suffix = path.suffix.lower()

    if suffix in {".xlsx", ".xlsm"}:
        frame = pd.read_excel(path, sheet_name=0, dtype=object)
        frame = frame.dropna(how="all")  # drop fully empty rows
        headers = [str(col).strip() for col in frame.columns]
        frame.columns = headers
        frame = frame.astype(object).where(pd.notna(frame), None)
        return frame.to_dict(orient="records"), headers

    if suffix == ".json":
        rows = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            raise ValueError("JSON catalog must be a list of course objects")
        headers = list(rows[0].keys()) if rows and isinstance(rows[0], dict) else []
        return rows, headers

    raise ValueError(f"Unsupported catalog format: {suffix}. Use .xlsx or .json")


def _check_required_columns(headers: list[str]) -> None:
    missing = [
        column
        for key, column in CATALOG_KEYS.items()
        if key in REQUIRED_KEYS and column not in headers
    ]
    if missing:
        raise ValueError(
            f"Catalog is missing required column(s): {missing}. Headers found: {headers}"
        )


def _clean_value(value: Any) -> Any:
    """Turn Excel cell values into plain values the models accept."""
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    if isinstance(value, bool | int | float):
        return value
    # Dates, times and other Excel types become text.
    return str(value)


def _to_internal(row: dict) -> dict:
    mapped = {}
    for internal, column in CATALOG_KEYS.items():
        cleaned = _clean_value(row.get(column))
        if cleaned is not None:
            mapped[internal] = cleaned
    return mapped


def load_catalog(path: Path) -> tuple[list[CatalogCourse], dict]:
    """Return published courses only, plus stats for the report."""
    rows, headers = _read_rows(path)
    if headers:
        _check_required_columns(headers)

    status_column = CATALOG_KEYS["status"]
    status_counts = Counter(str(row.get(status_column)).strip() for row in rows)

    courses: list[CatalogCourse] = []
    invalid: list[str] = []
    skipped_unpublished = 0
    seen_slugs: set[str] = set()

    for index, row in enumerate(rows):
        excel_row = index + 2  # +1 for the header row, +1 because Excel rows start at 1
        try:
            course = CatalogCourse.model_validate(_to_internal(row))
        except ValidationError as exc:
            fields = sorted({str(err["loc"][0]) for err in exc.errors() if err.get("loc")})
            message = f"row {excel_row}: invalid field(s): {', '.join(fields)}"
            invalid.append(message)
            logger.warning("Catalog %s", message)
            continue

        if course.status != "published":
            skipped_unpublished += 1
            continue
        if course.slug in seen_slugs:
            raise ValueError(f"Duplicate published slug: {course.slug!r}")
        seen_slugs.add(course.slug)
        courses.append(course)

    stats = {
        "total_rows": len(rows),
        "published": len(courses),
        "skipped_unpublished": skipped_unpublished,
        "status_counts": dict(status_counts),
        "invalid_rows": invalid,
    }
    return courses, stats


def load_tags(path: Path) -> dict[str, CourseTags]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {slug: CourseTags.model_validate(entry) for slug, entry in raw.items()}