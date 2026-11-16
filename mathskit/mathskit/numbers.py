"""Numbers as they are written in working: short exact decimals, money,
rounding. Pure Python.

    numbers.text(Fraction(32, 5))     # '6.4'
    numbers.money(Fraction(4411, 4))  # '1102.75'
    numbers.round_to(value, 2)        # Decimal, rounded half up
"""
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction


def round_to(value, places):
    """value (int, Fraction or Decimal) rounded half up to places decimal
    places, as a Decimal."""
    value = Fraction(value)
    exact = Decimal(value.numerator) / Decimal(value.denominator)
    return exact.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def text(value, places=6):
    """A number as a short decimal: 12, 6.4, -0.35. Values that do not end
    within places decimal places are rounded there."""
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    shown = format(round_to(value, places), 'f')
    return shown.rstrip('0').rstrip('.')


def frac_tex(value):
    """TeX for an exact value: 3, -2, \\frac{1}{2}, -\\frac{3}{4}."""
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return r'%s\frac{%d}{%d}' % ('-' if value < 0 else '', abs(value.numerator),
                                 value.denominator)


def paren_tex(value):
    """frac_tex, bracketed when negative: for substituting, 3 \\times (-2)."""
    return '(%s)' % frac_tex(value) if Fraction(value) < 0 else frac_tex(value)


def money(value):
    """Two decimal places: 1102.50."""
    return format(round_to(value, 2), 'f')
