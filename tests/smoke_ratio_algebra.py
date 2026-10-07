"""Changing-ratio construction, unique recovery, corruption and specimens."""
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from launch_mathsgen import load_engine


def reject(generator, q):
    try:
        generator.validate(q)
    except ValueError:
        return
    raise AssertionError("Corrupt ratio question accepted")


def main():
    load_engine()
    from mathsgen.ratio_algebra import RatioAlgebra, check_parameters
    from mathsgen.export import export_worksheet
    generator = RatioAlgebra()
    example = {"context": "equal_increase", "a": 4, "b": 5,
               "c": 5, "d": 6, "increase": 3}
    assert check_parameters(example, 1) == {"A": 12, "B": 15}
    specimen = []
    for level in (1, 2, 3, 4):
        changes = set()
        for seed in range(40):
            q = generator.generate(seed, level)
            generator.validate(q)
            generator.validate_independently(q)
            assert q.to_dict() == generator.generate(seed, level).to_dict()
            reject(generator, replace(q, answer={}))
            reject(generator, replace(q, prompt=replace(q.prompt, text="Wrong givens")))
            key = "increase" if level == 1 else "change_a" if level == 2 else "transfer"
            reject(generator, replace(q, parameters=dict(q.parameters, **{key: 0})))
            if level == 2:
                changes.add(q.parameters["change_b"] > 0)
            if seed < 2:
                specimen.append(q)
                print("L{}: {} -> {}".format(level, q.prompt.text, q.answer_display.text))
        if level == 2:
            assert changes == {True, False}
    for level, p in (
        (1, dict(example, c=4, d=5)),
        (4, {"context": "two_changes", "a": 1, "b": 1, "c": 2, "d": 3,
             "e": 1, "f": 2, "transfer": 5}),
    ):
        try:
            check_parameters(p, level)
        except ValueError:
            pass
        else:
            raise AssertionError("Singular ratio problem accepted")
    sheet = SimpleNamespace(
        title="Algebra and changing ratios", id="ratio-algebra-specimen-v1",
        specification={}, questions=tuple(specimen),
    )
    # Use the standard renderer directly: this source is not registered yet.
    from mathsgen.pdf import render_pdf
    output = PROJECT_ROOT / "exports" / "specimens" / "ratio_algebra_v1"
    output.mkdir(parents=True, exist_ok=True)
    for mode in ("questions", "answers"):
        print(render_pdf(sheet, output / (mode + ".pdf"), mode))
    print("PASS: 160 independent ratio checks, exact example, corruptions and PDF export.")


if __name__ == "__main__":
    main()