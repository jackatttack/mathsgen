"""Check varied trigonometry diagrams, answers and a printable specimen."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import tempfile
from dataclasses import replace
from fractions import Fraction
from types import SimpleNamespace

from launch_mathsgen import load_engine


def rejects(generator, question, label):
    try:
        generator.validate(question)
    except ValueError:
        return
    raise AssertionError("{} was accepted".format(label))


def main():
    registry = load_engine()
    from mathsgen.visuals import drawing_for
    from mathsgen.pdf import render_pdf

    generator = registry.get("geometry.trigonometry.right_angled")
    specimen = []
    for level in range(1, 5):
        orientations = set()
        for seed in range(40):
            question = generator.generate(seed, level)
            assert "horizontal side" not in question.prompt.text
            assert "vertical side" not in question.prompt.text
            assert "slanted side" not in question.prompt.text
            generator.validate(question)
            if seed < 8:
                generator.validate_independently(question)
            orientation = question.parameters["orientation"]
            orientations.add(tuple(orientation))
            for width in (360, 250):
                drawing_for(question.question_visuals[0], width)
            if seed == 0:
                specimen.append(question)
                altered = json.loads(json.dumps(question.parameters))
                altered["orientation"] = [999, False]
                rejects(generator, replace(question, parameters=altered),
                        "unknown orientation")
                wrong = dict(question.answer)
                wrong["value"] = str(Fraction(wrong["value"]) + 1)
                rejects(generator, replace(question, answer=wrong),
                        "incorrect answer")
        assert len(orientations) >= 3, (
            "Level {} has too little diagram variation".format(level)
        )
        print("L{}: {} orientations in 40 seeds; {}".format(
            level, len(orientations), specimen[-1].prompt.text))

    export_root = PROJECT_ROOT / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(
        prefix="trigonometry_v4_specimen_", dir=str(export_root)))
    worksheet = SimpleNamespace(
        title="Trigonometry diagram specimen", id="trig-v4",
        specification={}, questions=specimen)
    print(render_pdf(worksheet, directory / "questions.pdf", "questions"))
    print("PASS: four levels, independent answers, diagram widths, rejection, specimen.")


if __name__ == "__main__":
    main()