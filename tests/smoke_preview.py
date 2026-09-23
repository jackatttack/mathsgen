"""Verify preview routing and exact preservation without rendering new PDFs."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from launch_mathsgen import load_engine


def main():
    load_engine()
    from mathsgen.preview import create_preview, save_preview

    with patch("mathsgen.preview.export_worksheet") as renderer:
        sentinel = object()
        create_preview(sentinel, answers=True)
        args, kwargs = renderer.call_args
        assert args[0] is sentinel
        assert args[1] == Path(tempfile.gettempdir()) / "mathsgen_previews"
        assert kwargs == {"answers": True}

    with tempfile.TemporaryDirectory(prefix="mathsgen_save_test_") as folder:
        root = Path(folder)
        source = root / "preview"
        source.mkdir()
        questions = b"%PDF-test-question-bytes"
        answers = b"%PDF-test-answer-bytes"
        manifest = b'{"seed": 12345, "questions": ["exact snapshot"]}'
        (source / "questions.pdf").write_bytes(questions)
        (source / "answers.pdf").write_bytes(answers)
        (source / "teacher_manifest.json").write_bytes(manifest)
        report = {
            "directory": str(source),
            "teacher_manifest": str(source / "teacher_manifest.json"),
            "worksheet_id": "test",
            "seed": 12345,
            "question_count": 1,
            "pdfs": [
                {"mode": mode, "path": str(source / (mode + ".pdf"))}
                for mode in ("questions", "answers")
            ],
        }
        original = json.dumps(report, sort_keys=True)
        destination = root / "exports"
        saved = save_preview(report, destination)
        assert json.dumps(report, sort_keys=True) == original
        assert Path(saved["directory"]).parent == destination
        for item, expected in zip(saved["pdfs"], (questions, answers)):
            assert Path(item["path"]).read_bytes() == expected
        assert Path(saved["teacher_manifest"]).read_bytes() == manifest
        assert (source / "questions.pdf").read_bytes() == questions
        disk_report = json.loads(
            (Path(saved["directory"]) / "export_report.json").read_text()
        )
        assert disk_report == saved

        second = save_preview(report, destination)
        assert second["directory"] != saved["directory"]
        before = set(destination.iterdir())
        with patch("mathsgen.preview.shutil.copyfile", side_effect=OSError("test")):
            try:
                save_preview(report, destination)
            except OSError:
                pass
            else:
                raise AssertionError("Copy failure was hidden")
        assert set(destination.iterdir()) == before
        assert Path(saved["pdfs"][0]["path"]).read_bytes() == questions
        assert (source / "questions.pdf").exists()

    print("PASS: previews route to OS temporary storage.")
    print("PASS: saved PDFs and manifest preserve exact bytes; paths are updated.")
    print("PASS: repeat saves never overwrite; failed copies preserve existing files.")
    print("Device check: generate, open, save, then reopen both PDFs.")


if __name__ == "__main__":
    main()