"""All index forms, exact known cases, bad answers and a progression PDF."""
import sys
import tempfile
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from launch_mathsgen import load_engine


def rejects(check, q):
    try:
        check(q)
    except ValueError:
        return
    raise AssertionError("Corrupted index answer accepted")


def main():
    registry = load_engine()
    from mathsgen.core import require, rational_text
    from mathsgen.index_rule_forms import parts
    from mathsgen.pdf import render_pdf

    generator = registry.get("number.indices.rules")
    samples = {}
    operations = set()
    comparisons = set()
    for level in range(1, 5):
        seen, independent = set(), {}
        for seed in range(60):
            q = generator.generate(seed, level)
            form = q.parameters.get("form", "single_power")
            seen.add(form)
            samples.setdefault((level, form), q)
            if independent.get(form, 0) < 8:
                generator.validate_independently(q)
                independent[form] = independent.get(form, 0) + 1
            if form == "combined_powers":
                operations.add(q.parameters["operator"])
            if form == "compare_roots":
                comparisons.add(q.answer["greater"])
            wrong = dict(q.answer)
            if form == "compare_roots":
                wrong["difference"] = rational_text(
                    Fraction(wrong["difference"]) + 1
                )
            else:
                wrong["value"] = rational_text(
                    Fraction(wrong["value"]) + 1
                )
            rejects(generator.validate, replace(q, answer=wrong))
            rejects(generator.validate_independently, replace(q, answer=wrong))
        expected = {
            1: {"single_power"}, 2: {"single_power"},
            3: {"single_power", "compare_roots"},
            4: {"single_power", "combined_powers"},
        }[level]
        require(seen == expected, "Missing index form at L{}".format(level))
        print("L{} forms: {}".format(level, sorted(seen)))
    require(operations == {"multiply", "divide"},
            "Both two-step operations must appear")
    require(comparisons == {"first", "second", "equal"},
            "Need greater, smaller and equal comparison outcomes")

    for level, p, expected in (
        (3, {"form": "compare_roots",
             "first": {"base": 16, "exponent": "1/2"},
             "second": {"base": 27, "exponent": "1/3"}},
         {"kind": "index_comparison", "greater": "first", "difference": "1"}),
        (3, {"form": "compare_roots",
             "first": {"base": 16, "exponent": "1/2"},
             "second": {"base": 64, "exponent": "1/3"}},
         {"kind": "index_comparison", "greater": "equal", "difference": "0"}),
        (4, {"form": "combined_powers",
             "first": {"base": 27, "exponent": "2/3"},
             "second": {"base": 16, "exponent": "-1/2"},
             "operator": "multiply"},
         {"kind": "exact_value", "value": "9/4"}),
        (4, {"form": "combined_powers",
             "first": {"base": 27, "exponent": "2/3"},
             "second": {"base": 16, "exponent": "-1/2"},
             "operator": "divide"},
         {"kind": "exact_value", "value": "36"}),
    ):
        prompt, answer, display = parts(p)
        require(answer == expected, "Known index result changed")
        q = generator.generate(12345, level)
        known = replace(q, parameters=p, prompt=prompt, answer=answer,
                        answer_display=display,
                        marks=3 if level == 3 else 4,
                        layout_hint=replace(q.layout_hint,
                                            working_lines=4 if level == 3 else 5))
        generator.validate(known)
        generator.validate_independently(known)

    export_root = ROOT / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="index_progression_",
                                      dir=str(export_root)))
    worksheet = SimpleNamespace(
        title="Index rules progression", id="index-progression",
        specification={}, questions=[samples[key] for key in sorted(samples)],
    )
    for mode in ("questions", "answers"):
        print(render_pdf(worksheet, directory / (mode + ".pdf"), mode))
    print("PASS: index forms, exact cases, answer rejection and specimen.")


if __name__ == "__main__":
    main()