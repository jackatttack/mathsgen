"""Negative numbers and the order of operations, with integer answers.

Each question displays an expression built from a template and integers.
validate() evaluates exactly the displayed plain expression (standard
precedence, every division exact); validate_independently() re-parses the
same text with SymPy. Answers are checked against what students see.

Plain notation uses ×, ÷ and ^. Placeholders are {a} to {e}:
    ({a})  a bracketed single number, which must be negative
    {a}    at the start or straight after "(": any nonzero integer
    {a}    anywhere else: a positive integer
so a display such as "5 + -3" can never be produced.
"""
import ast
from collections import namedtuple
from fractions import Fraction
import re

from .core import Content, GeneratorInfo, rational_text, require
from .family import GeneratorFamily
from . import rich_blocks as rb


PLACEHOLDER = re.compile(r"\{([a-e])\}")
MAX_VALUE = 60
MAX_ANSWER = 999

# plain: display template; make: rng -> values; over: (numerator, denominator)
# templates when the expression is shown with a fraction bar.
Template = namedtuple("Template", "plain make over")
Template.__new__.__defaults__ = (None,)


# ------------------------------------------------------- expression helpers

def python_form(plain):
    return plain.replace("×", "*").replace("÷", "/").replace("^", "**")


def evaluate_display(plain):
    """Exact value of a displayed expression; every division must be exact."""
    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return Fraction(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -walk(node.operand)
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
                require(result.denominator == 1, "Every division must be exact")
                return result
            if isinstance(node.op, ast.Pow):
                require(right.denominator == 1 and 0 <= right <= 3, "Unsupported power")
                return left ** int(right)
        raise ValueError("Unsupported expression")
    return walk(ast.parse(python_form(plain), mode="eval"))


def render(template, values):
    """Substitute values, enforcing the bracket and sign rules."""
    require(isinstance(values, dict) and set(values) == set(PLACEHOLDER.findall(template)),
            "Values do not match the template")
    for match in PLACEHOLDER.finditer(template):
        value = values[match.group(1)]
        require(type(value) is int and value != 0 and abs(value) <= MAX_VALUE,
                "Value outside bounds")
        before = template[match.start() - 1] if match.start() else ""
        after = template[match.end()] if match.end() < len(template) else ""
        if before == "(" and after == ")":
            require(value < 0, "Brackets around a single number are reserved for negatives")
        elif before not in ("", "("):
            require(value > 0, "A negative number must be bracketed")
    return PLACEHOLDER.sub(lambda m: str(values[m.group(1)]), template)


def tex_of(plain):
    tex = plain.replace("×", r"\times").replace("÷", r"\div")
    for power in "23":
        tex = tex.replace("^" + power, "^{" + power + "}")
    return tex


def subset(values, template):
    return {name: values[name] for name in PLACEHOLDER.findall(template)}


def displayed(template, values):
    """(plain, tex) for a template, using a fraction bar where declared."""
    plain = render(template.plain, values)
    if template.over is None:
        return plain, tex_of(plain)
    top, bottom = template.over
    tex = r"\frac{" + tex_of(render(top, subset(values, top))) + "}{" + tex_of(
        render(bottom, subset(values, bottom))) + "}"
    return plain, tex


def nonzero(rng, limit):
    return rng.choice([v for v in range(-limit, limit + 1) if v != 0])


def divisors(value, largest):
    return [d for d in range(2, min(value, largest) + 1) if value % d == 0]


# ---------------------------------------------------- negative-number makers

def _negative_minus(rng):
    return {"a": -rng.randint(2, 15), "b": rng.randint(2, 12)}


def _subtract_past_zero(rng):
    a = rng.randint(2, 12)
    return {"a": a, "b": a + rng.randint(1, 12)}


def _signed_quotient(rng):
    b = -rng.randint(2, 12)
    return {"a": nonzero(rng, 5) * b, "b": b}


def _negative_quotient(rng):
    b = -rng.randint(2, 12)
    return {"a": rng.randint(2, 5) * b, "b": b}


def _product_then_divide(rng):
    c = -rng.randint(2, 6)
    return {"a": rng.randint(2, 9), "b": c * rng.randint(2, 6), "c": c}


NEGATIVE_TEMPLATES = {
    1: {
        "negative_plus": Template("{a} + {b}", lambda r: {"a": -r.randint(2, 15), "b": r.randint(2, 20)}),
        "past_zero": Template("{a} - {b}", _subtract_past_zero),
        "negative_minus": Template("{a} - {b}", _negative_minus),
        "add_negative": Template("{a} + ({b})", lambda r: {"a": r.randint(2, 15), "b": -r.randint(2, 20)}),
    },
    2: {
        "subtract_negative": Template("{a} - ({b})", lambda r: {"a": nonzero(r, 12), "b": -r.randint(2, 15)}),
        "two_negatives": Template("{a} + ({b}) - ({c})", lambda r: {
            "a": r.randint(2, 15), "b": -r.randint(2, 12), "c": -r.randint(2, 12)}),
        "minus_then_negative": Template("{a} - {b} - ({c})", lambda r: {
            "a": nonzero(r, 10), "b": r.randint(2, 12), "c": -r.randint(2, 12)}),
        "mixed_signs": Template("{a} - ({b}) + ({c})", lambda r: {
            "a": nonzero(r, 10), "b": -r.randint(2, 12), "c": -r.randint(2, 12)}),
    },
    3: {
        "times_negative": Template("{a} × ({b})", lambda r: {"a": r.randint(2, 12), "b": -r.randint(2, 12)}),
        "negative_times": Template("{a} × {b}", lambda r: {"a": -r.randint(2, 12), "b": r.randint(2, 12)}),
        "both_negative": Template("({a}) × ({b})", lambda r: {"a": -r.randint(2, 12), "b": -r.randint(2, 12)}),
        "divide_by_negative": Template("{a} ÷ ({b})", _signed_quotient),
        "negative_by_negative": Template("({a}) ÷ ({b})", _negative_quotient),
    },
    4: {
        "square_minus": Template("({a})^2 - {b}", lambda r: {"a": -r.randint(2, 9), "b": r.randint(1, 30)}),
        "minus_square": Template("{a} - ({b})^2", lambda r: {"a": r.randint(2, 20), "b": -r.randint(2, 6)}),
        "three_negatives": Template("({a}) × ({b}) × ({c})", lambda r: {
            "a": -r.randint(2, 5), "b": -r.randint(2, 5), "c": -r.randint(2, 5)}),
        "product_divide": Template("{a} × ({b}) ÷ ({c})", _product_then_divide),
        "cube": Template("({a})^3", lambda r: {"a": -r.randint(2, 5)}),
        "precedence": Template("{a} - ({b}) × {c}", lambda r: {
            "a": r.randint(2, 20), "b": -r.randint(2, 9), "c": r.randint(2, 9)}),
    },
}


# ------------------------------------------------ order-of-operations makers

def _times_minus(rng):
    a, b = rng.randint(2, 9), rng.randint(2, 9)
    return {"a": a, "b": b, "c": rng.randint(1, min(MAX_VALUE, a * b - 1))}


def _minus_times(rng):
    b, c = rng.randint(2, 6), rng.randint(2, 6)
    return {"a": b * c + rng.randint(1, 20), "b": b, "c": c}


def _plus_divide(rng):
    c = rng.randint(2, 9)
    return {"a": rng.randint(2, 20), "b": c * rng.randint(2, 6), "c": c}


def _times_bracket(rng):
    b = rng.randint(3, 15)
    return {"a": rng.randint(2, 9), "b": b, "c": rng.randint(1, b - 1)}


def _bracket_divide(rng):
    b, c = rng.randint(2, 12), rng.randint(2, 9)
    return {"a": b + c * rng.randint(2, 5), "b": b, "c": c}


def _four_terms(rng):
    a, b, c = rng.randint(2, 20), rng.randint(2, 9), rng.randint(2, 9)
    return {"a": a, "b": b, "c": c, "d": rng.randint(1, min(MAX_VALUE, a + b * c - 1))}


def _square_divide(rng):
    b = rng.randint(2, 9)
    return {"a": rng.randint(2, 50), "b": b, "c": rng.choice(divisors(b * b, MAX_VALUE))}


def _fraction_bar(rng):
    b, c, k, e = rng.randint(2, 6), rng.randint(2, 6), rng.randint(2, 9), rng.randint(1, 9)
    product = b * c
    q = rng.randint(product // k + 1, (product + 30) // k)
    return {"a": k * q - product, "b": b, "c": c, "d": e + k, "e": e}


def _nested(rng):
    c = rng.randint(1, 9)
    return {"a": rng.randint(2, 20), "b": rng.randint(2, 6), "c": c, "d": c + rng.randint(1, 8)}


def _square_bracket_divide(rng):
    m, b = rng.randint(2, 6), rng.randint(1, 10)
    return {"a": b + m, "b": b, "c": rng.choice(divisors(m * m, MAX_VALUE)), "d": rng.randint(1, 20)}


def _bracket_quotient(rng):
    a, b, d = rng.randint(3, 9), rng.randint(3, 9), rng.randint(2, 6)
    lowest = max(1, -(-(a * b - MAX_VALUE) // d))
    q = rng.randint(lowest, (a * b - 1) // d)
    return {"a": a, "b": b, "c": a * b - d * q, "d": d, "e": rng.randint(1, 15)}


ORDER_TEMPLATES = {
    1: {
        "plus_times": Template("{a} + {b} × {c}", lambda r: {
            "a": r.randint(2, 20), "b": r.randint(2, 9), "c": r.randint(2, 9)}),
        "times_minus": Template("{a} × {b} - {c}", _times_minus),
        "minus_times": Template("{a} - {b} × {c}", _minus_times),
        "plus_divide": Template("{a} + {b} ÷ {c}", _plus_divide),
    },
    2: {
        "bracket_times": Template("({a} + {b}) × {c}", lambda r: {
            "a": r.randint(2, 12), "b": r.randint(2, 12), "c": r.randint(2, 9)}),
        "times_bracket": Template("{a} × ({b} - {c})", _times_bracket),
        "bracket_divide": Template("({a} - {b}) ÷ {c}", _bracket_divide),
        "four_terms": Template("{a} + {b} × {c} - {d}", _four_terms),
    },
    3: {
        "plus_square": Template("{a} + {b}^2", lambda r: {"a": r.randint(2, 20), "b": r.randint(2, 9)}),
        "times_square": Template("{a} × {b}^2", lambda r: {"a": r.randint(2, 5), "b": r.randint(2, 9)}),
        "bracket_square": Template("({a} + {b})^2 - {c}", lambda r: {
            "a": r.randint(1, 6), "b": r.randint(1, 6), "c": r.randint(1, 30)}),
        "square_minus_product": Template("{a}^2 - {b} × {c}", lambda r: {
            "a": r.randint(3, 9), "b": r.randint(2, 6), "c": r.randint(2, 6)}),
        "square_divide": Template("{a} - {b}^2 ÷ {c}", _square_divide),
    },
    4: {
        "fraction_bar": Template(
            "({a} + {b} × {c})/({d} - {e})", _fraction_bar,
            ("{a} + {b} × {c}", "{d} - {e}"),
        ),
        "nested": Template("{a} - {b} × ({c} - {d})", _nested),
        "square_bracket_divide": Template("({a} - {b})^2 ÷ {c} + {d}", _square_bracket_divide),
        "bracket_quotient": Template("({a} × {b} - {c}) ÷ {d} - {e}", _bracket_quotient),
        "negative_power": Template("{a} - ({b})^2 × {c}", lambda r: {
            "a": r.randint(2, 40), "b": -r.randint(2, 5), "c": r.randint(2, 4)}),
    },
}


# -------------------------------------------------------------- generators

class ExpressionFamily(GeneratorFamily):
    """Work out a displayed expression. Subclasses set info and TEMPLATES."""
    TEMPLATES = {}
    MARKS = {}
    keys = {1: {"template", "values"}, 2: {"template", "values"},
            3: {"template", "values"}, 4: {"template", "values"}}

    def build(self, level, rng):
        key = rng.choice(sorted(self.TEMPLATES[level]))
        return {"template": key, "values": self.TEMPLATES[level][key].make(rng)}

    def check_rules(self, p, level):
        require(p["template"] in self.TEMPLATES[level], "Template outside this level")
        plain, _ = displayed(self.TEMPLATES[level][p["template"]], p["values"])
        value = evaluate_display(plain)
        require(value.denominator == 1 and abs(value) <= MAX_ANSWER, "Answer outside bounds")

    def parts(self, p, level):
        plain, tex = displayed(self.TEMPLATES[level][p["template"]], p["values"])
        value = evaluate_display(plain)
        return {
            "prompt": Content(
                "Work out {}.".format(plain),
                blocks=(rb.prose("Work out"), rb.equation(tex, plain)),
            ),
            "answer": {"kind": "rational", "value": rational_text(value)},
            "answer_display": Content(rational_text(value), rational_text(value)),
            "marks": self.MARKS[level],
            "working_lines": {1: 2, 2: 3, 3: 3, 4: 4}[level],
        }

    def validate_independently(self, question):
        """Re-parse the displayed expression with SymPy."""
        import sympy
        p = question.parameters
        plain, _ = displayed(self.TEMPLATES[question.difficulty][p["template"]], p["values"])
        expected = sympy.sympify(python_form(plain))
        require(expected == sympy.Rational(question.answer["value"]), "Independent evaluation failed")
        return True


class NegativeNumbers(ExpressionFamily):
    info = GeneratorInfo(
        id="number.integers.negatives",
        version=2,
        topic="number",
        subtopic="negative_numbers",
        title="Calculate with negative numbers",
        difficulty_descriptions={
            1: "Add and subtract with one negative number; or a temperature change.",
            2: "Subtract negatives and combine three terms; or a temperature gap or bank balance.",
            3: "Multiply and divide negative numbers; or a steady fall or negative marking.",
            4: "Mix operations with squares and cubes; or a mean or missing temperature.",
        },
        tags=("negative_numbers", "integers", "directed_numbers"),
    )
    TEMPLATES = NEGATIVE_TEMPLATES
    MARKS = {1: 1, 2: 1, 3: 1, 4: 2}

    def generate(self, seed, difficulty=1, settings=None):
        """Draw once to choose a worded form; bare questions keep their old seeds."""
        from .core import make_context
        from . import negative_contexts as worded_forms
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        if context.rng.random() < worded_forms.CONTEXT_SHARE.get(difficulty, 0.0):
            return worded_forms.generate(self, context)
        return ExpressionFamily.generate(self, seed, difficulty, settings)

    def validate(self, question):
        from .worded import is_worded
        if is_worded(question):
            from .negative_contexts import validate as validate_worded
            return validate_worded(self, question)
        return ExpressionFamily.validate(self, question)

    def validate_independently(self, question):
        from .worded import is_worded
        if is_worded(question):
            from .negative_contexts import validate_independently as independent_worded
            return independent_worded(question)
        return ExpressionFamily.validate_independently(self, question)


class OrderOfOperations(ExpressionFamily):
    info = GeneratorInfo(
        id="number.operations.order",
        version=1,
        topic="number",
        subtopic="order_of_operations",
        title="Use the order of operations",
        difficulty_descriptions={
            1: "Multiply or divide before adding or subtracting.",
            2: "Brackets first, including three operations.",
            3: "Powers with multiplication, division and brackets.",
            4: "Fraction bars, nested brackets and squared negatives.",
        },
        tags=("order_of_operations", "bidmas", "priority_of_operations"),
    )
    TEMPLATES = ORDER_TEMPLATES
    MARKS = {1: 1, 2: 2, 3: 2, 4: 3}