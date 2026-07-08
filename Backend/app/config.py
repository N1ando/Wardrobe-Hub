"""Application settings.

All values are overridable via environment variables prefixed with ``WARDROBE_``,
e.g. ``WARDROBE_SEGMENTATION_BACKEND=threshold``.
"""

from functools import lru_cache
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

SegmentationBackend = Literal["threshold", "custom"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WARDROBE_", env_file=".env")

    app_name: str = "WardrobeHub Measurement API"

    # --- Segmentation ---
    # "threshold" is a classical Otsu backend (no ML, no training) and the default
    # so the pipeline runs out of the box. "custom" runs YOUR self-trained model
    # (see app/models/); point model_weights_path at its weights.
    segmentation_backend: SegmentationBackend = "threshold"
    model_weights_path: Optional[str] = None  # weights for the "custom" backend
    threshold_subject_is_dark: bool = True  # Otsu backend: subject darker than bg
    morph_ksize: int = 5  # morphological cleanup kernel size

    # --- Image handling ---
    max_image_dim: int = 1024  # downscale longest side to this for speed

    # --- Body proportions (fraction of body height, measured from the top) ---
    waist_fraction: float = 0.375  # 3/8 (paper)
    hip_fraction: float = 0.5  # 1/2 (paper)
    thigh_fraction: float = 0.625  # 5/8 (paper)

    # Search bands used to refine waist (narrowest) and hip (widest) rows.
    waist_band_low: float = 0.30
    waist_band_high: float = 0.45
    hip_band_low: float = 0.45
    hip_band_high: float = 0.60
    # If the waist band's width variation is below this, fall back to the
    # fixed 3/8 proportion rather than trusting a noisy "narrowest" row.
    flatness_eps: float = 0.05

    # --- Validation ---
    min_person_height_px: int = 50  # reject masks smaller than this
    min_height_cm: float = 50.0
    max_height_cm: float = 272.0

    # --- API ---
    cors_origins: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
