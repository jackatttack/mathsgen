"""Check compact sector diagrams and export a real worksheet PDF."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))


from pathlib import Path

from launch_mathsgen import load_engine


def main():
    from mathsgen.visuals import drawing_for
    from mathsgen.worksheets import build_worksheet
    from mathsgen.export import export_worksheet

    registry = load_engine()

    spec = {
        "title": "Compact sector diagram layout",
        "shuffle": False,
        "sections": [{
            "generator_ids": ["geometry.circles.sectors"],
            "count": 2,
            "difficulties": [3],
        }],
    }

    worksheet = build_worksheet(spec, 20260921, registry)

    assert len(worksheet.questions) == 2

    for question in worksheet.questions:
        assets = question.visual_assets("questions")
        assert len(assets) == 1

        scene = assets[0]
        assert scene["kind"] == "scene"

        drawing = drawing_for(scene, 238)

        original_width = 238
        original_height = scene["height"] * 238 / scene["width"]
        if scene.get("caption"):
            original_height += 22

        assert drawing.width < original_width, (
            "Diagram retained its unused horizontal canvas space"
        )
        assert drawing.height < original_height, (
            "Diagram retained its unused vertical canvas space"
        )

        # Suppressing the standard caption must produce the same drawing
        # dimensions as a scene that never had that caption.
        if scene.get("caption", "").strip().casefold() == "not drawn accurately":
            without_caption = dict(scene, caption="")
            plain = drawing_for(without_caption, 238)

            assert abs(drawing.width - plain.width) < 0.001
            assert abs(drawing.height - plain.height) < 0.001

        print(
            "PASS: sector diagram {:.1f} x {:.1f} points "
            "(original canvas {:.1f} x {:.1f})".format(
                drawing.width,
                drawing.height,
                original_width,
                original_height,
            )
        )

    # Exercise the complete PDF renderer, not just individual diagrams.
    output_root = Path(__file__).resolve().parent.parent / "exports"
    report = export_worksheet(
        worksheet,
        output_root,
        answers=True,
    )

    assert report["question_count"] == 2

    for pdf in report["pdfs"]:
        path = Path(pdf["path"])
        assert path.exists()
        assert path.read_bytes()[:5] == b"%PDF-"
        print("PASS: exported {} ({} bytes)".format(
            path.name,
            path.stat().st_size,
        ))
        print("PDF: " + str(path))

    print("PASS: compact sector diagram PDF export complete")
    print("VISUAL REVIEW: pending device inspection")


if __name__ == "__main__":
    main()