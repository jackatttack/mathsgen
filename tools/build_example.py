"""Rebuild the public example PDFs with the release engine and a fixed seed."""
from pathlib import Path
import shutil
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
CORE = str(ROOT / "core")
if CORE not in sys.path:
    sys.path.insert(0, CORE)

SAMPLE = (
    ("algebra.expressions.like_terms", 4),
    ("algebra.rearranging.changing_subject", 3),
    ("geometry.trigonometry.cosine_rule", 2),
    ("geometry.circle_theorems.centre_angle", 2),
    ("probability.venn.probabilities", 3),
)


def main():
    from mathsgen.catalogue import build_registry
    from mathsgen.export import export_worksheet
    from mathsgen.worksheets import Worksheet

    registry = build_registry()
    questions = tuple(
        registry.get(generator_id).generate(seed=7, difficulty=level)
        for generator_id, level in SAMPLE
    )
    for question in questions:
        registry.get(question.generator_id).validate(question)

    worksheet = Worksheet(
        id="mathsgen-public-example-20260923",
        title="MathsGen: Mixed GCSE Practice",
        seed=7,
        specification={"theme": "calm", "show_source": True},
        questions=questions,
    )
    examples = ROOT / "examples"
    examples.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mathsgen_example_") as temporary:
        report = export_worksheet(worksheet, temporary, answers=True)
        for item in report["pdfs"]:
            source = Path(item["path"])
            destination = examples / source.name
            shutil.copy2(str(source), str(destination))
            print(destination.name, destination.stat().st_size, "bytes")

    print("Example:", len(questions), "questions; answer key included")
    print("PDF actions target local mathsgen/tools/mathsgen_action.py")


if __name__ == "__main__":
    main()