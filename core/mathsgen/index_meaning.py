"""Misconception-based multiple choice for interpreting exponents."""
from fractions import Fraction
from functools import lru_cache

from .core import (
    Choice, Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)


INFO = GeneratorInfo(
    id="number.indices.meaning_mcq",
    version=2,
    topic="number",
    subtopic="indices",
    title="What does this power mean? (multiple choice)",
    difficulty_descriptions={
        1: "Interpret reciprocal integer powers as roots.",
        2: "Interpret positive fractional powers as roots and powers.",
        3: "Interpret negative integer powers as reciprocals.",
        4: "Combine negative and fractional powers.",
    },
    tags=("indices", "understanding", "multiple_choice", "misconceptions"),
)


def option_content(variable, kind, value):
    value = Fraction(value)
    if kind in ("power", "negative_power"):
        exponent = value
        numerator = abs(exponent.numerator)
        denominator = exponent.denominator
        inside_text = variable if numerator == 1 else variable + "^" + str(numerator)
        inside_tex = variable if numerator == 1 else variable + "^{" + str(numerator) + "}"
        if denominator > 1:
            text = "sqrt(" + inside_text + ")" if denominator == 2 else "root_{}({})".format(denominator, inside_text)
            tex = r"\sqrt{" + inside_tex + "}" if denominator == 2 else r"\sqrt[" + str(denominator) + "]{" + inside_tex + "}"
        else:
            text, tex = inside_text, inside_tex
        if exponent < 0:
            text, tex = "1/(" + text + ")", r"\frac{1}{" + tex + "}"
        if kind == "negative_power":
            text, tex = "-(" + text + ")", r"-\left(" + tex + r"\right)"
        return Content(text, tex)
    if kind == "scale":
        if value.numerator == 1:
            return Content(
                variable + "/" + str(value.denominator),
                r"\frac{" + variable + "}{" + str(value.denominator) + "}",
            )
        return Content(
            "(" + rational_text(value) + ")" + variable,
            rational_tex(value) + variable,
        )
    if kind == "constant":
        return Content(rational_text(value), rational_tex(value))
    raise ValueError("Unknown option type")


def candidate_descriptors(exponent, level):
    m, n = abs(exponent.numerator), exponent.denominator
    if level == 1:
        return [
            ("power", exponent), ("scale", Fraction(1, n)),
            ("scale", Fraction(n)), ("power", Fraction(n)),
            ("constant", Fraction(n)),
        ]
    if level == 2:
        return [
            ("power", exponent), ("power", 1 / exponent),
            ("scale", exponent), ("power", Fraction(m * n)),
            ("constant", exponent),
        ]
    if level == 3:
        return [
            ("power", exponent), ("negative_power", -exponent),
            ("scale", exponent), ("power", -exponent),
            ("constant", exponent),
        ]
    return [
        ("power", exponent), ("power", -exponent),
        ("negative_power", -exponent), ("power", 1 / exponent),
        ("scale", exponent),
    ]


@lru_cache(maxsize=256)
def equivalent_options(exponent_text, descriptors):
    """Symbolically classify each option on the stated domain x > 0.

    Cache only mathematical comparisons; every question still checks its
    actual displayed choices and answer mapping.
    """
    import sympy

    x = sympy.Symbol("x", positive=True)
    target = x ** sympy.Rational(exponent_text)
    matches = []
    for kind, text in descriptors:
        value = sympy.Rational(text)
        if kind == "power":
            expression = x ** value
        elif kind == "negative_power":
            expression = -(x ** value)
        elif kind == "scale":
            expression = value * x
        elif kind == "constant":
            expression = value
        else:
            raise ValueError("Unknown option type")
        matches.append(sympy.simplify(expression - target) == 0)
    return tuple(matches)


class IndexMeaning:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        variable = rng.choice(("x", "y", "a", "b", "t"))
        if difficulty == 1:
            exponent = Fraction(1, rng.choice((2, 3, 4, 5)))
        elif difficulty == 2:
            exponent = rng.choice((Fraction(2, 3), Fraction(3, 2), Fraction(3, 4), Fraction(2, 5)))
        elif difficulty == 3:
            exponent = Fraction(-rng.randint(2, 5))
        else:
            exponent = rng.choice((Fraction(-1, 2), Fraction(-1, 3), Fraction(-2, 3), Fraction(-3, 2)))
        candidates = [
            {"kind": kind, "value": rational_text(value), "correct": index == 0}
            for index, (kind, value) in enumerate(candidate_descriptors(exponent, difficulty))
        ]
        rng.shuffle(candidates)
        choices = tuple(
            Choice("option_" + str(index), option_content(variable, item["kind"], item["value"]))
            for index, item in enumerate(candidates)
        )
        correct_index = next(index for index, item in enumerate(candidates) if item["correct"])
        letter = chr(65 + correct_index)
        correct = choices[correct_index]
        instruction = "For {} > 0, which expression is equivalent to this? Choose one answer.".format(variable)
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
                instruction + " " + variable + "^(" + rational_text(exponent) + ")",
                variable + "^{" + rational_tex(exponent) + "}",
                display_text=instruction,
            ),
            answer={"kind": "choice", "choice_id": correct.id},
            answer_display=Content(
                letter + ": " + correct.content.text,
                r"\mathrm{" + letter + r"}:\quad " + correct.content.math_tex,
            ),
            worked_solution=(),
            marks=1,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=1),
            parameters={
                "variable": variable, "exponent": rational_text(exponent),
                "options": [{"kind": item["kind"], "value": item["value"]} for item in candidates],
            },
            choices=choices,
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in (1, 2, 3, 4), "Invalid difficulty")
        parameters = question.parameters
        variable = parameters["variable"]
        exponent = Fraction(parameters["exponent"])
        require(variable in ("x", "y", "a", "b", "t"), "Invalid variable")
        if level == 1:
            require(exponent.numerator == 1 and 2 <= exponent.denominator <= 5, "Expected root")
        elif level == 2:
            require(exponent in (Fraction(2, 3), Fraction(3, 2), Fraction(3, 4), Fraction(2, 5)), "Invalid fractional power")
        elif level == 3:
            require(exponent.denominator == 1 and -5 <= exponent <= -2, "Expected negative integer")
        else:
            require(exponent in (Fraction(-1, 2), Fraction(-1, 3), Fraction(-2, 3), Fraction(-3, 2)), "Invalid negative fraction")
        descriptors = parameters["options"]
        require(len(descriptors) == len(question.choices) == 5, "Expected five options")
        expected = sorted((kind, rational_text(value)) for kind, value in candidate_descriptors(exponent, level))
        actual = [(item["kind"], item["value"]) for item in descriptors]
        require(sorted(actual) == expected, "Unexpected option bank")
        for index, (choice, item) in enumerate(zip(question.choices, descriptors)):
            require(choice.id == "option_" + str(index), "Invalid option identifier")
            require(choice.content == option_content(variable, item["kind"], item["value"]), "Displayed option mismatch")
        require(len({choice.content.math_tex for choice in question.choices}) == 5, "Duplicate options")
        matches = equivalent_options(rational_text(exponent), tuple(actual))
        require(sum(matches) == 1, "Question must have exactly one correct option")
        correct_index = matches.index(True)
        correct = question.choices[correct_index]
        letter = chr(65 + correct_index)
        require(question.answer == {"kind": "choice", "choice_id": correct.id}, "Incorrect choice key")
        require(question.answer_display == Content(
            letter + ": " + correct.content.text,
            r"\mathrm{" + letter + r"}:\quad " + correct.content.math_tex,
        ), "Answer display mismatch")
        instruction = "For {} > 0, which expression is equivalent to this? Choose one answer.".format(variable)
        require(question.prompt == Content(
            instruction + " " + variable + "^(" + rational_text(exponent) + ")",
            variable + "^{" + rational_tex(exponent) + "}", display_text=instruction,
        ), "Prompt mismatch")
        return True

    def validate_independently(self, question):
        descriptors = tuple(
            (item["kind"], item["value"]) for item in question.parameters["options"]
        )
        matches = equivalent_options(question.parameters["exponent"], descriptors)
        require(sum(matches) == 1, "Ambiguous symbolic options")
        require(question.choices[matches.index(True)].id == question.answer["choice_id"],
                "Symbolic answer disagrees")
        return True