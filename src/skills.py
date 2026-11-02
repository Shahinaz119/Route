"""Deterministic skill-name normalization. No LLM involved.

The alias map is a seed. Extend it from real CV and job-description data,
not from guesses.
"""
from __future__ import annotations

import re

_ALIASES: dict[str, str] = {
    "py": "python",
    "python3": "python",
    "js": "javascript",
    "ml": "machine learning",
    "dl": "deep learning",
    "postgres": "postgresql",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "rest api": "rest apis",
    "restful apis": "rest apis",
    "llm": "large language models",
    "rag": "retrieval-augmented generation",
}

_WHITESPACE = re.compile(r"\s+")


def normalize_skill(raw: str) -> str:
    """Lowercase, collapse whitespace, replace underscores, apply aliases."""
    key = _WHITESPACE.sub(" ", raw.strip().lower()).replace("_", " ")
    return _ALIASES.get(key, key)
