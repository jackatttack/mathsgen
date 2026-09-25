"""Error intervals and bounds, as one generator.

Version 3 of number.bounds.measurement. It absorbs
number.bounds.error_intervals (retired 2026-09-25,
docs/CONSOLIDATION_PLAN.txt). Only level 4 (speed or density bounds) needs a
calculator, so no level mixes calculator and non-calculator routes.
"""
from .bounds import MeasurementBounds
from .core import GeneratorInfo
from .dispatch import DispatchFamily
from .error_intervals import ErrorIntervals


INFO = GeneratorInfo(
    id="number.bounds.measurement",
    version=3,
    topic="number",
    subtopic="bounds",
    title="Error intervals and bounds",
    difficulty_descriptions={
        1: "Error intervals and bounds for values rounded to whole units.",
        2: "Error intervals and bounds for values rounded to decimal places.",
        3: "Error intervals for significant figures or truncation; bounds of a sum or difference.",
        4: "Bounds of a speed or density calculated from two measurements.",
    },
    tags=("bounds", "error intervals", "accuracy", "measurement", "compound_measures"),
)


class BoundsFamily(DispatchFamily):
    info = INFO
    sources = {
        "interval": ErrorIntervals(),
        "measurement": MeasurementBounds(),
    }
    routes = {
        1: (("interval", 1), ("measurement", 1)),
        2: (("interval", 2), ("measurement", 2)),
        3: (("interval", 3), ("interval", 4), ("measurement", 3)),
        4: (("measurement", 4),),
    }