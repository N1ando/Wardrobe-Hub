# Self-trained models

This project trains its own model instead of using any pretrained AI. The
measurement pipeline depends only on a small, stable contract — implement it with
whatever framework you like (PyTorch, TensorFlow, etc.).

## Segmentation model

The pipeline needs a function that turns an RGB photo into a binary subject mask.

**Contract** (`app/models/segmentation_model.py`):

```python
model = SegmentationModel(weights_path)
model.load()                      # load YOUR trained weights
mask = model.predict(image_rgb)   # uint8 H x W, foreground=255, background=0
```

Both `load` and `predict` currently raise `NotImplementedError` — that is the
placeholder you replace.

### Training

`app/models/train.py` is a CLI skeleton (dataset → model → loop → save weights).
Fill in `build_dataset`, `build_model`, and `train`, then:

```bash
python -m app.models.train --data ./data --out ./weights.pt --epochs 50
```

Training data is `(image, mask)` pairs where the mask marks the subject
(foreground=255, background=0).

### Using your trained model

```bash
export WARDROBE_SEGMENTATION_BACKEND=custom
export WARDROBE_MODEL_WEIGHTS_PATH=/path/to/weights.pt
uvicorn app.main:app --reload
```

## Fallback backend

Until your model is trained, the service defaults to
`WARDROBE_SEGMENTATION_BACKEND=threshold` — a classical Otsu backend (no ML, no
training) that works against reasonably plain backgrounds. Tests use it too.
