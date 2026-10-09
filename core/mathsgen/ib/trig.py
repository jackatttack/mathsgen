"""Degree-based trigonometry for the IB geometry generators.

Every result is a Fraction of a 30-digit mpmath value, so later rounding
is decided on digits. Bearings are measured clockwise from north, with
x pointing east and y pointing north.
"""
from fractions import Fraction

import mpmath

from ..rounding import fixed_text, round_half_up
from . import distributions as dist


def run(expression):
    with mpmath.workdps(dist.PRECISION):
        return dist.fraction(expression())


def mp(value):
    return dist.mp(value)


def sin_deg(angle):
    return run(lambda: mpmath.sin(mpmath.radians(mp(angle))))


def cos_deg(angle):
    return run(lambda: mpmath.cos(mpmath.radians(mp(angle))))


def asin_deg(value):
    return run(lambda: mpmath.degrees(mpmath.asin(mp(value))))


def acos_deg(value):
    return run(lambda: mpmath.degrees(mpmath.acos(mp(value))))


def atan_deg(value):
    return run(lambda: mpmath.degrees(mpmath.atan(mp(value))))


def sqrt(value):
    return dist.square_root(value)


def pi():
    return run(lambda: mpmath.pi)


def cosine_rule_side(b, c, angle):
    return sqrt(Fraction(b) ** 2 + Fraction(c) ** 2 - 2 * Fraction(b) * Fraction(c) * cos_deg(angle))


def triangle_area(b, c, angle):
    return Fraction(1, 2) * Fraction(b) * Fraction(c) * sin_deg(angle)


def step(distance, bearing):
    """(east, north) displacement for a distance on a bearing."""
    return Fraction(distance) * sin_deg(bearing), Fraction(distance) * cos_deg(bearing)


def bearing_of(east, north):
    """Bearing of the direction (east, north), in [0, 360)."""
    return run(lambda: mpmath.degrees(mpmath.atan2(mp(east), mp(north)))) % 360


def bearing_text(value):
    """Three-figure bearing to 1 decimal place when needed: 045°, 236.4°."""
    value = round_half_up(Fraction(value) % 360, 1)
    if value == 360:
        value = Fraction(0)
    text = fixed_text(value, 1) if value.denominator != 1 else str(value.numerator)
    whole, _, tenths = text.partition(".")
    return whole.rjust(3, "0") + ("." + tenths if tenths else "") + "°"