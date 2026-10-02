"""Focused applied similarity smoke using the shared worded-form checks."""
import sys
from pathlib import Path
TESTS = Path(__file__).resolve().parent
for path in (TESTS.parent, TESTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
for name in list(sys.modules):
    if name == "mathsgen" or name.startswith("mathsgen."):
        del sys.modules[name]

from launch_mathsgen import load_engine
from worded_smoke import run


def main():
    registry = load_engine()
    run(registry, "geometry.similarity.scale_factors", {
        1: {"equation"},
        2: {"equation", "cylinder_height_to_mass"},
        3: {"equation", "cylinder_mass_to_height"},
        4: {"equation", "three_cylinder_ratios"},
    }, "Similar cylinders: lengths, masses and areas", "similar_cylinders_")
    # Check every applied diagram at the actual worksheet widths.
    from mathsgen import similar_cylinder_contexts as forms
    from mathsgen.circle_figures import CHECK_WIDTHS, labels_clear
    from mathsgen.visuals import drawing_for
    from mathsgen.core import require
    generator = registry.get("geometry.similarity.scale_factors")
    for level in (2, 3, 4):
        checked = 0
        for seed in range(120):
            q = generator.generate(seed, level)
            if q.parameters.get("context") not in forms.CONTEXTS:
                continue
            generator.validate_independently(q)
            scene = q.visual_assets("questions")[0]
            require(labels_clear(scene), "Cylinder label crosses a line")
            for width in CHECK_WIDTHS:
                drawing_for(scene, width)
            checked += 1
        require(checked >= 20, "Insufficient applied coverage")
        print("L{}: {} applied diagrams; independent invariants and three widths".format(
            level, checked))
    print("PASS: cylinder diagrams and independent ratio checks")


if __name__ == "__main__":
    main()