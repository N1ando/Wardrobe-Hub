"""HTTP routes for the measurement service."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.config import Settings, get_settings
from app.errors import ImageDecodeError, NoPersonDetectedError
from app.schemas.measurement import HeightUnit, Measurements, MeasurementResponse
from app.services.pipeline import run_measurement

router = APIRouter()


@router.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


def _height_cm(value: float, unit: HeightUnit) -> float:
    return value * 2.54 if unit == HeightUnit.inch else value


@router.post("/api/v1/measurements", response_model=MeasurementResponse, tags=["measure"])
async def create_measurement(
    height_value: float = Form(..., gt=0, description="Subject height"),
    height_unit: HeightUnit = Form(..., description="Unit of height ('in' or 'cm')"),
    front: UploadFile = File(..., description="Front-view photo"),
    side: UploadFile = File(..., description="Side-view photo"),
    debug: bool = Form(False, description="Include masks/landmark overlays"),
    settings: Settings = Depends(get_settings),
) -> MeasurementResponse:
    height_cm = _height_cm(height_value, height_unit)
    if not (settings.min_height_cm <= height_cm <= settings.max_height_cm):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Height {height_value}{height_unit.value} is outside the plausible "
                f"range ({settings.min_height_cm}-{settings.max_height_cm} cm)."
            ),
        )

    front_bytes = await front.read()
    side_bytes = await side.read()

    try:
        result = run_measurement(
            front_bytes=front_bytes,
            side_bytes=side_bytes,
            height_value=height_value,
            settings=settings,
            debug=debug,
        )
    except ImageDecodeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except NoPersonDetectedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    rounded = {k: round(v, 1) for k, v in result["measurements"].items()}
    return MeasurementResponse(
        unit=height_unit,
        height=height_value,
        measurements=Measurements(**rounded),
        diagnostics=result["diagnostics"] if debug else None,
    )
