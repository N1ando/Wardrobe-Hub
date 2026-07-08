"""Image decoding and binary-mask geometry helpers.

Masks are ``uint8`` arrays where foreground (the subject) is 255 and background 0.
"""

from __future__ import annotations

import base64
from io import BytesIO

import cv2
import numpy as np
from PIL import Image, ImageOps

from app.errors import ImageDecodeError, MeasurementError, NoPersonDetectedError


# --------------------------------------------------------------------------- #
# Decoding / normalization
# --------------------------------------------------------------------------- #
def decode_image(data: bytes) -> np.ndarray:
    """Decode image bytes into an RGB uint8 array, honoring EXIF orientation."""
    if not data:
        raise ImageDecodeError("Empty image upload.")
    try:
        pil = Image.open(BytesIO(data))
        pil = ImageOps.exif_transpose(pil)  # rotate per camera orientation tag
        pil = pil.convert("RGB")
    except Exception as exc:  # noqa: BLE001 - surface any decode failure uniformly
        raise ImageDecodeError("Uploaded file is not a valid image.") from exc
    return np.asarray(pil, dtype=np.uint8)


def resize_max(img: np.ndarray, max_dim: int) -> np.ndarray:
    """Downscale so the longest side is at most ``max_dim`` (never upscales)."""
    h, w = img.shape[:2]
    longest = max(h, w)
    if longest <= max_dim:
        return img
    scale = max_dim / longest
    new_size = (max(1, int(round(w * scale))), max(1, int(round(h * scale))))
    return cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)


# --------------------------------------------------------------------------- #
# Mask cleanup
# --------------------------------------------------------------------------- #
def largest_component(mask: np.ndarray) -> np.ndarray:
    """Keep only the largest connected foreground blob."""
    binary = (mask > 0).astype(np.uint8)
    num, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if num <= 1:
        return (binary * 255).astype(np.uint8)
    # label 0 is background; pick the largest of the remaining labels
    largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return np.where(labels == largest, 255, 0).astype(np.uint8)


def clean_mask(mask: np.ndarray, ksize: int = 5) -> np.ndarray:
    """Fill small holes, drop specks, and keep the largest component."""
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    m = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel)
    return largest_component(m)


# --------------------------------------------------------------------------- #
# Geometry
# --------------------------------------------------------------------------- #
def vertical_extent(mask: np.ndarray) -> tuple[int, int]:
    """Return (top_row, bottom_row) of the foreground; both inclusive."""
    rows = np.where(mask.any(axis=1))[0]
    if rows.size == 0:
        raise NoPersonDetectedError("No subject silhouette found in image.")
    return int(rows[0]), int(rows[-1])


def foreground_runs(row: np.ndarray) -> list[tuple[int, int]]:
    """Contiguous foreground spans in a single mask row as ``[start, end)``."""
    fg = row > 0
    if not fg.any():
        return []
    # Pad with False on both ends to detect edges via diff.
    padded = np.concatenate(([False], fg, [False]))
    diff = np.diff(padded.astype(np.int8))
    starts = np.where(diff == 1)[0]
    ends = np.where(diff == -1)[0]
    return list(zip(starts.tolist(), ends.tolist()))


def torso_width_px(mask: np.ndarray, row: int) -> float:
    """Number of foreground pixels across a row (solid torso/limb width)."""
    return float(np.count_nonzero(mask[row]))


def single_leg_width_px(mask: np.ndarray, row: int) -> float:
    """Estimate one leg's width at a row.

    Front view: legs appear as two side-by-side runs -> the longer run is a leg.
    If the legs touch (one run), approximate a single leg as half the run.
    """
    runs = foreground_runs(mask[row])
    if not runs:
        return 0.0
    lengths = [end - start for start, end in runs]
    if len(runs) >= 2:
        return float(max(lengths))
    return float(lengths[0] / 2.0)


# --------------------------------------------------------------------------- #
# Debug overlay
# --------------------------------------------------------------------------- #
def encode_png(img_rgb: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR))
    if not ok:
        raise MeasurementError("Failed to encode debug overlay.")
    return buf.tobytes()


def overlay_b64(img_rgb: np.ndarray, mask: np.ndarray, rows: dict[str, int]) -> str:
    """Draw the mask contour and labeled landmark rows; return base64 PNG."""
    vis = img_rgb.copy()
    contours, _ = cv2.findContours(
        (mask > 0).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    cv2.drawContours(vis, contours, -1, (0, 200, 0), 2)
    colors = {"waist": (220, 0, 0), "low_hip": (0, 0, 220), "thigh": (230, 140, 0)}
    for name, row in rows.items():
        color = colors.get(name, (255, 255, 0))
        cv2.line(vis, (0, int(row)), (vis.shape[1], int(row)), color, 2)
    return base64.b64encode(encode_png(vis)).decode("ascii")
