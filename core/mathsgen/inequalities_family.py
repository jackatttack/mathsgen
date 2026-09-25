"""Inequalities, linear and quadratic, as one generator.

Version 3 of algebra.inequalities.linear. It absorbs
algebra.inequalities.quadratic (retired 2026-09-25,
docs/CONSOLIDATION_PLAN.txt). Levels 1-2 run through all four linear source
levels (with their worded contexts); levels 3-4 run through the quadratic
source.
"""
from .core import GeneratorInfo
from .dispatch import DispatchFamily
from .inequalities import LinearInequality
from .quadratic_inequalities import QuadraticInequalities


INFO = GeneratorInfo(
    id="algebra.inequalities.linear",
    version=3,
    topic="algebra",
    subtopic="inequalities",
    title="Inequalities: linear and quadratic",
    difficulty_descriptions={
        1: "Two-step inequalities or unknowns on both sides; or whole-number budget problems.",
        2: "Dividing by a negative reverses the sign; list integer solutions of a double inequality.",
        3: "Solve a quadratic inequality from factorised form or by factorising a monic quadratic.",
        4: "Non-monic quadratic inequalities, or rearrange from both sides first.",
    },
    tags=("inequalities", "linear", "quadratics", "integers", "intervals"),
)


class InequalitiesFamily(DispatchFamily):
    info = INFO
    sources = {
        "linear": LinearInequality(),
        "quadratic": QuadraticInequalities(),
    }
    routes = {
        1: (("linear", 1), ("linear", 2)),
        2: (("linear", 3), ("linear", 4)),
        3: (("quadratic", 1), ("quadratic", 2)),
        4: (("quadratic", 3), ("quadratic", 4)),
    }