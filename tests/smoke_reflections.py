"""Reflection mathematics, corruption rejection and student/teacher plots."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from copy import deepcopy
from dataclasses import replace

from launch_mathsgen import load_engine


def reject(checker, question):
    try:
        checker(question)
    except ValueError:
        return
    raise AssertionError("Corrupted question accepted")


def main():
    registry = load_engine()
    from mathsgen.core import Content, require
    from mathsgen.reflections import allowed_lines
    from mathsgen.visuals import VisualFlowable

    generator = registry.get("geometry.transformations.reflection")
    checked = 0
    renders = 0
    for level in range(1, 5):
        seen = set()
        for seed in range(100):
            question = generator.generate(seed, level)
            generator.validate_independently(question)
            require(
                question.to_dict() == generator.generate(seed, level).to_dict(),
                "Reproducibility failed",
            )
            line = question.parameters["line"]
            seen.add((line["axis"], line["offset"]))

            wrong = deepcopy(question.answer)
            if level == 4:
                if wrong["line"]["axis"] == "diagonal":
                    wrong["line"]["offset"] *= -1
                else:
                    wrong["line"]["offset"] += 1
            else:
                wrong["vertices"][0][0] += 1
            for checker in (generator.validate, generator.validate_independently):
                reject(checker, replace(question, answer=wrong))

            if level != 4:
                missing = deepcopy(question.answer)
                missing["vertices"].pop()
                for checker in (generator.validate, generator.validate_independently):
                    reject(checker, replace(question, answer=missing))

            wrong_parameters = deepcopy(question.parameters)
            wrong_parameters["image"][0][1] += 1
            reject(generator.validate, replace(question, parameters=wrong_parameters))
            reject(
                generator.validate,
                replace(question, answer_display=Content("Incorrect answer")),
            )
            reject(
                generator.validate,
                replace(question, prompt=Content("Incorrect instruction")),
            )
            if level != 4:
                reject(
                    generator.validate,
                    replace(question, question_visuals=question.answer_visuals),
                )

            for mode in ("questions", "answers"):
                for asset in question.visual_assets(mode):
                    for width in (250, 360):
                        flowable = VisualFlowable(asset)
                        actual_width, actual_height = flowable.wrap(width, 700)
                        require(
                            actual_width <= width and 0 < actual_height <= 700,
                            "Diagram does not fit",
                        )
                        renders += 1
            checked += 1

        expected = {
            (line["axis"], line["offset"])
            for line in allowed_lines(level)
        }
        require(seen == expected, "Mirror-line coverage incomplete at level " + str(level))
        sample = generator.generate(12345, level)
        print("Level", level, sample.prompt.text)
        print("Answer:", sample.answer_display.text)

    try:
        generator.generate(0, 1, {"unsupported": True})
    except ValueError:
        pass
    else:
        raise AssertionError("Unsupported settings accepted")

    print(
        "PASS:", checked, "questions;", renders,
        "diagram renders; independent geometry, reproducibility,",
        "line coverage and corruption rejection.",
    )


if __name__ == "__main__":
    main()