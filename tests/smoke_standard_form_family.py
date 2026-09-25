"""Standard form v3 (dispatcher): every route, rejection and a specimen."""
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
INDEPENDENT_SEEDS = 8
SPECIMEN_SEEDS = (5, 6, 7)


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


def rejects(generator, make_question, reason):
    try:
        generator.validate(make_question())
    except (ValueError, KeyError, TypeError):
        return
    raise AssertionError("{} accepted {}".format(generator.info.id, reason))


def main():
    load_engine()
    from mathsgen.pdf import render_pdf
    from mathsgen.standard_form_family import StandardForm

    generator = StandardForm()
    specimen = []
    for level in (1, 2, 3, 4):
        prompts, routes = set(), {}
        for seed in range(SEEDS):
            q = generator.generate(seed, level)
            if seed < INDEPENDENT_SEEDS:
                generator.validate_independently(q)
            prompts.add(q.prompt.text)
            route = (q.parameters["source"], q.parameters["source_level"])
            routes[route] = routes.get(route, 0) + 1

            def wrong_answer(q=q):
                return replace(q, answer=dict(q.answer, tampered=True))

            def altered_prompt(q=q):
                return replace(q, prompt=replace(q.prompt, text=q.prompt.text + " "))

            def altered_inner(q=q):
                inner, changed = bump_first_int(json.loads(json.dumps(q.parameters["inner"])))
                if not changed:
                    raise ValueError("Nothing to alter")
                return replace(q, parameters=dict(q.parameters, inner=inner))

            def wrong_route(q=q):
                other = 1 if q.parameters["source_level"] != 1 else 4
                return replace(q, parameters=dict(q.parameters, source_level=other))

            rejects(generator, wrong_answer, "a wrong answer")
            rejects(generator, altered_prompt, "an altered prompt")
            rejects(generator, altered_inner, "altered source parameters")
            rejects(generator, wrong_route, "a route from another level")
        missing = set(generator.routes[level]) - set(routes)
        assert not missing, "L{} never used {}".format(level, sorted(missing))
        for seed in SPECIMEN_SEEDS:
            specimen.append(generator.generate(seed, level))
        sample = specimen[-1]
        print("L{} ({} distinct / {}, routes {}):\n  {}\n  -> {}".format(
            level, len(prompts), SEEDS, routes, sample.prompt.text,
            sample.answer_display.text))

    export_root = Path(__file__).resolve().parent.parent / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="standard_form_", dir=str(export_root)))
    worksheet = SimpleNamespace(title="Standard form specimen", id="standard-form-specimen",
                                specification={}, questions=specimen)
    for mode in ("questions", "answers"):
        print(render_pdf(worksheet, directory / (mode + ".pdf"), mode))
    print("PASS: standard form v3 dispatcher.")


if __name__ == "__main__":
    main()