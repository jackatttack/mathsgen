"""Simultaneous equations, linear and linear-quadratic, as one generator.

Version 3 of algebra.simultaneous.linear. It absorbs
algebra.simultaneous.linear_quadratic (retired 2026-09-25,
docs/CONSOLIDATION_PLAN.txt). Levels 1-2 run through all four linear source
levels (with their worded contexts); levels 3-4 run through the
linear-quadratic source, so the grades climb steadily.
"""
from .core import GeneratorInfo
from .dispatch import DispatchFamily
from .simultaneous_linear import SimultaneousLinear
from .simultaneous_quadratic import SimultaneousQuadratic


INFO = GeneratorInfo(
    id="algebra.simultaneous.linear",
    version=3,
    topic="algebra",
    subtopic="simultaneous_equations",
    title="Simultaneous equations: linear and linear-quadratic",
    difficulty_descriptions={
        1: "Eliminate with matching or scaled coefficients; or sum-and-difference and shop problems.",
        2: "Scale both equations or collect terms first; or form and solve from tickets or coins.",
        3: "Substitute a line into a parabola, rearranging first where needed.",
        4: "Substitute into an equation containing xy, or intersect a line and a circle.",
    },
    tags=("algebra", "simultaneous", "elimination", "substitution", "quadratics"),
)


class SimultaneousFamily(DispatchFamily):
    info = INFO
    sources = {
        "linear": SimultaneousLinear(),
        "quadratic": SimultaneousQuadratic(),
    }
    routes = {
        1: (("linear", 1), ("linear", 2)),
        2: (("linear", 3), ("linear", 4)),
        3: (("quadratic", 1), ("quadratic", 2)),
        4: (("quadratic", 3), ("quadratic", 4)),
    }