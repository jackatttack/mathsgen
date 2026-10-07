"""Check current L4 inequality routes in the actual drill renderer."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.drill import build_drill, drill_stages
    from mathsgen.export import export_worksheet
    from mathsgen.question_actions import content_digest

    blocks = [{
        "generator_id": "algebra.inequalities.linear",
        "levels": [4], "count": 24, "apply": 4, "apply_levels": [4],
    }]
    sheet = build_drill(registry, blocks, "Quadratic inequality practice", seed=19)
    repeated = build_drill(registry, blocks, "Quadratic inequality practice", seed=19)
    assert sheet.id == repeated.id
    assert [q.to_dict() for q in sheet.questions] == [
        q.to_dict() for q in repeated.questions]
    assert len(sheet.questions) == 28
    assert len({content_digest(q, True) for q in sheet.questions}) == 28
    routes = set()
    generator = registry.get("algebra.inequalities.linear")
    for block, stages in drill_stages(sheet):
        for stage, questions in stages:
            assert len(questions) == stage["count"]
            for q in questions:
                generator.validate(q)
                if stage["kind"] == "drill":
                    routes.add((q.parameters["source"], q.parameters["source_level"]))
    assert routes == set(generator.routes[4]), routes
    result = export_worksheet(
        sheet, PROJECT_ROOT / "exports" / "specimens", answers=True)
    print("SPECIMEN:", result["directory"])
    for report in result["pdfs"]:
        print(report["mode"], report["pages"], "pages")
    print("PASS: 28 distinct items, all four L4 drill routes, reproducibility and export.")
    print("Device review still needed for mixed single/combined-question density.")


if __name__ == "__main__":
    main()