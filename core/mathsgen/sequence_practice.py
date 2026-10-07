"""Focused sequence practice and three separately selectable teaching families.

Practice sources keep each drill section on one task. Existing generators
supply additional standard questions and applications without being rewritten.
All sequences start at n = 1 and all arithmetic is exact.
"""
from fractions import Fraction

from . import rich_blocks as rb
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)
from .dispatch import DispatchFamily
from .nth_term import LinearNthTerm, QuadraticNthTerm, expression
from .geometric_sequences import GeometricSequences


DESCRIPTIONS = {
    "arithmetic": {
        1: "Increasing sequences with positive whole-number differences and nonnegative offsets.",
        2: "Increasing sequences with negative offsets.",
        3: "Decreasing sequences.",
        4: "Fractional common differences.",
    },
    "quadratic": {
        1: "Square numbers shifted by a constant.",
        2: "Monic quadratic rules with a linear term.",
        3: "Non-unit positive quadratic coefficients.",
        4: "Negative second differences.",
    },
    "geometric": {
        1: "Whole-number common ratios; continue sequences and find ratios.",
        2: "Fractional common ratios; nth-term rules and term calculations.",
        3: "Negative common ratios; missing first terms and surd sequences.",
        4: "Fractional first terms and ratios; algebraic and threshold problems.",
    },
}
FRACTIONAL_RATIOS = (Fraction(1, 2), Fraction(1, 3), Fraction(2, 3), Fraction(3, 2))
NEGATIVE_RATIOS = tuple(map(Fraction, (-2, -3, -4)))
HARD_RATIOS = (Fraction(-1, 2), Fraction(-2, 3), Fraction(1, 2), Fraction(3, 2))


def values_for(kind, parameters):
    if kind == "geometric":
        first, ratio = Fraction(parameters["first"]), Fraction(parameters["ratio"])
        return [first * ratio ** n for n in range(5)]
    a, b, c = map(Fraction, parameters["coefficients"])
    return [a * n * n + b * n + c for n in range(1, 6)]


def rule_for(kind, parameters, tex=False):
    if kind != "geometric":
        return expression(parameters["coefficients"], tex)
    first, ratio = Fraction(parameters["first"]), Fraction(parameters["ratio"])
    formatter = rational_tex if tex else rational_text
    base = formatter(ratio)
    if ratio < 0 or ratio.denominator != 1:
        base = (r"\left(" + base + r"\right)") if tex else "(" + base + ")"
    power = base + ("^{n-1}" if tex else "^(n-1)")
    if first == 1:
        return power
    return formatter(first) + (r" \times " if tex else " x ") + power


def presentation(kind, task, parameters):
    values = values_for(kind, parameters)
    listed = ", ".join(rational_text(value) for value in values)
    listed_tex = r",\quad ".join(rational_tex(value) for value in values)
    rule, rule_tex = rule_for(kind, parameters), rule_for(kind, parameters, True)
    if task == "terms":
        instruction = "Write the first five terms of each sequence. Start at n = 1."
        plain, tex = "u_n = " + rule, "u_n = " + rule_tex
        answer = {"kind": "terms", "values": [rational_text(value) for value in values]}
        display = Content(listed, listed_tex)
    else:
        instruction = "Find the nth term of each {} sequence. The first term is n = 1.".format(kind)
        plain, tex = listed + ", ...", listed_tex + r",\quad\ldots"
        if kind == "geometric":
            answer = {"kind": "geometric_nth", "first": parameters["first"],
                      "ratio": parameters["ratio"]}
        else:
            answer = {"kind": "polynomial", "variable": "n",
                      "coefficients_descending": list(parameters["coefficients"])}
        display = Content(rule, rule_tex)
    prompt = Content(instruction + " " + plain, blocks=(
        rb.prose(instruction), rb.equation(tex, plain),
    ))
    return prompt, answer, display


class SequencePractice:
    """One sequence type and task, with four structural difficulty levels."""

    def __init__(self, kind, task):
        self.kind, self.task = kind, task
        self.info = GeneratorInfo(
            id="algebra.sequences.practice_{}_{}".format(kind, task),
            version=1, topic="algebra", subtopic="sequences",
            title="{} sequences: {}".format(kind.title(), task),
            difficulty_descriptions=DESCRIPTIONS[kind],
            tags=("sequences", kind, "nth_term"),
        )

    def draw(self, rng, level):
        nonzero = [n for n in range(-12, 13) if n]
        if self.kind == "geometric":
            if level == 1:
                first, ratio = Fraction(rng.randint(1, 20)), Fraction(rng.randint(2, 5))
            elif level == 2:
                first, ratio = Fraction(rng.randint(1, 20)), rng.choice(FRACTIONAL_RATIOS)
            elif level == 3:
                first, ratio = Fraction(rng.choice(nonzero)), rng.choice(NEGATIVE_RATIOS)
            else:
                first = Fraction(rng.choice((-11, -9, -7, -5, -3, -1, 1, 3, 5, 7, 9, 11)), 2)
                ratio = rng.choice(HARD_RATIOS)
            return {"first": rational_text(first), "ratio": rational_text(ratio)}
        if self.kind == "arithmetic":
            a = 0
            if level == 1:
                b, c = rng.randint(1, 12), rng.randint(0, 20)
            elif level == 2:
                b, c = rng.randint(1, 12), -rng.randint(1, 20)
            elif level == 3:
                b, c = -rng.randint(1, 12), rng.randint(1, 40)
            else:
                b = Fraction(rng.choice((-9, -7, -5, -3, -1, 1, 3, 5, 7, 9)), 2)
                c = rng.randint(-15, 15)
        else:
            shifts = [n for n in range(-40, 41) if n] if level == 1 else nonzero
            c = rng.choice(shifts)
            a = 1 if level <= 2 else rng.randint(2, 5) if level == 3 else -rng.randint(1, 4)
            b = 0 if level == 1 else rng.choice(nonzero)
        return {"coefficients": [rational_text(value) for value in (a, b, c)]}

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "Sequence practice accepts no settings")
        parameters = self.draw(context.rng, difficulty)
        prompt, answer, display = presentation(self.kind, self.task, parameters)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=3 if self.kind == "quadratic" and self.task == "nth" else 2,
            tags=self.info.tags, layout_hint=LayoutHint(working_lines=5),
            parameters=parameters,
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level, p = question.difficulty, question.parameters
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")
        require(isinstance(p, dict), "Invalid parameters")
        if self.kind == "geometric":
            require(set(p) == {"first", "ratio"}, "Unexpected parameters")
            first, ratio = Fraction(p["first"]), Fraction(p["ratio"])
            require(p == {"first": rational_text(first), "ratio": rational_text(ratio)},
                    "Non-canonical parameters")
            if level == 1:
                valid = first.denominator == 1 and 1 <= first <= 20 and ratio in (2, 3, 4, 5)
            elif level == 2:
                valid = first.denominator == 1 and 1 <= first <= 20 and ratio in FRACTIONAL_RATIOS
            elif level == 3:
                valid = first.denominator == 1 and 1 <= abs(first) <= 12 and ratio in NEGATIVE_RATIOS
            else:
                valid = first.denominator == 2 and abs(first) <= Fraction(11, 2) and ratio in HARD_RATIOS
            require(valid, "Unexpected geometric structure")
        else:
            require(set(p) == {"coefficients"} and isinstance(p["coefficients"], list)
                    and len(p["coefficients"]) == 3, "Invalid coefficients")
            a, b, c = map(Fraction, p["coefficients"])
            require(p["coefficients"] == [rational_text(v) for v in (a, b, c)],
                    "Non-canonical coefficients")
            if self.kind == "arithmetic":
                require(a == 0 and c.denominator == 1, "Not an arithmetic rule")
                if level == 1:
                    valid = b.denominator == 1 and 1 <= b <= 12 and 0 <= c <= 20
                elif level == 2:
                    valid = b.denominator == 1 and 1 <= b <= 12 and -20 <= c <= -1
                elif level == 3:
                    valid = b.denominator == 1 and -12 <= b <= -1 and 1 <= c <= 40
                else:
                    valid = b.denominator == 2 and abs(b) <= Fraction(9, 2) and -15 <= c <= 15
                require(valid, "Unexpected arithmetic structure")
            else:
                require(all(v.denominator == 1 for v in (a, b, c))
                        and 1 <= abs(c) <= (40 if level == 1 else 12),
                        "Unexpected quadratic coefficients")
                require((a == 1 and b == 0) if level == 1 else
                        (1 <= abs(b) <= 12 and
                         (a == 1 if level == 2 else 2 <= a <= 5 if level == 3 else -4 <= a <= -1)),
                        "Unexpected quadratic structure")
        prompt, answer, display = presentation(self.kind, self.task, p)
        require(question.prompt == prompt, "Prompt mismatch")
        require(question.answer == answer, "Incorrect answer")
        require(question.answer_display == display, "Answer display mismatch")
        return True

    def validate_independently(self, question):
        """Check forward tasks by recurrence and inverse tasks by differences/ratios."""
        p, answer = question.parameters, question.answer
        if self.task == "terms":
            if self.kind == "geometric":
                current, ratio = Fraction(p["first"]), Fraction(p["ratio"])
                expected = []
                for _ in range(5):
                    expected.append(current)
                    current *= ratio
            else:
                a, b, c = map(Fraction, p["coefficients"])
                current, difference = a + b + c, 3 * a + b
                expected = []
                for _ in range(5):
                    expected.append(current)
                    current += difference
                    difference += 2 * a
            require(list(map(Fraction, answer["values"])) == expected, "Recurrence disagrees")
        else:
            shown = values_for(self.kind, p)
            if self.kind == "geometric":
                ratio = shown[1] / shown[0]
                require(all(right / left == ratio for left, right in zip(shown, shown[1:])),
                        "Inconsistent common ratio")
                require(Fraction(answer["first"]) == shown[0]
                        and Fraction(answer["ratio"]) == ratio, "Recovered rule disagrees")
            else:
                first_difference = shown[1] - shown[0]
                second_difference = shown[2] - 2 * shown[1] + shown[0]
                a = second_difference / 2
                b = first_difference - 3 * a
                c = shown[0] - a - b
                require(list(map(Fraction, answer["coefficients_descending"])) == [a, b, c],
                        "Finite differences disagree")
        return True


def sources_for(kind, existing):
    sources = {"terms": SequencePractice(kind, "terms"),
               "nth": SequencePractice(kind, "nth"), "applied": existing}
    if kind in ("arithmetic", "geometric"):
        from .algebraic_sequence_terms import AlgebraicSequenceTerms
        sources["algebraic"] = AlgebraicSequenceTerms(kind)
    return sources


def routes_for(names):
    return {level: tuple((name, level) for name in names) for level in (1, 2, 3, 4)}


class ArithmeticSequences(DispatchFamily):
    info = GeneratorInfo(
        id="algebra.sequences.linear_nth", version=6, topic="algebra",
        subtopic="sequences", title="Arithmetic sequences",
        difficulty_descriptions={
            **DESCRIPTIONS["arithmetic"],
            3: "Decreasing sequences; or find x from three consecutive algebraic terms.",
        },
        tags=("sequences", "arithmetic", "linear", "nth_term"),
    )
    sources = sources_for("arithmetic", LinearNthTerm())
    routes = routes_for(("terms", "nth", "applied"))
    routes[3] = routes[3] + (("algebraic", 3),)
    drill_routes = routes_for(("terms", "nth"))


class QuadraticSequences(DispatchFamily):
    info = GeneratorInfo(
        id="algebra.sequences.quadratic_nth", version=3, topic="algebra",
        subtopic="sequences", title="Quadratic sequences",
        difficulty_descriptions=DESCRIPTIONS["quadratic"],
        tags=("sequences", "quadratic", "nth_term"),
    )
    sources = sources_for("quadratic", QuadraticNthTerm())
    routes = routes_for(("terms", "nth", "applied"))
    drill_routes = routes_for(("terms", "nth"))


class GeometricSequenceFamily(DispatchFamily):
    info = GeneratorInfo(
        id="algebra.sequences.geometric", version=3, topic="algebra",
        subtopic="sequences", title="Geometric sequences",
        difficulty_descriptions={
            **DESCRIPTIONS["geometric"],
            4: "Fractional first terms and ratios; thresholds; or solve a quadratic from three algebraic terms.",
        },
        tags=("sequences", "geometric", "nth_term"),
    )
    sources = sources_for("geometric", GeometricSequences())
    routes = routes_for(("terms", "nth", "applied"))
    routes[4] = routes[4] + (("algebraic", 4),)
    drill_routes = routes_for(("terms", "nth"))