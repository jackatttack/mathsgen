"""Fraction of an amount v2 and recurring decimals v2: forms, checks, tampering, PDF."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from launch_mathsgen import load_engine


SEEDS = 60


def rejects(checker, question):
    try:
        checker(question)
    except ValueError:
        return True
    return False


def main():
    registry = load_engine()
    from mathsgen.core import Content, require
    from mathsgen.fraction_skills import AMOUNT_FORMS, RECURRING_FORMS
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    specimens, checked = [], 0
    for gid, forms_by_level in (("number.fractions.of_amount", AMOUNT_FORMS),
                                ("number.fractions.recurring_decimals", RECURRING_FORMS)):
        generator = registry.get(gid)
        require(generator.info.version == 2, "Expected v2 for " + gid)
        for level in range(1, 5):
            forms, shown = set(), set()
            for seed in range(SEEDS):
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
                    numeric = next(k for k in ("amount", "part", "left", "integer") if k in p)
                    for bad in (dict(p, form="banana"), dict(p, **{numeric: p[numeric] + 1})):
                        require(rejects(generator.validate, replace(q, parameters=bad)),
                                "Tampered parameters accepted: " + str(bad))
                    if q.answer["kind"] == "recurring":
                        wrong = dict(q.answer, integer=q.answer["integer"] + 1)
                    else:
                        wrong = dict(q.answer, value=q.answer["value"] + "1")
                    for checker in (generator.validate, generator.validate_independently):
                        require(rejects(checker, replace(q, answer=wrong)), "Wrong answer accepted")
                    require(rejects(generator.validate, replace(q, prompt=Content("Wrong"))),
                            "Wrong prompt accepted")
                checked += 1
            require(forms == set(forms_by_level[level]),
                    "{} level {} forms: saw {}".format(gid, level, sorted(forms)))

    report = export_worksheet(
        Worksheet(id="fraction-skills-v2-specimens", title="Fractions of amounts and recurring decimals",
                  seed=20260923, specification={"specimens": True}, questions=tuple(specimens)),
        _MATHSGEN_PROJECT_ROOT / "exports", answers=True,
    )
    print("Specimen:", report["directory"])
    print("PASS:", checked, "questions; independent checks, tampering and PDF")


if __name__ == "__main__":
    main()