"""Silhouette extraction: turn an RGB image into a clean binary subject mask.

Backends:
  * ``threshold`` - Otsu binarization (classical image processing, no training;
    assumes a reasonably plain background). This is the default so the pipeline
    runs out of the box.
  * ``custom``    - YOUR self-trained segmentation model. This is a placeholder;
    implement ``app/models/segmentation_model.py`` and point
    ``WARDROBE_MODEL_WEIGHTS_PATH`` at your trained weights.

There is intentionally NO pretrained-AI backend here: this project requires
training the model yourself.
"""

from __future__ import annotations

import cv2
import numpy as np

from app.config import Settings
from app.errors import MeasurementError
from app.utils.imaging import clean_mask

# Cached instance of the user's self-trained model (loaded once).
_custom_model = None


def extract_silhouette(img_rgb: np.ndarray, settings: Settings) -> np.ndarray:
    """Return a cleaned binary mask (uint8, foreground=255)."""
    backend = settings.segmentation_backend
    if backend == "threshold":
        mask = _threshold_backend(img_rgb, settings)
    elif backend == "custom":
        mask = _custom_backend(img_rgb, settings)
    else:  # pragma: no cover - guarded by the Settings Literal type
        raise MeasurementError(f"Unknown segmentation backend: {backend!r}")
    return clean_mask(mask, settings.morph_ksize)


def _threshold_backend(img_rgb: np.ndarray, settings: Settings) -> np.ndarray:
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    _thresh, binary = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    # Otsu marks pixels brighter than the threshold as 255. If the subject is
    # darker than the background, invert so the subject becomes foreground.
    if settings.threshold_subject_is_dark:
        binary = cv2.bitwise_not(binary)
    return binary


def _custom_backend(img_rgb: np.ndarray, settings: Settings) -> np.ndarray:
    """Run inference with the self-trained model (see app/models/)."""
    global _custom_model
    if _custom_model is None:
        from app.models.segmentation_model import SegmentationModel

        _custom_model = SegmentationModel(settings.model_weights_path)
        _custom_model.load()
    mask = _custom_model.predict(img_rgb)
    return (mask > 0).astype(np.uint8) * 255
