"""Exact expansion, root and vertex corruption checks."""
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
    from mathsgen.core import Content, rational_text, require
    generator = registry.get("algebra.quadratic.completing_square")
    extrema = set()
    for level in range(1, 5):
        for seed in range(50):
            q = generator.generate(seed, level)
            generator.validate_independently(q)
            corruptions = []
            for name in ("a", "shift", "offset"):
                wrong = deepcopy(q.answer)
                wrong["form"][name] = rational_text(Fraction(wrong["form"][name]) + 1)
                corruptions.append(wrong)
            if level == 3:
                extrema.add(q.answer["extremum"])
                for index in (0, 1):
                    wrong = deepcopy(q.answer)
                    wrong["vertex"][index] = rational_text(
                        Fraction(wrong["vertex"][index]) + 1
                    )
                    corruptions.append(wrong)
                wrong = deepcopy(q.answer)
                wrong["extremum"] = (
                    "maximum" if wrong["extremum"] == "minimum" else "minimum"
                )
                corruptions.append(wrong)
            if level == 4:
                wrong = deepcopy(q.answer)
                wrong["roots"][0] += 1
                corruptions.append(wrong)
                wrong = deepcopy(q.answer)
                wrong["roots"][1] += 1
                corruptions.append(wrong)
            for wrong in corruptions:
                for checker in (generator.validate, generator.validate_independently):
                    try:
                        checker(replace(q, answer=wrong))
                    except ValueError:
                        pass
                    else:
                        raise AssertionError("Corrupted answer accepted")
            try:
                generator.validate(replace(q, prompt=Content("Wrong polynomial")))
            except ValueError:
                pass
            else:
                raise AssertionError("Wrong prompt accepted")
        sample = generator.generate(12345, level)
        print("Level", level, sample.prompt.text)
        print("Answer:", sample.answer_display.text)
    require(extrema == {"minimum", "maximum"}, "Missing extremum variation")
    print("PASS: 200 questions; exact checks and corruption rejection")


if __name__ == "__main__":
    main()