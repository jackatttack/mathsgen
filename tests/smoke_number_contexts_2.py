"""Worded forms for negatives and the four fraction families."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_TESTS = _MathsGenTestPath(__file__).resolve().parent
for _path in (_MATHSGEN_TESTS.parent, _MATHSGEN_TESTS):
    if str(_path) not in _mathsgen_test_sys.path:
        _mathsgen_test_sys.path.insert(0, str(_path))

from launch_mathsgen import load_engine
from worded_smoke import run


CASES = (
    ("number.integers.negatives", {
        1: {"equation", "temperature_change"},
        2: {"equation", "temperature_difference", "bank"},
        3: {"equation", "falling", "quiz"},
        4: {"equation", "mean_temps", "missing_temp"}}),
    ("number.fractions.addition", {
        1: {"equation"}, 2: {"equation", "split_nested"},
        3: {"equation", "split_coprime"}, 4: {"equation", "split_count"}}),
    ("number.fractions.multiplication", {
        1: {"equation"}, 2: {"equation", "part_of_part"},
        3: {"equation", "batches"}, 4: {"equation", "rug"}}),
    ("number.fractions.division", {
        1: {"equation"}, 2: {"equation", "share_cake"},
        3: {"equation", "pieces"}, 4: {"equation", "shelves"}}),
    ("number.fractions.mixed_numbers", {
        1: {"equation"}, 2: {"equation", "mixed_same"},
        3: {"equation", "mixed_different"}, 4: {"equation", "paint"}}),
)


def main():
    registry = load_engine()
    for generator_id, forms in CASES:
        prefix = generator_id.replace(".", "_") + "_specimen_"
        run(registry, generator_id, forms, generator_id + " specimen", prefix)


if __name__ == "__main__":
    main()