"""Known cases distinguish shared factors, repeated powers and common multiples."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.catalogue import source_registry
    registry = source_registry(registry)
    from mathsgen.core import require
    from mathsgen.prime_factors import common_value, factorise

    require(factorise(360) == {2: 3, 3: 2, 5: 1}, "Repeated-prime case failed")
    require(common_value([12, 18], "hcf") == 6, "HCF case failed")
    require(common_value([12, 18], "lcm") == 36, "LCM case failed")
    require(common_value([30, 42, 70], "hcf") == 2, "Three-number HCF failed")
    require(common_value([30, 42, 70], "lcm") == 210, "Three-number LCM failed")

    for generator_id in (
        "number.primes.factorisation", "number.factors.hcf", "number.multiples.lcm"
    ):
        generator = registry.get(generator_id)
        for level in range(1, 5):
            question = generator.generate(12345, level)
            generator.validate_independently(question)
            wrong = (
                {"kind": "prime_factorisation", "factors": {"2": 20}}
                if question.answer["kind"] == "prime_factorisation"
                else {"kind": "integer", "value": 999999}
            )
            try:
                generator.validate(replace(question, answer=wrong))
            except ValueError:
                pass
            else:
                raise AssertionError("Corrupted answer accepted")
        print(generator.info.title)
        print(question.prompt.text)
        print("Answer: " + question.answer_display.text)
    print("PASS: known cases and corrupt-answer rejection for all levels.")


if __name__ == "__main__":
    main()