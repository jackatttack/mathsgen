"""Standard form v3, both directions: forms, exact values, tampering, PDF."""
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
    from mathsgen.standard_form import ordinary_text, standard_form_text, FORMS
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    require(ordinary_text("8003", -6) == "0.000008003", "Ordinary text failed")
    require(standard_form_text("8003", -6) == "8.003 × 10^-6", "Standard form text failed")

    specimens, checked = [], 0
    for gid in ("number.standard_form.from_decimal", "number.standard_form.to_decimal"):
        generator = registry.get(gid)
        require(generator.info.version == 3, "Expected v3 for " + gid)
        for level in range(1, 5):
            forms, shapes, shown = set(), set(), set()
            for seed in range(SEEDS):
                q = generator.generate(seed, level)
                generator.validate(q)
                generator.validate_independently(q)
                p = q.parameters
                forms.add(p["form"])
                shapes.add(q.prompt.display_text or q.prompt.text.split(":")[0][:40])
                if p["form"] not in shown:
                    shown.add(p["form"])
                    specimens.append(q)
                    print("{} L{} [{}] {}".format(gid.split(".")[-1], level, p["form"],
                                                  q.prompt.text))
                    print("  Answer:", q.answer_display.text)
                if seed < 5:
                    tampered = [dict(p, form="banana")]
                    if p["form"] == "order":
                        items = [list(item) for item in p["items"]]
                        items[0][1] += 1
                        tampered.append(dict(p, items=items))
                        wrong = dict(q.answer, items=list(reversed(q.answer["items"])))
                    else:
                        tampered.append(dict(p, exponent=p["exponent"] + 1))
                        if q.answer["kind"] == "standard_form":
                            wrong = dict(q.answer, exponent=q.answer["exponent"] + 1)
                        else:
                            wrong = dict(q.answer, value=q.answer["value"] + "1")
                    for bad in tampered:
                        require(rejects(generator.validate, replace(q, parameters=bad)),
                                "Tampered parameters accepted: " + str(bad))
                    for checker in (generator.validate, generator.validate_independently):
                        require(rejects(checker, replace(q, answer=wrong)),
                                "Wrong answer accepted")
                    require(rejects(generator.validate, replace(q, prompt=Content("Wrong"))),
                            "Wrong prompt accepted")
                checked += 1
            require(forms == set(FORMS[level]),
                    "{} level {} forms: saw {}".format(gid, level, sorted(forms)))
            print("  {} L{}: forms {}, {} prompt shapes".format(
                gid.split(".")[-1], level, sorted(forms), len(shapes)))

    report = export_worksheet(
        Worksheet(id="standard-form-v3-specimens", title="Standard form",
                  seed=20260923, specification={"specimens": True},
                  questions=tuple(specimens)),
        _MATHSGEN_PROJECT_ROOT / "exports", answers=True,
    )
    print("Specimen:", report["directory"])
    print("PASS:", checked, "questions; exact values, tampering and PDF")


if __name__ == "__main__":
    main()