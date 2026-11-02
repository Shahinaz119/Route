"""Load project settings from .env once, before anything reads the environment."""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

# override=False: variables already set in the terminal win over values in .env.
load_dotenv(ENV_FILE, override=False)