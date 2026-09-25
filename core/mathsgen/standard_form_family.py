"""Standard form: converting and calculating, as one generator.

Version 3 of number.standard_form.calculations. It absorbs
number.standard_form.from_decimal and number.standard_form.to_decimal
(retired 2026-09-25, docs/CONSOLIDATION_PLAN.txt). The three well-built
source classes are unchanged and no longer registered; this family routes
each level to them (see mathsgen/dispatch.py).

Levels
    1  Write numbers in standard form or as ordinary numbers, large and
       small, bare or in a context.
    2  Internal zeros, correcting a non-standard number, and ordering a mix
       of standard-form and ordinary numbers.
    3  Multiply or divide in standard form, bare or in a context.
    4  Calculations that need renormalising, and adding or subtracting.
"""
from .core import GeneratorInfo
from .dispatch import DispatchFamily
from .standard_form import WriteAsOrdinaryNumber, WriteInStandardForm
from .standard_form_calculations import StandardFormCalculations


INFO = GeneratorInfo(
    id="number.standard_form.calculations",
    version=3,
    topic="number",
    subtopic="standard_form",
    title="Standard form: converting and calculating",
    difficulty_descriptions={
        1: "Write numbers in standard form or as ordinary numbers, bare or in context.",
        2: "Internal zeros, correcting non-standard numbers, and ordering.",
        3: "Multiply or divide in standard form, bare or in context.",
        4: "Calculations that need renormalising, and adding or subtracting.",
    },
    tags=("standard form", "indices", "place value", "calculation", "exact"),
)


class StandardForm(DispatchFamily):
    info = INFO
    sources = {
        "write_standard": WriteInStandardForm(),
        "write_ordinary": WriteAsOrdinaryNumber(),
        "calculate": StandardFormCalculations(),
    }
    # (source, source level) pairs for each level, chosen with equal weight.
    routes = {
        1: (("write_standard", 1), ("write_standard", 2),
            ("write_ordinary", 1), ("write_ordinary", 2)),
        2: (("write_standard", 3), ("write_standard", 4),
            ("write_ordinary", 3), ("write_ordinary", 4)),
        3: (("calculate", 1), ("calculate", 2)),
        4: (("calculate", 3), ("calculate", 4)),
    }