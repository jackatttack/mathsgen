"""Worded forms: simplifying and combining ratios, estimation, standard form."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_TESTS = _MathsGenTestPath(__file__).resolve().parent
for _path in (_MATHSGEN_TESTS.parent, _MATHSGEN_TESTS):
    if str(_path) not in _mathsgen_test_sys.path:
        _mathsgen_test_sys.path.insert(0, str(_path))

from launch_mathsgen import load_engine
from worded_smoke import run


CASES = (
    ("ratio.simplifying", {
        1: {"equation", "pair_count"}, 2: {"equation", "triple_count"},
        3: {"equation", "ratio_to_fraction", "fraction_to_ratio"},
        4: {"equation", "mixed_units"}}),
    ("ratio.combining.three_part", {
        1: {"equation"}, 2: {"equation", "combine_story2"},
        3: {"equation", "combine_story3"}, 4: {"equation", "combine_total"}}),
    ("number.estimation.product", {
        1: {"equation", "boxes"}, 2: {"equation", "stadium"},
        3: {"equation", "shop"}, 4: {"equation", "tap"}}),
    ("number.estimation.quotient", {
        1: {"equation", "share"}, 2: {"equation", "coaches"},
        3: {"equation", "fuel"}, 4: {"equation", "ribbon"}}),
    ("number.standard_form.calculations", {
        1: {"equation", "virus", "signal", "rice"},
        2: {"equation", "density", "computer"},
        3: {"equation", "rice_renormalise", "computer_renormalise"},
        4: {"equation", "planets", "cargo"}}),
)


def main():
    # Several IDs here are now sources behind dispatch families; the source
    # registry serves them under their own IDs (mathsgen/dispatch.py).
    registry = load_engine()
    from mathsgen.catalogue import source_registry
    registry = source_registry(registry)
    only = set(_mathsgen_test_sys.argv[1:])
    for generator_id, forms in CASES:
        if only and generator_id not in only:
            continue
        prefix = generator_id.replace(".", "_") + "_specimen_"
        run(registry, generator_id, forms, generator_id + " specimen", prefix)


if __name__ == "__main__":
    main()