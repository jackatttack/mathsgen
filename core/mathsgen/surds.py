"""Surds: simplifying, arithmetic, expanding brackets and rationalising.

Every surd is held as a rational coefficient and a squarefree integer
radicand, so "simplified" is a property of the representation rather than
something detected afterwards. An expression is a sum of such terms, which
covers a rational number (radicand 1), a single surd, and a binomial.

Notation follows index_meaning.py: sqrt(2) in plain text, \\sqrt{2} in TeX.

Difficulty follows the operation rather than the size of the numbers:
level 1 simplifies and collects like surds, level 2 multiplies and divides,
level 3 expands brackets or finds an exact triangle perimeter, and level 4
rationalises a denominator, sometimes to find a rectangle perimeter.
"""
from fractions import Fraction
from math import gcd

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)
from . import figures
from .worded import rich_prompt


# --- Editable difficulty bounds -------------------------------------------
# Radicands are squarefree; each level draws from a pool chosen so the
# arithmetic stays reasonable without a calculator.
RADICANDS = {
    1: (2, 3, 5, 6, 7, 10),
    2: (2, 3, 5, 6, 7, 11, 13),
    3: (2, 3, 5, 6, 7),
    4: (2, 3, 5, 6, 7, 10, 11),
}

SQUARE_FACTORS = (2, 3, 4, 5, 6)


def squarefree(value):
    """Whether an integer has no square factor above one."""
    require(type(value) is int and value >= 1, "Radicand must be a positive integer")
    factor = 2
    while factor * factor <= value:
        if value % (factor * factor) == 0:
            return False
        factor += 1
    return True


def simplify_root(radicand):
    """Split a positive integer into an integer coefficient and a squarefree part.

    For example 72 becomes (6, 2), because 72 is 36 times 2.
    """
    require(type(radicand) is int and radicand >= 1, "Radicand must be positive")
    coefficient, remaining = 1, radicand
    factor = 2
    while factor * factor <= remaining:
        while remaining % (factor * factor) == 0:
            remaining //= factor * factor
            coefficient *= factor
        factor += 1
    return coefficient, remaining


class Term:
    """A rational coefficient multiplying the square root of a squarefree integer.

    A radicand of 1 is an ordinary rational number, which is what lets one
    representation carry both the rational and irrational parts of an answer.
    """

    def __init__(self, coefficient, radicand=1):
        coefficient = Fraction(coefficient)
        extra, radicand = simplify_root(int(radicand))
        self.coefficient = coefficient * extra
        self.radicand = radicand
        if self.coefficient == 0:
            self.radicand = 1

    def __eq__(self, other):
        return (self.coefficient == other.coefficient
                and self.radicand == other.radicand)

    def multiply(self, other):
        """Multiply two terms; the shared square part comes outside the root."""
        product = self.radicand * other.radicand
        extra, radicand = simplify_root(product)
        return Term(self.coefficient * other.coefficient * extra, radicand)

    def value(self):
        """A SymPy value, used only by the independent check."""
        import sympy
        return sympy.Rational(self.coefficient) * sympy.sqrt(self.radicand)

    def text(self, tex=False):
        coefficient = self.coefficient
        if self.radicand == 1:
            return rational_tex(coefficient) if tex else rational_text(coefficient)
        root = (r"\sqrt{" + str(self.radicand) + "}" if tex
                else "sqrt(" + str(self.radicand) + ")")
        if coefficient == 1:
            return root
        if coefficient == -1:
            return "-" + root
        if coefficient.denominator != 1:
            # A fractional coefficient reads as a fraction of the surd:
            # sqrt(6)/3 rather than (1/3)sqrt(6).
            numerator = abs(coefficient.numerator)
            sign = "-" if coefficient < 0 else ""
            top = root if numerator == 1 else str(numerator) + root
            if tex:
                return sign + r"\frac{" + top + "}{" + str(coefficient.denominator) + "}"
            return sign + top + "/" + str(coefficient.denominator)
        written = rational_tex(coefficient) if tex else rational_text(coefficient)
        return written + root


def collect(terms):
    """Add like terms and drop anything that cancels to zero.

    Terms are ordered with the rational part last, which is how an answer
    such as 2sqrt(3) + 5 is conventionally written.
    """
    totals = {}
    for term in terms:
        totals[term.radicand] = totals.get(term.radicand, 0) + term.coefficient
    # The rational part is written first, then surds by increasing radicand,
    # which is how an answer such as 166 - 40sqrt(6) is conventionally set out.
    ordered = sorted(
        (radicand for radicand in totals if totals[radicand] != 0),
        key=lambda radicand: (radicand != 1, radicand),
    )
    collected = [Term(totals[radicand], radicand) for radicand in ordered]
    return collected or [Term(0)]


def expression_text(terms, tex=False):
    """Join collected terms with the signs written the way a student would."""
    pieces = []
    for index, term in enumerate(terms):
        written = term.text(tex)
        if index == 0:
            pieces.append(written)
        elif written.startswith("-"):
            pieces.append(" - " + written[1:])
        else:
            pieces.append(" + " + written)
    return "".join(pieces)


def multiply_expressions(first, second):
    return collect([a.multiply(b) for a in first for b in second])


def right_triangle_scene(parameters):
    leg = parameters["leg"]
    nodes = [
        {"type": "polygon", "points": [[70, 45], [270, 45], [70, 245]]},
        {"type": "right_angle", "vertex": [70, 45],
         "first": [270, 45], "second": [70, 245]},
        {"type": "label", "point": [170, 23], "text": "{} cm".format(leg)},
        {"type": "label", "point": [34, 145], "text": "{} cm".format(leg)},
    ]
    scene = {
        "kind": "scene", "version": 1, "width": 360, "height": 255,
        "caption": "Not drawn accurately", "nodes": nodes,
    }
    return figures.orient_scene(scene, parameters["orientation"])


def presentation(parameters):
    form = parameters["form"]

    if form == "simplify":
        radicand = parameters["radicand"]
        instruction = "Simplify the following surd."
        return Content(
            "{} sqrt({})".format(instruction, radicand),
            r"\sqrt{" + str(radicand) + "}",
            display_text=instruction,
        )

    if form == "collect":
        terms = [Term(Fraction(c), r) for c, r in parameters["terms"]]
        instruction = "Simplify the following, giving your answer in surd form."
        plain = expression_text(terms)
        return Content(
            instruction + " " + plain, expression_text(terms, True),
            display_text=instruction,
        )

    if form in ("multiply", "divide"):
        first = Term(Fraction(parameters["first"][0]), parameters["first"][1])
        second = Term(Fraction(parameters["second"][0]), parameters["second"][1])
        symbol, tex_symbol = (("×", r"\times") if form == "multiply"
                              else ("÷", r"\div"))
        instruction = "Work out the following, giving your answer in surd form."
        plain = "{} {} {}".format(first.text(), symbol, second.text())
        maths = "{} {} {}".format(first.text(True), tex_symbol, second.text(True))
        return Content(instruction + " " + plain, maths, display_text=instruction)

    if form == "expand":
        left = [Term(Fraction(c), r) for c, r in parameters["left"]]
        right = [Term(Fraction(c), r) for c, r in parameters["right"]]
        instruction = "Expand and simplify, giving your answer in surd form."
        if parameters["left"] == parameters["right"]:
            # Identical brackets are written as a square, as a paper would.
            plain = "({})^2".format(expression_text(left))
            maths = r"\left(" + expression_text(left, True) + r"\right)^{2}"
        else:
            plain = "({})({})".format(expression_text(left), expression_text(right))
            maths = r"\left({}\right)\left({}\right)".format(
                expression_text(left, True), expression_text(right, True)
            )
        return Content(instruction + " " + plain, maths, display_text=instruction)

    if form == "right_triangle":
        leg = parameters["leg"]
        instruction = "Find the exact perimeter in simplest surd form."
        return Content(
            "A right-angled isosceles triangle has two perpendicular sides "
            "of {} cm. {}".format(leg, instruction),
            display_text=instruction,
        )

    if form == "rectangle_perimeter":
        width = [Term(parameters["width_rational"]),
                 Term(1, parameters["width_radicand"])]
        return rich_prompt((
            "A rectangle has area {} cm² and width ".format(parameters["area"]),
            (expression_text(width, True), expression_text(width)),
            " cm. Find its exact perimeter in simplest surd form.",
        ))

    # Rationalising: the denominator is one term or a binomial.
    numerator = [Term(Fraction(c), r) for c, r in parameters["numerator"]]
    denominator = [Term(Fraction(c), r) for c, r in parameters["denominator"]]
    instruction = "Rationalise the denominator, simplifying your answer."

    def bracketed(terms):
        """Brackets only where a side has more than one term."""
        written = expression_text(terms)
        return "(" + written + ")" if len(terms) > 1 else written

    plain = "{} / {}".format(bracketed(numerator), bracketed(denominator))
    maths = (r"\frac{" + expression_text(numerator, True) + "}{"
             + expression_text(denominator, True) + "}")
    return Content(instruction + " " + plain, maths, display_text=instruction)


def answer_terms(parameters):
    """The exact simplified answer, as a list of collected terms."""
    form = parameters["form"]

    if form == "simplify":
        coefficient, radicand = simplify_root(parameters["radicand"])
        return [Term(coefficient, radicand)]

    if form == "collect":
        return collect([Term(Fraction(c), r) for c, r in parameters["terms"]])

    if form == "multiply":
        first = Term(Fraction(parameters["first"][0]), parameters["first"][1])
        second = Term(Fraction(parameters["second"][0]), parameters["second"][1])
        return [first.multiply(second)]

    if form == "divide":
        first = Term(Fraction(parameters["first"][0]), parameters["first"][1])
        second = Term(Fraction(parameters["second"][0]), parameters["second"][1])
        # Dividing by sqrt(b) is multiplying by sqrt(b)/b, which keeps the
        # result in coefficient-and-radicand form without a surd below.
        radicand = second.radicand
        rationalised = Term(
            first.coefficient / (second.coefficient * radicand), 1
        ).multiply(Term(1, first.radicand * radicand))
        return [rationalised]

    if form == "expand":
        left = [Term(Fraction(c), r) for c, r in parameters["left"]]
        right = [Term(Fraction(c), r) for c, r in parameters["right"]]
        return multiply_expressions(left, right)

    if form == "right_triangle":
        leg = parameters["leg"]
        return collect([Term(2 * leg), Term(leg, 2)])

    if form == "rectangle_perimeter":
        b = parameters["width_rational"]
        r = parameters["width_radicand"]
        area = parameters["area"]
        divisor = b * b - r
        # The other side is area/(b + sqrt(r)).
        height = [Term(Fraction(area * b, divisor)),
                  Term(Fraction(-area, divisor), r)]
        return collect([Term(2 * b), Term(2, r)] +
                       [Term(2 * term.coefficient, term.radicand)
                        for term in height])

    numerator = [Term(Fraction(c), r) for c, r in parameters["numerator"]]
    denominator = [Term(Fraction(c), r) for c, r in parameters["denominator"]]
    if len(denominator) == 1:
        term = denominator[0]
        multiplier = [Term(1, term.radicand)]
        divisor = term.coefficient * term.radicand
    else:
        # Multiply by the conjugate: the difference of two squares leaves a
        # rational denominator.
        first, second = denominator
        multiplier = [first, Term(-second.coefficient, second.radicand)]
        product = multiply_expressions(denominator, multiplier)
        require(len(product) == 1 and product[0].radicand == 1,
                "Conjugate did not rationalise the denominator")
        divisor = product[0].coefficient

    scaled = multiply_expressions(numerator, multiplier)
    return collect([Term(term.coefficient / divisor, term.radicand)
                    for term in scaled])


def answer_for(parameters):
    terms = answer_terms(parameters)
    answer = {
        "kind": "surd_expression",
        "terms": [[rational_text(term.coefficient), term.radicand] for term in terms],
    }
    display = Content(expression_text(terms), expression_text(terms, True))
    return answer, display


INFO = GeneratorInfo(
    id="number.surds.manipulation", version=2,
    topic="number", subtopic="surds",
    title="Simplify and manipulate surds",
    difficulty_descriptions={
        1: "Simplify a surd, or collect like surds.",
        2: "Multiply or divide surds, simplifying the result.",
        3: "Expand surd brackets or find an exact triangle perimeter.",
        4: "Rationalise a denominator, sometimes to find a rectangle perimeter.",
    },
    tags=("surds", "roots", "exact", "simplifying", "rationalising"),
)


class SurdManipulation:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        builders = {
            1: self.make_level_one, 2: self.make_level_two,
            3: self.make_level_three, 4: self.make_level_four,
        }
        if difficulty == 3 and rng.random() < 0.4:
            parameters = self.make_right_triangle(rng)
        elif difficulty == 4 and rng.random() < 0.4:
            parameters = self.make_rectangle_perimeter(rng)
        else:
            parameters = builders[difficulty](rng)

        prompt = presentation(parameters)
        answer, display = answer_for(parameters)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=(5 if parameters["form"] == "rectangle_perimeter"
                   else 3 if difficulty >= 3 else 2),
            tags=self.info.tags,
            layout_hint=LayoutHint(
                working_lines=6 if parameters["form"] == "rectangle_perimeter"
                else 4 if difficulty >= 3 else 3
            ),
            parameters=parameters,
            question_visuals=((right_triangle_scene(parameters),)
                              if parameters["form"] == "right_triangle" else ()),
        )
        self.validate(question)
        return question

    def make_level_one(self, rng):
        if rng.choice((True, False)):
            base = rng.choice(RADICANDS[1])
            square = rng.choice(SQUARE_FACTORS)
            return {"form": "simplify", "radicand": base * square * square}
        # Collecting like surds: at least two share a radicand so something
        # genuinely combines.
        radicand = rng.choice(RADICANDS[1])
        first = rng.randint(2, 9)
        second = rng.choice([value for value in range(-9, 10)
                             if value and value != -first])
        terms = [[str(first), radicand], [str(second), radicand]]
        if rng.choice((True, False)):
            other = rng.choice([value for value in RADICANDS[1] if value != radicand])
            terms.append([str(rng.randint(2, 6)), other])
        rng.shuffle(terms)
        return {"form": "collect", "terms": terms}

    def make_level_two(self, rng):
        form = rng.choice(("multiply", "divide"))
        if form == "multiply":
            first_radicand = rng.choice(RADICANDS[2])
            second_radicand = rng.choice(RADICANDS[2])
            return {
                "form": "multiply",
                "first": [str(rng.randint(1, 6)), first_radicand],
                "second": [str(rng.randint(1, 6)), second_radicand],
            }
        # Division is constructed so the result is a whole multiple of a surd
        # rather than an awkward fraction.
        # The product of the two radicands is stored directly, so the pair
        # must be coprime: 2 and 6 would give 12, which has a square factor.
        pairs = [
            (first, second)
            for first in RADICANDS[2] for second in RADICANDS[2]
            if first != second and gcd(first, second) == 1
        ]
        inner, outer = rng.choice(pairs)
        second_coefficient = rng.randint(1, 4)
        first_coefficient = second_coefficient * rng.randint(2, 6)
        return {
            "form": "divide",
            "first": [str(first_coefficient), inner * outer],
            "second": [str(second_coefficient), outer],
        }

    def make_level_three(self, rng):
        radicand = rng.choice(RADICANDS[3])
        left = [[str(rng.randint(1, 5)), radicand],
                [str(rng.choice([v for v in range(-6, 7) if v])), 1]]
        if rng.choice((True, False)):
            # A square such as (3 + sqrt(5))^2, where the cross terms double.
            right = [list(part) for part in left]
        else:
            right = [[str(rng.randint(1, 5)), radicand],
                     [str(rng.choice([v for v in range(-6, 7) if v])), 1]]
        return {"form": "expand", "left": left, "right": right}

    def make_right_triangle(self, rng):
        parameters = {"form": "right_triangle", "leg": rng.randint(3, 10),
                      "orientation": [0, False]}
        parameters["orientation"] = figures.choose_orientation(
            rng, lambda orientation: right_triangle_scene(
                dict(parameters, orientation=orientation)
            )
        )
        return parameters

    def make_rectangle_perimeter(self, rng):
        while True:
            b = rng.choice((4, 5))
            radicand = rng.choice([r for r in RADICANDS[4] if r < b * b])
            area = rng.randint(6, 20)
            if area != b * b - radicand:
                return {"form": "rectangle_perimeter", "width_rational": b,
                        "width_radicand": radicand, "area": area}

    def make_level_four(self, rng):
        radicand = rng.choice(RADICANDS[4])
        if rng.choice((True, False)):
            denominator = [[str(rng.randint(1, 4)), radicand]]
            numerator = [[str(rng.randint(2, 12)), 1]]
        else:
            # A binomial denominator, rationalised with its conjugate.
            rational = rng.choice([value for value in range(-6, 7) if value])
            surd = rng.choice([value for value in range(-4, 5) if value])
            # The rational part is stated first, matching how answers are
            # written, and the numerator stays positive so the question is
            # about rationalising rather than about sign bookkeeping.
            denominator = [[str(rational), 1], [str(surd), radicand]]
            numerator = [[str(rng.randint(2, 9)), 1]]
        return {
            "form": "rationalise",
            "numerator": numerator, "denominator": denominator,
        }

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")

        parameters = question.parameters
        form = parameters.get("form")
        allowed = {
            1: ("simplify", "collect"), 2: ("multiply", "divide"),
            3: ("expand", "right_triangle"),
            4: ("rationalise", "rectangle_perimeter"),
        }
        require(form in allowed[level], "Form does not match difficulty")

        self.check_structure(parameters, level)

        answer, display = answer_for(parameters)
        for coefficient, radicand in answer["terms"]:
            require(squarefree(radicand), "Answer contains an unsimplified surd")
            require(Fraction(coefficient) != 0 or len(answer["terms"]) == 1,
                    "Answer contains a zero term")
        require(question.answer == answer, "Incorrect answer")
        require(question.answer_display == display, "Display mismatch")
        require(question.prompt == presentation(parameters), "Prompt mismatch")
        expected_visuals = ((right_triangle_scene(parameters),)
                            if form == "right_triangle" else ())
        require(question.visual_assets("questions") == expected_visuals
                and question.visual_assets("answers") == (),
                "Surd diagram mismatch")
        return True

    def check_structure(self, parameters, level):
        form = parameters["form"]

        if form == "simplify":
            require(set(parameters) == {"form", "radicand"}, "Unexpected parameters")
            radicand = parameters["radicand"]
            require(type(radicand) is int and radicand > 1, "Invalid radicand")
            coefficient, remaining = simplify_root(radicand)
            require(coefficient > 1, "This surd is already simplified")
            require(remaining > 1, "A perfect square is not a surd question")
            return

        if form == "collect":
            require(set(parameters) == {"form", "terms"}, "Unexpected parameters")
            terms = self.read_terms(parameters["terms"])
            require(2 <= len(terms) <= 3, "Unexpected number of terms")
            radicands = [term.radicand for term in terms]
            require(all(value > 1 for value in radicands), "Expected surd terms")
            require(len(set(radicands)) < len(radicands),
                    "Nothing to collect: no repeated radicand")
            return

        if form in ("multiply", "divide"):
            require(set(parameters) == {"form", "first", "second"},
                    "Unexpected parameters")
            first = self.read_terms([parameters["first"]])[0]
            second = self.read_terms([parameters["second"]])[0]
            require(first.radicand > 1 and second.radicand > 1,
                    "Expected surds on both sides")
            require(1 <= first.coefficient <= 36 and 1 <= second.coefficient <= 36,
                    "Coefficient outside difficulty bounds")
            if form == "divide":
                result = answer_terms(parameters)[0]
                require(result.coefficient.denominator == 1,
                        "Division should give a whole coefficient")
            return

        if form == "expand":
            require(set(parameters) == {"form", "left", "right"},
                    "Unexpected parameters")
            for side in ("left", "right"):
                terms = self.read_terms(parameters[side])
                require(len(terms) == 2, "Expected a binomial")
                require(sorted(term.radicand for term in terms)[0] == 1,
                        "Expected one rational and one surd term")
                require(max(term.radicand for term in terms) > 1,
                        "Expected a surd term")
            return

        if form == "right_triangle":
            require(set(parameters) == {"form", "leg", "orientation"},
                    "Unexpected triangle parameters")
            require(type(parameters["leg"]) is int
                    and 3 <= parameters["leg"] <= 10,
                    "Triangle leg outside bounds")
            require(figures.valid_orientation(parameters["orientation"]),
                    "Invalid triangle orientation")
            return

        if form == "rectangle_perimeter":
            require(set(parameters) == {
                "form", "width_rational", "width_radicand", "area"
            }, "Unexpected rectangle parameters")
            b, r, area = (parameters["width_rational"],
                          parameters["width_radicand"], parameters["area"])
            require(type(b) is int and b in (4, 5)
                    and type(r) is int and r in RADICANDS[4]
                    and r < b * b and type(area) is int
                    and 6 <= area <= 20 and area != b * b - r,
                    "Rectangle givens outside bounds")
            return

        require(set(parameters) == {"form", "numerator", "denominator"},
                "Unexpected parameters")
        numerator = self.read_terms(parameters["numerator"])
        denominator = self.read_terms(parameters["denominator"])
        require(len(numerator) >= 1, "Expected a numerator")
        require(len(denominator) in (1, 2), "Expected one or two denominator terms")
        if len(denominator) == 1:
            require(denominator[0].radicand > 1, "Denominator is already rational")
        else:
            radicands = sorted(term.radicand for term in denominator)
            require(radicands[0] == 1 and radicands[1] > 1,
                    "Expected a rational and a surd term")
            first, second = denominator
            product = multiply_expressions(
                denominator, [first, Term(-second.coefficient, second.radicand)]
            )
            require(len(product) == 1 and product[0].coefficient != 0,
                    "Conjugate would give a zero denominator")

    @staticmethod
    def read_terms(raw):
        """Rebuild terms from stored pairs, checking the stored form is canonical."""
        terms = []
        for pair in raw:
            require(isinstance(pair, list) and len(pair) == 2, "Invalid stored term")
            coefficient, radicand = pair
            require(type(radicand) is int and radicand >= 1, "Invalid radicand")
            require(squarefree(radicand), "Stored radicand is not squarefree")
            value = Fraction(coefficient)
            require(coefficient == rational_text(value), "Non-canonical coefficient")
            terms.append(Term(value, radicand))
        return terms

    def validate_independently(self, question):
        """Compare against SymPy's own simplification of the stated expression."""
        import sympy

        parameters = question.parameters
        form = parameters["form"]

        def expression(raw):
            total = sympy.Integer(0)
            for coefficient, radicand in raw:
                total += sympy.Rational(coefficient) * sympy.sqrt(radicand)
            return total

        if form == "simplify":
            expected = sympy.sqrt(parameters["radicand"])
        elif form == "collect":
            expected = expression(parameters["terms"])
        elif form == "multiply":
            expected = expression([parameters["first"]]) * expression(
                [parameters["second"]]
            )
        elif form == "divide":
            expected = expression([parameters["first"]]) / expression(
                [parameters["second"]]
            )
        elif form == "expand":
            expected = expression(parameters["left"]) * expression(
                parameters["right"]
            )
        elif form == "right_triangle":
            leg = sympy.Integer(parameters["leg"])
            expected = 2 * leg + sympy.sqrt(leg * leg + leg * leg)
        elif form == "rectangle_perimeter":
            width = (sympy.Integer(parameters["width_rational"])
                     + sympy.sqrt(parameters["width_radicand"]))
            expected = 2 * (width + sympy.Rational(parameters["area"]) / width)
        else:
            expected = expression(parameters["numerator"]) / expression(
                parameters["denominator"]
            )

        submitted = expression(question.answer["terms"])
        require(sympy.simplify(submitted - expected) == 0,
                "Independent surd simplification disagrees")

        # The answer must also be in surd form: no root left in a denominator.
        for coefficient, radicand in question.answer["terms"]:
            value = sympy.Rational(coefficient)
            require(value.q >= 1, "Coefficient is not rational")
            require(sympy.Integer(radicand).is_integer, "Radicand is not an integer")
        return True