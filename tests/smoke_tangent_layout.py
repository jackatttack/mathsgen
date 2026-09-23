"""Find which tangent diagrams the renderer refuses, and which labels collide.

The overlap check runs at render time, not at validation time, so a
generator can pass ten thousand independent checks and still produce a
diagram that cannot be drawn.
"""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from launch_mathsgen import load_engine


def label_boxes(asset, scale):
    """Approximate each label's box, so a failure names the guilty pair."""
    from reportlab.pdfbase.pdfmetrics import stringWidth

    boxes = []
    for node in asset["nodes"]:
        if node["type"] != "label":
            continue
        text = node.get("text") or node.get("tex", "")
        width = stringWidth(text, "Helvetica", 11) * 0.9
        x, y = node["point"]
        boxes.append((text, x * scale, y * scale, width, 11))
    return boxes


def crossing_lines(asset, scale):
    """Labels sitting on a drawn line.

    The renderer checks label against label but not label against line, so
    a label can be legally placed and still be unreadable where it crosses
    a radius or a tangent.
    """
    from reportlab.pdfbase.pdfmetrics import stringWidth

    segments = [
        [tuple(point) for point in node["points"]]
        for node in asset["nodes"] if node["type"] == "line"
    ]
    hits = []
    for node in asset["nodes"]:
        if node["type"] != "label":
            continue
        text = node.get("text") or node.get("tex", "")
        half = stringWidth(text, "Helvetica", 11) * 0.45
        x, y = node["point"]
        for (x1, y1), (x2, y2) in segments:
            length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            if not length:
                continue
            # Distance from the label centre to the segment's line, and
            # whether the nearest point falls within the segment itself.
            t = ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / length ** 2
            if not 0 <= t <= 1:
                continue
            near_x, near_y = x1 + t * (x2 - x1), y1 + t * (y2 - y1)
            gap = ((x - near_x) ** 2 + (y - near_y) ** 2) ** 0.5
            # An angle label belongs near the rays it marks, so only a label
            # genuinely written over a line counts: the text's own half-height
            # plus a small margin, not its width.
            if gap < 9:
                hits.append((text, round(gap)))
                break
    return hits


def overlapping(boxes):
    pairs = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            first, second = boxes[i], boxes[j]
            dx = abs(first[1] - second[1])
            dy = abs(first[2] - second[2])
            if dx < (first[3] + second[3]) / 2 and dy < 11:
                pairs.append((first[0], second[0], round(dx), round(dy)))
    return pairs


def main():
    registry = load_engine()
    from mathsgen.visuals import VisualFlowable

    generator = registry.get("geometry.circle_theorems.tangents")
    failures = []

    for level in range(1, 5):
        for seed in range(60):
            question = generator.generate(seed, level)
            for asset in question.visual_assets("questions"):
                for width in (360, 250):
                    try:
                        VisualFlowable(asset).wrap(width, 400)
                    except ValueError:
                        scale = width / asset["width"]
                        failures.append(
                            (level, seed, width, overlapping(label_boxes(asset, scale)))
                        )
                        break

    # Label-on-line is a separate defect: the renderer accepts it, but a
    # label written across a radius is unreadable on the page.
    crossings = []
    for level in range(1, 5):
        for seed in range(60):
            question = generator.generate(seed, level)
            for asset in question.visual_assets("questions"):
                hits = crossing_lines(asset, 1.0)
                if hits:
                    crossings.append((level, seed, hits))

    if crossings:
        print("{} diagrams have labels crossing lines.".format(len(crossings)))
        for level, seed, hits in crossings[:6]:
            print("Level {} seed {}: {}".format(level, seed, hits))
    else:
        print("No label crosses a drawn line.")

    if not failures:
        print("PASS: every tangent diagram lays out at both widths.")
        return

    print("{} diagrams failed.".format(len(failures)))
    for level, seed, width, pairs in failures[:6]:
        print("Level {} seed {} at width {}:".format(level, seed, width))
        for text_a, text_b, dx, dy in pairs:
            print("  '{}' vs '{}': dx {} dy {}".format(text_a, text_b, dx, dy))
        if not pairs:
            print("  (no pair found by the approximation)")


if __name__ == "__main__":
    main()