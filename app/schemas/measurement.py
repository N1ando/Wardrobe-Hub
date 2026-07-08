"""Request/response models for the measurement API."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class HeightUnit(str, Enum):
    inch = "in"
    cm = "cm"


class Measurements(BaseModel):
    waist: float = Field(..., description="Waist circumference")
    low_hip: float = Field(..., description="Lower-hip circumference")
    thigh: float = Field(..., description="Thigh circumference")


class MeasurementResponse(BaseModel):
    unit: HeightUnit
    height: float
    measurements: Measurements
    diagnostics: Optional[dict[str, Any]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "unit": "in",
                "height": 70.0,
                "measurements": {"waist": 33.1, "low_hip": 38.4, "thigh": 21.2},
                "diagnostics": None,
            }
        }
    }
