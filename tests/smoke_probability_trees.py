"""Probability trees: mathematical and diagram validation."""
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

    from mathsgen.core import require
    from mathsgen.probability_tree_diagrams import (
        check_label_clearance,
        branch_probabilities,
        decimal_if_exact,
    )
    from mathsgen.visuals import VisualFlowable

    generator = registry.get("probability.trees.two_stage")

    checked = 0
    events = set()
    decimal_trees = 0

    for level in range(1, 5):
        for seed in range(50):
            question = generator.generate(seed, level)

            generator.validate_independently(question)
            events.add(question.parameters["event"])

            for mode in ("questions", "answers"):
                for asset in question.visual_assets(mode):
                    for width in (250, 360):
                        check_label_clearance(asset, width)

                        drawing = VisualFlowable(asset)
                        actual_width, actual_height = drawing.wrap(
                            width, 700
                        )

                        require(
                            actual_width <= width
                            and actual_height > 0,
                            "Probability-tree drawing does not fit",
                        )

                        checked += 1

            completed = question.visual_assets("answers")[0]

            labels = [
                node["text"]
                for node in completed["nodes"]
                if node["type"] == "label"
            ]

            if any("." in label for label in labels):
                decimal_trees += 1

            wrong = deepcopy(question.answer)
            wrong["value"] = str(
                Fraction(wrong["value"]) + Fraction(1, 10)
            )

            corrupted = replace(question, answer=wrong)

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
                        "Corrupted probability was accepted"
                    )

        sample = generator.generate(12345, level)

        print("Level", level)
        print(sample.prompt.text)
        print("Answer:", sample.answer_display.text)

    require(
        events == {
            "ordered", "one_each",
            "at_least_one", "conditional",
        },
        "Not all event types were tested",
    )

    require(
        decimal_trees > 0,
        "No trees with decimal probabilities were generated",
    )

    # Check the actual tree model across a wider range of counter counts.
    for red in range(2, 10):
        for blue in range(2, 10):
            for replacement in (False, True):
                probabilities = branch_probabilities(
                    red, blue, replacement
                )

                for index in (0, 2, 4):
                    require(
                        probabilities[index]
                        + probabilities[index + 1] == 1,
                        "Sibling branch probabilities do not sum to one",
                    )

                for probability in probabilities:
                    decimal = decimal_if_exact(probability)

                    if decimal is not None:
                        require(
                            Fraction(decimal) == probability,
                            "Decimal label changes probability",
                        )

    print(
        "PASS: 200 questions, independent enumeration, "
        "corruption rejection and all event types"
    )
    print(
        "PASS:", checked,
        "student/teacher diagram checks at two widths"
    )
    print(
        "PASS: branch sums and exact decimal conversions"
    )


if __name__ == "__main__":
    main()