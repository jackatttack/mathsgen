"""Algebra basics: collecting like terms, expanding single brackets, substitution.

Expressions are lists of terms [coefficient, monomial]. A monomial is a list
of [variable, power] pairs in the order written, so "ba" displays as written
but collects with "ab". Answers are the canonical simplified form: highest
degree first, and squares before products of the same degree.

Substitution level 4 uses formula templates evaluated exactly: every
division and square root must come out whole.
"""
import ast
from collections import namedtuple
from fractions import Fraction
from math import isqrt

from .core import Content, GeneratorInfo, rational_text, require
from .family import GeneratorFamily
from . import rich_blocks as rb


# ------------------------------------------------------------ choice pools

VARIABLES = ("a", "b", "m", "n", "p", "t", "x", "y")
PAIRS = (("a", "b"), ("m", "n"), ("p", "q"), ("x", "y"))
ALL_LETTERS = set(VARIABLES) | {"q"}
SUPERSCRIPTS = {2: "²", 3: "³"}
MAX_ANSWER = 999


# ---------------------------------------------------------- term helpers

def monomial_key(monomial):
    """Canonical form: variables sorted, repeated variables merged."""
    powers = {}
    for variable, power in monomial:
        powers[variable] = powers.get(variable, 0) + power
    return tuple(sorted(powers.items()))


def monomial_text(monomial, tex=False):
    pieces = []
    for variable, power in monomial:
        if power == 1:
            pieces.append(variable)
        elif tex:
            pieces.append(variable + "^{" + str(power) + "}")
        else:
            pieces.append(variable + SUPERSCRIPTS[power])
    return "".join(pieces)


def term_text(coefficient, monomial, first, tex=False):
    body = monomial_text(monomial, tex)
    magnitude = abs(coefficient)
    number = "" if (magnitude == 1 and body) else str(magnitude)
    if first:
        return ("-" if coefficient < 0 else "") + number + body
    return (" - " if coefficient < 0 else " + ") + number + body


def expression_text(terms, tex=False):
    return "".join(
        term_text(c, m, index == 0, tex) for index, (c, m) in enumerate(terms)
    ) or "0"


def canonical_order(key):
    """Highest degree first; within a degree, higher single powers first."""
    return (-sum(power for _, power in key), tuple((v, -power) for v, power in key))


def collect(terms):
    """Collected terms in canonical order, dropping zero totals."""
    totals = {}
    for coefficient, monomial in terms:
        key = monomial_key(monomial)
        totals[key] = totals.get(key, 0) + coefficient
    ordered = sorted((key for key, total in totals.items() if total), key=canonical_order)
    return [[totals[key], [list(pair) for pair in key]] for key in ordered]


def variables_in(terms):
    return {variable for _, monomial in terms for variable, _ in monomial}


def degree(monomial):
    return sum(power for _, power in monomial)


def valid_terms(terms, max_power, limit):
    require(isinstance(terms, list) and bool(terms), "Expected a list of terms")
    for term in terms:
        require(isinstance(term, list) and len(term) == 2, "Invalid term")
        coefficient, monomial = term
        require(type(coefficient) is int and coefficient != 0 and abs(coefficient) <= limit,
                "Coefficient outside bounds")
        require(isinstance(monomial, list), "Invalid monomial")
        for pair in monomial:
            require(isinstance(pair, list) and len(pair) == 2, "Invalid factor")
            require(pair[0] in ALL_LETTERS, "Unknown letter")
            require(type(pair[1]) is int and 1 <= pair[1] <= max_power, "Power outside bounds")
        require(len({v for v, _ in monomial}) == len(monomial), "Repeated letter in one term")


def polynomial_answer(terms):
    return (
        {"kind": "polynomial_terms", "terms": terms},
        Content(expression_text(terms), expression_text(terms, True)),
    )


def sympy_terms(terms):
    import sympy
    total = sympy.Integer(0)
    for coefficient, monomial in terms:
        product = sympy.Integer(coefficient)
        for variable, power in monomial:
            product *= sympy.Symbol(variable) ** power
        total += product
    return total


def require_simplified(expression, answer_terms):
    """The answer equals the expression and has one term per distinct monomial."""
    import sympy
    expanded = sympy.expand(expression)
    require(sympy.expand(expanded - sympy_terms(answer_terms)) == 0, "Independent algebra disagrees")
    require(len(expanded.as_coefficients_dict()) == len(answer_terms), "Answer not fully simplified")


def nonzero(rng, limit):
    return rng.choice([v for v in range(-limit, limit + 1) if v != 0])


def nonzero_between(rng, low, high):
    return rng.choice([v for v in range(low, high + 1)] + [-v for v in range(low, high + 1)])


def split(rng, total, pieces, limit=12):
    """Nonzero parts summing to total, each within the limit."""
    for _ in range(200):
        parts = [nonzero(rng, limit) for _ in range(pieces - 1)]
        last = total - sum(parts)
        if last != 0 and abs(last) <= limit:
            return parts + [last]
    raise ValueError("Could not split a coefficient")


def statement(instruction, plain, tex):
    return Content(
        "{} {}.".format(instruction, plain),
        blocks=(rb.prose(instruction), rb.equation(tex, plain)),
    )


# -------------------------------------------------------- like terms

class LikeTerms(GeneratorFamily):
    info = GeneratorInfo(
        id="algebra.expressions.like_terms",
        version=1,
        topic="algebra",
        subtopic="simplifying_expressions",
        title="Simplify by collecting like terms",
        difficulty_descriptions={
            1: "One letter, with or without constants.",
            2: "Two letters, with constants.",
            3: "Squared, linear and constant terms of one letter.",
            4: "Two letters, including products written in either order.",
        },
        tags=("algebra", "simplifying", "like_terms"),
    )
    keys = {level: {"terms"} for level in (1, 2, 3, 4)}

    def build(self, level, rng):
        if level == 1:
            v = rng.choice(VARIABLES)
            groups = [([[v, 1]], 3)] if rng.random() < 0.5 else [([[v, 1]], 2), ([], 2)]
        elif level == 2:
            v, w = rng.choice(PAIRS)
            groups = [([[v, 1]], 2), ([[w, 1]], 2)]
            if rng.random() < 0.5:
                groups.append(([], 1))
        elif level == 3:
            v = rng.choice(VARIABLES)
            groups = [([[v, 2]], 2), ([[v, 1]], 2), ([], rng.choice((1, 2)))]
        else:
            v, w = rng.choice(PAIRS)
            second = [[v, 2]] if rng.random() < 0.5 else [[v, 1]]
            groups = [("product", 2), (second, 2), ([[w, 1]], rng.choice((1, 2)))]
        terms = []
        for monomial, pieces in groups:
            for coefficient in split(rng, nonzero(rng, 12), pieces):
                written = monomial
                if monomial == "product":
                    written = rng.choice(([[v, 1], [w, 1]], [[w, 1], [v, 1]]))
                terms.append([coefficient, [list(pair) for pair in written]])
        rng.shuffle(terms)
        return {"terms": terms}

    def check_rules(self, p, level):
        terms = p["terms"]
        valid_terms(terms, 2 if level in (3, 4) else 1, 12)
        require(3 <= len(terms) <= 7, "Term count outside bounds")
        require(len(variables_in(terms)) == (2 if level in (2, 4) else 1), "Wrong number of letters")
        keys = [monomial_key(m) for _, m in terms]
        require(len(set(keys)) < len(keys), "Nothing to collect")
        require(bool(collect(terms)), "Everything cancels")
        if level == 3:
            require(any(degree(m) == 2 for _, m in terms), "Expected a squared term")
        if level == 4:
            require(any(len(m) == 2 for _, m in terms), "Expected a product term")

    def parts(self, p, level):
        terms = p["terms"]
        answer, shown = polynomial_answer(collect(terms))
        return {
            "prompt": statement("Simplify", expression_text(terms), expression_text(terms, True)),
            "answer": answer, "answer_display": shown,
            "marks": {1: 1, 2: 2, 3: 2, 4: 3}[level],
            "working_lines": {1: 2, 2: 3, 3: 3, 4: 4}[level],
        }

    def validate_independently(self, question):
        require_simplified(sympy_terms(question.parameters["terms"]), question.answer["terms"])
        return True


# ---------------------------------------------------------- single brackets

def bracket_text(multiplier, inner, first, tex=False):
    coefficient, monomial = multiplier
    body = monomial_text(monomial, tex)
    magnitude = "" if (abs(coefficient) == 1 and body) else str(abs(coefficient))
    if first:
        sign = "-" if coefficient < 0 else ""
    else:
        sign = " - " if coefficient < 0 else " + "
    return sign + magnitude + body + "(" + expression_text(inner, tex) + ")"


def brackets_text(brackets, tex=False):
    return "".join(
        bracket_text(multiplier, inner, index == 0, tex)
        for index, (multiplier, inner) in enumerate(brackets)
    )


def expand(brackets):
    terms = []
    for (coefficient, monomial), inner in brackets:
        for inner_coefficient, inner_monomial in inner:
            terms.append([coefficient * inner_coefficient, monomial + inner_monomial])
    return collect(terms)


def linear_inner(rng, v):
    return [[rng.randint(1, 6), [[v, 1]]], [nonzero(rng, 12), []]]


def is_linear_inner(inner):
    return (
        len(inner) == 2 and len(inner[0][1]) == 1 and inner[0][1][0][1] == 1
        and 1 <= inner[0][0] <= 6 and inner[1][1] == []
    )


class SingleBrackets(GeneratorFamily):
    info = GeneratorInfo(
        id="algebra.expanding.single_brackets",
        version=1,
        topic="algebra",
        subtopic="expanding_brackets",
        title="Expand single brackets",
        difficulty_descriptions={
            1: "A positive number multiplies a linear bracket.",
            2: "Negative or letter multipliers, or two letters inside.",
            3: "Expand two brackets and simplify, including subtraction.",
            4: "Letter multipliers on two brackets, then collect like terms.",
        },
        tags=("algebra", "expanding", "brackets"),
    )
    keys = {level: {"brackets"} for level in (1, 2, 3, 4)}

    def build(self, level, rng):
        if level == 1:
            v = rng.choice(VARIABLES)
            return {"brackets": [[[rng.randint(2, 9), []], linear_inner(rng, v)]]}
        if level == 2:
            kind = rng.choice(("negative", "letter", "two_letters"))
            if kind == "negative":
                v = rng.choice(VARIABLES)
                return {"brackets": [[[-rng.randint(2, 9), []], linear_inner(rng, v)]]}
            if kind == "letter":
                v = rng.choice(VARIABLES)
                return {"brackets": [[[rng.choice((1, 2, 3, -1, -2)), [[v, 1]]], linear_inner(rng, v)]]}
            v, w = rng.choice(PAIRS)
            inner = [[rng.randint(1, 6), [[v, 1]]], [nonzero(rng, 6), [[w, 1]]]]
            return {"brackets": [[[nonzero_between(rng, 2, 9), []], inner]]}
        if level == 3:
            v = rng.choice(VARIABLES)
            return {"brackets": [
                [[rng.randint(2, 9), []], linear_inner(rng, v)],
                [[nonzero_between(rng, 2, 9), []], linear_inner(rng, v)],
            ]}
        for _ in range(200):
            if rng.random() < 0.5:
                v = rng.choice(VARIABLES)
                brackets = [
                    [[rng.randint(1, 4), [[v, 1]]], linear_inner(rng, v)],
                    [[rng.choice((-3, -2, -1, 1, 2, 3)), [[v, 1]]], linear_inner(rng, v)],
                ]
            else:
                v, w = rng.choice(PAIRS)
                brackets = [
                    [[rng.randint(1, 4), [[v, 1]]],
                     [[rng.randint(1, 5), [[v, 1]]], [nonzero(rng, 6), [[w, 1]]]]],
                    [[rng.choice((-3, -2, -1, 1, 2, 3)), [[w, 1]]],
                     [[rng.randint(1, 5), [[v, 1]]], [nonzero(rng, 6), [[w, 1]]]]],
                ]
            if 2 <= len(expand(brackets)) < 4:
                return {"brackets": brackets}
        raise ValueError("Could not build a level 4 expansion")

    def check_rules(self, p, level):
        brackets = p["brackets"]
        require(isinstance(brackets, list) and len(brackets) == (1 if level <= 2 else 2),
                "Wrong number of brackets")
        for bracket in brackets:
            require(isinstance(bracket, list) and len(bracket) == 2, "Invalid bracket")
            multiplier, inner = bracket
            valid_terms([multiplier], 1, 9)
            valid_terms(inner, 1, 12)
            require(len(inner) == 2, "Each bracket holds two terms")
        (c, m), inner = brackets[0]
        if level == 1:
            require(2 <= c <= 9 and m == [] and is_linear_inner(inner), "Outside level 1 forms")
        elif level == 2:
            two_letters = len(variables_in(inner)) == 2
            require(
                (m == [] and c < 0 and is_linear_inner(inner))
                or (len(m) == 1 and c in (1, 2, 3, -1, -2) and is_linear_inner(inner))
                or (m == [] and two_letters),
                "Outside level 2 forms",
            )
        elif level == 3:
            (c2, m2), inner2 = brackets[1]
            require(m == [] and m2 == [] and 2 <= c <= 9 and 2 <= abs(c2) <= 9, "Expected number multipliers")
            require(is_linear_inner(inner) and is_linear_inner(inner2)
                    and variables_in(inner) == variables_in(inner2), "Expected like linear brackets")
        else:
            require(all(len(multiplier[1]) == 1 and abs(multiplier[0]) <= 4 for multiplier, _ in brackets),
                    "Expected letter multipliers")
            require(2 <= len(expand(brackets)) < 4, "Expected like terms to collect")

    def parts(self, p, level):
        brackets = p["brackets"]
        instruction = "Expand" if level <= 2 else "Expand and simplify"
        answer, shown = polynomial_answer(expand(brackets))
        return {
            "prompt": statement(instruction, brackets_text(brackets), brackets_text(brackets, True)),
            "answer": answer, "answer_display": shown,
            "marks": {1: 1, 2: 2, 3: 2, 4: 3}[level],
            "working_lines": {1: 2, 2: 3, 3: 4, 4: 4}[level],
        }

    def validate_independently(self, question):
        import sympy
        total = sympy.Integer(0)
        for multiplier, inner in question.parameters["brackets"]:
            total += sympy_terms([multiplier]) * sympy_terms(inner)
        require_simplified(total, question.answer["terms"])
        return True


# ---------------------------------------------------------------- substitution

Formula = namedtuple("Formula", "plain tex python names make")


def evaluate_formula(python, values):
    """Exact value; every division and square root must be whole."""
    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return Fraction(node.value)
        if isinstance(node, ast.Name):
            return Fraction(values[node.id])
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -walk(node.operand)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "sqrt" and len(node.args) == 1):
            inside = walk(node.args[0])
            require(inside.denominator == 1 and inside >= 0
                    and isqrt(int(inside)) ** 2 == inside, "Square root must be exact")
            return Fraction(isqrt(int(inside)))
        if isinstance(node, ast.BinOp):
            left, right = walk(node.left), walk(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                require(right != 0, "Division by zero")
                result = left / right
                require(result.denominator == 1, "Division must be exact")
                return result
            if isinstance(node.op, ast.Pow):
                require(right == 2, "Only squares are supported")
                return left ** 2
        raise ValueError("Unsupported formula")
    return walk(ast.parse(python, mode="eval"))


def _quotient(rng):
    for _ in range(200):
        c = nonzero_between(rng, 2, 6)
        a = nonzero(rng, 12)
        b = c * nonzero(rng, 6) - a
        if b != 0 and abs(b) <= 12:
            return {"a": a, "b": b, "c": c}
    raise ValueError("Could not build a quotient")


def _squared_difference(rng):
    p = nonzero(rng, 8)
    return {"p": p, "q": rng.choice([v for v in range(-8, 9) if v not in (0, p)])}


def _hypotenuse(rng):
    x, y = rng.choice(((3, 4), (6, 8), (5, 12), (8, 15), (9, 12)))
    if rng.random() < 0.5:
        x, y = y, x
    return {"x": x * rng.choice((1, -1)), "y": y * rng.choice((1, -1))}


def _motion(rng):
    return {"a": nonzero(rng, 10), "t": rng.randint(2, 10), "u": nonzero(rng, 20)}


def _product_over(rng):
    for _ in range(200):
        c, a, b = nonzero_between(rng, 2, 6), nonzero(rng, 10), nonzero(rng, 10)
        if (a * b) % c == 0:
            return {"a": a, "b": b, "c": c}
    raise ValueError("Could not build a product quotient")


FORMULAS = {
    "quotient": Formula("(a + b)/c", r"\frac{a + b}{c}", "(a + b)/c", ("a", "b", "c"), _quotient),
    "squared_difference": Formula("2(p - q)²", r"2(p - q)^{2}", "2*(p - q)**2", ("p", "q"),
                                  _squared_difference),
    "hypotenuse": Formula("√(x² + y²)", r"\sqrt{x^{2} + y^{2}}", "sqrt(x**2 + y**2)", ("x", "y"),
                          _hypotenuse),
    "motion": Formula("u + at", "u + at", "u + a*t", ("a", "t", "u"), _motion),
    "product_over": Formula("ab/c", r"\frac{ab}{c}", "a*b/c", ("a", "b", "c"), _product_over),
}


def evaluate_terms(terms, values):
    total = 0
    for coefficient, monomial in terms:
        product = coefficient
        for variable, power in monomial:
            product *= values[variable] ** power
        total += product
    return total


def assignment_runs(values):
    names = sorted(values)
    runs, plain = [], []
    for index, name in enumerate(names):
        if index:
            joiner = " and " if index == len(names) - 1 else ", "
            runs.append(rb.text(joiner))
            plain.append(joiner)
        text = "{} = {}".format(name, values[name])
        runs.append(rb.maths(text, text))
        plain.append(text)
    return runs, "".join(plain)


def valid_values(values, names, limit):
    require(isinstance(values, dict) and set(values) == set(names), "Values do not match the letters")
    require(all(type(v) is int and v != 0 and abs(v) <= limit for v in values.values()),
            "Value outside bounds")


class Substitution(GeneratorFamily):
    info = GeneratorInfo(
        id="algebra.substitution.values",
        version=1,
        topic="algebra",
        subtopic="substitution",
        title="Substitute into expressions",
        difficulty_descriptions={
            1: "One letter, a positive value.",
            2: "Two letters, including a negative value.",
            3: "Squares and products with negative values.",
            4: "Fractions, brackets, square roots and formulae.",
        },
        tags=("algebra", "substitution", "negative_numbers"),
    )
    keys = {1: {"terms", "values"}, 2: {"terms", "values"}, 3: {"terms", "values"},
            4: {"template", "values"}}

    def build(self, level, rng):
        if level == 1:
            v = rng.choice(VARIABLES)
            return {"terms": [[rng.randint(2, 9), [[v, 1]]], [nonzero(rng, 15), []]],
                    "values": {v: rng.randint(2, 10)}}
        if level == 2:
            v, w = rng.choice(PAIRS)
            terms = [[rng.randint(2, 9), [[v, 1]]], [nonzero_between(rng, 2, 9), [[w, 1]]]]
            if rng.random() < 0.5:
                terms.append([nonzero(rng, 15), []])
            chosen = [nonzero(rng, 6), nonzero(rng, 6)]
            if min(chosen) > 0:
                chosen[rng.randint(0, 1)] *= -1
            return {"terms": terms, "values": {v: chosen[0], w: chosen[1]}}
        if level == 3:
            v, w = rng.choice(PAIRS)
            c, d, k = rng.randint(1, 5), nonzero(rng, 6), nonzero(rng, 12)
            shape = rng.choice(("square_plus", "quadratic", "square_product", "product_minus_square"))
            if shape == "square_plus":
                terms, names = [[c, [[v, 2]]], [k, []]], (v,)
            elif shape == "quadratic":
                terms, names = [[c, [[v, 2]]], [d, [[v, 1]]], [k, []]], (v,)
            elif shape == "square_product":
                terms, names = [[c, [[v, 2], [w, 1]]]], (v, w)
            else:
                terms, names = [[c, [[v, 1], [w, 1]]], [d, [[w, 2]]]], (v, w)
            chosen = [nonzero(rng, 6) for _ in names]
            if min(chosen) > 0:
                chosen[rng.randint(0, len(chosen) - 1)] *= -1
            return {"terms": terms, "values": dict(zip(names, chosen))}
        key = rng.choice(sorted(FORMULAS))
        return {"template": key, "values": FORMULAS[key].make(rng)}

    def check_rules(self, p, level):
        if level == 4:
            require(p["template"] in FORMULAS, "Unknown formula")
            formula = FORMULAS[p["template"]]
            valid_values(p["values"], formula.names, 20)
            value = evaluate_formula(formula.python, p["values"])
        else:
            terms, values = p["terms"], p["values"]
            valid_terms(terms, 2 if level == 3 else 1, 15)
            valid_values(values, variables_in(terms), 10)
            if level == 1:
                require(len(terms) == 2 and len(values) == 1
                        and all(2 <= v <= 10 for v in values.values()), "Outside level 1 forms")
            elif level == 2:
                require(len(values) == 2 and min(values.values()) < 0, "Expected a negative value")
            else:
                require(any(degree(m) >= 2 for _, m in terms), "Expected a square or product")
                require(min(values.values()) < 0, "Expected a negative value")
            value = Fraction(evaluate_terms(terms, values))
        require(value.denominator == 1 and abs(value) <= MAX_ANSWER, "Answer outside bounds")

    def expression(self, p, level):
        if level == 4:
            formula = FORMULAS[p["template"]]
            return formula.plain, formula.tex, evaluate_formula(formula.python, p["values"])
        terms = p["terms"]
        return (expression_text(terms), expression_text(terms, True),
                Fraction(evaluate_terms(terms, p["values"])))

    def parts(self, p, level):
        plain, tex, value = self.expression(p, level)
        runs, assignments = assignment_runs(p["values"])
        prompt = Content(
            "Work out the value of {} when {}.".format(plain, assignments),
            blocks=(rb.paragraph(
                rb.text("Work out the value of "), rb.maths(tex, plain),
                rb.text(" when "), *runs, rb.text("."),
            ),),
        )
        text = rational_text(value)
        return {
            "prompt": prompt,
            "answer": {"kind": "rational", "value": text},
            "answer_display": Content(text, text),
            "marks": {1: 1, 2: 2, 3: 2, 4: 2}[level],
            "working_lines": {1: 2, 2: 3, 3: 3, 4: 3}[level],
        }

    def validate_independently(self, question):
        """Substitute with SymPy into an independently built expression."""
        import sympy
        p = question.parameters
        if question.difficulty == 4:
            expression = sympy.sympify(FORMULAS[p["template"]].python)
        else:
            expression = sympy_terms(p["terms"])
        substituted = expression.subs({sympy.Symbol(k): v for k, v in p["values"].items()})
        require(sympy.simplify(substituted - sympy.Rational(question.answer["value"])) == 0,
                "Independent substitution failed")
        return True