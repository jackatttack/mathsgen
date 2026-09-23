"""Rearrange a formula for its subject, including collecting and factorising.

Every formula is linear in the subject, so each side is a list of terms and
each term is an integer multiplied by zero or more letters, optionally
multiplied by the subject. One renderer therefore serves the equation, the
numerator and the denominator, and the rearrangement is exact integer work.
Fractional and square/root forms are provided by subject_extended.py.
The PDF backend supports their fraction bars and square-root notation.
"""
from .core import Content, GeneratorInfo, LayoutHint, Question, make_context, require


INFO = GeneratorInfo(
    id="algebra.rearranging.changing_subject",
    version=3,
    topic="algebra",
    subtopic="changing_subject",
    title="Change the subject of a formula",
    difficulty_descriptions={
        1: "Undo a multiplication and an addition; or rearrange and use a taxi-fare formula.",
        2: "The subject's coefficient is negative; or rearrange and use a candle formula.",
        3: "Letter-coefficient and fractional formulas; or temperature and motion formulas.",
        4: "Factorise the subject, or squares and roots; or energy and falling formulas.",
    },
    tags=("algebra", "rearranging", "changing_subject", "factorising"),
)

SUBJECT = "x"
# Letters avoid x itself, and avoid e, i, l and o, which read poorly or
# invite confusion with familiar constants and digits. y is excluded too:
# beside the subject it reads as a product, so 3yx looks like a two-letter
# term rather than a coefficient multiplying x.
LETTERS = ("a", "b", "c", "d", "g", "h", "k", "m", "n", "p", "q", "r", "s",
           "t", "u", "v", "w", "z")


def make_term(number, letters=(), subject=False):
    return {"number": number, "letters": list(letters), "subject": subject}


def term_body(term):
    """One term without its sign, omitting a redundant coefficient of one."""
    symbol = "".join(term["letters"]) + (SUBJECT if term["subject"] else "")
    magnitude = abs(term["number"])
    if not symbol:
        return str(magnitude)
    return ("" if magnitude == 1 else str(magnitude)) + symbol


def side_text(terms):
    """A sum of terms, written with proper joining signs."""
    pieces = []
    for term in terms:
        body = term_body(term)
        if pieces:
            pieces.append((" - " if term["number"] < 0 else " + ") + body)
        else:
            pieces.append(("-" if term["number"] < 0 else "") + body)
    return "".join(pieces) or "0"


def negate(terms):
    return [dict(term, number=-term["number"]) for term in terms]


def drop_subject(terms):
    return [dict(term, subject=False) for term in terms]


def combine(terms):
    """Merge terms with identical letters, so 12 - 5 becomes 7."""
    merged = []
    for term in terms:
        key = (tuple(term["letters"]), term["subject"])
        for existing in merged:
            if (tuple(existing["letters"]), existing["subject"]) == key:
                existing["number"] += term["number"]
                break
        else:
            merged.append(dict(term, letters=list(term["letters"])))
    return [term for term in merged if term["number"] != 0]


def positive_first(terms):
    """Show a positive term first, so an answer reads y - 7 rather than -7 + y."""
    return sorted(terms, key=lambda term: term["number"] < 0)


def rearranged(left, right):
    """Collect the subject on one side and return (numerator, denominator)."""
    subject_side = combine(
        drop_subject([term for term in left if term["subject"]])
        + negate(drop_subject([term for term in right if term["subject"]]))
    )
    constant_side = combine(
        [term for term in right if not term["subject"]]
        + negate([term for term in left if not term["subject"]])
    )
    if subject_side and subject_side[0]["number"] < 0:
        subject_side, constant_side = negate(subject_side), negate(constant_side)
    return positive_first(constant_side), positive_first(subject_side)


def is_one(terms):
    return len(terms) == 1 and terms[0]["number"] == 1 and not terms[0]["letters"]


def needs_brackets(terms):
    """Plain text needs brackets wherever division would otherwise be ambiguous.

    A denominator such as 4s must be bracketed, because (y - 2)/4s could
    otherwise be read as ((y - 2)/4) multiplied by s. TeX needs none of this,
    since the fraction bar already groups the terms.
    """
    if len(terms) > 1:
        return True
    term = terms[0]
    return bool(term["letters"]) and abs(term["number"]) != 1


def answer_text(numerator, denominator, tex=False):
    top, bottom = side_text(numerator), side_text(denominator)
    if is_one(denominator):
        return SUBJECT + " = " + top
    if tex:
        return SUBJECT + " = " + r"\frac{" + top + "}{" + bottom + "}"
    if needs_brackets(numerator):
        top = "(" + top + ")"
    if needs_brackets(denominator):
        bottom = "(" + bottom + ")"
    return SUBJECT + " = " + top + "/" + bottom


def make_prompt(left, right):
    instruction = "Make {} the subject of the formula.".format(SUBJECT)
    _, denominator = rearranged(left, right)
    if any(term["letters"] for term in denominator):
        instruction += " Assume ({}) is nonzero.".format(side_text(denominator))
    equation = side_text(left) + " = " + side_text(right)
    return Content(instruction + " " + equation, equation, display_text=instruction)


class ChangingSubject:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        from . import subject_contexts as worded_forms
        if rng.random() < worded_forms.CONTEXT_SHARE.get(difficulty, 0.0):
            return worded_forms.generate(self, context)
        if difficulty >= 3 and rng.choice((False, True)):
            from .subject_extended import generate
            return generate(self, context)
        constants = [value for value in range(-12, 13) if value != 0]

        if difficulty == 1:
            subject_letter = rng.choice(LETTERS)
            left = [make_term(1, [subject_letter])]
            right = [
                make_term(rng.randint(2, 9), [], True),
                make_term(rng.choice(constants)),
            ]
        elif difficulty == 2:
            first, second = rng.sample(LETTERS, 2)
            left = [make_term(1, [first])]
            right = [
                make_term(rng.randint(2, 12), [second]),
                make_term(-rng.randint(2, 9), [], True),
            ]
        elif difficulty == 3:
            first, second, third = rng.sample(LETTERS, 3)
            left = [make_term(1, [first])]
            right = [
                make_term(rng.choice((1, 1, 2, 3, 4)), [second], True),
                make_term(rng.choice(constants[:12] + constants[12:]), [third]),
            ]
        else:
            first, second = rng.sample(LETTERS, 2)
            if rng.choice((False, True)):
                # Integer constants leave a purely numerical numerator.
                values = rng.sample([value for value in range(1, 13)], 2)
                left_constant = make_term(values[0])
                right_constant = make_term(values[1])
            else:
                third, fourth = rng.sample(
                    [letter for letter in LETTERS if letter not in (first, second)], 2
                )
                left_constant = make_term(1, [third])
                right_constant = make_term(1, [fourth])
            left = [make_term(1, [first], True), left_constant]
            right = [make_term(1, [second], True), right_constant]

        numerator, denominator = rearranged(left, right)
        require(numerator and denominator, "Rearrangement collapsed")

        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=make_prompt(left, right),
            answer={
                "kind": "subject_formula",
                "subject": SUBJECT,
                "numerator": numerator,
                "denominator": denominator,
            },
            answer_display=Content(
                answer_text(numerator, denominator),
                answer_text(numerator, denominator, True),
            ),
            worked_solution=(),
            marks=2 if difficulty <= 2 else (3 if difficulty == 3 else 4),
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=5 if difficulty <= 2 else 7),
            parameters={"left": left, "right": right},
        )
        self.validate(question)
        return question

    def validate(self, question):
        from .worded import is_worded
        if is_worded(question):
            from .subject_contexts import validate as validate_worded
            return validate_worded(self, question)
        try:
            return self.validate_bare(question)
        except (KeyError, TypeError, IndexError) as error:
            raise ValueError("Malformed question: {!r}".format(error))

    def validate_bare(self, question):
        if "form" in question.parameters:
            from .subject_extended import validate
            return validate(self, question)
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in (1, 2, 3, 4), "Invalid difficulty")
        left = question.parameters["left"]
        right = question.parameters["right"]
        for term in left + right:
            require(type(term["number"]) is int and term["number"] != 0,
                    "Expected a nonzero integer coefficient")
            require(abs(term["number"]) <= 12, "Coefficient outside bounds")
            require(all(letter in LETTERS for letter in term["letters"]),
                    "Unexpected letter")
            require(type(term["subject"]) is bool, "Malformed subject flag")

        subject_terms = [term for term in left + right if term["subject"]]
        require(len(subject_terms) == (2 if level == 4 else 1),
                "Unexpected number of subject terms")
        if level == 4:
            require(all(len(term["letters"]) == 1 for term in subject_terms),
                    "Expected letter coefficients on both subject terms")
            require(subject_terms[0]["letters"] != subject_terms[1]["letters"],
                    "Factorising requires different coefficients")
        elif level == 3:
            require(len(subject_terms[0]["letters"]) == 1,
                    "Expected a letter coefficient")
        else:
            require(not subject_terms[0]["letters"], "Unexpected letter coefficient")
            require((subject_terms[0]["number"] < 0) == (level == 2),
                    "Incorrect sign structure")

        numerator, denominator = rearranged(left, right)
        require(numerator and denominator, "Rearrangement collapsed")
        require(denominator[0]["number"] > 0, "Expected a positive leading denominator")
        require(any(term["letters"] for term in numerator + denominator),
                "A purely numerical answer needs no rearrangement")
        if level == 4:
            require(len(denominator) == 2, "Expected a factorised denominator")
        else:
            require(len(denominator) == 1, "Expected a single denominator term")

        require(question.answer["subject"] == SUBJECT, "Unexpected subject")
        require(question.answer["numerator"] == numerator, "Incorrect numerator")
        require(question.answer["denominator"] == denominator, "Incorrect denominator")
        require(question.prompt == make_prompt(left, right), "Prompt mismatch")
        require(question.answer_display == Content(
            answer_text(numerator, denominator),
            answer_text(numerator, denominator, True),
        ), "Displayed answer mismatch")
        return True

    def validate_independently(self, question):
        """Substitute the answer back into the emitted formula.

        This never consults the rearrangement logic: it puts the submitted
        expression where the subject stood and checks both sides agree.
        Clearing the denominator keeps the work polynomial, so expand alone
        settles it. Symbolic solving would also work but costs roughly
        twenty times as much per check.
        """
        from .worded import is_worded
        if is_worded(question):
            from .subject_contexts import validate_independently as independent_worded
            return independent_worded(question)
        if "form" in question.parameters:
            from .subject_extended import validate_independently
            return validate_independently(question)
        import sympy

        subject = sympy.Symbol(question.answer["subject"])

        def expression(terms):
            total = sympy.Integer(0)
            for term in terms:
                value = sympy.Integer(term["number"])
                for letter in term["letters"]:
                    value *= sympy.Symbol(letter)
                if term["subject"]:
                    value *= subject
                total += value
            return total

        numerator = expression(question.answer["numerator"])
        denominator = expression(question.answer["denominator"])
        require(not denominator.is_zero, "Independent denominator vanishes")

        # The subject can appear on both sides, so the substituted expression
        # may hold several copies of the fraction. Combining over a common
        # denominator and cancelling settles it however many there are.
        difference = (expression(question.parameters["left"])
                      - expression(question.parameters["right"]))
        substituted = difference.subs(subject, numerator / denominator)
        require(sympy.cancel(sympy.together(substituted)) == 0,
                "Independent substitution disagrees")
        require(sympy.cancel(difference.subs(subject, numerator + denominator)) != 0,
                "Formula is satisfied by any value, so the answer is untested")
        return True