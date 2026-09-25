"""Function generators: independence, rejection, rich widths and a specimen.

Cheap checks run on SEEDS questions per level. SymPy independence is slow
on device, so it runs on the first INDEPENDENT_SEEDS only. The exported
specimen (one question per generator and level) is for review by eye.
"""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

import tempfile
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from launch_mathsgen import load_engine


GENERATOR_IDS = (
    "algebra.functions.evaluate",
    "algebra.functions.inverse",
    "algebra.functions.composite",
    "algebra.functions.combined",
)
SEEDS = 100
INDEPENDENT_SEEDS = 20
SPECIMEN_SEED = 5
COLUMN_WIDTH = 460


def perturbed(parameters):
    """Nudge the first numeric parameter so the stored prompt no longer fits."""
    altered = dict(parameters)
    key = sorted(k for k in altered if k != "order")[0]
    value = altered[key]
    if isinstance(value, list):
        altered[key] = [value[0] + 1] + value[1:]
    else:
        altered[key] = value + 1
    return altered


def rejects(generator, question, reason):
    try:
        generator.validate(question)
    except ValueError:
        return
    raise AssertionError("{} accepted {}".format(generator.info.id, reason))


def check_width(content, body_style):
    """Raise if rich blocks or a legacy equation overflow the PDF column."""
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
                rejects(generator, replace(q, parameters=perturbed(q.parameters)), "altered parameters")
            sample = generator.generate(SPECIMEN_SEED, level)
            specimen.append(sample)
            print("{} L{} ({} distinct / {}): {}".format(
                generator_id, level, len(prompts), SEEDS, sample.prompt.text))

    export_root = Path(__file__).resolve().parent.parent / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="functions_specimen_", dir=str(export_root)))
    worksheet = SimpleNamespace(
        title="Functions specimen", id="functions-specimen",
        specification={}, questions=specimen,
    )
    for mode in ("questions", "answers"):
        print(render_pdf(worksheet, directory / (mode + ".pdf"), mode))
    print("PASS: rich prompts, independent checks, rejection, widths and specimen export.")


if __name__ == "__main__":
    main()