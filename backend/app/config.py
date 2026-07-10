"""Application settings.

All values are overridable via environment variables. Keys shared with the wider
FitOS stack (Fireworks, Gemma) are read WITHOUT a prefix so a single root
``.env`` works for the whole ``docker-compose`` stack; FitOS-specific knobs use
the ``FITOS_`` prefix.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo layout: <repo>/backend/app/config.py  -> BACKEND_DIR = <repo>/backend
BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
SEED_DIR = DATA_DIR / "seed"
CACHE_DIR = DATA_DIR / "cache"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    app_name: str = "FitOS API"

    # --- Database ---
    # SQLite by design (see plan: zero ops value in Postgres for this project).
    database_url: str = f"sqlite:///{DATA_DIR / 'fitos.db'}"

    # --- Gemma / AMD / Fireworks ---
    # Fallback ladder: AMD vLLM (gemma_url) -> Fireworks -> cache -> template.
    gemma_url: str = ""  # AMD Dev Cloud vLLM OpenAI-compatible base URL, e.g. http://host:8001/v1
    gemma_model: str = "fitos-gemma"  # served model name on the AMD vLLM box (weights: google/gemma-2-2b-it)
    fireworks_api_key: str = ""
    fireworks_model: str = "accounts/fireworks/models/gemma-2-9b-it"
    fireworks_base_url: str = "https://api.fireworks.ai/inference/v1"
    llm_timeout_s: float = 20.0
    use_cache: bool = True  # read/write data/cache/*.json for LLM outputs

    # --- API ---
    cors_origins: list[str] = ["*"]

    @property
    def cache_dir(self) -> Path:
        return CACHE_DIR

    @property
    def seed_dir(self) -> Path:
        return SEED_DIR


@lru_cache
def get_settings() -> Settings:
    return Settings()
