"""Prime factors, HCF and LCM, as one generator.

Version 3 of number.primes.factorisation. It absorbs number.factors.hcf and
number.multiples.lcm (retired 2026-09-25, docs/CONSOLIDATION_PLAN.txt). The
source classes in prime_factors.py, with their worded contexts, are unchanged
and no longer registered; this family routes each level to them.
"""
from .core import GeneratorInfo
from .dispatch import DispatchFamily
from .prime_factors import HighestCommonFactor, LowestCommonMultiple, PrimeFactorisation


INFO = GeneratorInfo(
    id="number.primes.factorisation",
    version=3,
    topic="number",
    subtopic="prime_factors",
    title="Prime factors, HCF and LCM",
    difficulty_descriptions={
        1: "Prime factorisation with two primes or a repeated prime; HCF or LCM where one number divides the other.",
        2: "Three primes or a square root from prime factors; HCF or LCM with shared factors, bare or in context.",
        3: "Factors with 11 or 13, or the smallest multiplier for a square or cube; HCF or LCM of three numbers.",
        4: "HCF or LCM from supplied prime decompositions, or equal bags and matching packs.",
    },
    tags=("prime_factors", "indices", "hcf", "lcm"),
)


class PrimeFactorFamily(DispatchFamily):
    info = INFO
    sources = {
        "prime": PrimeFactorisation(),
        "hcf": HighestCommonFactor(),
        "lcm": LowestCommonMultiple(),
    }
    routes = {
        1: (("prime", 1), ("prime", 2), ("hcf", 1), ("lcm", 1)),
        2: (("prime", 3), ("hcf", 2), ("lcm", 2)),
        3: (("prime", 4), ("hcf", 3), ("lcm", 3)),
        4: (("hcf", 4), ("lcm", 4)),
    }