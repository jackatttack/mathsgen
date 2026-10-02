"""Applied forms from Jack's inbox, batch 2: money, bags and workers."""
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


def forms(*names):
    return {1: {"equation"} | ({names[0]} if names[0] else set()),
            2: {"equation", names[1]}, 3: {"equation", names[2]}, 4: {"equation", names[3]}}


def check_family_dispatch(registry):
    """The registered proportion family must carry workers problems end to end."""
    family = registry.get("ratio.proportion.direct")
    applied = 0
    for seed in range(60):
        for level in (1, 2, 3, 4):
            question = family.generate(seed, level)
            family.validate(question)
            family.validate_independently(question)
            if isinstance(question.parameters["inner"].get("context"), str):
                applied += 1
    assert applied > 0, "The family produced no workers problems"
    print("proportion family dispatch: PASS ({} workers problems in 240)".format(applied))


def main():
    registry = load_engine()
    from mathsgen.catalogue import source_registry
    sources = source_registry(registry)
    run(registry, "ratio.money.problems",
        forms(None, "currency_compare", "fuel_compare", "fuel_percent"),
        "Money applied forms", "money_contexts_specimen_")
    run(registry, "probability.basics.events",
        forms(None, "bag_total", "bag_ratio", "bag_added"),
        "Bag probability applied forms", "bag_contexts_specimen_")
    run(sources, "ratio.proportion.inverse",
        forms("workers_days", "workers_deadline", "workers_join", "workers_needed"),
        "Workers applied forms", "workers_contexts_specimen_")
    check_family_dispatch(registry)


if __name__ == "__main__":
    main()