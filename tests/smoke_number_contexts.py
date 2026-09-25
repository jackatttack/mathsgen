"""Worded forms for the number batch: percentages, ratio, HCF, LCM, reverse %."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_TESTS = _MathsGenTestPath(__file__).resolve().parent
for _path in (_MATHSGEN_TESTS.parent, _MATHSGEN_TESTS):
    if str(_path) not in _mathsgen_test_sys.path:
        _mathsgen_test_sys.path.insert(0, str(_path))

from launch_mathsgen import load_engine
from worded_smoke import run


CASES = (
    ("number.percentages.of_amount", {
        1: {"equation", "discount"}, 2: {"equation", "new_price"},
        3: {"equation", "offers"}, 4: {"equation", "successive", "share_of_share"}}),
    ("ratio.sharing", {
        1: {"equation"}, 2: {"equation", "difference"},
        3: {"equation", "one_share"}, 4: {"equation", "ratio_change"}}),
    ("number.factors.hcf", {
        1: {"equation"}, 2: {"equation", "ribbons2"},
        3: {"equation", "ribbons3"}, 4: {"equation", "bags"}}),
    ("number.multiples.lcm", {
        1: {"equation"}, 2: {"equation", "buses"},
        3: {"equation", "lights"}, 4: {"equation", "packs"}}),
    ("number.percentages.reverse", {
        1: {"equation"}, 2: {"equation"},
        3: {"equation", "vat", "salary"}, 4: {"equation", "successive"}}),
)


def main():
    registry = load_engine()
    from mathsgen.catalogue import source_registry
    registry = source_registry(registry)
    for generator_id, forms in CASES:
        prefix = generator_id.replace(".", "_") + "_specimen_"
        run(registry, generator_id, forms, generator_id + " specimen", prefix)


if __name__ == "__main__":
    main()