"""Deterministic unit tests for the measurement math (no ML model)."""

import math

import numpy as np

from app.services.measure import circumference, image_scale
from app.utils.imaging import single_leg_width_px, torso_width_px


def test_image_scale_ratio():
    mask = np.zeros((120, 50), dtype=np.uint8)
    mask[10:110, 20:30] = 255  # rows 10..109 -> height_px = 99
    scale = image_scale(mask, height_units=100.0)
    assert scale.top == 10
    assert scale.height_px == 99
    assert math.isclose(scale.ratio, 100.0 / 99.0, rel_tol=1e-9)


def test_circumference_matches_paper_formula():
    # a = 5, b = 3  ->  2*pi*sqrt((25 + 9)/2)
    expected = 2 * math.pi * math.sqrt((25 + 9) / 2)
    assert math.isclose(circumference(10.0, 6.0), expected, rel_tol=1e-12)


def test_circumference_is_symmetric():
    assert math.isclose(circumference(8.0, 4.0), circumference(4.0, 8.0))


def test_torso_width_counts_foreground():
    row = np.zeros((1, 50), dtype=np.uint8)
    row[0, 10:30] = 255
    assert torso_width_px(row, 0) == 20.0


def test_single_leg_two_runs_takes_longest():
    row = np.zeros((1, 60), dtype=np.uint8)
    row[0, 10:20] = 255   # 10-wide leg
    row[0, 40:52] = 255   # 12-wide leg
    assert single_leg_width_px(row, 0) == 12.0


def test_single_leg_one_run_halves():
    row = np.zeros((1, 60), dtype=np.uint8)
    row[0, 10:30] = 255   # legs touching -> 20 wide -> single leg ~10
    assert single_leg_width_px(row, 0) == 10.0


def test_single_leg_empty_row():
    row = np.zeros((1, 60), dtype=np.uint8)
    assert single_leg_width_px(row, 0) == 0.0
