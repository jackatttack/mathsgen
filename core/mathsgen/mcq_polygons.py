"""Misconception-based options for angles in polygons (levels 1-3, regular forms).

Level 1 asks for an interior angle sum, level 2 for one angle of a regular
polygon, and level 3 for the number of sides from one regular angle. The
irregular quadrilateral exterior form (level 3) and the shared-side and
vertex forms (level 4) stay written questions.

Every distractor must be a whole positive number; a number of sides must
also be at least 3, since a student would reject anything smaller.
"""
from fractions import Fraction

from .core import Content, require
from .multiple_choice import RationalCandidate


SUPPORTED_LEVELS = {"geometry.angles.polygons": (1, 2, 3)}


def candidate(value, mistake, explanation):
    return RationalCandidate(Fraction(value), mistake, explanation)


def whole(found, smallest=1):
    return [item for item in found
            if item.value.denominator == 1 and item.value >= smallest]


def candidates(question):
    if question.difficulty not in SUPPORTED_LEVELS.get(question.generator_id, ()):
        return None
    p = question.parameters
    if "form" in p:
        return None
    if question.difficulty == 1:
        return angle_sum(p["sides"])
    if question.difficulty == 2:
        return one_angle(p["sides"], p["angle_kind"])
    return sides_from_angle(Fraction(p["angle"]), p["angle_kind"])


def angle_sum(n):
    return whole([
        candidate(n * 180, "n_times_180", "Multiplies the number of sides by 180°."),
        candidate((n - 3) * 180, "miscounts_triangles",
                  "Counts the diagonals from one vertex instead of the triangles they make."),
        candidate(360, "always_360", "Assumes every polygon's angles add up to 360°."),
    ])


def one_angle(n, kind):
    exterior = Fraction(360, n)
    interior = 180 - exterior
    if kind == "interior":
        return whole([
            candidate(exterior, "gives_exterior", "Gives the exterior angle instead of the interior angle."),
            candidate((n - 2) * 180, "forgets_to_divide", "Finds the angle sum but does not divide by the number of sides."),
            candidate(360 - exterior, "subtracts_from_360", "Subtracts the exterior angle from 360° instead of 180°."),
        ])
    return whole([
        candidate(interior, "gives_interior", "Gives the interior angle instead of the exterior angle."),
        candidate(Fraction(180, n), "uses_180", "Divides 180° by the number of sides instead of 360°."),
        candidate(360, "gives_total", "Gives the total of all the exterior angles."),
    ])


def sides_from_angle(angle, kind):
    if kind == "exterior":
        found = [
            candidate(Fraction(180, angle), "uses_180", "Divides 180° by the exterior angle instead of 360°."),
            candidate(Fraction(360, 180 - angle), "treats_as_interior",
                      "Treats the exterior angle as an interior angle."),
            candidate(180 - angle, "stops_at_interior",
                      "Finds the interior angle and gives it as the number of sides."),
            candidate(360 - angle, "subtracts_from_360",
                      "Subtracts the exterior angle from 360° instead of dividing."),
        ]
    else:
        found = [
            candidate(Fraction(360, angle), "divides_into_interior",
                      "Divides 360° by the interior angle instead of the exterior angle."),
            candidate(Fraction(180, 180 - angle), "uses_180", "Divides 180° by the exterior angle instead of 360°."),
            candidate(180 - angle, "stops_at_exterior",
                      "Finds the exterior angle and gives it as the number of sides."),
        ]
    return whole(found, smallest=3)


def format_candidate(question, candidate):
    value = Fraction(candidate.value)
    require(value.denominator == 1, "Polygon options must be whole numbers")
    value = int(value)
    if question.difficulty == 3:
        return Content("{} sides".format(value))
    return Content("{}°".format(value), "{}^{{\\circ}}".format(value))