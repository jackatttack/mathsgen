"""Venn reconstruction, exact linear algebra and PDF diagram smoke tests."""
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
    from mathsgen.venn_completion import (
        VARIANTS, rows_from_clues, solve_unique,
    )
    from mathsgen.visuals import drawing_for

    generator = registry.get("probability.venn.completion")
    seen = {level: set() for level in VARIANTS}
    questions = 0
    diagrams = 0

    for level in range(1, 5):
        for seed in range(200):
            question = generator.generate(seed, level)
            generator.validate_independently(question)
            seen[level].add(question.parameters["variant"])

            for mode in ("questions", "answers"):
                for asset in question.visual_assets(mode):
                    for width in (250, 360):
                        drawing = drawing_for(asset, width)
                        require(
                            drawing.width == width and drawing.height > 0,
                            "Completion diagram failed to render",
                        )
                        diagrams += 1

            wrong_answer = deepcopy(question.answer)
            wrong_answer["regions"][0] += 1
            corrupted = replace(question, answer=wrong_answer)

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
                        "Incorrect Venn completion answer was accepted"
                    )

            clues = dict(question.parameters["clues"])
            clues["total"] += 1
            broken = deepcopy(question.parameters)
            broken["clues"] = clues
            corrupted_clue = replace(question, parameters=broken)

            for checker in (
                generator.validate,
                generator.validate_independently,
            ):
                try:
                    checker(corrupted_clue)
                except ValueError:
                    pass
                else:
                    raise AssertionError(
                        "Inconsistent Venn clues were accepted"
                    )

            questions += 1

        sample = generator.generate(12345, level)
        print("Level", level, "|", sample.prompt.text)
        print("Answer:", sample.answer_display.text)

    for level, variants in VARIANTS.items():
        require(
            seen[level] == set(variants),
            "Not all completion variants were sampled",
        )

    # Removing a necessary equation must make the system non-unique.
    sample = generator.generate(98765, 4)
    incomplete = rows_from_clues(
        sample.parameters["clues"], sample.parameters["variant"]
    )[:-1]

    try:
        solve_unique(incomplete)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Insufficient information was accepted as uniquely solvable"
        )

    print("PASS:", questions, "independently reconstructed questions")
    print("PASS:", diagrams, "student/answer diagram renders")
    print("PASS: all variants; corrupted answers/clues rejected")
    print("PASS: underdetermined systems rejected")


if __name__ == "__main__":
    main()