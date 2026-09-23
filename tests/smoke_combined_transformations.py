"""Combined transformations: order, intermediate states and exact independent checks."""
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

    generator = registry.get("geometry.transformations.combined")
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
            seen.add(tuple(op["kind"] for op in question.parameters["operations"]))
            fields = ["intermediate", "final"]
            if level == 4:
                fields += ["reverse_intermediate", "reverse_final"]
            for field in fields:
                wrong = deepcopy(question.answer)
                wrong[field][0][0] += 1
                for checker in (generator.validate, generator.validate_independently):
                    reject(checker, replace(question, answer=wrong))
                wrong_parameters = deepcopy(question.parameters)
                wrong_parameters[field][0][1] += 1
                for checker in (generator.validate, generator.validate_independently):
                    reject(checker, replace(question, parameters=wrong_parameters))
            if level == 4:
                wrong = deepcopy(question.answer)
                wrong["same"] = True
                for checker in (generator.validate, generator.validate_independently):
                    reject(checker, replace(question, answer=wrong))
                swapped = deepcopy(question.parameters)
                swapped["operations"].reverse()
                for checker in (generator.validate, generator.validate_independently):
                    reject(checker, replace(question, parameters=swapped))
            reject(generator.validate, replace(question, prompt=Content("Wrong prompt")))
            reject(generator.validate, replace(question, answer_display=Content("Wrong answer")))
            reject(generator.validate, replace(question, question_visuals=question.answer_visuals))
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
            1: {("translation", "translation")},
            2: {("reflection", "translation"), ("translation", "reflection")},
            3: {("rotation", "reflection"), ("rotation", "translation")},
            4: {
                ("reflection", "translation"), ("translation", "reflection"),
                ("rotation", "translation"), ("translation", "rotation"),
            },
        }[level]
        require(seen == expected, "Missing operation-order coverage")
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
        "diagram renders; independent affine composition, intermediate/final",
        "corruption rejection, reverse-order checks and reproducibility.",
    )


if __name__ == "__main__":
    main()