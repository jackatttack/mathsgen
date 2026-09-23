"""Focused tank checks: water conservation, stages and corrupted answers."""
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
    from mathsgen.core import require, rational_text
    from mathsgen.content_rendering import content_flowables
    from mathsgen.pdf import styles

    generator = registry.get("problem_solving.liquid_flow.tanks")
    for level in range(1, 5):
        for seed in range(20):
            q = generator.generate(seed, level)
            generator.validate_independently(q)
            require(q.to_dict() == generator.generate(seed, level).to_dict(), "Not reproducible")
            fields = ["width", "litres_added"] if level == 3 else [
                "total_minutes", "first_litres", "remaining_litres", "after_minutes",
            ]
            for field in fields:
                wrong = deepcopy(q.answer)
                wrong[field] = rational_text(Fraction(wrong[field]) + 1)
                for checker in (generator.validate, generator.validate_independently):
                    try:
                        checker(replace(q, answer=wrong))
                    except ValueError:
                        pass
                    else:
                        raise AssertionError("Corrupted " + field + " accepted")
            for content in (q.prompt, q.answer_display):
                for flowable in content_flowables(content, styles()["body"]):
                    flowable.wrap(460, 700)
        sample = generator.generate(12345, level)
        print("Level", level, sample.prompt.text)
        print("Answer:", sample.answer_display.text)
    print("PASS: 80 questions, independent water conservation, corruption rejection,")
    print("reproducibility and rich-content width checks.")


if __name__ == "__main__":
    main()