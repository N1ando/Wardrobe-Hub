# WardrobeHub — Body-Size Measurement Backend

A Python/FastAPI service that estimates **waist, lower-hip, and thigh
circumferences** from a person's height plus a **front** and a **side** photo,
following the method in *Foysal et al., "Body Size Measurement Using a
Smartphone" (Electronics, 2021)*.

The pipeline: segment the subject silhouette → derive a pixel-to-unit ratio from
the known height (`ratio = height / person_height_px`) → locate landmarks by body
proportion (waist ≈ 3/8, hip ≈ 1/2, thigh ≈ 5/8 of height) → combine front width
and side depth into a circumference via the ellipse-perimeter approximation
`C = 2π·√((a² + b²) / 2)`.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the API. Default segmentation is the classical Otsu "threshold" backend
# (no ML, no pretrained model). Swap in your own trained model via the "custom"
# backend once it is ready (see app/models/README.md).
uvicorn app.main:app --reload
```

Open the interactive docs at <http://127.0.0.1:8000/docs>.

### Example request

```bash
curl -X POST http://127.0.0.1:8000/api/v1/measurements \
  -F height_value=70 \
  -F height_unit=in \
  -F front=@front.jpg \
  -F side=@side.jpg \
  -F debug=true
```

Response:

```json
{
  "unit": "in",
  "height": 70.0,
  "measurements": { "waist": 33.1, "low_hip": 38.4, "thigh": 21.2 },
  "diagnostics": { "...": "landmark rows, ratios, and base64 mask overlays when debug=true" }
}
```

Circumferences are returned in the same unit as the supplied height. Set
`debug=true` to get base64 PNG overlays (mask contour + landmark lines) for
visual sanity-checking.

## Endpoints

| Method | Path                    | Purpose                                  |
| ------ | ----------------------- | ---------------------------------------- |
| GET    | `/health`               | Liveness check                           |
| POST   | `/api/v1/measurements`  | Multipart: `height_value`, `height_unit` (`in`/`cm`), `front`, `side`, optional `debug` |

## Configuration

Environment variables (prefix `WARDROBE_`), e.g.:

- `WARDROBE_SEGMENTATION_BACKEND` — `threshold` (default) or `custom`.
  - `threshold` is a dependency-free classical Otsu backend (no ML/training).
  - `custom` runs your self-trained model; set `WARDROBE_MODEL_WEIGHTS_PATH`.
- `WARDROBE_MAX_IMAGE_DIM` — longest-side downscale for speed (default 1024).
- Body proportions and search bands (`WARDROBE_WAIST_FRACTION`, etc.).

See [app/config.py](app/config.py) for the full list.

## Tests

The suite uses the deterministic `threshold` backend, so it needs **no ML
model** and no trained weights:

```bash
pytest -q
```

## Layout

```
app/
  main.py            FastAPI app (uvicorn entrypoint)
  config.py          Pydantic settings
  api/routes.py      /health and /api/v1/measurements
  schemas/           request/response models
  services/          segmentation, landmarks, measure, pipeline
  models/            placeholder for YOUR self-trained segmentation model + trainer
  utils/imaging.py   decode, EXIF, resize, mask geometry, overlays
tests/               unit + API tests with synthetic silhouettes
```

## Scope & notes

- Stateless compute service: no database, auth, or job queue.
- The paper's preferred-waistline neural network is approximated by a
  narrowest-abdomen search within the waist band (a trainable regressor can slot
  into [app/services/landmarks.py](app/services/landmarks.py) later).
- 3D mannequin reconstruction is out of scope; only the three circumferences are
  produced.
