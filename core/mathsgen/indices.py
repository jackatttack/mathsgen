"""Laws of indices: simplifying, evaluating and working backwards.

Version 3 of number.indices.rules. It absorbs number.indices.product,
number.indices.quotient and number.indices.power_of_power (retired
2026-09-25, docs/CONSOLIDATION_PLAN.txt) and replaces index_rules.py and
index_rule_forms.py. Every question has two or three lettered parts, each
testing a different skill.

Levels
    1  Simplify to a single power: multiply, divide, raise a power to a power.
    2  Simplify with coefficients, negative indices and mixed laws.
    3  Evaluate zero, negative and unit-fraction indices, and a fraction
       raised to a negative power.
    4  Evaluate fractional powers of whole numbers and of fractions, combine
       two powers, and work backwards to an unknown index.

Bases are always positive and every numerical answer is exactly rational.
"""
from fractions import Fraction
from math import gcd

from .core import GeneratorInfo, rational_tex, rational_text, require
from .family import GeneratorFamily
from .worded import rich_prompt


INFO = GeneratorInfo(
    id="number.indices.rules",
    version=3,
    topic="number",
    subtopic="indices",
    title="Laws of indices",
    difficulty_descriptions={
        1: "Simplify to a single power: multiply, divide and raise a power to a power.",
        2: "Simplify with coefficients, negative indices and mixed laws.",
        3: "Evaluate zero, negative and unit-fraction indices.",
        4: "Fractional powers, combined powers and finding an unknown index.",
    },
    tags=("indices", "powers", "roots", "reciprocals", "exact"),
)


# ---------------------------------------------------------------------------
# Editable settings
# ---------------------------------------------------------------------------

VARIABLES = ("x", "y", "a", "b", "t")

# Which kinds of part each level uses, and how many parts a question has.
# Parts in one question are always different kinds.
LEVEL_KINDS = {
    1: ("product", "quotient", "power"),
    2: ("product_coefficients", "quotient_coefficients", "power_coefficients", "mixed"),
    3: ("zero", "negative", "root", "fraction_negative"),
    4: ("fractional", "fraction_fractional", "combined", "power_of", "solve"),
}
LEVEL_PART_COUNTS = {1: (2, 3), 2: (2,), 3: (3,), 4: (2,)}

LEVEL_INSTRUCTIONS = {
    1: "Simplify each expression, giving each answer as a single power.",
    2: "Simplify each expression fully.",
    3: "Work out the exact value of each of these.",
    4: None,  # level 4 parts carry their own instructions
}
WORKING_LINES = {1: 3, 2: 5, 3: 4, 4: 6}

# Level 1 index ranges.
PRODUCT_INDICES = (2, 9)
QUOTIENT_TOP = (4, 12)
POWER_INNER = (2, 6)
POWER_OUTER = (2, 5)

# Level 2 ranges. Indices may be negative but never zero.
SIGNED_INDICES = (-6, 9)
COEFFICIENTS = (2, 9)
DIVISORS = (2, 6)
POWER_COEFFICIENTS = (2, 5)
SIGNED_POWER_INNER = (-4, 6)
SMALL_OUTER = (2, 3)
MIXED_INDICES = (2, 9)

# Level 3: bases for each negative index, and the largest root for each
# unit-fraction index.
ZERO_BASES = (2, 25)
NEGATIVE_BASES = {1: 20, 2: 12, 3: 10, 4: 7}
ROOT_LIMITS = {2: 12, 3: 6, 4: 4, 5: 3}
FRACTION_PARTS = (2, 5)
FRACTION_NEGATIVE_POWERS = (1, 2)

# Level 4.
FRACTIONAL_ROOTS = {2: 9, 3: 5, 4: 3}
FRACTIONAL_NUMERATORS = (2, 3)
FRACTION_BASE_ROOTS = (2, 3, 4)
FRACTION_BASE_NUMERATORS = {2: (1, 3), 3: (1, 2)}
COMBINED_FIRST_NUMERATORS = {2: 3, 3: 2, 4: 3}
COMBINED_FIRST_ROOT = (2, 4)
COMBINED_SECOND_DENOMINATORS = (2, 3)
COMBINED_SECOND_ROOT = (2, 5)
REVERSE_ROOTS = (2, 3, 5)
REVERSE_BASE_POWERS = (1, 3)
REVERSE_TARGET_POWERS = (-5, 5)
REVERSE_BASE_LIMIT = 125
REVERSE_TARGET_LIMIT = 729

# Largest numerator and denominator allowed in a numerical answer.
ANSWER_NUMERATOR_LIMIT = 1000
ANSWER_DENOMINATOR_LIMIT = 20736

PART_MARKS = {
    "product": 1, "quotient": 1, "power": 1,
    "product_coefficients": 2, "quotient_coefficients": 2,
    "power_coefficients": 2, "mixed": 2,
    "zero": 1, "negative": 1, "root": 1, "fraction_negative": 2,
    "fractional": 2, "fraction_fractional": 2, "combined": 3,
    "power_of": 2, "solve": 2,
}


# ---------------------------------------------------------------------------
# Fixed structure
# ---------------------------------------------------------------------------

LETTERS = "abc"
PART_ATTEMPTS = 300
ALGEBRA_KINDS = ("product", "quotient", "power", "product_coefficients",
                 "quotient_coefficients", "power_coefficients", "mixed")
NUMBER_KINDS = ("zero", "negative", "root", "fraction_negative",
                "fractional", "fraction_fractional")
REVERSE_KINDS = ("power_of", "solve")

ALGEBRA_KEYS = {"kind", "variable", "coefficients", "indices"}
NUMBER_KEYS = {"kind", "base", "exponent"}
COMBINED_KEYS = {"kind", "first", "second", "operator"}
REVERSE_KEYS = {"kind", "root", "base_power", "target_power"}


# ---------------------------------------------------------------------------
# Exact powers
# ---------------------------------------------------------------------------

def integer_root(base, index):
    """Return the exact integer root, refusing anything that is not exact."""
    estimate = round(base ** (1.0 / index))
    for candidate in (estimate - 1, estimate, estimate + 1):
        if candidate > 0 and candidate ** index == base:
            return candidate
    raise ValueError("Base is not a perfect power for this index")


def exact_power(base, exponent):
    """A positive rational base to a rational power, exactly: root, then power."""
    base, exponent = Fraction(base), Fraction(exponent)
    require(base > 0, "Bases must be positive")
    denominator = exponent.denominator
    root = Fraction(integer_root(base.numerator, denominator),
                    integer_root(base.denominator, denominator))
    magnitude = root ** abs(exponent.numerator)
    return magnitude if exponent >= 0 else 1 / magnitude


def exact_value(base, exponent):
    """Kept for tests that evaluate single powers of whole numbers."""
    return exact_power(base, exponent)


def algebra_result(part):
    """(coefficient, exponent) of the simplified single term."""
    kind = part["kind"]
    c = [Fraction(value) for value in part["coefficients"]]
    i = [Fraction(value) for value in part["indices"]]
    if kind == "product":
        return Fraction(1), i[0] + i[1]
    if kind == "quotient":
        return Fraction(1), i[0] - i[1]
    if kind == "power":
        return Fraction(1), i[0] * i[1]
    if kind == "product_coefficients":
        return c[0] * c[1], i[0] + i[1]
    if kind == "quotient_coefficients":
        return c[0] / c[1], i[0] - i[1]
    if kind == "power_coefficients":
        return c[0] ** int(i[1]), i[0] * i[1]
    return Fraction(1), i[0] + i[1] - i[2]


def combined_value(part):
    first = exact_power(part["first"]["base"], part["first"]["exponent"])
    second = exact_power(part["second"]["base"], part["second"]["exponent"])
    return first * second if part["operator"] == "multiply" else first / second


def reverse_pieces(part):
    """(base, target, unknown index) for a work-backwards part."""
    root = part["root"]
    base = root ** part["base_power"]
    target = Fraction(root) ** part["target_power"]
    return base, target, Fraction(part["target_power"], part["base_power"])


# ---------------------------------------------------------------------------
# Written forms: every helper returns (tex, plain)
# ---------------------------------------------------------------------------

def exponent_plain(exponent):
    exponent = Fraction(exponent)
    written = rational_text(exponent)
    return "(" + written + ")" if exponent < 0 or exponent.denominator != 1 else written


def base_forms(base):
    base = Fraction(base)
    if base.denominator == 1:
        return str(base.numerator), str(base.numerator)
    return r"\left(" + rational_tex(base) + r"\right)", "(" + rational_text(base) + ")"


def number_power(base, exponent):
    tex, plain = base_forms(base)
    return tex + "^{" + rational_tex(exponent) + "}", plain + "^" + exponent_plain(exponent)


def term(coefficient, variable, exponent):
    """A coefficient times a power of the variable."""
    coefficient, exponent = Fraction(coefficient), Fraction(exponent)
    lead = "" if coefficient == 1 else rational_text(coefficient)
    if exponent == 1:
        return lead + variable, lead + variable
    return (lead + variable + "^{" + rational_tex(exponent) + "}",
            lead + variable + "^" + exponent_plain(exponent))


def joined(left, symbol_tex, symbol_plain, right):
    return (left[0] + " " + symbol_tex + " " + right[0],
            left[1] + " " + symbol_plain + " " + right[1])


def algebra_expression(part):
    kind, v = part["kind"], part["variable"]
    c, i = part["coefficients"], part["indices"]
    if kind == "product":
        return joined(term(1, v, i[0]), r"\times", "×", term(1, v, i[1]))
    if kind == "quotient":
        return joined(term(1, v, i[0]), r"\div", "÷", term(1, v, i[1]))
    if kind == "power":
        inner = term(1, v, i[0])
        return (r"\left(" + inner[0] + r"\right)^{" + str(i[1]) + "}",
                "(" + inner[1] + ")^" + str(i[1]))
    if kind == "product_coefficients":
        return joined(term(c[0], v, i[0]), r"\times", "×", term(c[1], v, i[1]))
    if kind == "quotient_coefficients":
        top, bottom = term(c[0], v, i[0]), term(c[1], v, i[1])
        return r"\frac{" + top[0] + "}{" + bottom[0] + "}", top[1] + " ÷ " + bottom[1]
    if kind == "power_coefficients":
        inner = term(c[0], v, i[0])
        return (r"\left(" + inner[0] + r"\right)^{" + str(i[1]) + "}",
                "(" + inner[1] + ")^" + str(i[1]))
    top = joined(term(1, v, i[0]), r"\times", "×", term(1, v, i[1]))
    bottom = term(1, v, i[2])
    return (r"\frac{" + top[0] + "}{" + bottom[0] + "}",
            "(" + top[1] + ") ÷ " + bottom[1])


def question_pieces(part):
    """The prose and maths pieces for one lettered part."""
    kind = part["kind"]
    if kind in ALGEBRA_KINDS:
        return (algebra_expression(part),)
    if kind in ("zero", "negative", "root", "fraction_negative"):
        return (number_power(part["base"], part["exponent"]),)
    if kind in ("fractional", "fraction_fractional"):
        return ("Work out the exact value of ", number_power(part["base"], part["exponent"]), ".")
    if kind == "combined":
        first = number_power(part["first"]["base"], part["first"]["exponent"])
        second = number_power(part["second"]["base"], part["second"]["exponent"])
        if part["operator"] == "multiply":
            expression = joined(first, r"\times", "×", second)
        else:
            expression = joined(first, r"\div", "÷", second)
        return ("Work out the exact value of ", expression, ".")
    base, target, _ = reverse_pieces(part)
    target_forms = (rational_tex(target), rational_text(target))
    if kind == "power_of":
        return ("Write ", target_forms, " as a power of ", (str(base), str(base)), ".")
    equation = (str(base) + "^{n} = " + rational_tex(target),
                str(base) + "^n = " + rational_text(target))
    return ("Find the value of n when ", equation, ".")


def answer_for(part):
    """(structured answer, (tex, plain) display) for one part."""
    kind = part["kind"]
    if kind in ALGEBRA_KINDS:
        coefficient, exponent = algebra_result(part)
        return ({"kind": kind, "coefficient": rational_text(coefficient),
                 "exponent": rational_text(exponent)},
                term(coefficient, part["variable"], exponent))
    if kind in REVERSE_KINDS:
        base, _, unknown = reverse_pieces(part)
        answer = {"kind": kind, "exponent": rational_text(unknown)}
        if kind == "power_of":
            return answer, number_power(base, unknown)
        return answer, ("n = " + rational_tex(unknown), "n = " + rational_text(unknown))
    value = combined_value(part) if kind == "combined" else exact_power(
        part["base"], part["exponent"])
    return ({"kind": kind, "value": rational_text(value)},
            (rational_tex(value), rational_text(value)))


# ---------------------------------------------------------------------------
# Building parts
# ---------------------------------------------------------------------------

def signed_index(rng, bounds):
    return rng.choice([value for value in range(bounds[0], bounds[1] + 1) if value != 0])


def build_part(kind, rng):
    if kind in ALGEBRA_KINDS:
        variable = rng.choice(VARIABLES)
        coefficients, indices = [], []
        if kind == "product":
            indices = [rng.randint(*PRODUCT_INDICES), rng.randint(*PRODUCT_INDICES)]
        elif kind == "quotient":
            top = rng.randint(*QUOTIENT_TOP)
            indices = [top, rng.randint(2, top - 2)]
        elif kind == "power":
            indices = [rng.randint(*POWER_INNER), rng.randint(*POWER_OUTER)]
        elif kind == "product_coefficients":
            coefficients = [rng.randint(*COEFFICIENTS), rng.randint(*COEFFICIENTS)]
            indices = [signed_index(rng, SIGNED_INDICES), signed_index(rng, SIGNED_INDICES)]
        elif kind == "quotient_coefficients":
            divisor = rng.randint(*DIVISORS)
            coefficients = [divisor * rng.randint(*COEFFICIENTS), divisor]
            indices = [signed_index(rng, SIGNED_INDICES), signed_index(rng, SIGNED_INDICES)]
        elif kind == "power_coefficients":
            coefficients = [rng.randint(*POWER_COEFFICIENTS)]
            indices = [signed_index(rng, SIGNED_POWER_INNER), rng.randint(*SMALL_OUTER)]
        else:
            indices = [rng.randint(*MIXED_INDICES) for _ in range(3)]
        return {"kind": kind, "variable": variable,
                "coefficients": coefficients, "indices": indices}

    if kind == "zero":
        return number_part(kind, rng.randint(*ZERO_BASES), Fraction(0))
    if kind == "negative":
        magnitude = rng.choice(sorted(NEGATIVE_BASES))
        return number_part(kind, rng.randint(2, NEGATIVE_BASES[magnitude]), Fraction(-magnitude))
    if kind == "root":
        denominator = rng.choice(sorted(ROOT_LIMITS))
        root = rng.randint(2, ROOT_LIMITS[denominator])
        return number_part(kind, root ** denominator, Fraction(1, denominator))
    if kind == "fraction_negative":
        top, bottom = rng.sample(range(FRACTION_PARTS[0], FRACTION_PARTS[1] + 1), 2)
        return number_part(kind, Fraction(top, bottom),
                           Fraction(-rng.choice(FRACTION_NEGATIVE_POWERS)))
    if kind == "fractional":
        denominator = rng.choice(sorted(FRACTIONAL_ROOTS))
        numerator = rng.choice(FRACTIONAL_NUMERATORS)
        root = rng.randint(2, FRACTIONAL_ROOTS[denominator])
        sign = rng.choice((1, -1))
        return number_part(kind, root ** denominator, Fraction(sign * numerator, denominator))
    if kind == "fraction_fractional":
        top, bottom = rng.sample(FRACTION_BASE_ROOTS, 2)
        denominator = rng.choice(sorted(FRACTION_BASE_NUMERATORS))
        numerator = rng.choice(FRACTION_BASE_NUMERATORS[denominator])
        sign = rng.choice((1, -1))
        return number_part(kind, Fraction(top ** denominator, bottom ** denominator),
                           Fraction(sign * numerator, denominator))
    if kind == "combined":
        first_denominator = rng.choice(sorted(COMBINED_FIRST_NUMERATORS))
        second_denominator = rng.choice(COMBINED_SECOND_DENOMINATORS)
        first_root = rng.randint(*COMBINED_FIRST_ROOT)
        second_root = rng.randint(*COMBINED_SECOND_ROOT)
        return {
            "kind": kind,
            "first": {"base": first_root ** first_denominator,
                      "exponent": rational_text(Fraction(
                          COMBINED_FIRST_NUMERATORS[first_denominator], first_denominator))},
            "second": {"base": second_root ** second_denominator,
                       "exponent": rational_text(Fraction(-1, second_denominator))},
            "operator": rng.choice(("multiply", "divide")),
        }
    return {"kind": kind, "root": rng.choice(REVERSE_ROOTS),
            "base_power": rng.randint(*REVERSE_BASE_POWERS),
            "target_power": signed_index(rng, REVERSE_TARGET_POWERS)}


def number_part(kind, base, exponent):
    return {"kind": kind, "base": rational_text(Fraction(base)),
            "exponent": rational_text(Fraction(exponent))}


# ---------------------------------------------------------------------------
# Checking parts
# ---------------------------------------------------------------------------

def int_list(raw, length):
    require(isinstance(raw, list) and len(raw) == length
            and all(type(value) is int for value in raw), "Unexpected whole-number list")
    return raw


def within(value, bounds):
    return bounds[0] <= value <= bounds[1]


def canonical_fraction(text):
    require(isinstance(text, str), "Expected exact text")
    value = Fraction(text)
    require(text == rational_text(value), "Non-canonical value")
    return value


def check_algebra(part):
    require(set(part) == ALGEBRA_KEYS, "Unexpected algebra part")
    require(part["variable"] in VARIABLES, "Unknown variable")
    kind = part["kind"]
    coefficient_counts = {"product": 0, "quotient": 0, "power": 0, "mixed": 0,
                          "product_coefficients": 2, "quotient_coefficients": 2,
                          "power_coefficients": 1}
    c = int_list(part["coefficients"], coefficient_counts[kind])
    i = int_list(part["indices"], 3 if kind == "mixed" else 2)
    if kind == "product":
        require(all(within(value, PRODUCT_INDICES) for value in i), "Index outside bounds")
    elif kind == "quotient":
        require(within(i[0], QUOTIENT_TOP) and 2 <= i[1] <= i[0] - 2, "Index outside bounds")
    elif kind == "power":
        require(within(i[0], POWER_INNER) and within(i[1], POWER_OUTER), "Index outside bounds")
    elif kind == "product_coefficients":
        require(all(within(value, COEFFICIENTS) for value in c), "Coefficient outside bounds")
        require(all(value != 0 and within(value, SIGNED_INDICES) for value in i),
                "Index outside bounds")
    elif kind == "quotient_coefficients":
        require(within(c[1], DIVISORS) and c[0] % c[1] == 0
                and within(c[0] // c[1], COEFFICIENTS), "Coefficients must divide exactly")
        require(all(value != 0 and within(value, SIGNED_INDICES) for value in i),
                "Index outside bounds")
    elif kind == "power_coefficients":
        require(within(c[0], POWER_COEFFICIENTS), "Coefficient outside bounds")
        require(i[0] != 0 and within(i[0], SIGNED_POWER_INNER) and within(i[1], SMALL_OUTER),
                "Index outside bounds")
    else:
        require(all(within(value, MIXED_INDICES) for value in i), "Index outside bounds")
    coefficient, exponent = algebra_result(part)
    require(exponent != 0, "The powers must not cancel completely")
    require(coefficient.denominator == 1, "Coefficient must be a whole number")


def check_number(part):
    require(set(part) == NUMBER_KEYS, "Unexpected number part")
    kind = part["kind"]
    base = canonical_fraction(part["base"])
    exponent = canonical_fraction(part["exponent"])
    require(base > 0, "Bases must be positive")
    whole_base = base.denominator == 1
    if kind == "zero":
        require(whole_base and within(base, ZERO_BASES) and exponent == 0, "Expected a zero index")
    elif kind == "negative":
        magnitude = -exponent
        require(whole_base and exponent.denominator == 1 and magnitude in NEGATIVE_BASES
                and 2 <= base <= NEGATIVE_BASES[magnitude], "Expected a negative whole index")
    elif kind == "root":
        require(whole_base and exponent.numerator == 1 and exponent.denominator in ROOT_LIMITS,
                "Expected a unit fractional index")
        root = integer_root(base.numerator, exponent.denominator)
        require(2 <= root <= ROOT_LIMITS[exponent.denominator], "Root outside bounds")
    elif kind == "fraction_negative":
        require(not whole_base and within(base.numerator, FRACTION_PARTS)
                and within(base.denominator, FRACTION_PARTS), "Expected a simple fraction base")
        require(exponent.denominator == 1 and -exponent in FRACTION_NEGATIVE_POWERS,
                "Expected a negative whole index")
    elif kind == "fractional":
        denominator = exponent.denominator
        require(whole_base and denominator in FRACTIONAL_ROOTS
                and abs(exponent.numerator) in FRACTIONAL_NUMERATORS,
                "Expected a fractional index with a numerator above one")
        root = integer_root(base.numerator, denominator)
        require(2 <= root <= FRACTIONAL_ROOTS[denominator], "Root outside bounds")
    else:
        denominator = exponent.denominator
        require(not whole_base and denominator in FRACTION_BASE_NUMERATORS
                and abs(exponent.numerator) in FRACTION_BASE_NUMERATORS[denominator],
                "Expected a fractional index on a fraction")
        top = integer_root(base.numerator, denominator)
        bottom = integer_root(base.denominator, denominator)
        require(top in FRACTION_BASE_ROOTS and bottom in FRACTION_BASE_ROOTS,
                "Roots outside bounds")
    value = exact_power(base, exponent)
    require(value.numerator <= ANSWER_NUMERATOR_LIMIT
            and value.denominator <= ANSWER_DENOMINATOR_LIMIT, "Answer outside bounds")


def check_combined(part):
    require(set(part) == COMBINED_KEYS, "Unexpected combined part")
    require(part["operator"] in ("multiply", "divide"), "Unknown operation")
    for role in ("first", "second"):
        power = part[role]
        require(isinstance(power, dict) and set(power) == {"base", "exponent"},
                "Invalid power")
        require(type(power["base"]) is int and power["base"] >= 2, "Invalid base")
        exponent = canonical_fraction(power["exponent"])
        denominator = exponent.denominator
        if role == "first":
            require(denominator in COMBINED_FIRST_NUMERATORS
                    and exponent.numerator == COMBINED_FIRST_NUMERATORS[denominator],
                    "Expected a non-unit fractional index")
            bounds = COMBINED_FIRST_ROOT
        else:
            require(denominator in COMBINED_SECOND_DENOMINATORS and exponent.numerator == -1,
                    "Expected a negative unit fractional index")
            bounds = COMBINED_SECOND_ROOT
        require(within(integer_root(power["base"], denominator), bounds), "Root outside bounds")
    value = combined_value(part)
    require(value.numerator <= ANSWER_NUMERATOR_LIMIT
            and value.denominator <= ANSWER_NUMERATOR_LIMIT, "Answer outside bounds")


def check_reverse(part):
    require(set(part) == REVERSE_KEYS, "Unexpected work-backwards part")
    root, base_power, target_power = part["root"], part["base_power"], part["target_power"]
    require(root in REVERSE_ROOTS, "Unexpected root")
    require(type(base_power) is int and within(base_power, REVERSE_BASE_POWERS),
            "Base power outside bounds")
    require(type(target_power) is int and target_power != 0
            and within(target_power, REVERSE_TARGET_POWERS), "Target power outside bounds")
    require(target_power != base_power, "The answer must not be 1")
    require(root ** base_power <= REVERSE_BASE_LIMIT
            and root ** abs(target_power) <= REVERSE_TARGET_LIMIT, "Numbers too large")


def check_part(part):
    require(isinstance(part, dict), "Each part must be a mapping")
    kind = part.get("kind")
    if kind in ALGEBRA_KINDS:
        check_algebra(part)
    elif kind in NUMBER_KINDS:
        check_number(part)
    elif kind == "combined":
        check_combined(part)
    elif kind in REVERSE_KINDS:
        check_reverse(part)
    else:
        raise ValueError("Unknown part kind")


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class LawsOfIndices(GeneratorFamily):
    """Two or three lettered index questions, each a different skill."""
    info = INFO
    keys = {1: {"parts"}, 2: {"parts"}, 3: {"parts"}, 4: {"parts"}}

    def build(self, level, rng):
        kinds = rng.sample(LEVEL_KINDS[level], rng.choice(LEVEL_PART_COUNTS[level]))
        return {"parts": [self.build_checked_part(kind, rng) for kind in kinds]}

    def build_checked_part(self, kind, rng):
        for attempt in range(PART_ATTEMPTS):
            part = build_part(kind, rng)
            try:
                check_part(part)
            except ValueError:
                continue
            return part
        raise ValueError("Could not construct an index part ({})".format(kind))

    def check_rules(self, parameters, level):
        parts = parameters["parts"]
        require(isinstance(parts, list) and len(parts) in LEVEL_PART_COUNTS[level],
                "Unexpected number of parts")
        kinds = [part.get("kind") if isinstance(part, dict) else None for part in parts]
        require(all(kind in LEVEL_KINDS[level] for kind in kinds),
                "Part kind does not belong to this level")
        require(len(set(kinds)) == len(kinds), "Parts must test different skills")
        for part in parts:
            check_part(part)

    def parts(self, parameters, level):
        sentences = []
        if LEVEL_INSTRUCTIONS[level]:
            sentences.append((LEVEL_INSTRUCTIONS[level],))
        answers, answer_sentences = [], []
        for letter, part in zip(LETTERS, parameters["parts"]):
            label = "({}) ".format(letter)
            sentences.append((label,) + question_pieces(part))
            answer, forms = answer_for(part)
            answers.append(answer)
            answer_sentences.append((label, forms))
        return {
            "prompt": rich_prompt(*sentences),
            "answer": {"kind": "index_laws", "parts": answers},
            "answer_display": rich_prompt(*answer_sentences),
            "marks": sum(PART_MARKS[part["kind"]] for part in parameters["parts"]),
            "working_lines": WORKING_LINES[level],
        }

    def validate_independently(self, question):
        """Let SymPy evaluate each printed expression directly."""
        import sympy

        parts = question.parameters["parts"]
        answers = question.answer["parts"]
        require(len(parts) == len(answers), "One answer per part")
        for part, answer in zip(parts, answers):
            kind = part["kind"]
            if kind in ALGEBRA_KINDS:
                x = sympy.Symbol(part["variable"], positive=True)
                c = [sympy.Integer(value) for value in part["coefficients"]]
                i = [sympy.Integer(value) for value in part["indices"]]
                expression = {
                    "product": lambda: x ** i[0] * x ** i[1],
                    "quotient": lambda: x ** i[0] / x ** i[1],
                    "power": lambda: (x ** i[0]) ** i[1],
                    "product_coefficients": lambda: c[0] * x ** i[0] * c[1] * x ** i[1],
                    "quotient_coefficients": lambda: (c[0] * x ** i[0]) / (c[1] * x ** i[1]),
                    "power_coefficients": lambda: (c[0] * x ** i[0]) ** i[1],
                    "mixed": lambda: x ** i[0] * x ** i[1] / x ** i[2],
                }[kind]()
                claimed = (sympy.Rational(answer["coefficient"])
                           * x ** sympy.Rational(answer["exponent"]))
                require(sympy.simplify(expression - claimed) == 0,
                        "Independent simplification disagrees")
            elif kind in REVERSE_KINDS:
                base = sympy.Integer(part["root"]) ** part["base_power"]
                target = sympy.Integer(part["root"]) ** part["target_power"]
                require(sympy.simplify(base ** sympy.Rational(answer["exponent"]) - target) == 0,
                        "Independent check of the unknown index disagrees")
            elif kind == "combined":
                first = sympy.Integer(part["first"]["base"]) ** sympy.Rational(
                    part["first"]["exponent"])
                second = sympy.Integer(part["second"]["base"]) ** sympy.Rational(
                    part["second"]["exponent"])
                value = first * second if part["operator"] == "multiply" else first / second
                require(sympy.simplify(value - sympy.Rational(answer["value"])) == 0,
                        "Independent combined value disagrees")
            else:
                value = sympy.Rational(part["base"]) ** sympy.Rational(part["exponent"])
                require(sympy.simplify(value - sympy.Rational(answer["value"])) == 0,
                        "Independent power disagrees")
        return True