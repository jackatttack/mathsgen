"""algebra.inequalities.linear v2: bare and worded forms."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_TESTS = _MathsGenTestPath(__file__).resolve().parent
for _path in (_MATHSGEN_TESTS.parent, _MATHSGEN_TESTS):
    if str(_path) not in _mathsgen_test_sys.path:
        _mathsgen_test_sys.path.insert(0, str(_path))

from launch_mathsgen import load_engine
from worded_smoke import run


EXPECTED_FORMS = {
    1: {"equation", "budget"},
    2: {"equation", "exceeds"},
    3: {"equation", "falling"},
    4: {"equation", "rectangle_double", "number_double"},
}


def main():
    run(load_engine(), "algebra.inequalities.linear", EXPECTED_FORMS,
        "Linear inequalities specimen", "inequalities_contexts_specimen_")


if __name__ == "__main__":
    main()