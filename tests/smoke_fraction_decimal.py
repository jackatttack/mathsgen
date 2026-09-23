"""Check exact decimal conversion, recurring rejection and corrupt answers."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from fractions import Fraction
from mathsgen_cli import main as run_cli


def main():
    # Refresh project imports using the established entrypoint.
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        status = run_cli(["info", "number.fdp.fraction_to_decimal", "--json"])
    if status:
        raise AssertionError("Generator discovery failed")

    from mathsgen.core import require
    from mathsgen.fraction_decimal import FractionToDecimal, terminating_decimal

    examples = {
        Fraction(1, 8): "0.125",
        Fraction(1, 125): "0.008",
        Fraction(-33, 16): "-2.0625",
        Fraction(7, 4): "1.75",
    }
    for value, expected in examples.items():
        require(terminating_decimal(value) == expected, "Exact decimal formatting failed")
    try:
        terminating_decimal(Fraction(1, 3))
    except ValueError:
        pass
    else:
        raise AssertionError("Recurring decimal was accepted")

    generator = FractionToDecimal()
    for level in range(1, 5):
        question = generator.generate(12345, level)
        generator.validate_independently(question)
        print("Level {}: {} Answer: {}".format(
            level, question.prompt.text, question.answer_display.text
        ))
        try:
            generator.validate(replace(
                question, answer={"kind": "decimal", "value": "99.99"}
            ))
        except ValueError:
            pass
        else:
            raise AssertionError("Incorrect answer was accepted")
    print("PASS: exact digits, leading zeros, negative values and rejection checks.")


if __name__ == "__main__":
    main()