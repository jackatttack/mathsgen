"""Laws of indices v3: known cases, every part kind, rejection and a specimen."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

import json
import tempfile
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

from launch_mathsgen import load_engine


SEEDS = 40
INDEPENDENT_SEEDS = 8
SPECIMEN_SEEDS = (5, 6, 7)


def bump_first_int(value):
    """Add one to the first integer found (dict keys in sorted order)."""
    if type(value) is int:
        return value + 1, True
    if isinstance(value, list):
        out, done = [], False
        for item in value:
            if not done:
                item, done = bump_first_int(item)
            out.append(item)
        return out, done
    if isinstance(value, dict):
        out, done = {}, False
        for key in sorted(value):
            item = value[key]
            if not done:
                item, done = bump_first_int(item)
            out[key] = item
        return out, done
    return value, False


def rejects(generator, make_question, reason):
    """make_question builds the corrupted question; building may itself fail."""
    try:
        generator.validate(make_question())
    except ValueError:
        return
    raise AssertionError("{} accepted {}".format(generator.info.id, reason))


def check_known_cases():
    from mathsgen.indices import algebra_result, exact_power, exact_value, reverse_pieces
    assert exact_value(7, Fraction(0)) == 1, "Zero index failed"
    assert exact_value(5, Fraction(-2)) == Fraction(1, 25), "Negative index failed"
    assert exact_value(81, Fraction(3, 2)) == 729, "Fractional index failed"
    assert exact_power(Fraction(8, 27), Fraction(-2, 3)) == Fraction(9, 4), "Fraction base failed"
    assert exact_power(Fraction(2, 5), Fraction(-2)) == Fraction(25, 4), "Reciprocal failed"
    part = {"kind": "product_coefficients", "variable": "x",
            "coefficients": [3, 5], "indices": [4, -2]}
    assert algebra_result(part) == (15, 2), "Coefficient product failed"
    part = {"kind": "power_coefficients", "variable": "x",
            "coefficients": [2], "indices": [3, 3]}
    assert algebra_result(part) == (8, 9), "Power of a product failed"
    part = {"kind": "solve", "root": 2, "base_power": 3, "target_power": 1}
    assert reverse_pieces(part) == (8, 2, Fraction(1, 3)), "8^n = 2 failed"
    part = {"kind": "power_of", "root": 2, "base_power": 1, "target_power": -5}
    assert reverse_pieces(part) == (2, Fraction(1, 32), -5), "1/32 as a power of 2 failed"
    for base, exponent in ((10, Fraction(1, 2)), (7, Fraction(1, 3))):
        try:
            exact_value(base, exponent)
        except ValueError:
            continue
        raise AssertionError("Irrational root accepted for {}".format(base))
    print("Known cases: PASS")


def main():
    load_engine()
    from mathsgen.indices import LEVEL_KINDS, LawsOfIndices
    from mathsgen.pdf import render_pdf

    check_known_cases()
    generator = LawsOfIndices()
    specimen = []
    for level in (1, 2, 3, 4):
        prompts, kinds = set(), {}
        for seed in range(SEEDS):
            q = generator.generate(seed, level)
            if seed < INDEPENDENT_SEEDS:
                generator.validate_independently(q)
            prompts.add(q.prompt.text)
            for part in q.parameters["parts"]:
                kinds[part["kind"]] = kinds.get(part["kind"], 0) + 1

            def wrong_answer(q=q):
                answer = json.loads(json.dumps(q.answer))
                first = answer["parts"][0]
                key = sorted(k for k in first if k != "kind")[0]
                first[key] = "999"
                return replace(q, answer=answer)

            def altered_prompt(q=q):
                return replace(q, prompt=replace(q.prompt, text=q.prompt.text + " "))

            def altered_parameters(q=q):
                altered, changed = bump_first_int(json.loads(json.dumps(q.parameters)))
                if not changed:
                    raise ValueError("Nothing to alter")
                return replace(q, parameters=altered)

            rejects(generator, wrong_answer, "a wrong answer")
            rejects(generator, altered_prompt, "an altered prompt")
            rejects(generator, altered_parameters, "altered parameters")
        missing = set(LEVEL_KINDS[level]) - set(kinds)
        assert not missing, "L{} never produced {}".format(level, sorted(missing))
        for seed in SPECIMEN_SEEDS:
            specimen.append(generator.generate(seed, level))
        sample = specimen[-1]
        print("L{} ({} distinct / {}, kinds {}):\n  {}\n  -> {}".format(
            level, len(prompts), SEEDS, kinds, sample.prompt.text, sample.answer_display.text))

    export_root = Path(__file__).resolve().parent.parent / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="indices_", dir=str(export_root)))
    worksheet = SimpleNamespace(title="Laws of indices specimen", id="indices-specimen",
                                specification={}, questions=specimen)
    for mode in ("questions", "answers"):
        print(render_pdf(worksheet, directory / (mode + ".pdf"), mode))
    print("PASS: laws of indices v3.")


if __name__ == "__main__":
    main()