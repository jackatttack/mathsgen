"""Misconception-based options for area, volume and capacity conversions.

Levels 1-3 convert with a squared or cubed length factor; the headline
mistake is using the length factor once (3 m² as 300 cm²). Level 4 converts
between volume and capacity, where 1 litre = 1000 cm³. Every option is
written in the answer's own unit, exactly as the original answer.
"""
from fractions import Fraction

from .core import Content
from .multiple_choice import RationalCandidate
from .unit_conversion import CAPACITY_CASES, LENGTH_STEPS, quantity_text


SUPPORTED_LEVELS = {"number.units.area_volume": (1, 2, 3, 4)}


def candidate(value, mistake, explanation):
    return RationalCandidate(Fraction(value), mistake, explanation)


def candidates(question):
    if question.difficulty not in SUPPORTED_LEVELS.get(question.generator_id, ()):
        return None
    p = question.parameters
    value = Fraction(p["value"])
    if p.get("form") == "power":
        return power_conversion(value, p)
    if p.get("form") == "capacity":
        return capacity_conversion(value, p["case"])
    return None


def power_conversion(value, p):
    length = Fraction(LENGTH_STEPS[p["step"]][2])
    dimension = p["dimension"]
    down = p["direction"] == "to_smaller"

    def apply(factor):
        return value * factor if down else value / factor

    wrong_power = 3 if dimension == 2 else 2
    return [
        candidate(apply(length), "length_factor_once",
                  "Uses the length factor once instead of {} it.".format(
                      "squaring" if dimension == 2 else "cubing")),
        candidate(apply(length ** wrong_power), "wrong_power",
                  "Cubes the length factor for an area." if dimension == 2
                  else "Squares the length factor for a volume."),
        candidate(value / length ** dimension if down else value * length ** dimension,
                  "wrong_direction",
                  "Divides instead of multiplying." if down else "Multiplies instead of dividing."),
    ]


def capacity_conversion(value, case):
    multiplier = CAPACITY_CASES[case][2]
    up = multiplier > 1
    found = [
        candidate(value / multiplier, "wrong_direction",
                  "Divides by 1000 instead of multiplying." if up
                  else "Multiplies by 1000 instead of dividing."),
        candidate(value * 100 if up else value / 100, "uses_100", "Uses 100 instead of 1000."),
    ]
    if "m3" in case and "cm3" not in case:
        found.append(candidate(value * 10 ** 6 if up else value / 10 ** 6, "converts_to_cm3",
                               "Converts between cubic metres and cubic centimetres instead of litres."))
    else:
        found.append(candidate(value, "one_to_one", "Treats 1 cm³ as 1 litre."))
    return found


def format_candidate(question, candidate):
    unit, dimension = question.answer["unit"], question.answer["dimension"]
    value = Fraction(candidate.value)
    return Content(quantity_text(value, unit, dimension),
                   quantity_text(value, unit, dimension, True))