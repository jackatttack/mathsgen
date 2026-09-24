"""Algebraic proof and basic probability: focused checks and a specimen.

Generators are built directly, not from the registry, so this smoke can gate
their registration.
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


SEEDS = 40
SPECIMEN_SEEDS = (5, 6)
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
    if content.blocks:
        for flowable in content_flowables(content, body_style):
            flowable.wrap(COLUMN_WIDTH, 700)


def main():
    load_engine()
    from mathsgen.algebraic_proof import AlgebraicProof
    from mathsgen.basic_probability import BasicProbability
    from mathsgen.pdf import render_pdf, styles
    body = styles()["body"]
    specimen = []
    for generator in (AlgebraicProof(), BasicProbability()):
        for level in (1, 2, 3, 4):
            prompts, forms = set(), {}
            for seed in range(SEEDS):
                q = generator.generate(seed, level)
                generator.validate_independently(q)
                prompts.add(q.prompt.text)
                form = q.parameters["form"]
                forms[form] = forms.get(form, 0) + 1
                check_width(q.prompt, body)
                rejects(generator, replace(q, answer={"kind": "quantity", "value": "999"}),
                        "a wrong answer")
                rejects(generator, replace(q, prompt=replace(q.prompt, text=q.prompt.text + " ")),
                        "an altered prompt")
                altered, changed = bump_first_int(json.loads(json.dumps(q.parameters)))
                if changed:
                    rejects(generator, replace(q, parameters=altered), "altered parameters")
            for seed in SPECIMEN_SEEDS:
                specimen.append(generator.generate(seed, level))
            sample = specimen[-1]
            print("{} L{} ({} distinct / {}, forms {}): {} -> {}".format(
                generator.info.id, level, len(prompts), SEEDS, forms,
                sample.prompt.text, sample.answer_display.text))

    export_root = Path(__file__).resolve().parent.parent / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="proof_probability_", dir=str(export_root)))
    worksheet = SimpleNamespace(title="Proof and probability specimen",
                                id="proof-probability-specimen",
                                specification={}, questions=specimen)
    for mode in ("questions", "answers"):
        print(render_pdf(worksheet, directory / (mode + ".pdf"), mode))
    print("PASS: algebraic proof and basic probability.")


if __name__ == "__main__":
    main()