"""Rotation geometry, identification, diagram and corruption checks."""
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
    raise AssertionError("Corruption accepted")


def main():
    registry = load_engine()
    from mathsgen.core import Content, require
    from mathsgen.rotations import allowed_turns
    from mathsgen.visuals import VisualFlowable

    generator = registry.get("geometry.transformations.rotation")
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
            seen.add(question.parameters["rotation"]["turns"])
            corruptions = []
            if level == 4:
                wrong = deepcopy(question.answer)
                wrong["rotation"]["centre"][0] += 1
                corruptions.append(wrong)
                wrong = deepcopy(question.answer)
                wrong["rotation"]["turns"] = wrong["rotation"]["turns"] % 3 + 1
                corruptions.append(wrong)
            else:
                wrong = deepcopy(question.answer)
                wrong["vertices"][0][0] += 1
                corruptions.append(wrong)
                wrong = deepcopy(question.answer)
                wrong["vertices"].pop()
                corruptions.append(wrong)
            for wrong in corruptions:
                for checker in (generator.validate, generator.validate_independently):
                    reject(checker, replace(question, answer=wrong))

            reject(generator.validate, replace(question, prompt=Content("Wrong prompt")))
            reject(generator.validate, replace(question, answer_display=Content("Wrong answer")))
            if level == 4:
                require(
                    question.question_visuals[0]["points"] == [],
                    "Student graph reveals the unknown centre",
                )
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
        require(seen == set(allowed_turns(level)), "Missing angle/direction coverage")
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
        "diagram renders; independent dot/cross-product checks,",
        "reproducibility, angle coverage and corruption rejection.",
    )


if __name__ == "__main__":
    main()