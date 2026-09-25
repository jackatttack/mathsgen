"""Rounding v2, both modes: forms, decimal-module checks, tampering, PDF."""
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
    from mathsgen.catalogue import source_registry
    registry = source_registry(registry)
    from mathsgen.core import Content, require
    from mathsgen.rounding import decimal_text
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    specimens, checked = [], 0
    for gid in ("number.rounding.decimal_places", "number.rounding.significant_figures"):
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
                    if q.answer["kind"] == "rounded_pair":
                        values = list(q.answer["values"])
                        values[0] = decimal_text(Fraction(values[0]) + 1)
                        wrong = dict(q.answer, values=values)
                    else:
                        wrong = dict(q.answer, value=decimal_text(Fraction(q.answer["value"]) + 1))
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
        Worksheet(id="rounding-v2-specimens", title="Rounding",
                  seed=20260923, specification={"specimens": True}, questions=tuple(specimens)),
        _MATHSGEN_PROJECT_ROOT / "exports", answers=True,
    )
    print("Specimen:", report["directory"])
    print("PASS:", checked, "questions; decimal-module checks, tampering and PDF")


if __name__ == "__main__":
    main()