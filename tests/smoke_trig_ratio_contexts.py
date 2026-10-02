"""Applied forms: equal trig ratios across right-angled triangles (trig v5)."""
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
    1: {"equation"},
    2: {"equation", "one_ratio"},
    3: {"equation", "equal_linear"},
    4: {"equation", "equal_quadratic"},
}


def main():
    registry = load_engine()
    run(registry, "geometry.trigonometry.right_angled", FORMS,
        "Equal trig ratios specimen", "trig_ratio_specimen_")


if __name__ == "__main__":
    main()