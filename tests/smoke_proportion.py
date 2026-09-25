"""Known proportion relationships, including squares, for both directions."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from fractions import Fraction
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.catalogue import source_registry
    registry = source_registry(registry)
    from mathsgen.core import require
    from mathsgen.proportion import DirectProportion, InverseProportion

    require(DirectProportion.apply(5, 4, 1) == 20, "Direct failed")
    require(DirectProportion.apply(3, 4, 2) == 48, "Direct square failed")
    require(InverseProportion.apply(60, 5, 1) == 12, "Inverse failed")
    require(InverseProportion.apply(100, 5, 2) == 4, "Inverse square failed")
    require(InverseProportion.apply(7, 2, 1) == Fraction(7, 2), "Fractional inverse failed")

    for generator_id in ("ratio.proportion.direct", "ratio.proportion.inverse"):
        generator = registry.get(generator_id)
        for level in range(1, 5):
            for seed in (5, 66, 777):
                question = generator.generate(seed, level)
                generator.validate_independently(question)
            # Perturb the real answer rather than substituting a constant:
            # a fixed value can coincide with the true one and make the
            # rejection test pass without testing anything.
            from fractions import Fraction as _Fraction
            wrong = dict(
                question.answer,
                value=str(_Fraction(question.answer["value"]) + 1),
            )
            try:
                generator.validate(replace(question, answer=wrong))
            except ValueError:
                pass
            else:
                raise AssertionError("Corrupted proportion accepted")
            print("Level {}: {}".format(level, question.prompt.text))
            print("Answer: " + question.answer_display.text)
        print(generator.info.title)
    print("PASS: known relationships and corrupt-answer rejection for all levels.")


if __name__ == "__main__":
    main()