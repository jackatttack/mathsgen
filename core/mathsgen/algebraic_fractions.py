"""Exact algebraic fractions with original-domain restrictions.

Polynomials use ascending coefficients: [2, 3, 1] means x^2 + 3x + 2.
Generation and simplification use Fraction arithmetic; SymPy is used only
by the independent validator.
"""
from fractions import Fraction
from functools import reduce
from math import gcd

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)

INFO = GeneratorInfo(
    id="algebra.fractions.manipulation", version=1,
    topic="algebra", subtopic="algebraic_fractions",
    title="Simplify and calculate with algebraic fractions",
    difficulty_descriptions={
        1: "Cancel numerical factors and powers of x.",
        2: "Factorise quadratics before cancelling common factors.",
        3: "Multiply or divide fractions with polynomial factors.",
        4: "Add or subtract fractions with different linear denominators.",
    },
    tags=("algebra", "fractions", "factorising"),
)


def trim(poly):
    result = [Fraction(value) for value in poly]
    while len(result) > 1 and result[-1] == 0:
        result.pop()
    return result


def multiply(first, second):
    result = [Fraction(0)] * (len(first) + len(second) - 1)
    for i, a in enumerate(first):
        for j, b in enumerate(second):
            result[i + j] += a * b
    return trim(result)


def add(first, second, sign=1):
    result = [Fraction(0)] * max(len(first), len(second))
    for i, value in enumerate(first):
        result[i] += value
    for i, value in enumerate(second):
        result[i] += sign * value
    return trim(result)


def divide_polynomials(top, bottom):
    """Polynomial long division over the rationals."""
    remainder, bottom = trim(top), trim(bottom)
    require(bottom != [0], "Zero polynomial divisor")
    quotient = [Fraction(0)] * max(1, len(remainder) - len(bottom) + 1)
    while remainder != [0] and len(remainder) >= len(bottom):
        power = len(remainder) - len(bottom)
        coefficient = remainder[-1] / bottom[-1]
        quotient[power] += coefficient
        remainder = add(
            remainder, [0] * power + [coefficient * v for v in bottom], -1
        )
    return trim(quotient), remainder


def canonical_fraction(top, bottom):
    """Cancel the polynomial gcd and normalise to primitive integer data."""
    top, bottom = trim(top), trim(bottom)
    require(bottom != [0], "Zero denominator")
    first, second = top, bottom
    while second != [0]:
        first, second = second, divide_polynomials(first, second)[1]
    common = [v / first[-1] for v in first]
    top, remainder = divide_polynomials(top, common)
    require(remainder == [0], "Numerator division failed")
    bottom, remainder = divide_polynomials(bottom, common)
    require(remainder == [0], "Denominator division failed")
    scale = 1
    for value in top + bottom:
        scale = scale * value.denominator // gcd(scale, value.denominator)
    integers = [int(v * scale) for v in top + bottom]
    content = reduce(gcd, (abs(v) for v in integers))
    sign = 1 if bottom[-1] > 0 else -1
    integers = [sign * v // content for v in integers]
    return integers[:len(top)], integers[len(top):]


def polynomial_text(poly, tex=False):
    parts = []
    for power in range(len(poly) - 1, -1, -1):
        value = int(poly[power])
        if not value:
            continue
        magnitude = abs(value)
        if power:
            body = (str(magnitude) if magnitude != 1 else "") + "x"
            if power > 1:
                body += ("^{" + str(power) + "}") if tex else "^" + str(power)
        else:
            body = str(magnitude)
        parts.append(("-" if value < 0 else "") + body if not parts else
                     (" - " if value < 0 else " + ") + body)
    return "".join(parts) or "0"


def fraction_text(pair, tex=False):
    top, bottom = [polynomial_text(poly, tex) for poly in pair]
    if bottom == "1":
        return top
    if tex:
        return r"\frac{" + top + "}{" + bottom + "}"
    return "(" + top + ")/(" + bottom + ")"


def expression_text(p, tex=False):
    fractions = [fraction_text(pair, tex) for pair in p["fractions"]]
    if p["operation"] == "single":
        return fractions[0]
    symbol = {
        "multiply": r" \times " if tex else " * ",
        "divide": r" \div " if tex else " / ",
        "add": " + ", "subtract": " - ",
    }[p["operation"]]
    return symbol.join(fractions)


def combined(p):
    top, bottom = p["fractions"][0]
    if p["operation"] == "single":
        return top, bottom
    other_top, other_bottom = p["fractions"][1]
    if p["operation"] == "multiply":
        return multiply(top, other_top), multiply(bottom, other_bottom)
    if p["operation"] == "divide":
        return multiply(top, other_bottom), multiply(bottom, other_top)
    sign = 1 if p["operation"] == "add" else -1
    return (
        add(multiply(top, other_bottom), multiply(other_top, bottom), sign),
        multiply(bottom, other_bottom),
    )


def roots(poly):
    """All zeros of our deliberately integer-rooted denominator factors."""
    remainder = trim(poly)
    found = []
    for value in range(-12, 13):
        factor = [-value, 1]
        while len(remainder) > 1:
            quotient, rest = divide_polynomials(remainder, factor)
            if rest != [0]:
                break
            found.append(value)
            remainder = quotient
    require(len(remainder) == 1 and remainder[0] != 0,
            "Unsupported denominator roots")
    return found


def excluded_values(p):
    excluded = set()
    for top, bottom in p["fractions"]:
        excluded.update(roots(bottom))
    if p["operation"] == "divide":
        excluded.update(roots(p["fractions"][1][0]))
    return sorted(excluded)


def answer_for(p):
    top, bottom = canonical_fraction(*combined(p))
    excluded = excluded_values(p)
    return {
        "kind": "rational_expression", "numerator": top,
        "denominator": bottom, "excluded": excluded,
    }


def display_for(answer):
    pair = (answer["numerator"], answer["denominator"])
    restrictions = ", ".join(str(v) for v in answer["excluded"])
    return Content(
        fraction_text(pair) + "; x must not equal " + restrictions,
        fraction_text(pair, True) + r"\quad x \ne " + restrictions,
    )


def prompt_for(p):
    instruction = (
        "Simplify fully. State every value of x for which the original "
        "expression is undefined."
    )
    return Content(instruction + " " + expression_text(p),
                   expression_text(p, True), display_text=instruction)


def quadratic(a, b):
    return [a * b, a + b, 1]


class AlgebraicFractions:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        constants = [v for v in range(-6, 7) if v]
        if difficulty == 1:
            common = rng.randint(2, 6)
            first = rng.randint(1, 5)
            second = rng.choice([v for v in range(2, 7) if gcd(first, v) == 1])
            low = rng.randint(1, 2)
            high = low + rng.randint(1, 2)
            powers = (low, high) if rng.choice((False, True)) else (high, low)
            p = {"operation": "single", "fractions": [[
                [0] * powers[0] + [common * first],
                [0] * powers[1] + [common * second],
            ]]}
        elif difficulty == 2:
            a, b, c = rng.sample(constants, 3)
            p = {"operation": "single", "fractions": [
                [quadratic(a, b), quadratic(a, c)]
            ]}
        elif difficulty == 3:
            a, b, c, d = rng.sample(constants, 4)
            operation = rng.choice(("multiply", "divide"))
            second = [[c, 1], [d, 1]]
            if operation == "divide":
                second.reverse()
            p = {"operation": operation, "fractions": [
                [quadratic(a, b), quadratic(a, c)], second,
            ]}
        else:
            a, b = rng.sample(constants, 2)
            first, second = rng.sample(range(1, 7), 2)
            p = {"operation": rng.choice(("add", "subtract")), "fractions": [
                [[first], [a, 1]], [[second], [b, 1]],
            ]}
        answer = answer_for(p)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(p), answer=answer,
            answer_display=display_for(answer), worked_solution=(),
            marks=3 if difficulty < 3 else 4, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=5), parameters=p,
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        require(type(q.difficulty) is int and q.difficulty in (1, 2, 3, 4),
                "Invalid level")
        require(q.settings == {}, "Unsupported settings")
        p = q.parameters
        require(set(p) == {"operation", "fractions"}, "Unexpected parameters")
        allowed = {1: ("single",), 2: ("single",),
                   3: ("multiply", "divide"), 4: ("add", "subtract")}
        require(p["operation"] in allowed[q.difficulty], "Wrong operation")
        require(len(p["fractions"]) == (1 if q.difficulty < 3 else 2),
                "Wrong fraction count")
        for pair in p["fractions"]:
            require(len(pair) == 2, "Malformed fraction")
            for poly in pair:
                require(isinstance(poly, list) and 1 <= len(poly) <= 5,
                        "Invalid polynomial")
                require(all(type(v) is int and abs(v) <= 42 for v in poly)
                        and poly[-1] != 0, "Invalid coefficients")
        first_top, first_bottom = p["fractions"][0]
        if q.difficulty == 1:
            require(all(v == 0 for v in first_top[:-1] + first_bottom[:-1]),
                    "Expected monomials")
            require(min(len(first_top), len(first_bottom)) >= 2
                    and len(first_top) != len(first_bottom),
                    "Expected cancellable, unequal powers")
            require(gcd(first_top[-1], first_bottom[-1]) > 1,
                    "Expected numerical cancellation")
        elif q.difficulty in (2, 3):
            require(len(first_top) == len(first_bottom) == 3
                    and first_top[-1] == first_bottom[-1] == 1,
                    "Expected monic quadratics")
            top_roots, bottom_roots = set(roots(first_top)), set(roots(first_bottom))
            require(len(top_roots) == len(bottom_roots) == 2
                    and len(top_roots & bottom_roots) == 1,
                    "Expected exactly one common linear factor")
            if q.difficulty == 3:
                other_top, other_bottom = p["fractions"][1]
                require(len(other_top) == len(other_bottom) == 2
                        and other_top[-1] == other_bottom[-1] == 1,
                        "Expected linear second fraction")
                cancelling = other_top if p["operation"] == "multiply" else other_bottom
                remaining = other_bottom if p["operation"] == "multiply" else other_top
                require(set(roots(cancelling)) == bottom_roots - top_roots,
                        "Expected cross-cancellation")
                require(not (set(roots(remaining)) & (top_roots | bottom_roots)),
                        "Expected distinct remaining factor")
        else:
            require(all(len(top) == 1 and 1 <= top[0] <= 6
                        and len(bottom) == 2 and bottom[-1] == 1
                        for top, bottom in p["fractions"]),
                    "Expected constants over linear denominators")
            require(p["fractions"][0][1] != p["fractions"][1][1]
                    and p["fractions"][0][0] != p["fractions"][1][0],
                    "Expected distinct denominators and numerators")
        answer = answer_for(p)
        require(q.answer == answer, "Incorrect or unsimplified answer/domain")
        require(q.prompt == prompt_for(p), "Prompt mismatch")
        require(q.answer_display == display_for(answer), "Display mismatch")
        require(not q.visual_assets("questions") and not q.visual_assets("answers"),
                "Unexpected visuals")
        return True

    def validate_independently(self, q):
        """Symbolic equivalence, coprimality and original-domain checks."""
        import sympy
        x = sympy.Symbol("x")

        def polynomial(values):
            return sum(sympy.Integer(v) * x ** i for i, v in enumerate(values))

        pairs = [(polynomial(top), polynomial(bottom))
                 for top, bottom in q.parameters["fractions"]]
        original = pairs[0][0] / pairs[0][1]
        operation = q.parameters["operation"]
        if len(pairs) == 2:
            other = pairs[1][0] / pairs[1][1]
            if operation == "multiply":
                original *= other
            elif operation == "divide":
                original /= other
            elif operation == "add":
                original += other
            else:
                original -= other
        answer = q.answer
        top, bottom = polynomial(answer["numerator"]), polynomial(answer["denominator"])
        require(bottom != 0, "Zero answer denominator")
        require(sympy.cancel(original - top / bottom) == 0,
                "Independent expression disagrees")
        require(sympy.degree(sympy.gcd(top, bottom), x) == 0,
                "Uncancelled polynomial factor")
        coefficients = answer["numerator"] + answer["denominator"]
        require(all(type(v) is int for v in coefficients)
                and reduce(gcd, (abs(v) for v in coefficients)) == 1,
                "Uncancelled numerical factor")
        forbidden = set()
        domain_polynomials = [bottom for top, bottom in pairs]
        if operation == "divide":
            domain_polynomials.append(pairs[1][0])
        for poly in domain_polynomials:
            forbidden.update(sympy.solve(poly, x))
        require(forbidden == set(map(sympy.Integer, answer["excluded"]))
                and len(answer["excluded"]) == len(forbidden),
                "Original domain restrictions disagree")
        return True