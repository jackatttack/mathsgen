"""Sequences: linear, quadratic and geometric, as one generator.

Version 3 of algebra.sequences.linear_nth. It absorbs
algebra.sequences.quadratic_nth and algebra.sequences.geometric (retired
2026-09-25, docs/CONSOLIDATION_PLAN.txt). Geometric level 4 is the only
calculator source level, so it has level 4 to itself.
"""
from .core import GeneratorInfo
from .dispatch import DispatchFamily
from .geometric_sequences import GeometricSequences
from .nth_term import LinearNthTerm, QuadraticNthTerm


INFO = GeneratorInfo(
    id="algebra.sequences.linear_nth",
    version=3,
    topic="algebra",
    subtopic="sequences",
    title="Sequences: linear, quadratic and geometric",
    difficulty_descriptions={
        1: "Find the nth term of an arithmetic sequence, increasing or decreasing.",
        2: "Fractional common differences; continue a geometric sequence or find its ratio, nth term or a term.",
        3: "Find the nth term of a quadratic sequence; find a geometric first term or a surd-sequence term.",
        4: "Geometric problems: find x from three terms, or the first term above a limit.",
    },
    tags=("sequences", "nth_term", "linear", "quadratic", "geometric"),
)


class SequencesFamily(DispatchFamily):
    info = INFO
    sources = {
        "linear": LinearNthTerm(),
        "quadratic": QuadraticNthTerm(),
        "geometric": GeometricSequences(),
    }
    routes = {
        1: (("linear", 1), ("linear", 2), ("linear", 3)),
        2: (("linear", 4), ("geometric", 1), ("geometric", 2)),
        3: (("quadratic", 1), ("quadratic", 2), ("quadratic", 3), ("quadratic", 4),
            ("geometric", 3)),
        4: (("geometric", 4),),
    }