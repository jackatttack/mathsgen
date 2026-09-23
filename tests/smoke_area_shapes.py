"""Basic shape areas: focused checks plus a specimen covering every shape at
every level, so any label overflow or overlap fails during rendering."""
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
from smoke_algebra_basics import bump_first_int, check_width, rejects


SEEDS = 40
INDEPENDENT_SEEDS = 8


def main():
    registry = load_engine()
    from mathsgen.pdf import render_pdf, styles
    body = styles()["body"]
    generator = registry.get("geometry.area.basic_shapes")
    specimen = {}

    for level in (1, 2, 3, 4):
        prompts = set()
        for seed in range(SEEDS):
            q = generator.generate(seed, level)
            if seed < INDEPENDENT_SEEDS:
                generator.validate_independently(q)
            prompts.add(q.prompt.text)
            check_width(q.answer_display, body)
            specimen.setdefault((level, q.parameters["shape"]), q)
            rejects(generator, replace(q, answer={"kind": "measure", "value": 999, "unit": "cm"}), "a wrong answer")
            rejects(generator, replace(q, prompt=replace(q.prompt, text=q.prompt.text + " ")), "an altered prompt")
            altered, _ = bump_first_int(json.loads(json.dumps(q.parameters)))
            rejects(generator, replace(q, parameters=altered), "altered parameters")
        sample = generator.generate(5, level)
        print("L{} ({} distinct / {}): {} -> {}".format(
            level, len(prompts), SEEDS, sample.prompt.text, sample.answer_display.text))

    questions = [specimen[key] for key in sorted(specimen)]
    print("specimen covers:", sorted(specimen))
    root = Path(__file__).resolve().parent.parent / "exports"
    root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="area_shapes_specimen_", dir=str(root)))
    worksheet = SimpleNamespace(title="Shape areas specimen", id="area-shapes",
                                specification={}, questions=questions)
    for mode in ("questions", "answers"):
        print(render_pdf(worksheet, directory / (mode + ".pdf"), mode))
    print("PASS: shape areas, independence, rejection and every shape rendered at every level.")


if __name__ == "__main__":
    main()