"""Environment settings used by the app and data collector."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Small, read-only collection of environment settings."""

    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    search_keyword: str = os.getenv("GEM_SEARCH_KEYWORD", "laptop")
    cache_path: Path = Path(os.getenv("GEM_CACHE_PATH", "data/cache/collection.json"))
    max_tenders: int = int(os.getenv("GEM_MAX_TENDERS", "5"))
    max_awards: int = int(os.getenv("GEM_MAX_AWARDS", "25"))
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))


def get_settings() -> Settings:
    """Read settings from the environment."""

    return Settings()
