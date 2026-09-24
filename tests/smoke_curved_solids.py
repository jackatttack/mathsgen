"""Curved solids: focused checks, notation and scene widths, and a specimen."""
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


GENERATOR_ID = "geometry.volume.curved_solids"
SEEDS = 40
SPECIMEN_SEEDS = (5, 6, 7)
SCENE_WIDTHS = (360, 250, 238)
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
    from mathsgen.pdf import render_pdf, styles
    from mathsgen.visuals import draw_scene
    body = styles()["body"]
    from mathsgen.curved_solids import CurvedSolids
    # Built directly, not from the registry, so this smoke can gate registration.
    generator = CurvedSolids()
    specimen = []
    for level in (1, 2, 3, 4):
        prompts, forms, solids = set(), {}, {}
        for seed in range(SEEDS):
            q = generator.generate(seed, level)
            generator.validate_independently(q)
            prompts.add(q.prompt.text)
            form = q.parameters["form"]
            forms[form] = forms.get(form, 0) + 1
            if "solid" in q.parameters:
                solids[q.parameters["solid"]] = solids.get(q.parameters["solid"], 0) + 1
            check_width(q.prompt, body)
            check_width(q.answer_display, body)
            for scene in q.visual_assets("questions"):
                for width in SCENE_WIDTHS:
                    draw_scene(scene, width)
            rejects(generator, replace(q, answer={"kind": "quantity", "value": "1"}),
                    "a wrong answer")
            rejects(generator, replace(q, prompt=replace(q.prompt, text=q.prompt.text + " ")),
                    "an altered prompt")
            altered, _ = bump_first_int(json.loads(json.dumps(q.parameters)))
            rejects(generator, replace(q, parameters=altered), "altered parameters")
        for seed in SPECIMEN_SEEDS:
            specimen.append(generator.generate(seed, level))
        sample = specimen[-1]
        print("L{} ({} distinct / {}, forms {}, solids {}): {} -> {}".format(
            level, len(prompts), SEEDS, forms, solids,
            sample.prompt.text, sample.answer_display.text))

    export_root = Path(__file__).resolve().parent.parent / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="curved_solids_", dir=str(export_root)))
    worksheet = SimpleNamespace(title="Curved solids specimen", id="curved-solids-specimen",
                                specification={}, questions=specimen)
    for mode in ("questions", "answers"):
        print(render_pdf(worksheet, directory / (mode + ".pdf"), mode))
    print("PASS: curved solids, independence, rejection, widths, scenes and specimen.")


if __name__ == "__main__":
    main()