"""Focused checks for volume relationships, rounding and schematic diagrams."""
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
    from mathsgen.visuals import VisualFlowable
    generator = registry.get("problem_solving.related_solids.volume")
    styles = set()
    shapes = set()
    for level in range(1, 5):
        for seed in range(20):
            q = generator.generate(seed, level)
            generator.validate_independently(q)
            require(q.to_dict() == generator.generate(seed, level).to_dict(), "Not reproducible")
            styles.add(q.parameters["relation"][0])
            shapes.add(q.parameters["known"]["shape"])
            wrong = deepcopy(q.answer)
            wrong["x_1dp"] = format(float(wrong["x_1dp"]) + 0.1, ".1f")
            for checker in (generator.validate, generator.validate_independently):
                try:
                    checker(replace(q, answer=wrong))
                except ValueError:
                    pass
                else:
                    raise AssertionError("Incorrect rounded answer accepted")
            wrong = deepcopy(q.answer)
            wrong["equation"] = "x = 0"
            try:
                generator.validate(replace(q, answer=wrong))
            except ValueError:
                pass
            else:
                raise AssertionError("Incorrect equation accepted")
            for width in (250, 360):
                flowable = VisualFlowable(q.question_visuals[0])
                actual_width, actual_height = flowable.wrap(width, 700)
                require(actual_width <= width and 0 < actual_height < 700, "Diagram does not fit")
        sample = generator.generate(12345, level)
        print("Level", level, sample.prompt.text)
        print("Answer:", sample.answer_display.text)
    require(styles == {"equal", "multiple", "percentage", "ratio"}, "Missing relationship wording")
    require(shapes == {"cuboid", "cylinder", "sphere"}, "Missing solid coverage")
    print("PASS: 80 questions, 160 diagram renders, independent rounding brackets,")
    print("reproducibility, corrupted answers and relationship/solid coverage.")


if __name__ == "__main__":
    main()