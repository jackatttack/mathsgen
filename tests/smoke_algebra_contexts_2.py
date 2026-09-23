"""Worded forms: non-monic quadratics and changing the subject."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_TESTS = _MathsGenTestPath(__file__).resolve().parent
for _path in (_MATHSGEN_TESTS.parent, _MATHSGEN_TESTS):
    if str(_path) not in _mathsgen_test_sys.path:
        _mathsgen_test_sys.path.insert(0, str(_path))

from launch_mathsgen import load_engine
from worded_smoke import run


CASES = (
    ("algebra.quadratic.factorisable_non_monic", {
        1: {"equation"}, 2: {"equation", "rectangle_x"},
        3: {"equation", "triangle_base", "number_product"},
        4: {"equation", "rectangle_perimeter"}}),
    ("algebra.rearranging.changing_subject", {
        1: {"equation", "taxi"}, 2: {"equation", "candle"},
        3: {"equation", "temperature", "motion"}, 4: {"equation", "energy", "falling"}}),
)


def main():
    registry = load_engine()
    for generator_id, forms in CASES:
        prefix = generator_id.replace(".", "_") + "_specimen_"
        run(registry, generator_id, forms, generator_id + " specimen", prefix)


if __name__ == "__main__":
    main()