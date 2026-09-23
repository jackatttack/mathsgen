"""Check paired solutions and reject omissions, duplicates and mismatching."""
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
    from mathsgen.core import rational_text
    generator = registry.get("algebra.simultaneous.linear_quadratic")
    for level in range(1, 5):
        for seed in range(50):
            q = generator.generate(seed, level)
            generator.validate_independently(q)
            corruptions = []
            wrong = deepcopy(q.answer)
            wrong["pairs"].pop()
            corruptions.append(wrong)
            wrong = deepcopy(q.answer)
            wrong["pairs"][1] = wrong["pairs"][0][:]
            corruptions.append(wrong)
            wrong = deepcopy(q.answer)
            wrong["pairs"][0][1], wrong["pairs"][1][1] = (
                wrong["pairs"][1][1], wrong["pairs"][0][1]
            )
            corruptions.append(wrong)
            wrong = deepcopy(q.answer)
            wrong["pairs"][0][0] = rational_text(Fraction(wrong["pairs"][0][0]) + 1)
            corruptions.append(wrong)
            for wrong in corruptions:
                for checker in (generator.validate, generator.validate_independently):
                    try:
                        checker(replace(q, answer=wrong))
                    except ValueError:
                        pass
                    else:
                        raise AssertionError("Corrupted pairs accepted")
        sample = generator.generate(12345, level)
        print("Level", level, sample.prompt.text)
        print("Answer:", sample.answer_display.text)
    print("PASS: 200 systems; exact completeness and paired-answer corruption")


if __name__ == "__main__":
    main()