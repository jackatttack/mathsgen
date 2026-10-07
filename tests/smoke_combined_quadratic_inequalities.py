"""Check intersections, boundary inclusion and independent quadratic solutions."""
import sys
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from launch_mathsgen import load_engine


def rejects(generator, question):
    try:
        generator.validate(question)
    except ValueError:
        return
    raise AssertionError("Corrupted intersection accepted")


def main():
    load_engine()
    from mathsgen.combined_quadratic_inequalities import (
        CombinedQuadraticInequalities, intersect, roots_of,
    )
    from mathsgen.pdf import render_pdf

    assert intersect([(0, 1, True, True)], [(1, 2, True, True)]) == [
        (1, 1, True, True)]
    assert intersect([(0, 1, True, False)], [(1, 2, True, True)]) == []
    assert intersect([(None, 2, False, True)], [(1, None, False, False)]) == [
        (1, 2, False, True)]

    generator = CombinedQuadraticInequalities()
    samples = []
    operators, signs = set(), set()
    for level in (1, 2):
        prompts = set()
        for seed in range(40):
            q = generator.generate(seed, level)
            prompts.add(q.prompt.text)
            assert q.to_dict() == generator.generate(seed, level).to_dict()
            if seed < 8:
                generator.validate_independently(q)
            rejects(generator, replace(q, answer={}))
            rejects(generator, replace(q, prompt=replace(q.prompt, text="Altered")))
            bad = deepcopy(q.answer)
            bad["intervals"][0]["lower_closed"] = not bad["intervals"][0]["lower_closed"]
            rejects(generator, replace(q, answer=bad))
            bad_parameters = deepcopy(q.parameters)
            bad_parameters["inequalities"][0]["operator"] = "?"
            rejects(generator, replace(q, parameters=bad_parameters))

            # Evaluate each boundary and every intervening open region directly.
            roots = sorted({r for item in q.parameters["inequalities"]
                            for r in roots_of(item["coefficients"])})
            probes = roots + [(a+b)/2 for a, b in zip(roots, roots[1:])]
            probes += [roots[0]-1, roots[-1]+1]
            for x in probes:
                conditions = []
                for item in q.parameters["inequalities"]:
                    a, b, c = item["coefficients"]
                    value = a*x*x + b*x + c
                    op = item["operator"]
                    operators.add(op)
                    signs.add(a > 0)
                    conditions.append({"<": value < 0, "<=": value <= 0,
                                       ">": value > 0, ">=": value >= 0}[op])
                included = False
                for interval in q.answer["intervals"]:
                    low, high = Fraction(interval["lower"]), Fraction(interval["upper"])
                    included = included or (
                        (x > low or (x == low and interval["lower_closed"]))
                        and (x < high or (x == high and interval["upper_closed"])))
                assert included == all(conditions), (level, seed, x)
            if seed < 2:
                samples.append(q)
                print(q.prompt.text, "->", q.answer_display.text)
        print("L{}: {} distinct prompts / 40".format(level, len(prompts)))
    assert operators == {"<", "<=", ">", ">="}
    assert signs == {False, True}

    output = PROJECT_ROOT / "exports" / "specimens" / "combined_quadratic_inequalities_v1"
    output.mkdir(parents=True, exist_ok=True)
    sheet = SimpleNamespace(
        title="Combined quadratic inequalities", id="combined-quadratics-v1",
        specification={}, questions=tuple(samples))
    for mode in ("questions", "answers"):
        print(render_pdf(sheet, output / (mode + ".pdf"), mode))
    print("PASS: 80 generated checks, 16 SymPy intersections, boundary probes,")
    print("corruptions, reproducibility and PDF export. Visual review pending.")


if __name__ == "__main__":
    main()