"""Averages and range v2: known cases, focused checks and a specimen PDF."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

import tempfile
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

from launch_mathsgen import load_engine


SEEDS = 40
INDEPENDENT_SEEDS = 8
SPECIMEN_SEEDS = (5, 6, 7)
VALUE_KEYS = ("values", "known", "hidden", "numbers")


def rejects(generator, question, reason):
    try:
        generator.validate(question)
    except ValueError:
        return
    raise AssertionError("{} accepted {}".format(generator.info.id, reason))


def check_known_cases():
    from mathsgen.median_range import (
        decimal_text, matching_hidden_sets, median_value, mode_value,
    )

    def fractions(*numbers):
        return [Fraction(number) for number in numbers]

    assert median_value(fractions(3, 1, 2)) == 2, "Odd median failed"
    assert median_value(fractions(1, 2, 3, 8)) == Fraction(5, 2), "Even midpoint failed"
    assert median_value(fractions(-5, 5)) == 0, "Signed midpoint failed"
    assert mode_value(fractions(1, 2, 2, 3)) == 2, "Single mode failed"
    assert mode_value(fractions(1, 2, 3)) is None, "No-mode case failed"
    assert mode_value(fractions(1, 1, 2, 2)) is None, "Two-mode case failed"
    assert decimal_text(Fraction(5, 2)) == "2.5", "Half formatting failed"
    assert decimal_text(Fraction(-13, 4)) == "-3.25", "Quarter formatting failed"

    # Three numbers: median 6, mean 7, range 9 -> 3, 6, 12 only.
    three = {"mean": Fraction(7), "median": Fraction(6), "range": Fraction(9)}
    assert matching_hidden_sets(3, [], three) == [[3, 6, 12]], "Three-number case failed"
    # Cards 3, 8, 8 and two face down; mean 7, range 9 -> 4 and 12 only.
    cards = {"mean": Fraction(7), "range": Fraction(9)}
    assert matching_hidden_sets(2, fractions(3, 8, 8), cards) == [[4, 12]], "Card case failed"
    # Four numbers with only mean 5 and range 4 are ambiguous.
    loose = {"mean": Fraction(5), "range": Fraction(4)}
    assert len(matching_hidden_sets(4, [], loose)) > 1, "Ambiguity was not detected"
    print("Known cases: PASS")


def main():
    load_engine()
    from mathsgen.core import rational_text
    from mathsgen.median_range import MedianAndRange
    from mathsgen.pdf import render_pdf

    check_known_cases()
    generator = MedianAndRange()
    specimen = []
    for level in (1, 2, 3, 4):
        prompts, forms = set(), {}
        for seed in range(SEEDS):
            q = generator.generate(seed, level)
            if seed < INDEPENDENT_SEEDS:
                generator.validate_independently(q)
            prompts.add(q.prompt.text)
            form = q.parameters["form"]
            forms[form] = forms.get(form, 0) + 1

            wrong = dict(q.answer)
            first_key = sorted(key for key in wrong if key != "kind")[0]
            wrong[first_key] = "999"
            rejects(generator, replace(q, answer=wrong), "a wrong answer")
            rejects(generator, replace(q, prompt=replace(q.prompt, text=q.prompt.text + " ")),
                    "an altered prompt")
            for key in VALUE_KEYS:
                if key in q.parameters:
                    altered = dict(q.parameters)
                    values = list(altered[key])
                    values[0] = rational_text(Fraction(values[0]) + 1)
                    altered[key] = values
                    rejects(generator, replace(q, parameters=altered),
                            "an altered {} value".format(key))
        for seed in SPECIMEN_SEEDS:
            specimen.append(generator.generate(seed, level))
        sample = specimen[-1]
        print("L{} ({} distinct / {}, forms {}):\n  {}\n  -> {}".format(
            level, len(prompts), SEEDS, forms, sample.prompt.text, sample.answer_display.text))

    export_root = Path(__file__).resolve().parent.parent / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="averages_range_", dir=str(export_root)))
    worksheet = SimpleNamespace(title="Averages and range specimen", id="averages-range-specimen",
                                specification={}, questions=specimen)
    for mode in ("questions", "answers"):
        print(render_pdf(worksheet, directory / (mode + ".pdf"), mode))
    print("PASS: averages and range v2.")


if __name__ == "__main__":
    main()