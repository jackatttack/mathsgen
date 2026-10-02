"""Pythonista-only adapter: save a GIF to Photos, keeping its animation.

GoodNotes flattens pasted GIFs to still images, but inserting from Photos
keeps the animation (confirmed on device 2026-09-26).
"""
from pathlib import Path


def save_gif_to_photos(path):
    """Add the GIF at path to the Photos library and return the asset."""
    import photos

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError("No GIF at {}".format(path))
    asset = photos.create_image_asset(str(path))
    if asset is None:
        raise RuntimeError("Photos did not create an asset for {}".format(path.name))
    return asset