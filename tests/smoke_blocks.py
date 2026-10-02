"""Smoke: block sheets keep the teacher's order, counts and settings.

Builds the example sheet (a fractions drill, six level-3 simultaneous
equations, eight level 1-4 percentages), then checks segments, levels,
reproducibility and that bad blocks give clear messages.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from launch_mathsgen import load_engine
from mathsgen.blocks import build_block_sheet
from mathsgen.drill import DEFAULT_APPLY_ITEMS, drill_skills

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def expect_error(registry, blocks, fragment, label):
    try:
        build_block_sheet(registry, blocks, "Bad", seed=1)
    except ValueError as error:
        check(fragment in str(error), "{}: message was {!r}".format(label, str(error)))
        return str(error)
    failures.append(label + ": no error raised")
    return ""


def main():
    registry = load_engine()
    drills = {info.id: levels for info, levels in drill_skills(registry)}
    drill_id = ("number.fractions.addition" if "number.fractions.addition" in drills
                else sorted(drills)[0])
    drill_levels = sorted(drills[drill_id])[:2]
    blocks = [
        {"generator_id": drill_id, "kind": "drill", "levels": drill_levels,
         "count": 4, "apply": True},
        {"generator_id": "algebra.simultaneous.linear", "kind": "questions",
         "levels": [3], "count": 6},
        {"generator_id": "number.percentages.of_amount", "kind": "questions",
         "levels": [1, 2, 3, 4], "count": 8},
    ]
    sheet = build_block_sheet(registry, blocks, "Block sheet smoke", seed=11)
    segments = sheet.specification["segments"]
    check([s["kind"] for s in segments] == ["drill", "questions", "questions"],
          "segment kinds or order wrong")
    check(sum(s["count"] for s in segments) == len(sheet.questions),
          "segment counts do not cover the questions")
    check(segments[0]["count"] == 4 * len(drill_levels) + DEFAULT_APPLY_ITEMS,
          "drill block size wrong: {}".format(segments[0]["count"]))
    check(segments[1]["count"] == 6 and segments[2]["count"] == 8,
          "question block sizes wrong")
    starts = [s["start"] for s in segments]
    check(starts == sorted(starts) and starts[0] == 0, "segments out of order")
    middle = sheet.questions[segments[1]["start"]:segments[1]["start"] + 6]
    check(all(q.difficulty == 3 for q in middle), "block 2 not all level 3")
    last = sheet.questions[segments[2]["start"]:]
    check({q.difficulty for q in last} <= {1, 2, 3, 4}, "block 3 levels wrong")
    again = build_block_sheet(registry, blocks, "Block sheet smoke", seed=11)
    check(again.id == sheet.id, "same seed gave a different sheet")
    other = build_block_sheet(registry, blocks, "Block sheet smoke", seed=12)
    check(other.id != sheet.id, "different seed gave the same sheet")

    no_drill = sorted({info.id for info in registry.list()} - set(drills))[0]
    messages = [
        expect_error(registry, [], "Add at least one block", "empty sheet"),
        expect_error(registry, [{"generator_id": no_drill, "kind": "drill",
                                 "levels": [1], "count": 3}],
                     "has no drill form", "drill on a non-drill skill"),
        expect_error(registry, [{"generator_id": "algebra.simultaneous.linear",
                                 "levels": [9], "count": 3}],
                     "at difficulty", "unsupported level"),
        expect_error(registry, [blocks[1], {"generator_id": "nope",
                                            "levels": [1], "count": 3}],
                     "Block 2", "unknown skill names its block"),
    ]

    print("Drill block:", drill_id, "levels", drill_levels)
    print("Segments:", [(s["kind"], s["count"]) for s in segments])
    print("Questions:", len(sheet.questions))
    for message in messages:
        print("  message:", message)
    for failure in failures:
        print("FAIL", failure)
    print("RESULT:", "FAIL" if failures else "PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())