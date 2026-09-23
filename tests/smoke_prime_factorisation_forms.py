"""Prime factorisation v2: forms, independent routes, tampering, PDF; HCF/LCM intact."""
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
    from mathsgen.prime_factors import PRIME_FORMS
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    generator = registry.get("number.primes.factorisation")
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
                if q.answer["kind"] == "prime_factorisation":
                    wrong = dict(q.answer, factors=dict(q.answer["factors"], **{"2": 9}))
                else:
                    wrong = dict(q.answer, value=q.answer["value"] + 1)
                for checker in (generator.validate, generator.validate_independently):
                    require(rejects(checker, replace(q, answer=wrong)), "Wrong answer accepted")
                require(rejects(generator.validate, replace(q, parameters=dict(p, form="banana"))),
                        "Bad form accepted")
                require(rejects(generator.validate, replace(q, prompt=Content("Wrong"))),
                        "Wrong prompt accepted")
            checked += 1
        require(forms == set(PRIME_FORMS[level]), "Level {} forms: saw {}".format(level, sorted(forms)))

    for gid in ("number.factors.hcf", "number.multiples.lcm"):
        other = registry.get(gid)
        for level in range(1, 5):
            for seed in range(10):
                q = other.generate(seed, level)
                other.validate(q)
                other.validate_independently(q)
    print("HCF and LCM still generate and validate.")

    report = export_worksheet(
        Worksheet(id="prime-factors-v2-specimens", title="Prime factors",
                  seed=20260923, specification={"specimens": True}, questions=tuple(specimens)),
        _MATHSGEN_PROJECT_ROOT / "exports", answers=True,
    )
    print("Specimen:", report["directory"])
    print("PASS:", checked, "questions; independent routes, tampering and PDF")


if __name__ == "__main__":
    main()