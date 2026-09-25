"""Rounding to decimal places and significant figures, as one generator.

Version 3 of number.rounding.decimal_places. It absorbs
number.rounding.significant_figures (retired 2026-09-25,
docs/CONSOLIDATION_PLAN.txt). Each level pairs the same source level of both
modes, so calculator-needing levels (level 2) are never mixed with
non-calculator ones.
"""
from .core import GeneratorInfo
from .dispatch import DispatchFamily
from .rounding import RoundDecimalPlaces, RoundSignificantFigures


INFO = GeneratorInfo(
    id="number.rounding.decimal_places",
    version=3,
    topic="number",
    subtopic="rounding",
    title="Rounding: decimal places and significant figures",
    difficulty_descriptions={
        1: "Round to one decimal place or one or two significant figures, bare or in context.",
        2: "Round to more places or figures, or calculate and then round.",
        3: "A digit of 5, a leading-zero decimal, or round one number two ways.",
        4: "Rounding that carries, sharing money to the penny, or a fraction to significant figures.",
    },
    tags=("rounding", "decimals", "significant_figures", "accuracy"),
)


class RoundingFamily(DispatchFamily):
    info = INFO
    sources = {
        "places": RoundDecimalPlaces(),
        "figures": RoundSignificantFigures(),
    }
    routes = {level: (("places", level), ("figures", level)) for level in (1, 2, 3, 4)}