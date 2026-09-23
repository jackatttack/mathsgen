"""Fraction and decimal conversion v2: forms, exact checks, tampering, PDF."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from launch_mathsgen import load_engine


def rejects(checker, question):
    try:
        checker(question)
    except ValueError:
        return True
    return False


def main():
    registry = load_engine()
    from mathsgen.core import Content, require
    from mathsgen.fraction_decimal import FORMS
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    generator = registry.get("number.fdp.fraction_to_decimal")
    require(generator.info.version == 2, "Expected v2")
    specimens, checked = [], 0
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
                print("L{} [{}] {}".format(level, p["form"], q.prompt.text))
                print("  Answer:", q.answer_display.text)
            if seed < 6:
                if p["form"] == "order":
                    bumped = dict(p, items=[[p["items"][0][0], "7/3"]] + p["items"][1:])
                    wrong = dict(q.answer, items=list(reversed(q.answer["items"])))
                else:
                    bumped = dict(p, fraction="1/3")
                    wrong = dict(q.answer, value=q.answer["value"] + "1")
                for bad in (dict(p, form="banana"), bumped):
                    require(rejects(generator.validate, replace(q, parameters=bad)),
                            "Tampered parameters accepted: " + str(bad))
                for checker in (generator.validate, generator.validate_independently):
                    require(rejects(checker, replace(q, answer=wrong)), "Wrong answer accepted")
                require(rejects(generator.validate, replace(q, prompt=Content("Wrong"))),
                        "Wrong prompt accepted")
            checked += 1
        require(forms == set(FORMS[level]), "Level {} forms: saw {}".format(level, sorted(forms)))

    report = export_worksheet(
        Worksheet(id="fraction-decimal-v2-specimens", title="Fractions and decimals",
                  seed=20260923, specification={"specimens": True}, questions=tuple(specimens)),
        _MATHSGEN_PROJECT_ROOT / "exports", answers=True,
    )
    print("Specimen:", report["directory"])
    print("PASS:", checked, "questions; exact checks, tampering and PDF")


if __name__ == "__main__":
    main()