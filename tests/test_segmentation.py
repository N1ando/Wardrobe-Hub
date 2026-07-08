"""Tests for the deterministic threshold segmentation backend."""

import numpy as np

from app.services.segmentation import extract_silhouette
from app.utils.imaging import vertical_extent
from tests.synthetic import front_array


def test_threshold_backend_extracts_subject(settings):
    img = front_array()
    mask = extract_silhouette(img, settings)

    assert mask.dtype == np.uint8
    assert set(np.unique(mask)).issubset({0, 255})
    assert np.count_nonzero(mask) > 0

    # The figure spans roughly the head (~y=30) to the feet (~y=780).
    top, bottom = vertical_extent(mask)
    assert top < 60
    assert bottom > 740
