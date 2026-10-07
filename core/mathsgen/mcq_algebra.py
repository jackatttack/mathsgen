"""Misconception-based options for simplifying and expanding bare expressions.

Only bare (non-worded) forms opt in: collecting like terms L1-4, and single
brackets reached through level 1 of the expanding family. Single brackets
are no longer registered on their own: they are the "single" source of
algebra.expanding.double_brackets; source levels 1-2 (one bracket) and 3
(two brackets, then simplify) are adapted. Every distractor follows a
stated wrong procedure applied to
the written terms. The engine compares results by exact collected form, so a
"mistake" that is really equivalent to the answer (writing ba for ab, say)
is discarded rather than shown as a wrong option.

Candidates are listed in priority order; the engine keeps the first three
that are distinct from the answer and from each other.
"""
from .algebra_basics import monomial_key
from .multiple_choice import PolynomialCandidate


LIKE_TERMS = "algebra.expressions.like_terms"
EXPANDING = "algebra.expanding.double_brackets"
SINGLE_SOURCE_LEVELS = (1, 2, 3)  # 1-2: one bracket; 3: two brackets, then simplify

SUPPORTED_LEVELS = {
    LIKE_TERMS: (1, 2, 3, 4),
    EXPANDING: (1,),
}


def candidate(terms, mistake, explanation):
    return PolynomialCandidate(terms, mistake, explanation)


def candidates(question):
    if question.difficulty not in SUPPORTED_LEVELS.get(question.generator_id, ()):
        return None
    from . import worded
    if worded.is_worded(question):
        return None
    p = question.parameters
    if question.generator_id == LIKE_TERMS:
        if set(p) != {"terms"}:
            return None
        return like_terms_candidates(p["terms"], question.difficulty)
    if set(p) != {"source", "source_level", "inner"}:
        return None
    if p["source"] != "single" or p["source_level"] not in SINGLE_SOURCE_LEVELS:
        return None
    if set(p["inner"]) != {"brackets"}:
        return None
    return bracket_candidates(p["inner"]["brackets"])


# ------------------------------------------------------- collecting like terms

def like_terms_candidates(terms, level):
    found = []
    if level in (3, 4):
        found.append(candidate(squares_as_linear(terms), "squares_as_linear",
                               "Treats squared terms and single-letter terms as like terms."))
    if level in (2, 4):
        found.append(candidate(combine_unlike_letters(terms), "combine_unlike_letters",
                               "Adds the coefficients of different letters and writes the letters together."))
    if level == 1 and any(not monomial for _, monomial in terms):
        found.append(candidate(absorb_constants(terms), "absorb_constants",
                               "Adds the number terms onto the letter terms."))
    if level in (1, 2, 3):
        found.append(candidate(square_when_adding(terms), "square_when_adding",
                               "Adds the coefficients but also squares the letter, as if multiplying."))
    found.append(candidate([[abs(c), m] for c, m in terms], "ignore_signs",
                           "Ignores the minus signs and adds every coefficient."))
    found.append(candidate(minus_carries_forward(terms), "minus_carries_forward",
                           "Once a minus sign appears, subtracts every later term as well."))
    return found


def is_single_letter(monomial):
    return len(monomial) == 1 and monomial[0][1] == 1


def squares_as_linear(terms):
    """x² and x collected together, written as x."""
    return [[c, [[variable, 1] for variable, _ in m]] for c, m in terms]


def square_when_adding(terms):
    """3x + 4x written as 7x²: single-letter terms gain a square."""
    return [[c, [[m[0][0], 2]] if is_single_letter(m) else m] for c, m in terms]


def combine_unlike_letters(terms):
    """3x + 2y written as 5xy; number terms are kept."""
    letters = []
    for _, monomial in terms:
        for variable, _ in monomial:
            if variable not in letters:
                letters.append(variable)
    total = sum(c for c, m in terms if m)
    return [[total, [[variable, 1] for variable in letters]]] + [[c, m] for c, m in terms if not m]


def absorb_constants(terms):
    """3x + 2 + 4x written as 9x (level 1 has one letter)."""
    letter = next(m for _, m in terms if m)
    return [[sum(c for c, _ in terms), letter]]


def minus_carries_forward(terms):
    """Every term after the first minus sign is subtracted, as if bracketed."""
    result, negative = [], False
    for c, m in terms:
        negative = negative or c < 0
        result.append([-abs(c) if negative else c, m])
    return result


# --------------------------------------------------------- expanding brackets

def bracket_candidates(brackets):
    if len(brackets) == 2:
        return two_bracket_candidates(brackets)
    if len(brackets) != 1:
        return None
    (k, outer), inner = brackets[0]
    (c0, m0), (c1, m1) = inner
    first = [k * c0, outer + m0]
    found = [
        candidate([first, [-k * c1, outer + m1]], "second_sign_wrong",
                  "Multiplies both terms but gives the second product the wrong sign."),
        candidate([first, [c1, m1]], "first_term_only",
                  "Multiplies only the first term in the bracket."),
    ]
    if not outer and not m1:
        found.append(candidate([first, [k + c1, []]], "add_to_number",
                               "Adds the multiplier to the number instead of multiplying it."))
    if outer and monomial_key(outer) == monomial_key(m0):
        found.append(candidate([[2 * k * c0, m0], [k * c1, outer + m1]], "square_as_double",
                               "Writes a letter times itself as double the letter instead of its square."))
    return found


# ------------------------------------------------- two brackets, then simplify

def products(multiplier, inner):
    """The correct products of one bracket, term by term."""
    k, outer = multiplier
    return [[k * c, outer + m] for c, m in inner]


def first_term_only(multiplier, inner):
    (k, outer), ((c0, m0), (c1, m1)) = multiplier, inner
    return [[k * c0, outer + m0], [c1, m1]]


def add_to_number(multiplier, inner):
    """3(x + 4) read as 3x + 7. Level 3 inners are letter then number."""
    (k, outer), ((c0, m0), (c1, m1)) = multiplier, inner
    return [[k * c0, outer + m0], [k + c1, m1]]


def two_bracket_candidates(brackets):
    """a(x + b) ± c(x + d): number multipliers on like linear brackets.

    The sign in front of the second bracket is its multiplier's sign, so a
    subtracted bracket has a negative multiplier.
    """
    (first_multiplier, first_inner), (second_multiplier, second_inner) = brackets
    k2, outer2 = second_multiplier
    first = products(first_multiplier, first_inner)
    second = products(second_multiplier, second_inner)
    last_sign_flipped = second[:-1] + [[-second[-1][0], second[-1][1]]]
    found = []
    if k2 < 0:
        found.append(candidate(first + last_sign_flipped, "minus_on_first_term_only",
                               "Applies the minus sign before the second bracket to its first term only."))
        found.append(candidate(first + products([abs(k2), outer2], second_inner),
                               "ignore_minus_before_bracket",
                               "Treats the subtracted bracket as added, ignoring the minus sign in front."))
    else:
        found.append(candidate(first + last_sign_flipped, "second_bracket_sign_wrong",
                               "Gives the last product in the second bracket the wrong sign."))
    found.append(candidate(first_term_only(first_multiplier, first_inner)
                           + first_term_only(second_multiplier, second_inner),
                           "first_term_only", "Multiplies only the first term in each bracket."))
    found.append(candidate(add_to_number(first_multiplier, first_inner)
                           + add_to_number(second_multiplier, second_inner),
                           "add_to_number",
                           "Adds each multiplier to the number in its bracket instead of multiplying."))
    return found