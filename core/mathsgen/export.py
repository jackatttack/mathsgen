"""Export orchestration. Renderers receive the same completed worksheet."""
import json
from pathlib import Path
import shutil
import tempfile

from .core import require


# --- Editable file naming ---------------------------------------------------
# A worksheet with at most this many subtopics is named by subtopic;
# beyond it the name falls back to topics (5xNumber_11xAlgebra).
NAME_SUBTOPIC_LIMIT = 3
# Topics shown before the rest are summarised as "+N-more".
NAME_TOPIC_LIMIT = 3


def name_label(key):
    """Turn an identifier such as box_plots into a filename word: Box-plots."""
    text = str(key or "questions").strip().lower()
    cleaned = "".join(
        character if character.isalnum() else "-" for character in text
    ).strip("-")
    return (cleaned or "questions").capitalize()


def counted_labels(keys, limit):
    """Count keys in first-appearance order, e.g. ["3xBox-plots", "+2-more"]."""
    counts = {}
    for key in keys:
        counts[key] = counts.get(key, 0) + 1
    ordered = list(counts)
    labels = [
        "{}x{}".format(counts[key], name_label(key)) for key in ordered[:limit]
    ]
    if len(ordered) > limit:
        labels.append("+{}-more".format(len(ordered) - limit))
    return labels


def worksheet_file_stem(worksheet):
    """A readable name built from the worksheet's own questions.

    Example: 4xBox-plots_6xPercentages_L1-3. Used for the export folder and
    every PDF, so worksheets can be told apart once opened, shared or saved.
    The worksheet id and seed stay in the manifest and export report.
    """
    questions = list(worksheet.questions)
    if not questions:
        return "Worksheet"
    subtopics = [question.subtopic for question in questions]
    if len(set(subtopics)) <= NAME_SUBTOPIC_LIMIT:
        parts = counted_labels(subtopics, NAME_SUBTOPIC_LIMIT)
    else:
        parts = counted_labels(
            [question.topic for question in questions], NAME_TOPIC_LIMIT
        )
    levels = [question.difficulty for question in questions]
    low, high = min(levels), max(levels)
    parts.append("L{}".format(low) if low == high else "L{}-{}".format(low, high))
    return "_".join(parts)


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

    if worksheet.specification.get("mode") == "drill":
        # Drill sheets have their own compact layout and no worked solutions.
        require(not worked, "Drill sheets do not have worked solutions.")
        from .drill_pdf import render_drill_pdf as render_pdf
    elif worksheet.specification.get("mode") == "blocks":
        # Block sheets mix question and drill layouts in the teacher's order.
        require(not worked, "Block sheets do not have worked solutions.")
        from .blocks_pdf import render_blocks_pdf as render_pdf

    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    stem = worksheet_file_stem(worksheet)
    destination = Path(tempfile.mkdtemp(
        prefix=stem + "_",
        dir=str(output_root),
    ))
    modes = ["questions"]
    if answers:
        modes.append("answers")
    if worked:
        modes.append("worked")
    try:
        reports = [
            render_pdf(worksheet, destination / "{}_{}.pdf".format(stem, mode), mode)
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