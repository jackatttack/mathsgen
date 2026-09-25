"""Explicit imports make curriculum coverage easy to inspect."""
from .core import Registry
from .linear_two_sided import TwoSidedLinear
from .common_factor import CommonFactor
from .fraction_addition import FractionAddition
from .percentage_amount import PercentageAmount
from .selection_probability import SelectionProbability
from .ratio_family import RatioFamily
from .fdp_family import FDPFamily
from .two_counter_draws import WithReplacement, WithoutReplacement
from .unknown_bag import UnknownBag
from .prime_factor_family import PrimeFactorFamily
from .index_meaning import IndexMeaning
from .sequences_family import SequencesFamily
from .simultaneous_family import SimultaneousFamily
from .reverse_percentage import ReversePercentage
from .quadratic_monic import MonicQuadratic
from .quadratic_non_monic import NonMonicQuadratic
from .quadratic_formula import QuadraticFormula
from .completing_square import CompletingSquare
from .quadratic_fractions import FractionalQuadratic
from .algebraic_fractions import AlgebraicFractions
from .standard_form_family import StandardForm
from .dispatch import SourceAwareRegistry
from .median_range import MedianAndRange
from .fraction_product import FractionMultiplication, FractionDivision
from .mixed_numbers import MixedNumbers
from .expanding_family import ExpandingFamily
from .changing_subject import ChangingSubject
from .difference_of_squares import DifferenceOfSquares
from .rounding_family import RoundingFamily
from .bounds_family import BoundsFamily
from .proportion_family import ProportionFamily
from .mixture_family import MixtureFamily
from .percentage_multiplier import FindMultiplier, InterpretMultiplier
from .estimation_family import EstimationFamily
from .frequency_tables import FrequencyTables
from .triangle_angles import TriangleAngles
from .pythagoras import PythagorasLengths
from .trigonometry import RightAngledTrigonometry
from .sine_rule import SineRule
from .cosine_rule import CosineRule
from .compound_area import CompoundRectangleArea
from .lines_family import StraightLinesFamily
from .inequalities_family import InequalitiesFamily
from .indices import LawsOfIndices

from .unit_conversion import AreaVolumeConversion
from .compound_interest import CompoundChange
from .surds import SurdManipulation
from .compound_measures import CompoundMeasures
from .box_plot_questions import BoxPlots
from .histograms import Histograms
from .cumulative_frequency import CumulativeFrequencyConstruction
from .parallel_angles import ParallelAngles
from .polygon_angles import PolygonAngles
from .similar_shapes import SimilarShapes
from .enlargements import Enlargements
from .reflections import Reflections
from .rotations import Rotations
from .translations import Translations
from .combined_transformations import CombinedTransformations
from .painting import PaintingBudget
from .related_solids import RelatedSolidVolumes
from .tank_flows import TankFlows
from .circle_centre_angles import CircleCentreAngles
from .circle_measures import CircleMeasures
from .sectors import Sectors
from .prism_volume import PrismVolume
from .prism_surface_area import PrismSurfaceArea
from .probability_trees import ProbabilityTrees
from .venn_notation import VennNotation
from .venn_probability import VennProbability
from .venn_completion import VennCompletion
from .same_segment_angles import SameSegmentAngles
from .cyclic_quadrilateral import CyclicQuadrilateral
from .tangent_theorems import TangentTheorems
from .alternate_segment import AlternateSegment
from .multi_step_circles import MultiStepCircles
from .simple_interest import SimpleInterest
from .product_rule_counting import ProductRuleCounting
from .recipes import Recipes
from .functions_family import FunctionsFamily
from .number_operations import NegativeNumbers, OrderOfOperations
from .fraction_skills import FractionOfAmount, RecurringDecimals
from .algebra_basics import LikeTerms, Substitution
from .probability_data import TwoWayTables, ExpectedFrequency
from .area_shapes import BasicShapeArea
from .capture_recapture import CaptureRecapture
from .frequency_trees import FrequencyTrees
from .bearings import Bearings
from .vector_geometry import VectorGeometry
from .iteration import Iteration
from .circle_equations import CircleEquations
from .money_problems import MoneyProblems
from .curved_solids import CurvedSolids
from .algebraic_proof import AlgebraicProof
from .basic_probability import BasicProbability
from .column_vectors import ColumnVectors
from .exact_trig import ExactTrig
from .scatter_graphs import ScatterGraphs
from .travel_graphs import TravelGraphs
from .place_value import PlaceValue
from .bar_pie_charts import BarPieCharts
from .graph_transformations import GraphTransformations
from .angle_facts import AngleFacts
from .three_d_trig import ThreeDTrig


def build_registry():
    registry = Registry()
    registry.register(TwoSidedLinear())
    registry.register(CommonFactor())
    registry.register(FractionAddition())
    registry.register(PercentageAmount())
    registry.register(SelectionProbability())
    registry.register(RatioFamily())
    registry.register(FDPFamily())
    registry.register(WithReplacement())
    registry.register(WithoutReplacement())
    registry.register(UnknownBag())
    registry.register(PrimeFactorFamily())
    registry.register(IndexMeaning())
    registry.register(SequencesFamily())
    registry.register(SimultaneousFamily())
    registry.register(ReversePercentage())
    registry.register(MonicQuadratic())
    registry.register(NonMonicQuadratic())
    registry.register(QuadraticFormula())
    registry.register(CompletingSquare())
    registry.register(FractionalQuadratic())
    registry.register(AlgebraicFractions())

    registry.register(MedianAndRange())
    registry.register(FractionMultiplication())
    registry.register(FractionDivision())
    registry.register(MixedNumbers())
    registry.register(ExpandingFamily())
    registry.register(ChangingSubject())
    registry.register(DifferenceOfSquares())
    registry.register(RoundingFamily())
    registry.register(Bearings())
    registry.register(VectorGeometry())
    registry.register(Iteration())
    registry.register(CircleEquations())
    registry.register(MoneyProblems())
    registry.register(CurvedSolids())
    registry.register(AlgebraicProof())
    registry.register(BasicProbability())
    registry.register(ColumnVectors())
    registry.register(ExactTrig())
    registry.register(ScatterGraphs())
    registry.register(TravelGraphs())
    registry.register(PlaceValue())
    registry.register(BarPieCharts())
    registry.register(GraphTransformations())
    registry.register(AngleFacts())
    registry.register(ThreeDTrig())
    registry.register(BoundsFamily())
    registry.register(ProportionFamily())
    registry.register(MixtureFamily())
    registry.register(FindMultiplier())
    registry.register(InterpretMultiplier())
    registry.register(EstimationFamily())
    registry.register(FrequencyTables())
    registry.register(TriangleAngles())
    registry.register(PythagorasLengths())
    registry.register(RightAngledTrigonometry())
    registry.register(SineRule())
    registry.register(CosineRule())
    registry.register(CompoundRectangleArea())
    registry.register(StraightLinesFamily())
    registry.register(InequalitiesFamily())
    registry.register(LawsOfIndices())
    registry.register(StandardForm())
    registry.register(AreaVolumeConversion())
    registry.register(CompoundChange())
    registry.register(SurdManipulation())
    registry.register(CompoundMeasures())
    registry.register(BoxPlots())
    registry.register(Histograms())
    registry.register(CumulativeFrequencyConstruction())
    registry.register(ParallelAngles())
    registry.register(PolygonAngles())
    registry.register(SimilarShapes())
    registry.register(Enlargements())
    registry.register(Reflections())
    registry.register(Rotations())
    registry.register(Translations())
    registry.register(CombinedTransformations())
    registry.register(PaintingBudget())
    registry.register(RelatedSolidVolumes())
    registry.register(TankFlows())
    registry.register(CircleCentreAngles())
    registry.register(CircleMeasures())
    registry.register(Sectors())
    registry.register(PrismVolume())
    registry.register(PrismSurfaceArea())
    registry.register(ProbabilityTrees())
    registry.register(VennNotation())
    registry.register(VennProbability())
    registry.register(VennCompletion())
    registry.register(SameSegmentAngles())
    registry.register(CyclicQuadrilateral())
    registry.register(TangentTheorems())
    registry.register(AlternateSegment())
    registry.register(MultiStepCircles())
    registry.register(SimpleInterest())
    registry.register(ProductRuleCounting())
    registry.register(Recipes())
    registry.register(FunctionsFamily())
    registry.register(NegativeNumbers())
    registry.register(OrderOfOperations())
    registry.register(FractionOfAmount())
    registry.register(RecurringDecimals())
    registry.register(LikeTerms())
    registry.register(Substitution())
    registry.register(TwoWayTables())
    registry.register(ExpectedFrequency())
    registry.register(BasicShapeArea())
    registry.register(CaptureRecapture())
    registry.register(FrequencyTrees())
    return registry


# Registered generators built by routing to unregistered source classes
# (mathsgen/dispatch.py). Keep in step with the registrations above.
DISPATCH_FAMILIES = (
    StandardForm, PrimeFactorFamily, RoundingFamily, EstimationFamily,
    BoundsFamily, FDPFamily, MixtureFamily, ProportionFamily,
    SimultaneousFamily, InequalitiesFamily, StraightLinesFamily,
    FunctionsFamily, SequencesFamily, ExpandingFamily, RatioFamily,
)


def source_registry(registry):
    """A registry view that also serves every dispatch source under its own ID.

    For smokes that test the source classes directly; worksheets, papers and
    the CLI use the real registry.
    """
    sources = {}
    for family in DISPATCH_FAMILIES:
        for source in family.sources.values():
            sources[source.info.id] = source
    return SourceAwareRegistry(registry, sources)