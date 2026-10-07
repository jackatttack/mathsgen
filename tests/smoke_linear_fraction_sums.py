"""Fractional linear sums: independent solutions, rejection and drill export."""
import sys
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from launch_mathsgen import load_engine


def reject(generator, question):
    try:
        generator.validate(question)
    except ValueError:
        return
    raise AssertionError("Invalid fractional equation accepted")


def main():
    load_engine()
    from mathsgen.catalogue import build_registry
    from mathsgen.core import make_context
    from mathsgen import linear_fraction_sums as forms
    from mathsgen.drill import build_drill
    from mathsgen.export import export_worksheet

    registry = build_registry()
    generator = registry.get("algebra.linear.two_sided")
    example = {"form": "fraction_sum", "a": 4, "c": 1, "m": 2,
               "b": 3, "d": 7, "n": 3, "sign": 1, "e": 0, "f": 10}
    assert forms.check_structure(example) == Fraction(43, 18)
    print("Requested example:", forms.presentation(example).text, "-> x = 43/18")
    seen = set()
    for seed in range(80):
        q = forms.generate(generator, make_context(generator.info, seed, 4))
        generator.validate(q)
        generator.validate_independently(q)
        assert q.to_dict() == forms.generate(
            generator, make_context(generator.info, seed, 4)).to_dict()
        p = q.parameters
        seen.add((p["sign"], bool(p["e"])))
        reject(generator, replace(q, answer={"kind": "variable_values", "values": {"x": "999"}}))
        reject(generator, replace(q, parameters=dict(p, m=0)))
        reject(generator, replace(q, prompt=replace(q.prompt, text="Wrong equation")))
        if seed < 6:
            print(q.prompt.text, "->", q.answer_display.text)
    assert seen == {(-1, False), (-1, True), (1, False), (1, True)}
    encountered = set()
    for level in (1, 2, 3, 4):
        for seed in range(40):
            q = generator.generate(seed, level)
            generator.validate(q)
            if seed < 8:
                generator.validate_independently(q)
            if level == 4:
                encountered.add(q.parameters.get("form", "context" if "context" in q.parameters else "two_fractions"))
    assert {"fraction_sum", "two_fractions", "context"} <= encountered
    sheet = build_drill(registry, [{
        "generator_id": generator.info.id, "levels": [4], "count": 18, "apply": 3,
    }], "Fractional linear equations", seed=715)
    assert any(q.parameters.get("form") == "fraction_sum" for q in sheet.questions)
    result = export_worksheet(sheet, PROJECT_ROOT / "exports" / "specimens", answers=True)
    print("SPECIMEN:", result["directory"])
    for report in result["pdfs"]:
        print(report["mode"], report["pages"], "pages")
    print("PASS: 80 independently solved sums, 160 family checks, rejection and drill PDF.")


if __name__ == "__main__":
    main()