"""Regression checks for ratio sharing and the original money-bound failure."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

import sys
from dataclasses import replace
from fractions import Fraction
from pathlib import Path


def main():
    project_root = str(Path(__file__).resolve().parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    for name in list(sys.modules):
        if name == "mathsgen" or name.startswith("mathsgen."):
            del sys.modules[name]

    from mathsgen.core import require
    from mathsgen.ratio_sharing import RatioSharing

    # Test-only version override recreates the original version-1 RNG
    # contexts. Production remains version 2 with new question identities.
    regression_generator = RatioSharing()
    regression_generator.info = replace(regression_generator.info, version=1)
    previous_failures = (874, 1194, 1402, 1566, 1614, 1898, 2906, 4282, 5306, 5782)
    for seed in previous_failures:
        question = regression_generator.generate(seed, 3)
        require(Fraction(question.parameters["total"]) <= 80, "Money bound regression")
        regression_generator.validate_independently(question)

    generator = RatioSharing()
    require(generator.info.version == 2, "Production version was not updated")
    for level in range(1, 5):
        question = generator.generate(12345, level)
        generator.validate_independently(question)
        wrong_values = dict(question.answer["values"])
        wrong_values["A"] = "9999"
        wrong_answer = dict(question.answer, values=wrong_values)
        try:
            generator.validate(replace(question, answer=wrong_answer))
        except ValueError:
            pass
        else:
            raise AssertionError("Validator accepted a corrupt share")
        print("Level {}: {}".format(level, question.prompt.text))
        print("  " + question.answer_display.text)

    print("PASS: all 10 recorded failure seeds under their original RNG contexts.")
    print("PASS: version 2 examples and corrupt-answer rejection at all four levels.")


if __name__ == "__main__":
    main()