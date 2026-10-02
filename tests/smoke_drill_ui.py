"""Drill UI smoke: the Worksheet Maker imports and builds valid drill blocks."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
for module_name in list(sys.modules):
    if module_name == "mathsgen" or module_name.startswith("mathsgen."):
        del sys.modules[module_name]

from mathsgen.catalogue import build_registry
from mathsgen.drill import DEFAULT_APPLY_ITEMS, DRILL_SKILLS, build_drill
from mathsgen.worksheet_ui import make_drill_blocks


def expect_error(action, fragment):
    try:
        action()
    except ValueError as error:
        assert fragment in str(error), "Wrong message: " + str(error)
        return
    raise AssertionError("Expected a ValueError containing: " + fragment)


registry = build_registry()
chosen = {"number.fractions.addition", "algebra.factorising.common_factor",
          "geometry.bearings.bearings"}   # bearings is not a drill skill: ignored
blocks = make_drill_blocks(registry, chosen, 10, {1, 2, 3})
assert [block["generator_id"] for block in blocks] == [
    "algebra.factorising.common_factor", "number.fractions.addition",
], blocks
fractions = blocks[1]
assert fractions["levels"] == [1, 3], "Drill levels limited to the skill's drill levels"
assert fractions["apply"] == DEFAULT_APPLY_ITEMS
assert fractions["apply_levels"] == [1, 2, 3], "Apply uses every chosen level the skill has"
assert all(block["apply"] == 0 for block in
           make_drill_blocks(registry, chosen, 10, {1}, apply=False))
build_drill(registry, blocks, "UI drill", seed=3)

expect_error(lambda: make_drill_blocks(registry, set(), 10, {1}), "Tick at least one")
expect_error(lambda: make_drill_blocks(registry, chosen, 0, {1}), "positive number")
expect_error(lambda: make_drill_blocks(registry, chosen, 61, {1}), "at most 60")
expect_error(lambda: make_drill_blocks(
    registry, {"number.fractions.of_amount"}, 10, {2}), "difficulty 1 only")
print("drill skills offered:", len(DRILL_SKILLS))
print("smoke_drill_ui: PASS")