"""Check harder task structures, corruption rejection and PDF notation."""
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
    generator = registry.get("algebra.linear.two_sided")
    from mathsgen.core import Content, rational_text, require
    from mathsgen.linear_harder_forms import check_structure
    from mathsgen.pdf import MathLine

    def rejects(q):
        try:
            generator.validate(q)
        except ValueError:
            return
        raise AssertionError("Corrupted question was accepted")

    for level in (3, 4):
        signs = set()
        for seed in range(100):
            q = generator.generate(seed, level)
            generator.validate_independently(q)
            p = q.parameters
            if "context" in p:
                continue  # worded forms are covered by smoke_linear_contexts.py
            check_structure(p, level)
            if level == 3:
                signs.add(p["n"] > 0)
            MathLine(q.prompt.math_tex).wrap(460, 800)
            wrong = Fraction(q.answer["values"]["x"]) + 1
            rejects(replace(q, answer={
                "kind": "variable_values",
                "values": {"x": rational_text(wrong)},
            }))
            rejects(replace(q, prompt=Content("Solve for x: x = 0")))
            altered = dict(p, d=p["d"] + 1)
            rejects(replace(q, parameters=altered))
        if level == 3:
            require(signs == {False, True}, "Missing negative-multiplier coverage")
        q = generator.generate(17, level)
        print(q.prompt.text)
        print(q.answer_display.text)

    try:
        check_structure({"a": 5, "b": 2, "c": 5, "d": -3,
                         "m": 5, "n": 5}, 3)
    except ValueError:
        pass
    else:
        raise AssertionError("Matching outer multipliers were accepted")
    print("PASS: task structures, signed brackets, independent answers,")
    print("wrong-answer/prompt/parameter rejection and MathText widths.")


if __name__ == "__main__":
    main()