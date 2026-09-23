"""Check equal-count selection and ordering without presenting the UI."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from collections import Counter
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import require
    from mathsgen.worksheet_ui import make_spec
    from mathsgen.worksheets import build_worksheet

    selected = {info.id for info in registry.list()}
    spec = make_spec(registry, selected, 5, {1, 2}, "UI test", False)
    ordered = build_worksheet(spec, 12345, registry)
    require(
        Counter(q.generator_id for q in ordered.questions) == {key: 5 for key in selected},
        "Unequal generator counts",
    )
    expected_order = [
        info.id for info in registry.list() if info.id in selected
        for _ in range(5)
    ]
    require(
        [q.generator_id for q in ordered.questions] == expected_order,
        "Set order did not group question types",
    )
    mixed_spec = make_spec(registry, selected, 5, {1, 2}, "UI test", True)
    mixed = build_worksheet(mixed_spec, 12345, registry)
    require(
        Counter(q.id for q in mixed.questions) == Counter(q.id for q in ordered.questions),
        "Random ordering changed the questions",
    )
    require(
        [q.id for q in mixed.questions] != [q.id for q in ordered.questions],
        "Random ordering did not change order",
    )
    try:
        make_spec(registry, set(), 5, {1}, "Empty", False)
    except ValueError:
        pass
    else:
        raise AssertionError("Empty selection accepted")

    print("PASS: {} generators discovered.".format(len(selected)))
    print("PASS: 5 per type, {} questions total.".format(len(ordered.questions)))
    print("PASS: grouped set order and shuffled order preserve the same questions.")
    print("Next: run launch_mathsgen.py directly to check the native interface.")


if __name__ == "__main__":
    main()