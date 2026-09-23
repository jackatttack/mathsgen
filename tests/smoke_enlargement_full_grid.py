"""Verify full square enlargement grids and preserved exact geometry."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import require
    from mathsgen.enlargements import FACTORS
    from mathsgen.visuals import VisualFlowable

    generator = registry.get("geometry.transformations.enlargement")
    checked = 0
    renders = 0
    for level in range(1, 5):
        seen = set()
        for seed in range(100):
            question = generator.generate(seed, level)
            generator.validate_independently(question)
            seen.add(question.parameters["factor"])
            require(question.generator_version == 2, "Expected version 2")
            for mode in ("questions", "answers"):
                for asset in question.visual_assets(mode):
                    x_low, x_high = asset["x_range"]
                    y_low, y_high = asset["y_range"]
                    require(
                        x_high - x_low == y_high - y_low == 28,
                        "Grid must be square",
                    )
                    require(asset["equal_units"] is True, "Unequal axis units")
                    require(
                        asset["x_step"] / asset["minor_divisions"] == 1
                        and asset["y_step"] / asset["minor_divisions"] == 1,
                        "Expected one-unit grid squares",
                    )
                    for name in ("object", "image"):
                        for x, y in question.parameters[name]:
                            require(
                                x_low < x < x_high and y_low < y < y_high,
                                "Shape lacks a grid margin",
                            )
                    for width in (250, 360):
                        flowable = VisualFlowable(asset)
                        actual_width, actual_height = flowable.wrap(width, 700)
                        require(
                            actual_width <= width and 0 < actual_height <= 700,
                            "Diagram does not fit",
                        )
                        renders += 1
            checked += 1
        require(seen == set(FACTORS[level]), "Scale-factor coverage incomplete")
    print(
        "PASS:", checked, "enlargement questions;", renders,
        "diagram renders; all scale factors, square grids,",
        "one-unit spacing, grid margins and independent geometry.",
    )


if __name__ == "__main__":
    main()