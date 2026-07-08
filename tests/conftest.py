"""Shared pytest fixtures.

Force the deterministic Otsu ``threshold`` segmentation backend so the whole
suite runs without downloading or importing any ML model.
"""

import os

os.environ.setdefault("WARDROBE_SEGMENTATION_BACKEND", "threshold")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def settings():
    from app.config import Settings

    return Settings(segmentation_backend="threshold")


@pytest.fixture
def client():
    from app.config import get_settings
    from app.main import app

    get_settings.cache_clear()
    return TestClient(app)
