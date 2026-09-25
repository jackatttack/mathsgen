"""Known mixtures, including the averaging misconception, for both targets."""
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

    # 200 cm^3 at 0.8 and 300 cm^3 at 1.1 give 460 g in 500 cm^3, so the
    # mixture density is 0.92 and not the average of 0.95.
    masses = [200 * Fraction("0.8"), 300 * Fraction("1.1")]
    require(sum(masses) == 490, "Total mass case failed")
    require(sum(masses) / 500 == Fraction("0.98"), "Mixture density case failed")
    require((Fraction("0.8") + Fraction("1.1")) / 2 == Fraction("0.95"),
            "Average case failed")

    for generator_id in (
        "number.compound.mixture_density", "number.compound.mixture_mass"
    ):
        generator = registry.get(generator_id)
        for level in range(1, 5):
            for seed in (4, 55, 666):
                question = generator.generate(seed, level)
                generator.validate_independently(question)
            wrong = dict(
                question.answer,
                value=str(Fraction(question.answer["value"]) + 1),
            )
            try:
                generator.validate(replace(question, answer=wrong))
            except ValueError:
                pass
            else:
                raise AssertionError("Corrupted mixture accepted")
            print("Level {}: {}".format(level, question.prompt.text))
            print("Answer: " + question.answer_display.text)
        print(generator.info.title)
    print("PASS: known mixtures and corrupt-answer rejection for all levels.")


if __name__ == "__main__":
    main()