"""Temporary PDF previews and explicit preservation of their exact bytes."""
import copy
import json
from pathlib import Path
import shutil
import tempfile

from .export import export_worksheet


def create_preview(worksheet, answers=False):
    """Use OS temporary storage; no automatic permanent project export."""
    root = Path(tempfile.gettempdir()) / "mathsgen_previews"
    return export_worksheet(worksheet, root, answers=answers)


def save_preview(report, output_root):
    """Copy an existing preview without regenerating questions or rendering.

    Return a report pointing to the permanent copies. A failed copy removes
    only the new destination created here; the preview remains available.
    """
    source = Path(report["directory"]).resolve()
    files = []
    modes = set()
    for item in report["pdfs"]:
        mode = item["mode"]
        if mode not in ("questions", "answers", "worked") or mode in modes:
            raise ValueError("Invalid or duplicate PDF mode")
        modes.add(mode)
        path = Path(item["path"]).resolve()
        if path.parent != source or not path.is_file():
            raise ValueError("Preview PDF is missing or outside its folder")
        files.append((path, mode + ".pdf"))
    if "questions" not in modes:
        raise ValueError("Preview has no question PDF")
    manifest = Path(report["teacher_manifest"]).resolve()
    if manifest.parent != source or not manifest.is_file():
        raise ValueError("Preview manifest is missing or outside its folder")
    files.append((manifest, "teacher_manifest.json"))

    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    destination = Path(tempfile.mkdtemp(prefix="saved_worksheet_", dir=str(root)))
    try:
        for path, filename in files:
            shutil.copyfile(str(path), str(destination / filename))
        saved = copy.deepcopy(report)
        saved["directory"] = str(destination)
        saved["teacher_manifest"] = str(destination / "teacher_manifest.json")
        for item in saved["pdfs"]:
            item["path"] = str(destination / (item["mode"] + ".pdf"))
        saved["storage"] = "saved"
        with (destination / "export_report.json").open("w", encoding="utf-8") as output:
            json.dump(saved, output, indent=2, ensure_ascii=False)
        return saved
    except Exception:
        shutil.rmtree(str(destination))
        raise