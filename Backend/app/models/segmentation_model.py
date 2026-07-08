"""Placeholder for a body-segmentation model that YOU train.

This is intentionally NOT implemented. Replace the bodies of ``load`` and
``predict`` with your own trained model (e.g. a U-Net / DeepLab in PyTorch or
TensorFlow). The rest of the pipeline only needs this contract:

    model = SegmentationModel(weights_path)
    model.load()
    mask = model.predict(image_rgb)   # -> uint8 H x W, foreground=255, background=0

To use it once implemented, run the API with:

    WARDROBE_SEGMENTATION_BACKEND=custom
    WARDROBE_MODEL_WEIGHTS_PATH=/path/to/your/trained/weights

See app/models/README.md and app/models/train.py for the training scaffold.
"""

from __future__ import annotations

import numpy as np


class SegmentationModel:
    def __init__(self, weights_path: str | None = None) -> None:
        self.weights_path = weights_path
        self._model = None  # your framework's model object goes here

    def load(self) -> None:
        """Load your trained weights into ``self._model``.

        Example (PyTorch):
            import torch
            self._model = MyUNet()
            self._model.load_state_dict(torch.load(self.weights_path, map_location="cpu"))
            self._model.eval()
        """
        raise NotImplementedError(
            "SegmentationModel.load is a placeholder. Train your own segmentation "
            "model and load its weights here. See app/models/README.md."
        )

    def predict(self, image_rgb: np.ndarray) -> np.ndarray:
        """Return a binary mask, same height/width as ``image_rgb``.

        Contract: uint8 array, foreground (subject) = 255, background = 0.

        Example outline:
            tensor = preprocess(image_rgb)          # resize/normalize to model input
            with torch.no_grad():
                logits = self._model(tensor)
            prob = logits.sigmoid().squeeze().cpu().numpy()
            prob = resize_back(prob, image_rgb.shape[:2])
            return (prob > 0.5).astype(np.uint8) * 255
        """
        raise NotImplementedError(
            "SegmentationModel.predict is a placeholder. Run inference with your "
            "trained model and return a uint8 mask (foreground=255)."
        )
