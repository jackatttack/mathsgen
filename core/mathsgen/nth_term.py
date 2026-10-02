"""Construct arithmetic and quadratic sequences from their exact nth terms."""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)


def expression(coefficients, tex=False):
    """Format an + b or an² + bn + c without redundant terms."""
    pieces = []
    formatter = rational_tex if tex else rational_text
    for coefficient, power in zip(coefficients, (2, 1, 0)):
        coefficient = Fraction(coefficient)
        if coefficient == 0:
            continue
        magnitude = abs(coefficient)
        if power == 0:
            body = formatter(magnitude)
        else:
            if magnitude == 1:
                body = ""
            elif not tex and magnitude.denominator != 1:
                body = "(" + formatter(magnitude) + ")"
            else:
                body = formatter(magnitude)
            body += "n"
            if power == 2:
                body += "^{2}" if tex else "^2"
        if pieces:
            pieces.append((" - " if coefficient < 0 else " + ") + body)
        else:
            pieces.append(("-" if coefficient < 0 else "") + body)
    return "".join(pieces) or "0"


def sequence_values(coefficients):
    a, b, c = map(Fraction, coefficients)
    return [a * n * n + b * n + c for n in range(1, 6)]


# --- Editable: using the rule -------------------------------------------------
# Share of plain linear questions that also ask for a far-off term, so the
# rule has to be used rather than the sequence continued by hand.
TERM_SHARE = 0.5
TERM_INDEX = 100


def ordinal(number):
    if 10 <= number % 100 <= 20:
        return "{}th".format(number)
    return "{}{}".format(number, {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th"))


def term_at(coefficients, n):
    a, b, c = map(Fraction, coefficients)
    return a * n * n + b * n + c


def answer_content(coefficients, term_index=None):
    """The nth-term expression, plus the requested term when one is asked for."""
    text = expression(coefficients)
    tex = expression(coefficients, True)
    if term_index:
        value = term_at(coefficients, term_index)
        text += "; {} term = {}".format(ordinal(term_index), rational_text(value))
        tex += r",\quad u_{%d} = %s" % (term_index, rational_tex(value))
    return Content(text, tex)


def make_prompt(values, quadratic, term_index=None):
    sequence_type = "a quadratic" if quadratic else "an arithmetic"
    instruction = (
        "The first five terms of {} sequence are shown. "
        "The first term corresponds to n = 1. Find an expression for the nth term."
    ).format(sequence_type)
    if term_index:
        instruction += " Use it to find the {} term.".format(ordinal(term_index))
    return Content(
        instruction + " " + ", ".join(rational_text(value) for value in values) + ", ...",
        r",\quad ".join(rational_tex(value) for value in values) + r",\quad\ldots",
        display_text=instruction,
    )


class NthTerm:
    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        if self.quadratic:
            from . import quadratic_sequence_contexts as contexts
        else:
            from . import sequence_contexts as contexts
        if rng.random() < contexts.CONTEXT_SHARE.get(difficulty, 0.0):
            return contexts.generate(self, context)
        nonzero = [value for value in range(-9, 10) if value]
        if not self.quadratic:
            a = Fraction(0)
            if difficulty == 1:
                b, c = Fraction(rng.randint(2, 9)), Fraction(0)
            elif difficulty == 2:
                b, c = Fraction(rng.randint(2, 9)), Fraction(rng.choice(nonzero))
            elif difficulty == 3:
                b, c = Fraction(-rng.randint(2, 9)), Fraction(rng.randint(10, 35))
            else:
                b = Fraction(rng.choice((1, 3, 5, 7, -1, -3, -5)), 2)
                c = Fraction(rng.choice(nonzero))
        else:
            if difficulty == 1:
                a, b, c = Fraction(1), Fraction(0), Fraction(rng.choice(nonzero))
            elif difficulty == 2:
                a, b, c = Fraction(1), Fraction(rng.choice(nonzero)), Fraction(rng.choice(nonzero))
            elif difficulty == 3:
                a, b, c = Fraction(rng.randint(2, 5)), Fraction(rng.choice(nonzero)), Fraction(rng.choice(nonzero))
            else:
                a, b, c = Fraction(-rng.randint(1, 4)), Fraction(rng.choice(nonzero)), Fraction(rng.choice(nonzero))
        coefficients = [rational_text(value) for value in (a, b, c)]
        values = sequence_values(coefficients)
        answer = {"kind": "polynomial", "variable": "n", "coefficients_descending": coefficients}
        parameters = {"terms": [rational_text(value) for value in values], "first_index": 1}
        term_index = None
        # Short-circuit keeps quadratic random streams unchanged.
        if not self.quadratic and rng.random() < TERM_SHARE:
            term_index = TERM_INDEX
            parameters["term_index"] = term_index
            answer["term"] = rational_text(term_at(coefficients, term_index))
        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=make_prompt(values, self.quadratic, term_index),
            answer=answer,
            answer_display=answer_content(coefficients, term_index),
            worked_solution=(),
            marks=3 if (self.quadratic or term_index) else 2,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=7 if self.quadratic else 4),
            parameters=parameters,
        )
        self.validate(question)
        return question

    def validate(self, question):
        from .worded import is_worded
        if is_worded(question):
            if self.quadratic:
                from .quadratic_sequence_contexts import validate
            else:
                from .sequence_contexts import validate
            return validate(self, question)
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in (1, 2, 3, 4), "Invalid difficulty")
        require(question.parameters["first_index"] == 1, "Incorrect starting index")
        terms = list(map(Fraction, question.parameters["terms"]))
        term_index = question.parameters.get("term_index")
        require(term_index is None or (not self.quadratic and term_index == TERM_INDEX),
                "Unexpected term request")
        expected_parameters = {"terms", "first_index"}
        expected_answer = {"kind", "variable", "coefficients_descending"}
        if term_index:
            expected_parameters.add("term_index")
            expected_answer.add("term")
        require(set(question.parameters) == expected_parameters, "Unexpected parameters")
        require(isinstance(question.answer, dict)
                and set(question.answer) == expected_answer, "Incorrect answer shape")
        coefficients = question.answer["coefficients_descending"]
        require(len(terms) == 5 and len(coefficients) == 3, "Incorrect sequence or coefficient count")
        require(question.answer["kind"] == "polynomial" and question.answer["variable"] == "n",
                "Incorrect answer type")
        a, b, c = map(Fraction, coefficients)
        require(coefficients == [rational_text(value) for value in (a, b, c)], "Non-canonical coefficients")
        require(sequence_values(coefficients) == terms, "Formula does not reproduce the sequence")
        require(max(map(abs, terms)) <= 200, "Terms outside intended bounds")
        differences = [right - left for left, right in zip(terms, terms[1:])]
        if self.quadratic:
            require(a != 0 and c != 0, "Unexpected quadratic structure")
            second = [right - left for left, right in zip(differences, differences[1:])]
            require(len(set(second)) == 1 and second[0] != 0, "Not a quadratic sequence")
            require(all(value.denominator == 1 for value in (a, b, c)), "Expected integer coefficients")
            if level == 1:
                require(a == 1 and b == 0, "Expected shifted square numbers")
            elif level == 2:
                require(a == 1 and b != 0, "Expected monic quadratic with linear term")
            elif level == 3:
                require(2 <= a <= 5 and b != 0, "Expected non-unit quadratic coefficient")
            else:
                require(-4 <= a <= -1 and b != 0, "Expected negative second difference")
        else:
            require(a == 0 and b != 0 and len(set(differences)) == 1, "Not arithmetic")
            if level == 1:
                require(b.denominator == 1 and b > 0 and c == 0, "Expected multiples")
            elif level == 2:
                require(b.denominator == 1 and b > 0 and c != 0, "Expected offset sequence")
            elif level == 3:
                require(b.denominator == 1 and b < 0 and c > 0, "Expected decreasing sequence")
            else:
                require(b.denominator == 2 and c.denominator == 1, "Expected fractional difference")
        if term_index:
            require(question.answer["term"] == rational_text(term_at(coefficients, term_index)),
                    "Incorrect requested term")
        require(question.prompt == make_prompt(terms, self.quadratic, term_index),
                "Prompt mismatch")
        require(question.answer_display == answer_content(coefficients, term_index),
                "Answer display mismatch")
        return True

    def validate_independently(self, question):
        """Recover the rule from displayed terms or solve the worded situation."""
        from .worded import is_worded
        if is_worded(question):
            if self.quadratic:
                from .quadratic_sequence_contexts import validate_independently
            else:
                from .sequence_contexts import validate_independently
            return validate_independently(question)
        import sympy

        terms = [sympy.Rational(value) for value in question.parameters["terms"]]
        first_difference = terms[1] - terms[0]
        second_difference = terms[2] - 2 * terms[1] + terms[0]
        a = second_difference / 2
        b = first_difference - 3 * a
        c = terms[0] - a - b
        recovered = [a, b, c]
        submitted = [sympy.Rational(value) for value in question.answer["coefficients_descending"]]
        require(recovered == submitted, "Independent finite-difference formula disagrees")
        require(all(a * n ** 2 + b * n + c == value
                    for n, value in enumerate(terms, 1)), "Remaining terms disagree")
        term_index = question.parameters.get("term_index")
        if term_index:
            # Count on from the first term in steps of the common difference.
            counted = terms[0] + (term_index - 1) * first_difference
            require(counted == sympy.Rational(question.answer["term"]),
                    "Independent requested term disagrees")
        return True


class LinearNthTerm(NthTerm):
    quadratic = False
    info = GeneratorInfo(
        id="algebra.sequences.linear_nth", version=4, topic="algebra",
        subtopic="sequences", title="Find the nth term of an arithmetic sequence",
        difficulty_descriptions={
            1: "Multiples with a zero constant term.",
            2: "Increasing sequences with a positive or negative offset.",
            3: "Decreasing sequences.",
            4: "Sequences with a fractional common difference.",
        },
        tags=("sequences", "nth_term", "linear"),
    )


class QuadraticNthTerm(NthTerm):
    quadratic = True
    info = GeneratorInfo(
        id="algebra.sequences.quadratic_nth", version=2, topic="algebra",
        subtopic="sequences", title="Find the nth term of a quadratic sequence",
        difficulty_descriptions={
            1: "Square numbers shifted by a constant.",
            2: "A monic quadratic with a nonzero linear term.",
            3: "A non-unit positive quadratic coefficient.",
            4: "Negative second differences.",
        },
        tags=("sequences", "nth_term", "quadratic"),
    )