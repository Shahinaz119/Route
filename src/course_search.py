"""Semantic course search using pre-built embeddings.

The model and embeddings are loaded once per session and passed in as parameters
to avoid reloading on every tool call.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from embeddings import EMBEDDINGS_PATH, MODEL_NAME, load_embeddings
from models import CatalogCourse

# Module-level cache as a fallback when no preloaded data is passed.
_slugs: list[str] | None = None
_vectors: np.ndarray | None = None
_model: SentenceTransformer | None = None


def _load_once(
    embeddings_path: Path = EMBEDDINGS_PATH,
    model_name: str = MODEL_NAME,
) -> tuple[list[str], np.ndarray, SentenceTransformer]:
    """Load embeddings and model once and cache them at module level."""
    global _slugs, _vectors, _model
    if _slugs is None or _vectors is None or _model is None:
        _slugs, raw_vectors = load_embeddings(embeddings_path)
        norms = np.linalg.norm(raw_vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        _vectors = raw_vectors / norms
        _model = SentenceTransformer(model_name)
    return _slugs, _vectors, _model


def search_courses(
    query: str,
    courses_by_slug: dict[str, CatalogCourse],
    top_k: int = 5,
    preloaded_slugs: list[str] | None = None,
    preloaded_vectors: np.ndarray | None = None,
    preloaded_model: SentenceTransformer | None = None,
    embeddings_path: Path = EMBEDDINGS_PATH,
    model_name: str = MODEL_NAME,
) -> list[tuple[CatalogCourse, float]]:
    """Return up to top_k (course, score) pairs ranked by semantic similarity.

    If preloaded data is provided (from Session), use it directly.
    Otherwise fall back to the module-level cache.
    """
    if (
        preloaded_slugs is not None
        and preloaded_vectors is not None
        and preloaded_model is not None
    ):
        slugs = preloaded_slugs
        vectors = preloaded_vectors
        model = preloaded_model
    else:
        slugs, vectors, model = _load_once(embeddings_path, model_name)

    query_vec = model.encode([query], convert_to_numpy=True)[0]
    norm = np.linalg.norm(query_vec)
    if norm > 0:
        query_vec = query_vec / norm

    scores = vectors @ query_vec
    top_indices = np.argsort(scores)[::-1][:top_k]

    results: list[tuple[CatalogCourse, float]] = []
    for idx in top_indices:
        slug = slugs[idx]
        course = courses_by_slug.get(slug)
        if course is not None:
            results.append((course, float(scores[idx])))
    return results