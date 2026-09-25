"""Functions: notation, inverses, composites and combined problems, as one generator.

Version 3 of algebra.functions.evaluate. It absorbs algebra.functions.inverse,
algebra.functions.composite and algebra.functions.combined (retired
2026-09-25, docs/CONSOLIDATION_PLAN.txt). All four sources live in
functions.py and are unchanged; levels are arranged by draft grade.
"""
from .core import GeneratorInfo
from .dispatch import DispatchFamily
from .functions import (
    CombinedFunctions, CompositeFunctions, EvaluateFunctions, InverseFunctions,
)


INFO = GeneratorInfo(
    id="algebra.functions.evaluate",
    version=3,
    topic="algebra",
    subtopic="functions",
    title="Functions: notation, inverses and composites",
    difficulty_descriptions={
        1: "Evaluate linear and quadratic functions, or solve f(x) = k.",
        2: "Substitute an expression into f; evaluate or find fg(x) for linear functions; invert ax + b.",
        3: "Invert (ax + b)/c or a/(x + b); composites with x^2 + c or into a quadratic; solve fg(x) = k.",
        4: "Invert (ax + b)/(x + c); solve f(x) = f^-1(x) or fg(x) = k with x^2 + c; find a from ff(n) = k.",
    },
    tags=("functions", "function_notation", "inverse_functions", "composite_functions"),
)


class FunctionsFamily(DispatchFamily):
    info = INFO
    sources = {
        "evaluate": EvaluateFunctions(),
        "inverse": InverseFunctions(),
        "composite": CompositeFunctions(),
        "combined": CombinedFunctions(),
    }
    routes = {
        1: (("evaluate", 1), ("evaluate", 2), ("evaluate", 3)),
        2: (("evaluate", 4), ("composite", 1), ("composite", 2), ("inverse", 1)),
        3: (("inverse", 2), ("inverse", 3), ("composite", 3), ("composite", 4),
            ("combined", 1)),
        4: (("inverse", 4), ("combined", 2), ("combined", 3), ("combined", 4)),
    }