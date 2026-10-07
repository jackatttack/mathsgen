"""Recover x from three algebraic consecutive sequence terms.

Arithmetic questions use equal differences. Geometric questions deliberately
give a genuine quadratic with two distinct, valid rational solutions.
All displayed terms are linear expressions; no float root calculation is used.
"""
from fractions import Fraction
from math import isqrt

from . import rich_blocks as rb
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)
from .linear_two_sided import linear_expression


def solve_parameters(parameters, kind):
    a, b, c = parameters["coefficients"]
    d, e, f = parameters["constants"]
    if kind == "arithmetic":
        coefficient = 2 * b - a - c
        require(coefficient != 0, "Equal differences must determine x")
        return [Fraction(d + f - 2 * e, coefficient)]
    # Middle squared equals first times third.
    A = b * b - a * c
    B = 2 * b * e - a * f - c * d
    C = e * e - d * f
    require(A != 0, "Geometric equation must be genuinely quadratic")
    discriminant = B * B - 4 * A * C
    require(discriminant > 0, "Require two distinct real solutions")
    root = isqrt(discriminant)
    require(root * root == discriminant, "Require exact rational solutions")
    return sorted({Fraction(-B - root, 2 * A), Fraction(-B + root, 2 * A)})


def check_parameters(parameters, kind, level):
    require(isinstance(parameters, dict)
            and set(parameters) == {"coefficients", "constants"},
            "Unexpected parameters")
    coefficients, constants = parameters["coefficients"], parameters["constants"]
    require(isinstance(coefficients, list) and isinstance(constants, list)
            and len(coefficients) == len(constants) == 3, "Three expressions required")
    require(all(type(value) is int for value in coefficients + constants),
            "Integer coefficients required")
    require(all(1 <= value <= 5 for value in coefficients), "Coefficient bounds")
    require(all(-8 <= value <= 8 for value in constants), "Constant bounds")
    require(len(set(zip(coefficients, constants))) == 3, "Distinct expressions required")
    solutions = solve_parameters(parameters, kind)
    require(all(0 < abs(value) <= 12 and value.denominator <= 6 for value in solutions),
            "Solution outside teaching bounds")
    if kind == "arithmetic":
        require(level == 3, "Arithmetic algebraic terms belong to source level 3")
    else:
        require(level == 4 and len(solutions) == 2, "Expected two geometric solutions")
    for value in solutions:
        terms = [coefficient * value + constant
                 for coefficient, constant in zip(coefficients, constants)]
        if kind == "arithmetic":
            require(terms[1] != terms[0], "Avoid constant arithmetic sequences")
        else:
            require(all(terms), "All three geometric terms must be nonzero")
            ratio = terms[1] / terms[0]
            require(ratio not in (-1, 1), "Avoid trivial repeating sequences")
    return solutions


def prompt_for(parameters, kind):
    plain = [linear_expression(a, b)
             for a, b in zip(parameters["coefficients"], parameters["constants"])]
    tex = [linear_expression(a, b, True)
           for a, b in zip(parameters["coefficients"], parameters["constants"])]
    name = "an arithmetic" if kind == "arithmetic" else "a geometric"
    instruction = (
        "These are three consecutive terms of {} sequence, in the order shown. "
        "{}"
    ).format(name, "Find x." if kind == "arithmetic" else "Find all possible values of x.")
    return Content(instruction + " " + ", ".join(plain), blocks=(
        rb.prose(instruction), rb.equation(r",\quad ".join(tex), ", ".join(plain)),
    ))


def answer_for(solutions):
    answer = {"kind": "solution_set", "variable": "x",
              "values": [rational_text(value) for value in solutions]}
    text = "x = " + " or x = ".join(rational_text(value) for value in solutions)
    tex = "x = " + r"\quad\mathrm{or}\quad x = ".join(
        rational_tex(value) for value in solutions)
    return answer, Content(text, tex)


class AlgebraicSequenceTerms:
    """A dispatch source for the harder arithmetic or geometric topic."""

    def __init__(self, kind):
        require(kind in ("arithmetic", "geometric"), "Unknown sequence type")
        self.kind = kind
        level = 3 if kind == "arithmetic" else 4
        self.info = GeneratorInfo(
            id="algebra.sequences.{}_algebraic_terms".format(kind),
            version=1, topic="algebra", subtopic="sequences",
            title="Algebraic terms of {} sequences".format(kind),
            difficulty_descriptions={level: "Find x from three consecutive algebraic terms."},
            tags=("sequences", kind, "algebraic_terms"),
        )

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This source accepts no settings")
        for _ in range(4000):
            parameters = {
                "coefficients": [context.rng.randint(1, 5) for _ in range(3)],
                "constants": [context.rng.randint(-8, 8) for _ in range(3)],
            }
            try:
                solutions = check_parameters(parameters, self.kind, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct suitable algebraic sequence terms")
        answer, display = answer_for(solutions)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(parameters, self.kind),
            answer=answer, answer_display=display, worked_solution=(),
            marks=3 if self.kind == "arithmetic" else 5,
            tags=self.info.tags, layout_hint=LayoutHint(
                working_lines=6 if self.kind == "arithmetic" else 9),
            parameters=parameters,
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id
                and question.generator_version == self.info.version, "Generator mismatch")
        require(type(question.difficulty) is int
                and question.difficulty in self.info.difficulty_descriptions,
                "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")
        solutions = check_parameters(question.parameters, self.kind, question.difficulty)
        answer, display = answer_for(solutions)
        require(question.answer == answer, "Incorrect solution set")
        require(question.answer_display == display, "Answer display mismatch")
        require(question.prompt == prompt_for(question.parameters, self.kind), "Prompt mismatch")
        return True

    def validate_independently(self, question):
        import sympy
        x = sympy.Symbol("x")
        p = question.parameters
        first, middle, last = [
            a * x + b for a, b in zip(p["coefficients"], p["constants"])]
        equation = (middle - first - (last - middle) if self.kind == "arithmetic"
                    else middle ** 2 - first * last)
        solved = sympy.solve(equation, x)
        expected = [sympy.Rational(value) for value in question.answer["values"]]
        require(set(solved) == set(expected), "Independent solution set disagrees")
        for value in solved:
            terms = [term.subs(x, value) for term in (first, middle, last)]
            if self.kind == "arithmetic":
                require(terms[1] - terms[0] == terms[2] - terms[1], "Differences disagree")
            else:
                require(all(term != 0 for term in terms), "Undefined geometric ratio")
                require(terms[1] / terms[0] == terms[2] / terms[1], "Ratios disagree")
        return True