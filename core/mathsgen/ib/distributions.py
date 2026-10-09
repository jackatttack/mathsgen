"""Probability distributions for the IB statistics generators.

scipy is not available in Pythonista, so these use mpmath (shipped with
SymPy) at 30 significant digits and return exact Fractions of those
digits; later rounding is then decided on digits.

The *_by_integration functions integrate each density numerically. They are
a mathematically distinct route used only by validate_independently.
"""
from fractions import Fraction

import mpmath


PRECISION = 30


def mp(value):
    value = Fraction(value)
    return mpmath.mpf(value.numerator) / value.denominator


def fraction(value):
    return Fraction(mpmath.nstr(value, PRECISION))


def square_root(value):
    with mpmath.workdps(PRECISION):
        return fraction(mpmath.sqrt(mp(value)))


def normal_cdf(x, mean, sd):
    """P(X < x) for X ~ N(mean, sd^2)."""
    with mpmath.workdps(PRECISION):
        return fraction(mpmath.ncdf(mp(x), mp(mean), mp(sd)))


def inverse_normal(probability, mean, sd):
    """The k with P(X < k) = probability."""
    with mpmath.workdps(PRECISION):
        z = mpmath.sqrt(2) * mpmath.erfinv(2 * mp(probability) - 1)
        return fraction(mp(mean) + mp(sd) * z)


def t_cdf(t, df):
    """P(T < t) for Student's t with df degrees of freedom."""
    with mpmath.workdps(PRECISION):
        t = mp(t)
        x = df / (df + t * t)
        tail = mpmath.betainc(mpmath.mpf(df) / 2, mpmath.mpf(1) / 2, 0, x, regularized=True) / 2
        return fraction(1 - tail if t > 0 else tail)


def chi_squared_upper(statistic, df):
    """P(chi-squared > statistic) with df degrees of freedom."""
    with mpmath.workdps(PRECISION):
        return fraction(mpmath.gammainc(mpmath.mpf(df) / 2, mp(statistic) / 2, mpmath.inf,
                                        regularized=True))


# ------------------------------------------------------------ independent routes

def normal_cdf_by_integration(x, mean, sd):
    mean, sd, x = float(mean), float(sd), float(x)
    with mpmath.workdps(20):
        density = lambda u: mpmath.exp(-(u - mean) ** 2 / (2 * sd * sd)) / (
            sd * mpmath.sqrt(2 * mpmath.pi))
        return float(mpmath.quad(density, [-mpmath.inf, mean, x]))


def t_upper_by_integration(t, df):
    """P(T > t)."""
    with mpmath.workdps(20):
        scale = mpmath.gamma((df + 1) / 2.0) / (mpmath.sqrt(df * mpmath.pi) * mpmath.gamma(df / 2.0))
        density = lambda u: scale * (1 + u * u / df) ** (-(df + 1) / 2.0)
        return float(mpmath.quad(density, [float(t), mpmath.inf]))


def chi_squared_upper_by_integration(statistic, df):
    with mpmath.workdps(20):
        k = df / 2.0
        density = lambda u: u ** (k - 1) * mpmath.exp(-u / 2) / (2 ** k * mpmath.gamma(k))
        return float(mpmath.quad(density, [float(statistic), mpmath.inf]))