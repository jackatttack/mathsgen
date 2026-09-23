"""Export orchestration. Renderers receive the same completed worksheet."""
import json
from pathlib import Path
import shutil
import tempfile

from .core import require


def export_worksheet(worksheet, output_root, answers=False, worked=False, backend="reportlab"):
    """Create a new export folder; never overwrite an earlier worksheet.

    Each successful export includes the question PDF and a teacher manifest.
    Optional answer and worked-solution PDFs use identical question ordering.
    The manifest contains answers and should not be distributed to students.
    Failed exports remove only the new folder created by this call.
    """
    require(backend == "reportlab", "Unsupported PDF backend: " + backend)
    if worked:
        missing = sorted({
            question.generator_id for question in worksheet.questions
            if not question.worked_solution
        })
        require(
            not missing,
            "Worked solutions are not available for: " + ", ".join(missing)
            + ". Export questions and answers instead.",
        )
    from .pdf import render_pdf

    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    destination = Path(tempfile.mkdtemp(
        prefix="worksheet_" + worksheet.id[:10] + "_",
        dir=str(output_root),
    ))
    modes = ["questions"]
    if answers:
        modes.append("answers")
    if worked:
        modes.append("worked")
    try:
        reports = [
            render_pdf(worksheet, destination / (mode + ".pdf"), mode)
            for mode in modes
        ]
        manifest = destination / "teacher_manifest.json"
        with manifest.open("w", encoding="utf-8") as output:
            json.dump(worksheet.to_dict(), output, indent=2, ensure_ascii=False)
        result = {
            "worksheet_id": worksheet.id,
            "seed": worksheet.seed,
            "question_count": len(worksheet.questions),
            "directory": str(destination),
            "teacher_manifest": str(manifest),
            "backend": backend,
            "pdfs": reports,
            "visual_review": "pending",
        }
        with (destination / "export_report.json").open("w", encoding="utf-8") as output:
            json.dump(result, output, indent=2, ensure_ascii=False)
        return result
    except Exception:
        shutil.rmtree(str(destination))
        raise