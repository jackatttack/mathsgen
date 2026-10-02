"""Applied forms: column vectors (points on a line) and simple interest after tax."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_TESTS = _MathsGenTestPath(__file__).resolve().parent
for _path in (_MATHSGEN_TESTS.parent, _MATHSGEN_TESTS):
    if str(_path) not in _mathsgen_test_sys.path:
        _mathsgen_test_sys.path.insert(0, str(_path))

# Pythonista keeps imported modules between runs; drop stale mathsgen copies.
for _name in list(_mathsgen_test_sys.modules):
    if _name == "mathsgen" or _name.startswith("mathsgen."):
        del _mathsgen_test_sys.modules[_name]

from launch_mathsgen import load_engine
from worded_smoke import run


CASES = (
    ("geometry.vectors.column", {
        1: {"equation"}, 2: {"equation", "midpoint_end"},
        3: {"equation", "divide_segment"}, 4: {"equation", "extend_line"}}),
    ("number.percentages.simple_interest", {
        1: {"equation"}, 2: {"equation", "after_tax"},
        3: {"equation", "tax_rate"}, 4: {"equation", "tax_principal"}}),
)


def main():
    registry = load_engine()
    for generator_id, forms in CASES:
        prefix = generator_id.replace(".", "_") + "_contexts_specimen_"
        run(registry, generator_id, forms, generator_id + " applied forms", prefix)


if __name__ == "__main__":
    main()