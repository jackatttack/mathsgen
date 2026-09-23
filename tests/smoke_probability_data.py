"""Two-way tables and expected/relative frequency: focused checks, specimen,
and a render check of every two-way context's table width."""
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


GENERATOR_IDS = ("probability.two_way.tables", "probability.frequency.expected")
SEEDS = 40
INDEPENDENT_SEEDS = 8
SPECIMEN_SEED = 5


def main():
    registry = load_engine()
    from mathsgen.pdf import render_pdf, styles
    from mathsgen.probability_data import CONTEXTS
    body = styles()["body"]
    specimen = []
    context_samples = {}

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
                context = q.parameters.get("context")
                if generator_id.startswith("probability.two_way") and context not in context_samples:
                    context_samples[context] = q
                rejects(generator, replace(q, answer={"kind": "rational", "value": "999"}), "a wrong answer")
                rejects(generator, replace(q, prompt=replace(q.prompt, text=q.prompt.text + " ")), "an altered prompt")
                altered, _ = bump_first_int(json.loads(json.dumps(q.parameters)))
                rejects(generator, replace(q, parameters=altered), "altered parameters")
            sample = generator.generate(SPECIMEN_SEED, level)
            specimen.append(sample)
            print("{} L{} ({} distinct / {}): {} -> {}".format(
                generator_id, level, len(prompts), SEEDS,
                sample.prompt.display_text or sample.prompt.text, sample.answer_display.text))

    root = Path(__file__).resolve().parent.parent / "exports"
    root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="probability_data_specimen_", dir=str(root)))
    for name, questions in (("specimen", specimen), ("contexts", list(context_samples.values()))):
        worksheet = SimpleNamespace(title="Probability " + name, id="probability-" + name,
                                    specification={}, questions=questions)
        for mode in ("questions", "answers"):
            print(render_pdf(worksheet, directory / "{}_{}.pdf".format(name, mode), mode))
    missing = set(CONTEXTS) - set(context_samples)
    print("contexts rendered: {}; missing: {}".format(sorted(context_samples), sorted(missing) or "none"))
    print("PASS: two probability generators, independence, rejection, widths and specimen.")


if __name__ == "__main__":
    main()