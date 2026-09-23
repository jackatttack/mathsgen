"""Shared focused smoke for generators that mix bare and worded forms.

Not a test by itself: smoke_*_contexts.py files call run().
Every expected form must appear at its level. SymPy independence runs on
the first INDEPENDENT_PER_FORM questions of each form, so rare forms are
covered. Bare questions report their form as "equation".
"""
import json
import tempfile
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace


SEEDS = 40
INDEPENDENT_PER_FORM = 8
COLUMN_WIDTH = 460


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


def run(registry, generator_id, expected_forms, title, prefix):
    from mathsgen.pdf import render_pdf, styles
    body = styles()["body"]
    generator = registry.get(generator_id)
    specimen = []

    for level in sorted(expected_forms):
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
        missing = expected_forms[level] - set(samples)
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
    directory = Path(tempfile.mkdtemp(prefix=prefix, dir=str(export_root)))
    worksheet = SimpleNamespace(title=title, id=prefix.strip("_"),
                                specification={}, questions=specimen)
    for mode in ("questions", "answers"):
        print(render_pdf(worksheet, directory / (mode + ".pdf"), mode))
    print("PASS: {}: all forms, independence, rejection, widths and specimen.".format(
        generator_id))