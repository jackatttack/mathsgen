"""Direct and inverse proportion, as one generator.

Version 3 of ratio.proportion.direct. It absorbs ratio.proportion.inverse
(retired 2026-09-25, docs/CONSOLIDATION_PLAN.txt). Each level pairs the same
source level of both relationships, with their contexts.
"""
from .core import GeneratorInfo
from .dispatch import DispatchFamily
from .proportion import DirectProportion, InverseProportion


INFO = GeneratorInfo(
    id="ratio.proportion.direct",
    version=4,
    topic="ratio",
    subtopic="proportion",
    title="Direct and inverse proportion",
    difficulty_descriptions={
        1: "Direct or inverse proportion with a whole-number constant; or workers and days.",
        2: "A larger constant or exact fractional answer; or beat a deadline with workers.",
        3: "Proportional or inversely proportional to a square; or workers join partway.",
        4: "Square relationships with a fractional answer; or the least workforce needed.",
    },
    tags=("proportion", "direct", "inverse", "constant_of_proportionality"),
)


class ProportionFamily(DispatchFamily):
    info = INFO
    sources = {
        "direct": DirectProportion(),
        "inverse": InverseProportion(),
    }
    routes = {level: (("direct", level), ("inverse", level)) for level in (1, 2, 3, 4)}