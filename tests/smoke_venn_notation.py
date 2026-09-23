"""Targeted mathematical and PDF-rendering checks for Venn notation."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from copy import deepcopy
from dataclasses import replace

from launch_mathsgen import load_engine


def main():
    registry = load_engine()

    from mathsgen.core import require
    from mathsgen.venn_notation import NOTATION, LEVEL_KEYS
    from mathsgen.visuals import drawing_for

    generator = registry.get("probability.venn.notation")
    seen = {level: set() for level in LEVEL_KEYS}
    checked = 0
    rendered = 0

    for level in range(1, 5):
        for seed in range(200):
            question = generator.generate(seed, level)
            generator.validate_independently(question)
            seen[level].add(question.parameters["key"])
            checked += 1

            for mode in ("questions", "answers"):
                for asset in question.visual_assets(mode):
                    for width in (250, 360):
                        drawing = drawing_for(asset, width)
                        require(
                            drawing.width == width and drawing.height > 0,
                            "Invalid Venn drawing",
                        )
                        rendered += 1

            wrong = deepcopy(question.answer)

            if wrong["kind"] == "regions":
                wrong["value"] = [
                    index for index in range(4)
                    if index not in wrong["value"]
                ]
            else:
                wrong["regions"] = [
                    index for index in range(4)
                    if index not in wrong["regions"]
                ]

            corrupted = replace(question, answer=wrong)

            for checker in (
                generator.validate,
                generator.validate_independently,
            ):
                try:
                    checker(corrupted)
                except ValueError:
                    pass
                else:
                    raise AssertionError(
                        "Incorrect Venn answer was accepted"
                    )

        sample = generator.generate(12345, level)
        print(
            "Level", level, "|", sample.prompt.text,
            "| answer:", sample.answer_display.text,
        )

    for level, keys in LEVEL_KEYS.items():
        require(
            seen[level] == set(keys),
            "Some notation variants were not sampled",
        )

    print("PASS:", checked, "questions and independent checks")
    print("PASS:", rendered, "student/answer diagram renders")
    print("PASS: all notation variants sampled and corruption rejected")


if __name__ == "__main__":
    main()