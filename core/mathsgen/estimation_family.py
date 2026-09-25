"""Estimating products and quotients, as one generator.

Version 3 of number.estimation.product. It absorbs number.estimation.quotient
(retired 2026-09-25, docs/CONSOLIDATION_PLAN.txt). Each level pairs the same
source level of both operations, with their worded contexts.
"""
from .core import GeneratorInfo
from .dispatch import DispatchFamily
from .estimation import EstimateProduct, EstimateQuotient


INFO = GeneratorInfo(
    id="number.estimation.product",
    version=3,
    topic="number",
    subtopic="estimation",
    title="Estimation: products and quotients",
    difficulty_descriptions={
        1: "Estimate products and quotients of two- and three-digit numbers, bare or in context.",
        2: "Larger whole numbers.",
        3: "Numbers with one decimal place.",
        4: "A value below one, so rounding shifts the place value.",
    },
    tags=("estimation", "rounding", "significant_figures", "division"),
)


class EstimationFamily(DispatchFamily):
    info = INFO
    sources = {
        "product": EstimateProduct(),
        "quotient": EstimateQuotient(),
    }
    routes = {level: (("product", level), ("quotient", level)) for level in (1, 2, 3, 4)}