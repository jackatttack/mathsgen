"""algebra.simultaneous.linear v2: bare and worded forms."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_TESTS = _MathsGenTestPath(__file__).resolve().parent
for _path in (_MATHSGEN_TESTS.parent, _MATHSGEN_TESTS):
    if str(_path) not in _mathsgen_test_sys.path:
        _mathsgen_test_sys.path.insert(0, str(_path))

from launch_mathsgen import load_engine
from worded_smoke import run


EXPECTED_FORMS = {
    1: {"equation", "sum_difference", "shop_matching"},
    2: {"equation", "shop_scaled"},
    3: {"equation", "tickets", "coins"},
    4: {"equation", "shop_followup", "rectangle"},
}


def main():
    registry = load_engine()
    from mathsgen.catalogue import source_registry
    run(source_registry(registry), "algebra.simultaneous.linear", EXPECTED_FORMS,
        "Simultaneous equations specimen", "simultaneous_contexts_specimen_")


if __name__ == "__main__":
    main()