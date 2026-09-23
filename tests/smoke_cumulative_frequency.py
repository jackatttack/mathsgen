"""Cumulative frequency: difficulty, mathematics and diagram smoke checks."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from copy import deepcopy
from dataclasses import replace
from fractions import Fraction

from launch_mathsgen import load_engine


def main():
    registry = load_engine()

    from mathsgen.core import require
    from mathsgen.visuals import VisualFlowable

    generator = registry.get("data.cumulative_frequency.construction")
    reading_types = set()

    for level in range(1, 5):
        for seed in range(50):
            question = generator.generate(seed, level)
            generator.validate_independently(question)

            if level == 4:
                reading_types.add(question.parameters["reading"])

            for mode in ("questions", "answers"):
                for asset in question.visual_assets(mode):
                    for width in (250, 360):
                        flowable = VisualFlowable(asset)
                        actual_width, actual_height = flowable.wrap(width, 700)
                        require(actual_width <= width and actual_height > 0,
                                "Visual does not fit the requested width")

            corruptions = []

            wrong = deepcopy(question.answer)
            wrong["totals"][0] += 1
            corruptions.append(wrong)

            if level >= 2:
                wrong = deepcopy(question.answer)
                wrong["points"][1][1] += 1
                corruptions.append(wrong)

            if level == 3:
                wrong = deepcopy(question.answer)
                wrong["iqr"] = str(Fraction(wrong["iqr"]) + 1)
                corruptions.append(wrong)

            if level == 4:
                wrong = deepcopy(question.answer)
                wrong["value"] = str(Fraction(wrong["value"]) + 1)
                corruptions.append(wrong)

            for wrong in corruptions:
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
                        raise AssertionError("Corrupted answer accepted")

        sample = generator.generate(12345, level)
        print("Level", level, sample.prompt.text)
        print("Answer:", sample.answer_display.text)

    require(
        reading_types == {"above", "percentile"},
        "Level 4 did not cover both interpretation types",
    )

    print(
        "PASS: 200 questions, four levels, independent mathematics, "
        "corruption rejection and student/teacher visuals at two widths"
    )


if __name__ == "__main__":
    main()