"""algebra.linear.two_sided v4: bare and worded forms, focused checks, specimen.

Every expected form must appear at its level. SymPy independence runs on the
first INDEPENDENT_PER_FORM questions of each form, so rare forms are covered.
"""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

import json
import tempfile
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from launch_mathsgen import load_engine


GENERATOR_ID = "algebra.linear.two_sided"
SEEDS = 40
INDEPENDENT_PER_FORM = 8
COLUMN_WIDTH = 460
EXPECTED_FORMS = {
    1: {"equation", "think_number"},
    2: {"equation"},
    3: {"equation", "tariffs", "savings", "polygon_perimeter"},
    4: {"equation", "ages", "isosceles_perimeter", "rectangle_area"},
}


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


def check_width(content, body_style):
    from mathsgen.content_rendering import content_flowables
    from mathsgen.pdf import MathLine
    if content.blocks:
        for flowable in content_flowables(content, body_style):
            flowable.wrap(COLUMN_WIDTH, 700)
    elif content.math_tex:
        MathLine(content.math_tex).wrap(COLUMN_WIDTH, 800)


def main():
    registry = load_engine()
    from mathsgen.pdf import render_pdf, styles
    body = styles()["body"]
    generator = registry.get(GENERATOR_ID)
    specimen = []

    for level in (1, 2, 3, 4):
        prompts, independent, samples = set(), {}, {}
        for seed in range(SEEDS):
            q = generator.generate(seed, level)
            form = q.parameters.get("context", "equation")
            if independent.get(form, 0) < INDEPENDENT_PER_FORM:
                generator.validate_independently(q)
                independent[form] = independent.get(form, 0) + 1
            samples.setdefault(form, q)
            prompts.add(q.prompt.text)
            check_width(q.prompt, body)
            check_width(q.answer_display, body)
            rejects(generator, replace(q, answer={"kind": "rational", "value": "999"}),
                    "a wrong answer")
            rejects(generator, replace(q, prompt=replace(q.prompt, text=q.prompt.text + " ")),
                    "an altered prompt")
            altered, changed = bump_first_int(json.loads(json.dumps(q.parameters)))
            if changed:
                rejects(generator, replace(q, parameters=altered), "altered parameters")
        missing = EXPECTED_FORMS[level] - set(samples)
        if missing:
            raise AssertionError("Level {} never produced {}".format(level, sorted(missing)))
        print("L{}: {} distinct / {}; SymPy per form {}".format(
            level, len(prompts), SEEDS, sorted(independent.items())))
        for form in sorted(samples):
            sample = samples[form]
            specimen.append(sample)
            print("  [{}] {}".format(form, sample.prompt.text))
            print("      -> {}".format(sample.answer_display.text))

    export_root = Path(__file__).resolve().parent.parent / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="linear_contexts_specimen_", dir=str(export_root)))
    worksheet = SimpleNamespace(
        title="Linear equations specimen", id="linear-contexts-specimen",
        specification={}, questions=specimen,
    )
    for mode in ("questions", "answers"):
        print(render_pdf(worksheet, directory / (mode + ".pdf"), mode))
    print("PASS: all forms, independence, rejection, widths and specimen.")


if __name__ == "__main__":
    main()