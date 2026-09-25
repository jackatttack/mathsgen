"""Like terms, single brackets and substitution: focused checks and specimen.

Cheap checks on SEEDS questions per level; SymPy independence (including a
fully-simplified check) on the first INDEPENDENT_SEEDS.
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


GENERATOR_IDS = (
    "algebra.expressions.like_terms",
    "algebra.expanding.single_brackets",
    "algebra.substitution.values",
)
SEEDS = 40
INDEPENDENT_SEEDS = 8
SPECIMEN_SEED = 5
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


def main():
    registry = load_engine()
    from mathsgen.catalogue import source_registry
    registry = source_registry(registry)
    from mathsgen.pdf import render_pdf, styles
    body = styles()["body"]
    specimen = []

    for generator_id in GENERATOR_IDS:
        generator = registry.get(generator_id)
        for level in (1, 2, 3, 4):
            prompts = set()
            for seed in range(SEEDS):
                q = generator.generate(seed, level)
                if seed < INDEPENDENT_SEEDS:
                    generator.validate_independently(q)
                prompts.add(q.prompt.text)
                check_width(q.prompt, body)
                check_width(q.answer_display, body)
                rejects(generator, replace(q, answer={"kind": "rational", "value": "999"}), "a wrong answer")
                rejects(generator, replace(q, prompt=replace(q.prompt, text=q.prompt.text + " ")), "an altered prompt")
                altered, _ = bump_first_int(json.loads(json.dumps(q.parameters)))
                rejects(generator, replace(q, parameters=altered), "altered parameters")
            sample = generator.generate(SPECIMEN_SEED, level)
            specimen.append(sample)
            print("{} L{} ({} distinct / {}): {} -> {}".format(
                generator_id, level, len(prompts), SEEDS,
                sample.prompt.text, sample.answer_display.text))

    export_root = Path(__file__).resolve().parent.parent / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="algebra_basics_specimen_", dir=str(export_root)))
    worksheet = SimpleNamespace(
        title="Algebra basics specimen", id="algebra-basics-specimen",
        specification={}, questions=specimen,
    )
    for mode in ("questions", "answers"):
        print(render_pdf(worksheet, directory / (mode + ".pdf"), mode))
    print("PASS: three algebra generators, independence, rejection, widths and specimen.")


if __name__ == "__main__":
    main()