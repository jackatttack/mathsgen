"""The IB AI SL registry, kept apart from the GCSE catalogue on purpose.

GCSE worksheets, exam papers, mini papers, drills, quick start and the
curriculum tags all read mathsgen.catalogue.build_registry(). Several of
those paths require every registered generator to carry GCSE curriculum
tags, so an IB generator there would either break them or leak into GCSE
papers. Register IB generators here, and only here.
"""
from ..core import Registry
from .binomial import BinomialDistribution
from .chi_squared import ChiSquaredTests
from .compound_interest import CompoundInterest
from .correlation import Correlation
from .descriptive import DescriptiveStatistics
from .discrete import DiscreteDistributions
from .exponential import ExponentialModels
from .bearings import Bearings
from .integration import Integration
from .optimisation import Optimisation
from .sectors import ArcsSectors
from .solids import Solids
from .triangles import TriangleTrigonometry
from .voronoi import VoronoiDiagrams
from .logarithms import LogarithmicScales
from .sinusoidal import SinusoidalModels
from .tangents import TangentsNormals
from .variation import Variation
from .loans import Loans
from .normal import NormalDistribution
from .sequences import SequenceModels
from .t_test import TwoSampleTTest
from .trapezoidal import TrapezoidalRule
from .venn_tree import VennAndTrees


GENERATORS = (
    CompoundInterest, Loans, SequenceModels, TrapezoidalRule,
    NormalDistribution, BinomialDistribution, ChiSquaredTests, TwoSampleTTest,
    DescriptiveStatistics, Correlation, VennAndTrees, DiscreteDistributions,
    TangentsNormals, ExponentialModels, Variation, SinusoidalModels, LogarithmicScales,
    Optimisation, Integration,
    TriangleTrigonometry, ArcsSectors, Solids, Bearings, VoronoiDiagrams,
)


def build_ib_registry():
    registry = Registry()
    for generator_class in GENERATORS:
        registry.register(generator_class())
    return registry


def build_sheet_registry(gcse_registry):
    """GCSE and IB generators together, for the Build sheet only.

    The Build sheet is where a teacher picks skills by hand, so IB skills
    may sit there beside GCSE ones. Never pass this registry to exam papers,
    mini papers, quick start, drill or curriculum code: those stay GCSE-only.
    """
    combined = Registry()
    for registry in (gcse_registry, build_ib_registry()):
        for info in registry.list():
            combined.register(registry.get(info.id))
    return combined


def library_entries(registry):
    """Skill-board entries for the IB generators in registry.

    The same shape as build_model.library_sections entries, without GCSE
    spec codes, years or grades; an empty grade list keeps IB skills out of
    GCSE grade-band filters.
    """
    from .common import TOPIC
    entries = {}
    for info in registry.list():
        if info.topic != TOPIC:
            continue
        levels = sorted(info.difficulty_descriptions)
        entries[info.id] = {
            "generator_id": info.id,
            "title": info.title,
            "detail": "IB AI SL · L{}–{}".format(levels[0], levels[-1]),
            "search": " ".join([info.title, info.id, "ib ai sl"] + list(info.tags)).lower(),
            "grades": [],
            "years": [],
            "order": (0, 0, info.title),
        }
    return entries