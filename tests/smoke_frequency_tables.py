"""Frequency tables v3: known cases, every form, rejection and a specimen."""
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
RENDER_WIDTHS = (360, 250)


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


def rejects(generator, question, reason):
    try:
        generator.validate(question)
    except ValueError:
        return
    raise AssertionError("{} accepted {}".format(generator.info.id, reason))


def check_known_cases():
    from mathsgen.frequency_tables import (
        grouped_estimate, median_class, table_mean, table_median, table_mode,
    )
    values = [Fraction(n) for n in (1, 2, 4, 7)]
    assert table_mean(values, [2, 4, 3, 1]) == Fraction(29, 10), "Weighted mean failed"
    assert table_median([Fraction(n) for n in (1, 2, 3, 4)], [1, 1, 1, 1]) == Fraction(5, 2), \
        "Even-total midpoint median failed"
    assert table_median([Fraction(n) for n in (1, 3)], [2, 2]) == 2, \
        "Median across two rows failed"
    assert table_median([Fraction(n) for n in (1, 2, 3)], [2, 2, 2]) == 2, \
        "Even-total median within one row failed"
    assert table_mode(values, [2, 4, 3, 1]) == 2, "Mode failed"
    assert table_mode(values, [4, 4, 3, 1]) is None, "Tied mode accepted"
    # Midpoints 5 and 15: (5 * 1 + 15 * 3) / 4 = 12.5
    assert grouped_estimate([0, 10, 20], [1, 3]) == Fraction(25, 2), "Grouped estimate failed"
    assert median_class([5, 5]) is None, "Straddling median class accepted"
    assert median_class([3, 5, 2]) == 1, "Median class failed"
    print("Known cases: PASS")


def main():
    load_engine()
    from mathsgen.core import rational_text
    from mathsgen.frequency_tables import LEVEL_FORMS, FrequencyTables
    from mathsgen.pdf import render_pdf
    from mathsgen.visuals import drawing_for

    check_known_cases()
    generator = FrequencyTables()
    specimen = []
    for level in (1, 2, 3, 4):
        prompts, forms, independent = set(), {}, {}
        for seed in range(SEEDS):
            q = generator.generate(seed, level)
            form = q.parameters["form"]
            forms[form] = forms.get(form, 0) + 1
            if independent.get(form, 0) < INDEPENDENT_SEEDS:
                generator.validate_independently(q)
                independent[form] = independent.get(form, 0) + 1
            prompts.add(q.prompt.text)
            for table in q.question_visuals:
                for width in RENDER_WIDTHS:
                    drawing_for(table, width)

            wrong = dict(q.answer)
            first_key = sorted(key for key in wrong if key != "kind")[0]
            wrong[first_key] = "999"
            rejects(generator, replace(q, answer=wrong), "a wrong answer")
            rejects(generator, replace(q, prompt=replace(q.prompt, text=q.prompt.text + " ")),
                    "an altered prompt")
            altered, changed = bump_first_int(json.loads(json.dumps(q.parameters)))
            if changed:
                rejects(generator, replace(q, parameters=altered), "an altered count")
            if "values" in q.parameters:
                altered = dict(q.parameters)
                values = list(altered["values"])
                values[-1] = rational_text(Fraction(values[-1]) + 1)
                altered["values"] = values
                rejects(generator, replace(q, parameters=altered), "an altered value")
        missing_forms = set(LEVEL_FORMS[level]) - set(forms)
        assert not missing_forms, "L{} never produced {}".format(level, sorted(missing_forms))
        for seed in SPECIMEN_SEEDS:
            specimen.append(generator.generate(seed, level))
        sample = specimen[-1]
        print("L{} ({} distinct / {}, forms {}):\n  {}\n  -> {}".format(
            level, len(prompts), SEEDS, forms, sample.prompt.display_text or sample.prompt.text,
            sample.answer_display.text))

    export_root = Path(__file__).resolve().parent.parent / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="frequency_tables_", dir=str(export_root)))
    worksheet = SimpleNamespace(title="Frequency tables specimen", id="frequency-tables-specimen",
                                specification={}, questions=specimen)
    for mode in ("questions", "answers"):
        print(render_pdf(worksheet, directory / (mode + ".pdf"), mode))
    print("PASS: frequency tables v3.")


if __name__ == "__main__":
    main()