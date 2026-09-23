"""iOS adapter. Importing this module does not import Pythonista-only modules."""
import io
from pathlib import Path


def pdf_to_image(path, size):
    import ctypes
    from PIL import Image, ImageChops, ImageOps
    from objc_util import (
        ObjCClass, CGSize, nsurl, on_main_thread, uiimage_to_png,
    )
    ctypes.CDLL("/System/Library/Frameworks/PDFKit.framework/PDFKit")
    outcome = {}

    @on_main_thread
    def raster():
        document = None
        try:
            document = ObjCClass("PDFDocument").alloc().initWithURL_(
                nsurl(str(path))
            )
            if document is None or document.pageCount() != 1:
                raise RuntimeError("Expected a readable, single-page card PDF.")
            page = document.pageAtIndex_(0)
            image = page.thumbnailOfSize_forBox_(
                CGSize(size[0] * 3, size[1] * 3), 0
            )
            if image is None:
                raise RuntimeError("PDFKit returned no image.")
            outcome["png"] = uiimage_to_png(image)
        except Exception as error:
            outcome["error"] = str(error)
        finally:
            if document is not None:
                document.release()

    raster()
    if "png" not in outcome:
        raise RuntimeError(outcome.get("error", "PDF raster callback did not complete."))

    rgba = Image.open(io.BytesIO(outcome["png"])).convert("RGBA")
    white = Image.new("RGBA", rgba.size, "white")
    white.alpha_composite(rgba)
    rgb = white.convert("RGB")
    difference = ImageChops.difference(
        rgb, Image.new("RGB", rgb.size, "white")
    ).convert("L")
    box = difference.point(lambda value: 255 if value > 15 else 0).getbbox()
    if box is None:
        raise RuntimeError("Rendered card was blank.")
    box = (
        max(0, box[0] - 3), max(0, box[1] - 3),
        min(rgb.width, box[2] + 3), min(rgb.height, box[3] + 3),
    )
    return ImageOps.expand(rgb.crop(box), border=24, fill="white")


def copy_png(path):
    from objc_util import ObjCClass, on_main_thread
    path = Path(path)
    outcome = {}

    @on_main_thread
    def put_image():
        try:
            image = ObjCClass("UIImage").imageWithContentsOfFile_(str(path))
            if image is None:
                raise RuntimeError("iOS could not load the saved PNG.")
            pasteboard = ObjCClass("UIPasteboard").generalPasteboard()
            before = pasteboard.changeCount()
            pasteboard.setImage_(image)
            if pasteboard.changeCount() == before:
                raise RuntimeError("Clipboard did not change.")
            if not pasteboard.hasImages() or pasteboard.image() is None:
                raise RuntimeError("Clipboard did not retain an image.")
            outcome["ok"] = True
        except Exception as error:
            outcome["error"] = str(error)

    put_image()
    if not outcome.get("ok"):
        raise RuntimeError(outcome.get("error", "Clipboard callback did not complete."))