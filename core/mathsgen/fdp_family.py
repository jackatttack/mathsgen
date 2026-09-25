"""Fractions, decimals and percentages, as one generator.

Version 3 of number.fdp.fraction_to_decimal. It absorbs
number.fdp.conversions (retired 2026-09-25, docs/CONSOLIDATION_PLAN.txt).
Each level pairs the same source level of both generators.
"""
from .core import GeneratorInfo
from .dispatch import DispatchFamily
from .fdp_conversions import FDPConversions
from .fraction_decimal import FractionToDecimal


INFO = GeneratorInfo(
    id="number.fdp.fraction_to_decimal",
    version=3,
    topic="number",
    subtopic="fdp_conversion",
    title="Fractions, decimals and percentages",
    difficulty_descriptions={
        1: "Common equivalences; familiar fractions to decimals and back.",
        2: "Eighths, twentieths and fiftieths; hundredths and thousandths, or ordering.",
        3: "Values above one, percentages with a half, improper fractions and mixed numbers.",
        4: "Complete an equivalent fraction, decimal and percentage; negative improper fractions.",
    },
    tags=("fractions", "decimals", "percentages", "conversion"),
)


class FDPFamily(DispatchFamily):
    info = INFO
    sources = {
        "conversions": FDPConversions(),
        "fraction_decimal": FractionToDecimal(),
    }
    routes = {level: (("conversions", level), ("fraction_decimal", level))
              for level in (1, 2, 3, 4)}