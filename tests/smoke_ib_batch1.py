"""IB AI SL generators: focused checks and a specimen PDF.

For every IB generator and level: SEEDS questions validate and fit the
column; the first INDEPENDENT_SEEDS pass the independent check; a wrong
answer, an altered prompt and altered parameters are each rejected.
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


SEEDS = 24
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
    for flowable in content_flowables(content, body_style):
        flowable.wrap(COLUMN_WIDTH, 700)


def main():
    # Pythonista keeps imported modules between runs; reload mathsgen so the
    # test always checks the code on disk.
    from launch_mathsgen import load_engine
    load_engine()
    from mathsgen.ib.catalogue import build_ib_registry
    from mathsgen.pdf import render_pdf, styles
    registry = build_ib_registry()
    body = styles()["body"]
    specimen = []

    # Optional arguments: generator ID prefixes to check (default: all).
    wanted = _mathsgen_test_sys.argv[1:]
    for info in registry.list():
        if wanted and not any(info.id.startswith(prefix) for prefix in wanted):
            continue
        generator = registry.get(info.id)
        for level in sorted(info.difficulty_descriptions):
            prompts = set()
            for seed in range(SEEDS):
                q = generator.generate(seed, level)
                if seed < INDEPENDENT_SEEDS:
                    generator.validate_independently(q)
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
            sample = generator.generate(SPECIMEN_SEED, level)
            specimen.append(sample)
            print("{} L{} ({} distinct / {}) [{} marks]".format(
                info.id, level, len(prompts), SEEDS, sample.marks))
            print("   " + sample.prompt.text.replace("\n", "\n   "))
            print("   -> " + sample.answer_display.text.replace("\n", "; "))

    export_root = Path(__file__).resolve().parent.parent / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="ib_batch1_specimen_", dir=str(export_root)))
    worksheet = SimpleNamespace(
        title="IB AI SL specimen", id="ib-ai-sl-specimen",
        specification={}, questions=specimen,
    )
    for mode in ("questions", "answers"):
        print(render_pdf(worksheet, directory / (mode + ".pdf"), mode))
    print("PASS: IB generators, independence, rejection, widths and specimen.")


if __name__ == "__main__":
    main()