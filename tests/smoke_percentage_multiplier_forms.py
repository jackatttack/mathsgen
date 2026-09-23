"""Percentage multipliers v2, both generators: forms, effect checks, tampering, PDF."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from fractions import Fraction
from launch_mathsgen import load_engine


def rejects(checker, question):
    try:
        checker(question)
    except ValueError:
        return True
    return False


def main():
    registry = load_engine()
    from mathsgen.core import Content, require, rational_text
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    specimens, checked = [], 0
    for gid in ("number.percentages.multiplier", "number.percentages.interpret_multiplier"):
        generator = registry.get(gid)
        require(generator.info.version == 2, "Expected v2 for " + gid)
        for level in range(1, 5):
            forms, shown = set(), set()
            for seed in range(60):
                q = generator.generate(seed, level)
                generator.validate(q)
                generator.validate_independently(q)
                p = q.parameters
                forms.add(p["form"])
                if p["form"] not in shown:
                    shown.add(p["form"])
                    specimens.append(q)
                    print("{} L{} [{}] {}".format(gid.split(".")[-1], level, p["form"],
                                                  q.prompt.text))
                    print("  Answer:", q.answer_display.text)
                if seed < 6:
                    key = "value" if q.answer["kind"] == "money" else "multiplier"
                    wrong = dict(q.answer, **{key: rational_text(Fraction(q.answer[key]) + 1)})
                    for checker in (generator.validate, generator.validate_independently):
                        require(rejects(checker, replace(q, answer=wrong)), "Wrong answer accepted")
                    require(rejects(generator.validate,
                                    replace(q, parameters=dict(p, form="banana"))),
                            "Bad form accepted")
                    require(rejects(generator.validate, replace(q, prompt=Content("Wrong"))),
                            "Wrong prompt accepted")
                checked += 1
            require(forms == set(generator.forms[level]),
                    "{} level {} forms: saw {}".format(gid, level, sorted(forms)))

    report = export_worksheet(
        Worksheet(id="multiplier-v2-specimens", title="Percentage multipliers",
                  seed=20260923, specification={"specimens": True}, questions=tuple(specimens)),
        _MATHSGEN_PROJECT_ROOT / "exports", answers=True,
    )
    print("Specimen:", report["directory"])
    print("PASS:", checked, "questions; effect checks, tampering and PDF")


if __name__ == "__main__":
    main()