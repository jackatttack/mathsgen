"""Mixtures: density and total mass, as one generator.

Version 3 of number.compound.mixture_density. It absorbs
number.compound.mixture_mass (retired 2026-09-25,
docs/CONSOLIDATION_PLAN.txt). Both sources need a calculator at every level.
"""
from .core import GeneratorInfo
from .dispatch import DispatchFamily
from .mixture_density import MixtureDensity, MixtureMass


INFO = GeneratorInfo(
    id="number.compound.mixture_density",
    version=3,
    topic="number",
    subtopic="compound_measures",
    title="Mixtures: density and total mass",
    difficulty_descriptions={
        1: "Volume and density stated for both liquids; find the mixture's density or mass.",
        2: "Densities to one decimal place; each liquid states any two quantities.",
        3: "Densities close together; each liquid states any two quantities.",
        4: "Densities to two decimal places; each liquid states any two quantities.",
    },
    tags=("density", "compound_measures", "mixture", "mass"),
)


class MixtureFamily(DispatchFamily):
    info = INFO
    sources = {
        "density": MixtureDensity(),
        "mass": MixtureMass(),
    }
    routes = {level: (("density", level), ("mass", level)) for level in (1, 2, 3, 4)}