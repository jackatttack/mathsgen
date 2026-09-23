"""Check algebraic equivalence, cancellation and original domain retention."""
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
    generator = registry.get("algebra.fractions.manipulation")
    operations = set()
    for level in range(1, 5):
        for seed in range(20):
            q = generator.generate(seed, level)
            generator.validate_independently(q)
            operations.add(q.parameters["operation"])
            corruptions = []
            wrong = deepcopy(q.answer)
            wrong["numerator"][0] += 1
            corruptions.append(wrong)
            wrong = deepcopy(q.answer)
            wrong["excluded"] = wrong["excluded"][1:]
            corruptions.append(wrong)
            wrong = deepcopy(q.answer)
            wrong["numerator"] = [2 * v for v in wrong["numerator"]]
            wrong["denominator"] = [2 * v for v in wrong["denominator"]]
            corruptions.append(wrong)
            for wrong in corruptions:
                for checker in (generator.validate, generator.validate_independently):
                    try:
                        checker(replace(q, answer=wrong))
                    except ValueError:
                        pass
                    else:
                        raise AssertionError("Corruption accepted")
        sample = generator.generate(12345, level)
        print("Level", level, sample.prompt.text)
        print("Answer:", sample.answer_display.text)
    require(operations == {"single", "multiply", "divide", "add", "subtract"},
            "An operation was not exercised")
    print("PASS: 80 questions; equivalence, simplification and domain corruption")


if __name__ == "__main__":
    main()