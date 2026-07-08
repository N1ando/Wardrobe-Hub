"""Training scaffold for the self-trained segmentation model.

This is a skeleton, not a working trainer. Fill in the dataset, model, and loop
with your framework of choice, then save weights to a path you pass via
WARDROBE_MODEL_WEIGHTS_PATH at inference time.

Run:  python -m app.models.train --data ./data --out ./weights.pt --epochs 50
"""

from __future__ import annotations

import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the segmentation model.")
    parser.add_argument("--data", required=True, help="Path to the training dataset.")
    parser.add_argument("--out", required=True, help="Where to save trained weights.")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-3)
    return parser.parse_args()


def build_dataset(data_dir: str):
    # TODO: load (image, mask) pairs. Masks: foreground=255, background=0.
    raise NotImplementedError("Implement dataset loading for your data.")


def build_model():
    # TODO: return your model (e.g. a U-Net).
    raise NotImplementedError("Define your segmentation model architecture.")


def train(args: argparse.Namespace) -> None:
    # TODO: standard loop — forward, loss (e.g. BCE/Dice), backward, step —
    # then save weights to args.out.
    raise NotImplementedError(
        "Implement the training loop, then save weights to args.out."
    )


if __name__ == "__main__":  # pragma: no cover
    train(parse_args())
