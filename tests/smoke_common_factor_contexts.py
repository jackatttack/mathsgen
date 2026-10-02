"""Applied forms: common-factor factorising (rectangles, multiples, incomplete)."""
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


FORMS = {
    1: {"equation", "rectangle_side"},
    2: {"equation", "always_multiple"},
    3: {"equation", "rectangle_letter"},
    4: {"equation", "incomplete"},
}


def main():
    registry = load_engine()
    run(registry, "algebra.factorising.common_factor", FORMS,
        "Common factor applied forms specimen", "common_factor_contexts_specimen_")


if __name__ == "__main__":
    main()