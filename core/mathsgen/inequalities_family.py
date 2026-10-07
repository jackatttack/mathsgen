"""Linear, quadratic and combined quadratic inequalities.

Version 4 of algebra.inequalities.linear. The quadratic source ID was
retired on 2026-09-25; see docs/CONSOLIDATION_PLAN.txt.
Levels 1-2 retain the linear sources, level 3 introduces quadratics,
and level 4 includes intersections of two quadratic solution sets.
"""
from .core import GeneratorInfo
from .dispatch import DispatchFamily
from .inequalities import LinearInequality
from .quadratic_inequalities import QuadraticInequalities
from .combined_quadratic_inequalities import CombinedQuadraticInequalities


INFO = GeneratorInfo(
    id="algebra.inequalities.linear",
    version=4,
    topic="algebra",
    subtopic="inequalities",
    title="Inequalities: linear and quadratic",
    difficulty_descriptions={
        1: "Two-step inequalities or unknowns on both sides; or whole-number budget problems.",
        2: "Dividing by a negative reverses the sign; list integer solutions of a double inequality.",
        3: "Solve a quadratic inequality from factorised form or by factorising a monic quadratic.",
        4: "Non-monic or rearranged quadratics; intersect two quadratic solution sets, including fractional boundaries.",
    },
    tags=("inequalities", "linear", "quadratics", "integers", "intervals"),
)


class InequalitiesFamily(DispatchFamily):
    info = INFO
    sources = {
        "linear": LinearInequality(),
        "quadratic": QuadraticInequalities(),
        "combined": CombinedQuadraticInequalities(),
    }
    routes = {
        1: (("linear", 1), ("linear", 2)),
        2: (("linear", 3), ("linear", 4)),
        3: (("quadratic", 1), ("quadratic", 2)),
        4: (("quadratic", 3), ("quadratic", 4),
            ("combined", 1), ("combined", 2)),
    }