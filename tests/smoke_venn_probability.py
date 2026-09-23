"""Independent probability, corruption and two-width diagram checks."""
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
    from mathsgen.venn_probability import (
        LEVEL_KEYS, CONDITIONAL, event_regions,
    )
    from mathsgen.visuals import drawing_for

    generator = registry.get("probability.venn.probabilities")
    checked = 0
    rendered = 0
    seen = {level: set() for level in LEVEL_KEYS}

    for level in range(1, 5):
        for seed in range(200):
            question = generator.generate(seed, level)
            generator.validate_independently(question)
            seen[level].add(question.parameters["event"])

            for mode in ("questions", "answers"):
                for asset in question.visual_assets(mode):
                    for width in (250, 360):
                        drawing = drawing_for(asset, width)
                        require(
                            drawing.width == width and drawing.height > 0,
                            "Venn probability diagram failed to render",
                        )
                        rendered += 1

            corrupted_answer = deepcopy(question.answer)
            corrupted_answer["value"] = rational_text(
                Fraction(corrupted_answer["value"]) + Fraction(1, 10)
            )
            corrupted = replace(
                question, answer=corrupted_answer
            )
            for checker in (
                generator.validate,
                generator.validate_independently,
            ):
                try:
                    checker(corrupted)
                except ValueError:
                    pass
                else:
                    raise AssertionError(
                        "Incorrect Venn probability was accepted"
                    )

            checked += 1

        sample = generator.generate(12345, level)
        print(
            "Level", level,
            "| event:", sample.parameters["event"],
            "| counts:", sample.parameters["counts"],
            "| answer:", sample.answer_display.text,
        )

    for level, variants in LEVEL_KEYS.items():
        require(
            seen[level] == set(variants),
            "Missing Venn probability variants at level " + str(level),
        )

    # For conditional events the favourable region must be entirely
    # contained within the group specified after "given".
    for key in CONDITIONAL:
        favourable, given = event_regions(key)
        require(
            set(favourable) <= set(given),
            "Conditional event is outside its given population",
        )

    print("PASS:", checked, "independently checked probability questions")
    print("PASS:", rendered, "student/answer diagram renders")
    print("PASS: all events sampled and corrupted answers rejected")


if __name__ == "__main__":
    main()