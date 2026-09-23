"""Check scaling structures, reversed labels and nonsimplified answers."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from launch_mathsgen import load_engine


def reject(check, question):
    try:
        check(question)
    except ValueError:
        return
    raise AssertionError("Incorrect ratio accepted")


def main():
    registry = load_engine()
    generator = registry.get("ratio.combining.three_part")
    for level in range(1, 5):
        seed = 12345
        question = generator.generate(seed, level)
        while "context" in question.parameters:  # worded: smoke_ratio_number_contexts.py
            seed += 1
            question = generator.generate(seed, level)
        generator.validate_independently(question)
        print("Level {}: {}".format(level, question.prompt.text))
        print("Answer: " + question.answer_display.text)
        values = question.answer["parts"]
        for bad_parts in (
            [values[0] + 1, values[1], values[2]],
            [2 * value for value in values],
        ):
            corrupted = replace(
                question, answer=dict(question.answer, parts=bad_parts)
            )
            reject(generator.validate, corrupted)
            reject(generator.validate_independently, corrupted)

    from mathsgen.core import Content
    from mathsgen.combine_ratios import prompt_for
    # A:B=2:3 and C:B=5:4 gives A:B:C=8:12:15.
    base = generator.generate(0, 4)
    known = replace(
        base,
        parameters={"first": [2, 3], "second": [5, 4], "reversed_pair": True},
        prompt=prompt_for([2, 3], [5, 4], True),
        answer={"kind": "ratio", "labels": ["A", "B", "C"], "parts": [8, 12, 15]},
        answer_display=Content("8 : 12 : 15"),
    )
    generator.validate(known)
    generator.validate_independently(known)
    wrong_order = replace(
        known, parameters=dict(known.parameters, reversed_pair=False)
    )
    reject(generator.validate, wrong_order)
    reject(generator.validate_independently, wrong_order)
    print("PASS: all four structures, known reversed pair and corruption rejection.")


if __name__ == "__main__":
    main()