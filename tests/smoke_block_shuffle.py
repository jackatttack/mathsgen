"""Shuffled block sheets: same questions, random reproducible order, drills in place.

Run from Forge: RUN icloud:projects/mathsgen/tests/smoke_block_shuffle.py
"""
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))
for name in list(sys.modules):
    if name == "mathsgen" or name.startswith("mathsgen."):
        del sys.modules[name]

from mathsgen.blocks import build_block_sheet
from mathsgen.catalogue import build_registry

BLOCKS = [
    {"generator_id": "number.fractions.addition", "kind": "questions", "levels": [1], "count": 5},
    {"generator_id": "number.fractions.addition", "kind": "drill", "levels": [1], "count": 3},
    {"generator_id": "ratio.changing.algebra", "kind": "questions", "levels": [1, 2], "count": 5},
]
failures = []


def check(condition, message):
    print(("ok   " if condition else "FAIL ") + message)
    if not condition:
        failures.append(message)


def ids(sheet, kind):
    return [question.id
            for segment in sheet.specification["segments"] if segment["kind"] == kind
            for question in sheet.questions[segment["start"]:segment["start"] + segment["count"]]]


registry = build_registry()
plain = build_block_sheet(registry, BLOCKS, "Shuffle smoke", seed=11)
mixed = build_block_sheet(registry, BLOCKS, "Shuffle smoke", seed=11, shuffle=True)
again = build_block_sheet(registry, BLOCKS, "Shuffle smoke", seed=11, shuffle=True)

check([s["kind"] for s in plain.specification["segments"]] == ["questions", "drill", "questions"],
      "set order keeps one segment per block")
check([s["kind"] for s in mixed.specification["segments"]] == ["questions", "drill"],
      "shuffle pools question blocks where the first stood; drill keeps its place")
check(sorted(ids(plain, "questions")) == sorted(ids(mixed, "questions")),
      "shuffle keeps exactly the same questions")
check(ids(plain, "questions") != ids(mixed, "questions"), "shuffle changes the order")
check(ids(plain, "drill") == ids(mixed, "drill"), "drill questions unchanged")
check([q.id for q in mixed.questions] == [q.id for q in again.questions],
      "same seed gives the same shuffled order")
check(mixed.specification["shuffle"] is True and plain.specification["shuffle"] is False,
      "specification records the shuffle choice")

print("RESULT: " + ("FAIL" if failures else "PASS"))
if failures:
    raise SystemExit(1)