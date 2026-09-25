"""Every DispatchFamily: all routes, independent checks, rejection and a specimen."""
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
SPECIMEN_SEED = 5


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


def corrupted(value):
    """A different value of the same general shape."""
    if type(value) is int:
        return value + 1
    if isinstance(value, str):
        return value + "9"
    if isinstance(value, list):
        return value + value[:1] if value else ["9"]
    if isinstance(value, dict):
        return dict(value, corrupted=True)
    return "999"


def rejects(generator, make_question, reason):
    try:
        generator.validate(make_question())
    except (ValueError, KeyError, TypeError):
        return
    raise AssertionError("{} accepted {}".format(generator.info.id, reason))


def check_family(generator, specimen):
    levels = sorted(generator.routes)
    all_routes = {route for level in levels for route in generator.routes[level]}
    for level in levels:
        prompts, routes = set(), {}
        for seed in range(SEEDS):
            q = generator.generate(seed, level)
            if seed < INDEPENDENT_SEEDS:
                generator.validate_independently(q)
            prompts.add(q.prompt.text)
            route = (q.parameters["source"], q.parameters["source_level"])
            routes[route] = routes.get(route, 0) + 1

            def wrong_answer(q=q):
                # Corrupt an existing answer field; some sources check named
                # fields rather than the whole answer, so an added key proves
                # nothing about correctness.
                answer = json.loads(json.dumps(q.answer))
                key = sorted(k for k in answer if k != "kind")[0]
                answer[key] = corrupted(answer[key])
                return replace(q, answer=answer)

            def altered_prompt(q=q):
                return replace(q, prompt=replace(q.prompt, text=q.prompt.text + " "))

            def altered_inner(q=q):
                inner, changed = bump_first_int(json.loads(json.dumps(q.parameters["inner"])))
                if not changed:
                    raise ValueError("Nothing to alter")
                return replace(q, parameters=dict(q.parameters, inner=inner))

            def foreign_route(q=q):
                others = sorted(all_routes - set(generator.routes[level]))
                if not others:
                    raise ValueError("No foreign route")
                name, other_level = others[0]
                return replace(q, parameters=dict(q.parameters, source=name,
                                                  source_level=other_level))

            rejects(generator, wrong_answer, "a wrong answer")
            rejects(generator, altered_prompt, "an altered prompt")
            rejects(generator, altered_inner, "altered source parameters")
            rejects(generator, foreign_route, "a route from another level")
        missing = set(generator.routes[level]) - set(routes)
        assert not missing, "{} L{} never used {}".format(generator.info.id, level, sorted(missing))
        sample = generator.generate(SPECIMEN_SEED, level)
        specimen.append(sample)
        print("{} L{} ({} distinct / {}): {}\n  -> {}".format(
            generator.info.id, level, len(prompts), SEEDS, sample.prompt.text,
            sample.answer_display.text))


def main():
    load_engine()
    from mathsgen.bounds_family import BoundsFamily
    from mathsgen.estimation_family import EstimationFamily
    from mathsgen.fdp_family import FDPFamily
    from mathsgen.mixture_family import MixtureFamily
    from mathsgen.pdf import render_pdf
    from mathsgen.prime_factor_family import PrimeFactorFamily
    from mathsgen.proportion_family import ProportionFamily
    from mathsgen.rounding_family import RoundingFamily
    from mathsgen.standard_form_family import StandardForm
    from mathsgen.simultaneous_family import SimultaneousFamily
    from mathsgen.inequalities_family import InequalitiesFamily
    from mathsgen.lines_family import StraightLinesFamily
    from mathsgen.functions_family import FunctionsFamily
    from mathsgen.sequences_family import SequencesFamily
    from mathsgen.expanding_family import ExpandingFamily
    from mathsgen.ratio_family import RatioFamily

    specimen = []
    families = (StandardForm, PrimeFactorFamily, RoundingFamily, EstimationFamily,
                BoundsFamily, FDPFamily, MixtureFamily, ProportionFamily,
                SimultaneousFamily, InequalitiesFamily, StraightLinesFamily,
                FunctionsFamily, SequencesFamily, ExpandingFamily, RatioFamily)
    for family in families:
        check_family(family(), specimen)

    export_root = Path(__file__).resolve().parent.parent / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="dispatch_families_", dir=str(export_root)))
    worksheet = SimpleNamespace(title="Merged generators specimen", id="dispatch-specimen",
                                specification={}, questions=specimen)
    for mode in ("questions", "answers"):
        print(render_pdf(worksheet, directory / (mode + ".pdf"), mode))
    print("PASS: every dispatch family.")


if __name__ == "__main__":
    main()