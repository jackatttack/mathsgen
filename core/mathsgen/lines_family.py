"""Straight-line graphs with parallel and perpendicular lines, as one generator.

Version 3 of algebra.graphs.straight_lines. It absorbs
algebra.graphs.related_lines (retired 2026-09-25,
docs/CONSOLIDATION_PLAN.txt). Levels 1-2 run through the straight-line
source; levels 3-4 through parallel and perpendicular lines.
"""
from .core import GeneratorInfo
from .dispatch import DispatchFamily
from .related_lines import RelatedLines
from .straight_lines import StraightLines


INFO = GeneratorInfo(
    id="algebra.graphs.straight_lines",
    version=3,
    topic="algebra",
    subtopic="straight_line_graphs",
    title="Straight-line graphs: equations, parallel and perpendicular lines",
    difficulty_descriptions={
        1: "Draw a line from y = mx + c, or find the equation of a displayed line.",
        2: "Test points, find a line through two points, rearrange, or find an intersection.",
        3: "Find a parallel line from an intercept or through a point.",
        4: "Find a perpendicular line through a point, rearranging line A first where needed.",
    },
    tags=("graphs", "linear", "gradient", "intercept", "parallel", "perpendicular"),
)


class StraightLinesFamily(DispatchFamily):
    info = INFO
    sources = {
        "straight": StraightLines(),
        "related": RelatedLines(),
    }
    routes = {
        1: (("straight", 1), ("straight", 2)),
        2: (("straight", 3), ("straight", 4)),
        3: (("related", 1), ("related", 2)),
        4: (("related", 3), ("related", 4)),
    }