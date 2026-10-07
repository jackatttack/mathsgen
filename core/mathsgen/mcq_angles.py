"""Misconception-based options for angle facts and angles in triangles.

geometry.angles.triangle opts in at every level. geometry.angles.basic_facts
opts in at every level except its two-part forms (vertically opposite x and
y, and a quadrilateral's x plus its largest angle), which return None and
retry like any unsupported form.

Options are compact: angles as 55°, solved unknowns as x = 12, so four
options usually fit on one row. Every distractor must be a whole, positive
number; a wrong method that gives a fraction or a negative is dropped rather
than shown, because a student would see at once that it is impossible.
"""
from fractions import Fraction

from .core import Content, require
from .multiple_choice import RationalCandidate


TRIANGLE = "geometry.angles.triangle"
FACTS = "geometry.angles.basic_facts"
SUPPORTED_LEVELS = {TRIANGLE: (1, 2, 3, 4), FACTS: (1, 2, 3, 4)}

# Forms whose answer is the value of x rather than an angle.
SOLVE_FOR_X = ("algebra", "algebra_isosceles",
               "algebraic_line", "algebraic_point", "algebraic_quad")
FACT_TOTALS = {"algebraic_line": 180, "algebraic_point": 360, "algebraic_quad": 360}


def candidate(value, mistake, explanation):
    return RationalCandidate(Fraction(value), mistake, explanation)


def believable(found):
    """Whole, positive values only."""
    return [item for item in found if item.value > 0 and item.value.denominator == 1]


def candidates(question):
    if question.difficulty not in SUPPORTED_LEVELS.get(question.generator_id, ()):
        return None
    p = question.parameters
    forms = TRIANGLE_FORMS if question.generator_id == TRIANGLE else FACT_FORMS
    builder = forms.get(p.get("form"))
    if builder is None:
        return None
    return believable(builder(p))


def others(angles, index):
    return [angle for i, angle in enumerate(angles) if i != index]


# ------------------------------------------------------------ triangles

def triangle_missing(p):
    a, b = others(p["angles"], p["unknown"])
    return [
        candidate(360 - a - b, "uses_360", "Subtracts the two angles from 360° instead of 180°."),
        candidate(a + b, "adds_known_angles", "Adds the two given angles instead of subtracting them from 180°."),
        candidate(180 - a, "subtracts_one_angle", "Subtracts only one of the given angles from 180°."),
    ]


def isosceles_base(p):
    apex = p["angles"][2]
    return [
        candidate(180 - apex, "forgets_to_halve",
                  "Subtracts the apex from 180° but does not share the rest between the two base angles."),
        candidate(apex, "base_equals_apex", "Assumes the base angle equals the apex angle."),
        candidate(Fraction(360 - apex, 2), "uses_360", "Uses 360° instead of 180° before halving."),
    ]


def isosceles_apex(p):
    base = p["angles"][0]
    return [
        candidate(180 - base, "subtracts_one_base_angle", "Subtracts only one base angle from 180°."),
        candidate(base, "apex_equals_base", "Assumes the apex equals the given base angle."),
        candidate(Fraction(180 - base, 2), "treats_given_as_apex",
                  "Treats the given base angle as the apex and halves what is left."),
    ]


def exterior(p):
    vertex = p["vertex"]
    a, b = others(p["angles"], vertex)
    return [
        candidate(p["angles"][vertex], "gives_interior_angle",
                  "Gives the interior angle beside the exterior angle."),
        candidate(360 - a - b, "uses_360", "Subtracts the two opposite angles from 360°."),
        candidate(abs(a - b), "difference_of_opposite_angles",
                  "Subtracts the two opposite interior angles instead of adding them."),
    ]


def isosceles_exterior(p):
    base, apex = p["angles"][0], p["angles"][2]
    return [
        candidate(base, "gives_interior_angle", "Gives the interior base angle instead of the exterior angle."),
        candidate(180 - apex, "uses_apex", "Subtracts the apex angle from 180° instead of the base angle."),
        candidate(apex, "forgets_to_halve",
                  "Forgets to halve when finding the base angle, so the exterior angle comes out as the apex."),
    ]


def solve_for_x(terms, total, wrong_total):
    """Distractors for k1 x + b1 + k2 x + b2 + ... = total."""
    k = sum(term[0] for term in terms)
    b = sum(term[1] for term in terms)
    return [
        candidate(Fraction(wrong_total - b, k), "wrong_total",
                  "Uses {}° instead of {}°.".format(wrong_total, total)),
        candidate(Fraction(total, k), "ignores_constants", "Ignores the number terms in the expressions."),
        candidate(Fraction(total + b, k), "adds_constants",
                  "Moves the number terms to the other side without changing their signs."),
        candidate(total - b, "forgets_to_divide", "Does not divide by the number of x."),
    ]


def triangle_algebra(p):
    found = []
    if p["form"] == "algebra_isosceles":
        (k_base, b_base), _, (k_apex, b_apex) = p["terms"]
        found.append(candidate(Fraction(180 - b_base - b_apex, k_base + k_apex), "counts_base_once",
                               "Uses the equal base expression only once."))
    return found + solve_for_x(p["terms"], 180, 360)


TRIANGLE_FORMS = {
    "missing": triangle_missing,
    "isosceles_base": isosceles_base,
    "isosceles_apex": isosceles_apex,
    "exterior": exterior,
    "isosceles_exterior": isosceles_exterior,
    "algebra": triangle_algebra,
    "algebra_isosceles": triangle_algebra,
}


# ------------------------------------------------------------ angle facts

def straight_line(p):
    (a,) = others(p["angles"], p["unknown"])
    return [
        candidate(360 - a, "uses_360", "Subtracts from 360° instead of 180° on a straight line."),
        candidate(a, "assumes_equal", "Assumes the two angles on the line are equal."),
        candidate(90 - a, "uses_90", "Subtracts from 90° as if the angles made a right angle."),
    ]


def around_point(p):
    a, b = others(p["angles"], p["unknown"])
    return [
        candidate(180 - a - b, "uses_180", "Subtracts from 180° instead of 360° around a point."),
        candidate(a + b, "adds_known_angles", "Adds the given angles instead of subtracting them from 360°."),
        candidate(360 - a, "subtracts_one_angle", "Subtracts only one of the given angles from 360°."),
    ]


def quadrilateral(p):
    known = others(p["angles"], p["unknown"])
    total = sum(known)
    found = [
        candidate(360 - total + known[-1], "leaves_out_last_angle", "Leaves out one of the given angles."),
        candidate(360 - total + known[0], "leaves_out_first_angle", "Leaves out a different given angle."),
        candidate(180 - total, "uses_180", "Subtracts from 180° instead of 360°."),
    ]
    if total < 360:
        found.append(candidate(total, "adds_known_angles",
                               "Adds the given angles instead of subtracting them from 360°."))
    return found


def fact_algebra(p):
    total = FACT_TOTALS[p["form"]]
    return solve_for_x(p["terms"], total, 540 - total)


FACT_FORMS = {
    "straight_line": straight_line,
    "around_point": around_point,
    "quadrilateral": quadrilateral,
    "algebraic_line": fact_algebra,
    "algebraic_point": fact_algebra,
    "algebraic_quad": fact_algebra,
}


# ------------------------------------------------------------ display

def format_candidate(question, candidate):
    value = Fraction(candidate.value)
    require(value.denominator == 1, "Angle options must be whole numbers")
    value = int(value)
    if question.parameters["form"] in SOLVE_FOR_X:
        text = "x = {}".format(value)
        return Content(text, text)
    return Content("{}°".format(value), "{}^{{\\circ}}".format(value))