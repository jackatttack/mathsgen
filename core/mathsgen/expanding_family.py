"""Expanding brackets: single, double and triple, as one generator.

Version 3 of algebra.expanding.double_brackets. It absorbs
algebra.expanding.single_brackets and algebra.expanding.triple_brackets
(retired 2026-09-25, docs/CONSOLIDATION_PLAN.txt). Levels climb from one
bracket to three.
"""
from .algebra_basics import SingleBrackets
from .core import GeneratorInfo
from .dispatch import DispatchFamily
from .expanding_brackets import ExpandDoubleBrackets
from .triple_brackets import TripleBrackets


INFO = GeneratorInfo(
    id="algebra.expanding.double_brackets",
    version=3,
    topic="algebra",
    subtopic="expanding",
    title="Expanding brackets: single, double and triple",
    difficulty_descriptions={
        1: "Expand single brackets, including negative and letter multipliers; expand two and simplify.",
        2: "Letter multipliers on two brackets; expand double brackets with positive or negative constants.",
        3: "Squared brackets and a leading coefficient; x times two brackets, or three brackets.",
        4: "Three brackets with coefficients above one, or a cubed bracket.",
    },
    tags=("algebra", "expanding", "brackets", "quadratics"),
)


class ExpandingFamily(DispatchFamily):
    info = INFO
    sources = {
        "single": SingleBrackets(),
        "double": ExpandDoubleBrackets(),
        "triple": TripleBrackets(),
    }
    routes = {
        1: (("single", 1), ("single", 2), ("single", 3)),
        2: (("single", 4), ("double", 1), ("double", 2)),
        3: (("double", 3), ("double", 4), ("triple", 1), ("triple", 2)),
        4: (("triple", 3), ("triple", 4)),
    }