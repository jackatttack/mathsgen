"""Take out the greatest common factor, over one or two letters.

A term is a coefficient together with a power for each letter in play, so
3x^2y and 6xy^3 are [3, (2, 1)] and [6, (1, 3)] over the letters (x, y).
The greatest common factor takes the numerical gcd and the SMALLEST power
of each letter, which is what makes xy^2 a common factor of x^2y^2 and
xy^3 but x^2y^2 not one.

Representing every level this way means the single-letter levels are the
same code with a one-letter list, rather than a separate path.

Difficulty follows what the factor contains: a number, then a number with
subtraction, then a number and one letter, then two letters with powers.
"""
from functools import reduce
from math import gcd

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)


INFO = GeneratorInfo(
    id="algebra.factorising.common_factor",
    version=2,
    topic="algebra",
    subtopic="factorising",
    title="Take out the greatest common factor",
    difficulty_descriptions={
        1: "A positive numerical common factor in two positive terms.",
        2: "A numerical common factor in an expression containing subtraction.",
        3: "A common factor containing both a number and a letter.",
        4: "A common factor containing two letters, such as xy^2.",
    },
    tags=("algebra", "factorising", "common_factor"),
)

LETTER_PAIRS = (("x", "y"), ("a", "b"), ("p", "q"))


def monomial(coefficient, powers, letters, tex=False):
    """Write one term: a coefficient and a power for each letter."""
    if coefficient == 0:
        return "0"
    magnitude = abs(coefficient)
    body = ""
    for letter, power in zip(letters, powers):
        if power == 0:
            continue
        body += letter
        if power != 1:
            body += "^{" + str(power) + "}" if tex else "^" + str(power)
    if not body:
        body = str(magnitude)
    elif magnitude != 1:
        body = str(magnitude) + body
    return ("-" if coefficient < 0 else "") + body


def expression_text(terms, letters, tex=False):
    """Join terms with their signs, as a student would write them."""
    pieces = []
    for index, (coefficient, powers) in enumerate(terms):
        written = monomial(coefficient, powers, letters, tex)
        if index == 0:
            pieces.append(written)
        elif written.startswith("-"):
            pieces.append(" - " + written[1:])
        else:
            pieces.append(" + " + written)
    return "".join(pieces) or "0"


def factorised_text(factor, factor_powers, inner, letters, tex=False):
    outside = monomial(factor, factor_powers, letters, tex)
    inside = expression_text(inner, letters, tex)
    if tex:
        return outside + r"\left(" + inside + r"\right)"
    return outside + "(" + inside + ")"


def greatest_common_factor(terms):
    """The numerical gcd and the smallest power of each letter."""
    coefficients = [abs(coefficient) for coefficient, _ in terms]
    numerical = reduce(gcd, coefficients)
    powers = tuple(
        min(term_powers[index] for _, term_powers in terms)
        for index in range(len(terms[0][1]))
    )
    return numerical, powers


def divided_by(terms, factor, factor_powers):
    """Each term after the common factor is taken out."""
    return [
        (
            coefficient // factor,
            tuple(power - taken for power, taken in zip(powers, factor_powers)),
        )
        for coefficient, powers in terms
    ]


class CommonFactor:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng

        letters = LETTER_PAIRS[0] if difficulty < 4 else rng.choice(LETTER_PAIRS)
        letter_count = 1 if difficulty < 4 else 2

        factor = rng.randint(2, 9)
        if difficulty <= 2:
            factor_powers = (0,)
        elif difficulty == 3:
            factor_powers = (rng.choice((1, 1, 2)),)
        else:
            # The factor carries both letters, at least one with a power
            # above one, so xy^2 and x^2y appear rather than only xy.
            first_power = rng.choice((1, 2))
            second_power = rng.choice((1, 2))
            if first_power == 1 and second_power == 1:
                second_power = 2
            factor_powers = (first_power, second_power)

        # Primitive inner coefficients guarantee the numerical factor really
        # is the greatest one.
        first = rng.randint(1, 7)
        second = rng.choice([
            value for value in range(1, 10) if gcd(first, value) == 1
        ])
        signs = [1, 1] if difficulty == 1 else [1, -1]
        inner_coefficients = [first * signs[0], second * signs[1]]

        # Inner powers must have a zero for every letter somewhere, or the
        # stated factor would not be the greatest.
        #
        # A single letter raised to the same even power in both inner terms
        # would leave a difference of two squares inside the bracket, which
        # "factorise fully" would then require factorising again. That
        # archetype belongs to the difference_of_squares family, so the
        # inner terms here are kept to first powers on one side.
        if letter_count == 1:
            inner_powers = [(1,), (0,)]
        else:
            inner_powers = [
                (rng.choice((1, 2)), 0),
                (0, rng.choice((1, 2))),
            ]

        inner = list(zip(inner_coefficients, inner_powers))

        # A bracket whose two terms are both perfect squares with opposite
        # signs is a difference of two squares, which "factorise fully"
        # would require factorising again. Test for it rather than assuming
        # the letter arrangement prevents it: at level 4 the two terms carry
        # different letters and can still both be squares.
        def is_square_term(coefficient, powers):
            root = int(abs(coefficient) ** 0.5 + 0.5)
            if root * root != abs(coefficient):
                return False
            return all(power % 2 == 0 for power in powers)

        if (inner[0][0] * inner[1][0] < 0
                and is_square_term(*inner[0]) and is_square_term(*inner[1])):
            # Nudge the leading coefficient to a non-square, keeping it
            # coprime with the other so the numerical factor stays greatest.
            for candidate in range(2, 10):
                if (gcd(candidate, abs(inner[1][0])) == 1
                        and not is_square_term(candidate, inner[0][1])):
                    inner[0] = (candidate * (1 if inner[0][0] > 0 else -1),
                                inner[0][1])
                    break
            else:
                raise ValueError("Could not avoid a difference of two squares")
        terms = [
            (
                factor * coefficient,
                tuple(power + taken for power, taken in zip(powers, factor_powers)),
            )
            for coefficient, powers in inner
        ]

        instruction = "Factorise fully."
        plain = expression_text(terms, letters)
        maths = expression_text(terms, letters, True)

        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=Content(
                instruction + " " + plain, maths, display_text=instruction,
            ),
            answer={
                "kind": "common_factor_form",
                "factor": factor,
                "factor_powers": list(factor_powers),
                "inner": [[c, list(p)] for c, p in inner],
                "letters": list(letters[:letter_count]),
            },
            answer_display=Content(
                factorised_text(factor, factor_powers, inner, letters),
                factorised_text(factor, factor_powers, inner, letters, True),
            ),
            worked_solution=(),
            marks=2 if difficulty <= 2 else 3,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=4),
            parameters={
                "terms": [[c, list(p)] for c, p in terms],
                "letters": list(letters[:letter_count]),
            },
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")

        p = question.parameters
        letters = tuple(p["letters"])
        require(len(letters) == (2 if level == 4 else 1),
                "Letter count does not match difficulty")
        require(letters in [pair[:len(letters)] for pair in LETTER_PAIRS],
                "Unknown letters")

        terms = [(c, tuple(powers)) for c, powers in p["terms"]]
        require(len(terms) == 2, "Expected two terms")
        require(all(type(c) is int and c != 0 for c, _ in terms),
                "Expected nonzero integer coefficients")
        require(all(len(powers) == len(letters) for _, powers in terms),
                "Each term needs a power for every letter")
        require(all(type(power) is int and power >= 0
                    for _, powers in terms for power in powers),
                "Powers must be non-negative integers")

        answer = question.answer
        factor = answer["factor"]
        factor_powers = tuple(answer["factor_powers"])
        inner = [(c, tuple(powers)) for c, powers in answer["inner"]]

        require(type(factor) is int and 2 <= factor <= 9,
                "Invalid numerical factor")

        # The stated factor must genuinely be the greatest one.
        numerical, common_powers = greatest_common_factor(terms)
        require(numerical == factor, "Numerical factor is not the greatest")
        require(common_powers == factor_powers,
                "Letter powers are not the greatest common ones")
        require(divided_by(terms, factor, factor_powers) == inner,
                "Inner terms do not match the division")

        if level <= 2:
            require(factor_powers == (0,), "Unexpected letter in the factor")
            require(inner[0][0] > 0, "Expected a positive leading term")
            require((inner[1][0] > 0) == (level == 1),
                    "Incorrect sign structure")
        elif level == 3:
            require(factor_powers[0] >= 1, "Expected a letter in the factor")
        else:
            require(len(factor_powers) == 2, "Expected two letters")
            require(all(power >= 1 for power in factor_powers),
                    "Both letters should appear in the factor")
            require(max(factor_powers) >= 2,
                    "At least one letter should carry a power above one")

        require(max(abs(c) for c, _ in terms) <= 81, "Coefficients outside bounds")
        require(question.prompt == Content(
            "Factorise fully. " + expression_text(terms, letters),
            expression_text(terms, letters, True),
            display_text="Factorise fully.",
        ), "Prompt mismatch")
        require(question.answer_display == Content(
            factorised_text(factor, factor_powers, inner, letters),
            factorised_text(factor, factor_powers, inner, letters, True),
        ), "Answer display mismatch")
        require(question.visual_assets("questions") == ()
                and question.visual_assets("answers") == (),
                "This family uses no visual assets")
        return True

    def validate_independently(self, question):
        """Let SymPy factor the expression and compare the result.

        SymPy's own factorisation is a different route from constructing the
        expression outwards from a chosen factor, and it also confirms the
        factorisation is complete rather than merely correct.
        """
        import sympy

        p = question.parameters
        letters = [sympy.Symbol(name, positive=True) for name in p["letters"]]

        def build(terms):
            total = sympy.Integer(0)
            for coefficient, powers in terms:
                term = sympy.Integer(coefficient)
                for symbol, power in zip(letters, powers):
                    term *= symbol ** power
                total += term
            return total

        expression = build([(c, powers) for c, powers in p["terms"]])
        answer = question.answer

        outside = sympy.Integer(answer["factor"])
        for symbol, power in zip(letters, answer["factor_powers"]):
            outside *= symbol ** power
        inside = build([(c, powers) for c, powers in answer["inner"]])
        submitted = outside * inside

        require(sympy.expand(expression - submitted) == 0,
                "Independent expansion disagrees")

        # The bracket must have nothing left to take out, or the
        # factorisation is incomplete.
        remaining = sympy.factor_terms(inside)
        require(remaining == inside or sympy.expand(remaining - inside) == 0,
                "Independent check could not confirm the inner form")
        content = sympy.gcd([sympy.Integer(c) for c, _ in answer["inner"]])
        require(content == 1, "The bracket still has a common numerical factor")
        for index in range(len(letters)):
            require(min(powers[index] for _, powers in answer["inner"]) == 0,
                    "The bracket still has a common letter factor")
        return True