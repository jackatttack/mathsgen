"""Translation and inverse-translation checks with full square diagrams."""
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
    from mathsgen.visuals import VisualFlowable

    generator = registry.get("geometry.transformations.translation")
    checked = 0
    renders = 0
    for level in range(1, 5):
        directions = set()
        for seed in range(100):
            question = generator.generate(seed, level)
            generator.validate_independently(question)
            require(
                question.to_dict() == generator.generate(seed, level).to_dict(),
                "Reproducibility failed",
            )
            vector = question.parameters["vector"]
            directions.add(tuple((value > 0) - (value < 0) for value in vector))
            wrong = deepcopy(question.answer)
            if level == 4:
                wrong["vector"][0] += 1
            else:
                wrong["vertices"][0][0] += 1
            for checker in (generator.validate, generator.validate_independently):
                reject(checker, replace(question, answer=wrong))

            if level != 4:
                missing = deepcopy(question.answer)
                missing["vertices"].pop()
                for checker in (generator.validate, generator.validate_independently):
                    reject(checker, replace(question, answer=missing))
                reject(
                    generator.validate,
                    replace(question, question_visuals=question.answer_visuals),
                )
            if level == 3:
                wrong = deepcopy(question.answer)
                wrong["vertices"] = deepcopy(question.parameters["image"])
                for checker in (generator.validate, generator.validate_independently):
                    reject(checker, replace(question, answer=wrong))
                require(
                    question.question_visuals[0]["curves"][0]["segments"][0][:-1]
                    == question.parameters["image"],
                    "Inverse question must show the image",
                )

            reject(generator.validate, replace(question, prompt=Content("Wrong prompt")))
            reject(generator.validate, replace(question, answer_display=Content("Wrong answer")))
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

        expected = (
            {(1, 0), (-1, 0), (0, 1), (0, -1)}
            if level == 1 else {(1, 1), (1, -1), (-1, 1), (-1, -1)}
        )
        require(directions == expected, "Missing direction coverage")
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
        "diagram renders; independent displacement checks,",
        "inverse construction, reproducibility and corruption rejection.",
    )


if __name__ == "__main__":
    main()