"""Helpers to persist plot images and thumbnails to disk."""

from __future__ import annotations

import base64
import os
import uuid
from typing import Optional, Tuple

from PIL import Image


def save_plot_assets(
    project_path: str, image_base64: str, thumbnail_size: Tuple[int, int] = (360, 240)
) -> Tuple[str, Optional[str]]:
    """Save the plot image and a thumbnail under the project directory."""
    plots_dir = os.path.join(project_path, "plots")
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)

    plot_id = uuid.uuid4().hex
    image_path = os.path.join(plots_dir, f"plot_{plot_id}.png")
    thumbnail_path = os.path.join(plots_dir, f"plot_{plot_id}_thumb.png")

    image_bytes = base64.b64decode(image_base64)
    with open(image_path, "wb") as f:
        f.write(image_bytes)

    image = Image.open(image_path)
    image.thumbnail(thumbnail_size)
    image.save(thumbnail_path, format="PNG")

    return image_path, thumbnail_path


def create_thumbnail(
    image_path: str, thumbnail_path: str, thumbnail_size: Tuple[int, int] = (360, 240)
) -> None:
    """Generate a thumbnail PNG for an existing image path."""
    target_dir = os.path.dirname(thumbnail_path)
    if target_dir and not os.path.exists(target_dir):
        os.makedirs(target_dir)

    image = Image.open(image_path)
    image.thumbnail(thumbnail_size)
    image.save(thumbnail_path, format="PNG")
