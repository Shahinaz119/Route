"""Build and persist catalog embeddings using a local multilingual model.

Run once (or whenever the catalog changes):
  python src/embeddings.py --catalog data/courses.xlsx

Writes data/catalog_embeddings.npz  (vectors + slugs, ready for search).
No internet connection or API quota needed after the model is downloaded once.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

import config  # noqa: F401
from catalog import load_catalog
from models import CatalogCourse

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDINGS_PATH = Path("data/catalog_embeddings.npz")
MAX_TEXT_CHARS = 500


def course_text(course: CatalogCourse) -> str:
    """Combine the most useful fields into one searchable string."""
    parts = [
        course.title_en,
        course.title_ar,
        course.short_description_en,
        course.overview_en[:MAX_TEXT_CHARS],
    ]
    return " | ".join(p for p in parts if p)


def build_embeddings(
    courses: list[CatalogCourse],
    model: SentenceTransformer,
) -> tuple[list[str], np.ndarray]:
    """Return (slugs, matrix) where matrix[i] is the embedding for slugs[i]."""
    texts = [course_text(c) for c in courses]
    slugs = [c.slug for c in courses]
    print(f"Encoding {len(texts)} courses ...")
    vectors = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    return slugs, vectors


def save_embeddings(path: Path, slugs: list[str], vectors: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, slugs=np.array(slugs), vectors=vectors)
    print(f"Saved {len(slugs)} embeddings to {path}")


def load_embeddings(path: Path) -> tuple[list[str], np.ndarray]:
    data = np.load(path, allow_pickle=False)
    return data["slugs"].tolist(), data["vectors"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build catalog embeddings")
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=EMBEDDINGS_PATH)
    parser.add_argument("--model", default=MODEL_NAME)
    args = parser.parse_args()

    courses, stats = load_catalog(args.catalog)
    print(f"Published courses: {stats['published']} (of {stats['total_rows']} rows)")

    model = SentenceTransformer(args.model)
    slugs, vectors = build_embeddings(courses, model)
    save_embeddings(args.out, slugs, vectors)


if __name__ == "__main__":
    main()