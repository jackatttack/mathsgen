"""Separate sequence topics: exact answers, drill routes, variety and PDFs."""
import sys
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from launch_mathsgen import load_engine


def rejects(generator, question):
    try:
        generator.validate(question)
    except ValueError:
        return
    raise AssertionError("Corrupted sequence accepted")


def main():
    load_engine()
    from mathsgen.catalogue import build_registry
    from mathsgen.sequence_practice import (
        ArithmeticSequences, QuadraticSequences, GeometricSequenceFamily,
    )
    from mathsgen.drill import build_drill, drill_stages
    from mathsgen.drill_pdf import shared_instruction
    from mathsgen.curriculum import load_level_tags
    from mathsgen.build_model import library_sections, drill_levels_by_skill
    from mathsgen.export import export_worksheet

    registry = build_registry()
    tags = load_level_tags(registry)
    sections = library_sections(registry, tags, drill_levels_by_skill(registry))
    visible = {entry["generator_id"]: entry["title"]
               for _, entries in sections for entry in entries}
    checked = 0
    for family in (ArithmeticSequences(), QuadraticSequences(), GeometricSequenceFamily()):
        assert visible[family.info.id] == family.info.title
        for level in (1, 2, 3, 4):
            for task in ("terms", "nth"):
                source = family.sources[task]
                for seed in range(40):
                    q = source.generate(seed, level)
                    source.validate(q)
                    source.validate_independently(q)
                    assert q.to_dict() == source.generate(seed, level).to_dict()
                    rejects(source, replace(q, answer={}))
                    rejects(source, replace(q, prompt=replace(q.prompt, text="Wrong prompt")))
                    damaged = deepcopy(q.parameters)
                    if "coefficients" in damaged:
                        damaged["coefficients"][2] = "999"
                    else:
                        damaged["ratio"] = "0"
                    rejects(source, replace(q, parameters=damaged))
                    checked += 1
                print(family.info.title, "L" + str(level), task,
                      q.prompt.text, "->", q.answer_display.text)
            for seed in range(8):
                q = family.generate(seed, level)
                family.validate(q)
                family.validate_independently(q)
        # Exercise the maximum drill count, including the narrowest pools.
        request = [{"generator_id": family.info.id, "levels": [1, 2, 3, 4],
                    "count": 60}]
        sheet = build_drill(registry, request, family.info.title, seed=712)
        assert len(sheet.questions) == 240
        stages = drill_stages(sheet)[0][1]
        assert len(stages) == 8
        assert [stage["route"][0] for stage, _ in stages] == ["terms", "nth"] * 4
        for stage, questions in stages:
            assert len(questions) == 30
            assert all([q.parameters["source"], q.parameters["source_level"]]
                       == stage["route"] for q in questions)
            assert shared_instruction(questions)[2] == len(questions)
        for count in (1, 2, 5):
            small = build_drill(registry, [{
                "generator_id": family.info.id, "levels": [1], "count": count,
            }], seed=713)
            assert len(small.questions) == count
            assert all(q.parameters["source"] in ("terms", "nth") for q in small.questions)
        specimen = build_drill(registry, [{
            "generator_id": family.info.id, "levels": [1, 2, 3, 4],
            "count": 8, "apply": 4,
        }], family.info.title, seed=714)
        result = export_worksheet(
            specimen, PROJECT_ROOT / "exports" / "specimens", answers=True)
        print("SPECIMEN:", result["directory"])
        for report in result["pdfs"]:
            print(report["mode"], report["pages"], "pages")
    print("PASS:", checked, "practice checks; three topics, maximum drills, curriculum and PDFs.")


if __name__ == "__main__":
    main()