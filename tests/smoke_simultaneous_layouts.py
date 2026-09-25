"""Check every rearranged layout actually appears at level 4.

Three layouts are defined; if one never survives construction the level is
narrower than it looks, and a student would see the same shape every time.
This counts which layouts occur across many seeds and prints one example of
each, so a missing branch is obvious rather than inferred from samples.
"""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from launch_mathsgen import load_engine

SEEDS = 300


def main():
    registry = load_engine()
    from mathsgen.catalogue import source_registry
    registry = source_registry(registry)
    generator = registry.get("algebra.simultaneous.linear")

    counts = {}
    examples = {}
    for seed in range(SEEDS):
        question = generator.generate(seed, 4)
        if "context" in question.parameters:
            continue  # worded forms are covered by smoke_simultaneous_contexts.py
        for layout in question.parameters["layouts"]:
            counts[layout] = counts.get(layout, 0) + 1
        key = tuple(question.parameters["layouts"])
        examples.setdefault(key, question.prompt.text)

    print("Layout occurrences across {} questions:".format(SEEDS))
    for layout in ("y_left", "x_right", "constant_left"):
        print("  {}: {}".format(layout, counts.get(layout, 0)))

    print("Distinct layout pairs seen: {}".format(len(examples)))
    for key in sorted(examples):
        print("  {}".format(" + ".join(key)))
        print("    " + examples[key])

    missing = [
        layout for layout in ("y_left", "x_right", "constant_left")
        if not counts.get(layout)
    ]
    if missing:
        print("MISSING layouts: " + ", ".join(missing))
        raise SystemExit(1)
    print("PASS: every layout appears.")


if __name__ == "__main__":
    main()