"""Ratio: simplifying, sharing and combining, as one generator.

Version 3 of ratio.simplifying. It absorbs ratio.sharing and
ratio.combining.three_part (retired 2026-09-25,
docs/CONSOLIDATION_PLAN.txt). The worded-context modules key their shares by
source ID, which the dispatcher restores during validation.
"""
from .combine_ratios import CombineRatios
from .core import GeneratorInfo
from .dispatch import DispatchFamily
from .ratio_sharing import RatioSharing
from .simplify_ratio import SimplifyRatio


INFO = GeneratorInfo(
    id="ratio.simplifying",
    version=3,
    topic="ratio",
    subtopic="ratio",
    title="Ratio: simplifying, sharing and combining",
    difficulty_descriptions={
        1: "Simplify two- and three-part ratios, or share a quantity between two people.",
        2: "Ratios with decimals or fractions; share between three, from a difference, or in money.",
        3: "Ratios in mixed units; share a length or after a change; combine ratios with a shared part.",
        4: "Combine ratios by scaling both, from reversed pairs, or to find a count from a total.",
    },
    tags=("ratio", "simplifying", "sharing", "combining", "units"),
)


class RatioFamily(DispatchFamily):
    info = INFO
    sources = {
        "simplify": SimplifyRatio(),
        "share": RatioSharing(),
        "combine": CombineRatios(),
    }
    routes = {
        1: (("simplify", 1), ("simplify", 2), ("share", 1)),
        2: (("simplify", 3), ("share", 2), ("share", 3)),
        3: (("simplify", 4), ("share", 4), ("combine", 1), ("combine", 2)),
        4: (("combine", 3), ("combine", 4)),
    }