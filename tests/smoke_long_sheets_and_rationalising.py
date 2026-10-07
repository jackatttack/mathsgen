"""Check longer topic sheets and focused level-4 rationalising drills."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from launch_mathsgen import load_engine


def main():
    load_engine()
    from mathsgen.catalogue import build_registry
    from mathsgen.blocks import build_block_sheet, MAXIMUM_QUESTIONS_PER_BLOCK
    from mathsgen.build_model import maximum_count, usable_blocks
    from mathsgen.drill import build_drill, drill_skills, drill_stages
    from mathsgen.export import export_worksheet

    registry = build_registry()
    assert MAXIMUM_QUESTIONS_PER_BLOCK == maximum_count("questions") == 200
    block = {
        "generator_id": "algebra.expressions.like_terms",
        "kind": "questions", "levels": [1, 2, 3, 4],
        "count": 200, "apply": False,
    }
    assert usable_blocks([block], registry)[0]["count"] == 200
    sheet = build_block_sheet(registry, [block], "Long topic practice", seed=710)
    assert len(sheet.questions) == 200
    assert len({q.prompt.text for q in sheet.questions}) == 200
    for question in sheet.questions:
        registry.get(question.generator_id).validate(question)
    try:
        build_block_sheet(registry, [dict(block, count=201)], seed=710)
    except ValueError as error:
        assert "at most 200" in str(error)
    else:
        raise AssertionError("Accepted a count above the new limit")
    print("PASS: 200 distinct questions, saved count retained, 201 rejected.")

    surd_id = "number.surds.manipulation"
    offered = {info.id: levels for info, levels in drill_skills(registry)}
    assert 4 in offered[surd_id]
    request = [{"generator_id": surd_id, "levels": [4], "count": 24,
                "apply": 4, "apply_levels": [4]}]
    drill = build_drill(registry, request, "Rationalising denominators", seed=711)
    repeated = build_drill(registry, request, "Rationalising denominators", seed=711)
    assert drill.to_dict() == repeated.to_dict()
    assert len(drill.questions) == 28
    stages = drill_stages(drill)[0][1]
    practice = stages[0][1]
    assert len(practice) == 24
    assert all("denominator" in q.parameters for q in practice)
    assert {len(q.parameters["denominator"]) for q in practice} == {1, 2}
    generator = registry.get(surd_id)
    for question in drill.questions:
        generator.validate(question)
    for question in practice[:8]:
        generator.validate_independently(question)
    for question in practice[:4]:
        print(question.prompt.text, "->", question.answer_display.text)
    result = export_worksheet(
        drill, PROJECT_ROOT / "exports" / "specimens", answers=True)
    print("Specimen:", result["directory"])
    for report in result["pdfs"]:
        print(report["mode"], report["pages"], "pages")
    print("PASS: rationalising drill, both denominator forms, exact checks and export.")


if __name__ == "__main__":
    main()