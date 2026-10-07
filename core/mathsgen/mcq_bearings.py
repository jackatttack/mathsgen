"""Misconception-based options for back bearings (level 1).

Only the back-bearing form opts in. Levels 2-4 need diagrams, two-part
answers or rounding, and stay written questions for now.

Display uses the generator's three-figure format. A wrong answer above
360° (adding 180° to a bearing that is already 180° or more) is shown as
written, because that is exactly what a student would write.
"""
from fractions import Fraction

from .bearings import bearing_text
from .core import Content, require
from .multiple_choice import RationalCandidate


SUPPORTED_LEVELS = {"geometry.bearings.bearings": (1,)}


def candidate(value, mistake, explanation):
    return RationalCandidate(Fraction(value), mistake, explanation)


def candidates(question):
    if question.difficulty not in SUPPORTED_LEVELS.get(question.generator_id, ()):
        return None
    p = question.parameters
    if p.get("form") != "back":
        return None
    bearing = int(p["bearing"])
    found = []
    if bearing >= 180:
        found.append(candidate(bearing + 180, "add_180_past_360",
                               "Adds 180° to a bearing that is already 180° or more, giving more than 360°."))
    found.append(candidate(360 - bearing, "subtract_from_360",
                           "Subtracts the bearing from 360° instead of turning through 180°."))
    if bearing < 180:
        found.append(candidate(180 - bearing, "subtract_from_180",
                               "Subtracts the bearing from 180° instead of adding 180°."))
    found.append(candidate(bearing, "same_bearing",
                           "Gives the original bearing, mixing up which point it is measured from."))
    return found


def format_candidate(question, candidate):
    value = Fraction(candidate.value)
    require(value.denominator == 1 and value >= 0,
            "A bearing option must be a whole number of degrees")
    return Content(bearing_text(int(value)))