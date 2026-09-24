"""Explicit imports make curriculum coverage easy to inspect."""
from .core import Registry
from .linear_two_sided import TwoSidedLinear
from .ratio_sharing import RatioSharing
from .common_factor import CommonFactor
from .fraction_addition import FractionAddition
from .percentage_amount import PercentageAmount
from .missing_mean import MissingMean
from .selection_probability import SelectionProbability
from .simplify_ratio import SimplifyRatio
from .fraction_decimal import FractionToDecimal
from .fdp_conversions import FDPConversions
from .two_counter_draws import WithReplacement, WithoutReplacement
from .unknown_bag import UnknownBag
from .prime_factors import PrimeFactorisation, HighestCommonFactor, LowestCommonMultiple
from .index_meaning import IndexMeaning
from .nth_term import LinearNthTerm, QuadraticNthTerm
from .index_product import IndexProduct
from .simultaneous_linear import SimultaneousLinear
from .simultaneous_quadratic import SimultaneousQuadratic
from .reverse_percentage import ReversePercentage
from .combine_ratios import CombineRatios
from .quadratic_monic import MonicQuadratic
from .quadratic_non_monic import NonMonicQuadratic
from .quadratic_formula import QuadraticFormula
from .completing_square import CompletingSquare
from .quadratic_fractions import FractionalQuadratic
from .algebraic_fractions import AlgebraicFractions
from .standard_form import WriteInStandardForm, WriteAsOrdinaryNumber
from .median_range import MedianAndRange
from .fraction_product import FractionMultiplication, FractionDivision
from .mixed_numbers import MixedNumbers
from .expanding_brackets import ExpandDoubleBrackets
from .changing_subject import ChangingSubject
from .difference_of_squares import DifferenceOfSquares
from .index_laws import IndexQuotient, IndexPower
from .rounding import RoundDecimalPlaces, RoundSignificantFigures
from .bounds import MeasurementBounds
from .proportion import DirectProportion, InverseProportion
from .mixture_density import MixtureDensity, MixtureMass
from .percentage_multiplier import FindMultiplier, InterpretMultiplier
from .estimation import EstimateProduct, EstimateQuotient
from .frequency_mean import FrequencyMean
from .grouped_mean import GroupedMean
from .missing_frequency import MissingFrequency
from .frequency_missing_value import FrequencyMissingValue
from .triangle_angles import TriangleAngles
from .pythagoras import PythagorasLengths
from .trigonometry import RightAngledTrigonometry
from .sine_rule import SineRule
from .cosine_rule import CosineRule
from .compound_area import CompoundRectangleArea
from .straight_lines import StraightLines
from .related_lines import RelatedLines
from .inequalities import LinearInequality
from .quadratic_inequalities import QuadraticInequalities
from .index_rules import IndexRules
from .standard_form_calculations import StandardFormCalculations
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
from .error_intervals import ErrorIntervals
from .simple_interest import SimpleInterest
from .product_rule_counting import ProductRuleCounting
from .recipes import Recipes
from .functions import (
    EvaluateFunctions, InverseFunctions, CompositeFunctions, CombinedFunctions,
)
from .number_operations import NegativeNumbers, OrderOfOperations
from .fraction_skills import FractionOfAmount, RecurringDecimals
from .algebra_basics import LikeTerms, SingleBrackets, Substitution
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
from .triple_brackets import TripleBrackets
from .geometric_sequences import GeometricSequences
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
    registry.register(RatioSharing())
    registry.register(CommonFactor())
    registry.register(FractionAddition())
    registry.register(PercentageAmount())
    registry.register(MissingMean())
    registry.register(SelectionProbability())
    registry.register(SimplifyRatio())
    registry.register(FractionToDecimal())
    registry.register(FDPConversions())
    registry.register(WithReplacement())
    registry.register(WithoutReplacement())
    registry.register(UnknownBag())
    registry.register(PrimeFactorisation())
    registry.register(HighestCommonFactor())
    registry.register(LowestCommonMultiple())
    registry.register(IndexMeaning())
    registry.register(LinearNthTerm())
    registry.register(QuadraticNthTerm())
    registry.register(IndexProduct())
    registry.register(SimultaneousLinear())
    registry.register(SimultaneousQuadratic())
    registry.register(ReversePercentage())
    registry.register(CombineRatios())
    registry.register(MonicQuadratic())
    registry.register(NonMonicQuadratic())
    registry.register(QuadraticFormula())
    registry.register(CompletingSquare())
    registry.register(FractionalQuadratic())
    registry.register(AlgebraicFractions())
    registry.register(WriteInStandardForm())
    registry.register(WriteAsOrdinaryNumber())
    registry.register(MedianAndRange())
    registry.register(FractionMultiplication())
    registry.register(FractionDivision())
    registry.register(MixedNumbers())
    registry.register(ExpandDoubleBrackets())
    registry.register(ChangingSubject())
    registry.register(DifferenceOfSquares())
    registry.register(IndexQuotient())
    registry.register(IndexPower())
    registry.register(RoundDecimalPlaces())
    registry.register(Bearings())
    registry.register(VectorGeometry())
    registry.register(Iteration())
    registry.register(CircleEquations())
    registry.register(MoneyProblems())
    registry.register(CurvedSolids())
    registry.register(AlgebraicProof())
    registry.register(BasicProbability())
    registry.register(TripleBrackets())
    registry.register(GeometricSequences())
    registry.register(ColumnVectors())
    registry.register(ExactTrig())
    registry.register(ScatterGraphs())
    registry.register(TravelGraphs())
    registry.register(PlaceValue())
    registry.register(BarPieCharts())
    registry.register(GraphTransformations())
    registry.register(AngleFacts())
    registry.register(ThreeDTrig())
    registry.register(RoundSignificantFigures())
    registry.register(MeasurementBounds())
    registry.register(DirectProportion())
    registry.register(InverseProportion())
    registry.register(MixtureDensity())
    registry.register(MixtureMass())
    registry.register(FindMultiplier())
    registry.register(InterpretMultiplier())
    registry.register(EstimateProduct())
    registry.register(EstimateQuotient())
    registry.register(FrequencyMean())
    registry.register(GroupedMean())
    registry.register(MissingFrequency())
    registry.register(FrequencyMissingValue())
    registry.register(TriangleAngles())
    registry.register(PythagorasLengths())
    registry.register(RightAngledTrigonometry())
    registry.register(SineRule())
    registry.register(CosineRule())
    registry.register(CompoundRectangleArea())
    registry.register(StraightLines())
    registry.register(RelatedLines())
    registry.register(LinearInequality())
    registry.register(QuadraticInequalities())
    registry.register(IndexRules())
    registry.register(StandardFormCalculations())
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
    registry.register(ErrorIntervals())
    registry.register(SimpleInterest())
    registry.register(ProductRuleCounting())
    registry.register(Recipes())
    registry.register(EvaluateFunctions())
    registry.register(InverseFunctions())
    registry.register(CompositeFunctions())
    registry.register(CombinedFunctions())
    registry.register(NegativeNumbers())
    registry.register(OrderOfOperations())
    registry.register(FractionOfAmount())
    registry.register(RecurringDecimals())
    registry.register(LikeTerms())
    registry.register(SingleBrackets())
    registry.register(Substitution())
    registry.register(TwoWayTables())
    registry.register(ExpectedFrequency())
    registry.register(BasicShapeArea())
    registry.register(CaptureRecapture())
    registry.register(FrequencyTrees())
    return registry