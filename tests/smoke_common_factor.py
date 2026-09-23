"""Check no common-factor answer leaves a factorisable bracket.

The instruction says "factorise fully", so a bracket that SymPy can factor
further makes the stated answer wrong. The independent check inside the
generator only tests that nothing common remains, which does not catch a
difference of two squares such as x^2 - 9 or 4x^2 - 9y^2.

This walks many seeds at every level and reports any bracket SymPy can
still factor, along with the corruption rejection the family had no smoke
for.
"""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from launch_mathsgen import load_engine

SEEDS = 200


def main():
    registry = load_engine()
    import sympy
    from mathsgen.core import require

    generator = registry.get("algebra.factorising.common_factor")
    unfactorised = []
    checked = 0

    for level in range(1, 5):
        for seed in range(SEEDS):
            question = generator.generate(seed, level)
            checked += 1
            answer = question.answer
            letters = [
                sympy.Symbol(name, positive=True)
                for name in question.parameters["letters"]
            ]
            inside = sympy.Integer(0)
            for coefficient, powers in answer["inner"]:
                term = sympy.Integer(coefficient)
                for symbol, power in zip(letters, powers):
                    term *= symbol ** power
                inside += term
            # factor() returns a product when more can be taken out; if it
            # differs structurally from the bracket, the answer is not full.
            factored = sympy.factor(inside)
            if factored != inside and not factored.equals(inside * 1):
                unfactorised.append((level, seed, str(inside), str(factored)))
            elif factored.is_Mul and not inside.is_Mul:
                unfactorised.append((level, seed, str(inside), str(factored)))

    print("Checked {} answers.".format(checked))
    if unfactorised:
        print("{} brackets can be factorised further:".format(len(unfactorised)))
        for level, seed, inside, factored in unfactorised[:10]:
            print("  level {} seed {}: {} -> {}".format(
                level, seed, inside, factored
            ))
        raise SystemExit(1)
    print("No bracket can be factorised further.")

    # Corruption: a perturbed factor or a wrong inner term must be rejected.
    for level in range(1, 5):
        question = generator.generate(5, level)
        wrong_factor = dict(question.answer, factor=question.answer["factor"] + 1)
        try:
            generator.validate(replace(question, answer=wrong_factor))
        except ValueError:
            pass
        else:
            raise AssertionError("A wrong numerical factor was accepted")

        inner = [list(pair) for pair in question.answer["inner"]]
        inner[0][0] += 1
        wrong_inner = dict(question.answer, inner=inner)
        try:
            generator.validate(replace(question, answer=wrong_inner))
        except ValueError:
            pass
        else:
            raise AssertionError("A wrong inner coefficient was accepted")

    print("PASS: full factorisation and corruption rejection at every level.")


if __name__ == "__main__":
    main()