"""Drill mode smoke: staged build rules, reproducibility, rejections, every
DRILL_SKILLS entry with an apply stage, and a specimen PDF."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

for module_name in list(sys.modules):
    if module_name == "mathsgen" or module_name.startswith("mathsgen."):
        del sys.modules[module_name]

from mathsgen.catalogue import build_registry
from mathsgen.core import canonical_json
from mathsgen.drill import DRILL_SKILLS, build_drill, drill_stages, is_bare
from mathsgen.export import export_worksheet


SPECIMEN_BLOCKS = [
    {"generator_id": "algebra.expressions.like_terms", "levels": [1, 2], "count": 12,
     "apply": 4},
    {"generator_id": "algebra.factorising.common_factor", "levels": [1, 2, 3], "count": 9},
    {"generator_id": "number.percentages.of_amount", "levels": [1, 2], "count": 12,
     "apply": 4, "apply_levels": [1, 2, 3, 4]},
    {"generator_id": "number.fractions.addition", "levels": [1, 3], "count": 9,
     "apply": 4, "apply_levels": [1, 2, 3, 4]},
    {"generator_id": "algebra.expanding.double_brackets", "levels": [1, 2, 3], "count": 6,
     "apply": 3, "apply_levels": [1, 2, 3, 4]},
    {"generator_id": "number.operations.order", "levels": [1, 2, 3, 4], "count": 6},
    {"generator_id": "geometry.trigonometry.right_angled", "levels": [1, 2], "count": 6,
     "apply": 2},
    {"generator_id": "geometry.angles.parallel_lines", "levels": [1, 2, 3], "count": 6},
    {"generator_id": "algebra.graphs.straight_lines", "levels": [1], "count": 8},
    {"generator_id": "number.rounding.decimal_places", "levels": [1], "count": 12},
]
ITEMS_PER_LEVEL_CHECK = 4
APPLY_ITEMS_CHECK = 3


def expect_error(action, fragment):
    try:
        action()
    except ValueError as error:
        assert fragment in str(error), "Wrong message: " + str(error)
        return
    raise AssertionError("Expected a ValueError containing: " + fragment)


def expected_total(blocks):
    return sum(
        block["count"] * len(block["levels"]) + block.get("apply", 0) for block in blocks
    )


def check_stages(registry, worksheet):
    fingerprints = set()
    for block, stages in drill_stages(worksheet):
        for stage, questions in stages:
            assert len(questions) == stage["count"]
            for question in questions:
                assert question.generator_id == block["generator_id"]
                registry.get(question.generator_id).validate(question)
                fingerprints.add(canonical_json([
                    question.prompt.text, question.prompt.math_tex,
                    question.visual_assets("questions"),
                ]))
            levels = [question.difficulty for question in questions]
            if stage["kind"] == "drill":
                assert set(levels) == {stage["level"]}, "Drill stage must keep its level"
                if stage.get("route"):
                    assert all(
                        [question.parameters["source"], question.parameters["source_level"]]
                        == stage["route"] for question in questions
                    ), "Drill part must keep its route"
            else:
                assert set(levels) <= set(stage["levels"]), "Apply level outside its levels"
                assert levels == sorted(levels), "Apply items must run easiest first"
        assert stages[0][0]["kind"] == "drill"
        assert all(stage["kind"] == "drill" for stage, _ in stages[:-1])
    assert len(fingerprints) == len(worksheet.questions), "Displayed prompts must be distinct"


def check_build(registry):
    first = build_drill(registry, SPECIMEN_BLOCKS, "Drill specimen", seed=7)
    second = build_drill(registry, SPECIMEN_BLOCKS, "Drill specimen", seed=7)
    assert first.id == second.id, "Same seed must rebuild the same drill"
    other = build_drill(registry, SPECIMEN_BLOCKS, "Drill specimen", seed=8)
    assert other.id != first.id, "A different seed must change the drill"
    assert len(first.questions) == expected_total(SPECIMEN_BLOCKS)
    check_stages(registry, first)
    print("build: PASS ({} items in {} exercises)".format(
        len(first.questions), len(SPECIMEN_BLOCKS)))
    return first


def check_rejections(registry):
    expect_error(lambda: build_drill(registry, []), "at least one block")
    expect_error(lambda: build_drill(registry, [
        {"generator_id": "no.such.generator", "count": 5}]), "Unknown generator")
    expect_error(lambda: build_drill(registry, [
        {"generator_id": "algebra.expressions.like_terms", "levels": [5], "count": 5}]),
        "drill difficulty 5")
    expect_error(lambda: build_drill(registry, [
        {"generator_id": "algebra.expressions.like_terms", "count": 0}]), "count from 1")
    expect_error(lambda: build_drill(registry, [
        {"generator_id": "algebra.expressions.like_terms", "count": 4, "apply": 13}]),
        "apply count")
    print("rejections: PASS")


def print_export(worksheet, result):
    bare_counts = [
        [sum(is_bare(question) for question in questions) for _, questions in stages]
        for _, stages in drill_stages(worksheet)
    ]
    for report in result["pdfs"]:
        print("{}: {} pages".format(report["mode"], report["pages"]))
        if report["mode"] != "questions":
            continue
        for block, bares in zip(report["blocks"], bare_counts):
            parts = []
            for stage, bare in zip(block["stages"], bares):
                parts.append("{}{}:{}c s{} b{} d{}".format(
                    "A" if stage["kind"] == "apply" else "L" + stage["part"],
                    stage["items"], stage["columns"], stage["shared"], bare,
                    stage["diagrams"]))
            print("   {:<30} {}".format(block["title"][:30], "  ".join(parts)))
    print("   folder:", Path(result["directory"]).name)


def check_every_skill(registry):
    """Every DRILL_SKILLS entry must build and render, including an apply stage."""
    blocks = []
    for generator_id, levels in DRILL_SKILLS.items():
        info = registry.get(generator_id).info
        blocks.append({
            "generator_id": generator_id, "levels": list(levels),
            "count": ITEMS_PER_LEVEL_CHECK, "apply": APPLY_ITEMS_CHECK,
            "apply_levels": sorted(info.difficulty_descriptions),
        })
    worksheet = build_drill(registry, blocks, "Every drill skill", seed=11)
    check_stages(registry, worksheet)
    result = export_worksheet(worksheet, PROJECT_ROOT / "exports" / "specimens", answers=True)
    print("every skill: PASS ({} skills)".format(len(blocks)))
    print_export(worksheet, result)


def main():
    registry = build_registry()
    specimen = check_build(registry)
    check_rejections(registry)
    result = export_worksheet(specimen, PROJECT_ROOT / "exports" / "specimens", answers=True)
    print("specimen (per stage: L/A items:columns, s shared, b bare):")
    print_export(specimen, result)
    check_every_skill(registry)
    print("smoke_drill: PASS")


main()