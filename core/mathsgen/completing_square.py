"""Complete the square using exact rational arithmetic throughout."""
from fractions import Fraction
from math import gcd

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)
from .quadratic_monic import polynomial
from .quadratic_formula import surd_form, surd_text, is_perfect_square


INFO = GeneratorInfo(
    id="algebra.quadratic.completing_square", version=1,
    topic="algebra", subtopic="quadratic_equations",
    title="Complete the square",
    difficulty_descriptions={
        1: "Complete the square with an integer shift.",
        2: "Complete the square with a fractional shift.",
        3: "Complete a non-monic square and state the turning point.",
        4: "Complete the square, then solve with exact surd answers.",
    },
    tags=("algebra", "quadratics", "completing_square", "turning_points"),
)


def completed(coefficients):
    a, b, c = coefficients
    shift = Fraction(b, 2 * a)
    offset = Fraction(c) - a * shift * shift
    return {
        "a": str(a), "shift": rational_text(shift),
        "offset": rational_text(offset),
    }


def square_text(form, tex=False):
    a = Fraction(form["a"])
    shift = Fraction(form["shift"])
    offset = Fraction(form["offset"])
    write = rational_tex if tex else rational_text
    inside = "x"
    if shift:
        inside += (" + " if shift > 0 else " - ") + write(abs(shift))
    prefix = "" if a == 1 else "-" if a == -1 else write(a)
    body = prefix + (
        r"\left(" + inside + r"\right)^{2}" if tex else "(" + inside + ")^2"
    )
    if offset:
        body += (" + " if offset > 0 else " - ") + write(abs(offset))
    return body


def answer_for(p, level):
    coefficients = p["coefficients"]
    form = completed(coefficients)
    answer = {"kind": "completed_square", "form": form}
    if level == 3:
        answer["vertex"] = [
            rational_text(-Fraction(form["shift"])), form["offset"]
        ]
        answer["extremum"] = "minimum" if coefficients[0] > 0 else "maximum"
    elif level == 4:
        a, b, c = coefficients
        answer["roots"] = list(surd_form(a, b, b * b - 4 * a * c))
    return answer


def display_for(answer, level):
    plain = square_text(answer["form"])
    tex = square_text(answer["form"], True)
    if level == 3:
        x, y = answer["vertex"]
        plain += "; {} at ({}, {})".format(answer["extremum"], x, y)
        tex += (
            r"\quad\mathrm{" + answer["extremum"] + r"}\quad ("
            + rational_tex(Fraction(x)) + ", " + rational_tex(Fraction(y)) + ")"
        )
    elif level == 4:
        plain += "; " + surd_text(answer["roots"])
        tex += r"\quad " + surd_text(answer["roots"], True)
    return Content(plain, tex)


def prompt_for(p, level):
    instruction = {
        1: "Write the expression in completed-square form.",
        2: "Write the expression in completed-square form. Use exact fractions.",
        3: (
            "Write the expression in completed-square form. Hence state the "
            "turning-point coordinates and whether it is a minimum or maximum."
        ),
        4: (
            "Show the completed-square form, then solve the equation by "
            "completing the square. Give both solutions in exact simplified surd form."
        ),
    }[level]
    plain = polynomial(p["coefficients"])
    tex = polynomial(p["coefficients"], True)
    if level == 4:
        plain += " = 0"
        tex += " = 0"
    return Content(instruction + " " + plain, tex, display_text=instruction)


def check_parameters(p, level):
    require(set(p) == {"coefficients"}, "Unexpected parameters")
    coefficients = p["coefficients"]
    require(isinstance(coefficients, list) and len(coefficients) == 3,
            "Expected three coefficients")
    require(all(type(v) is int for v in coefficients), "Expected integer inputs")
    a, b, c = coefficients
    require(a != 0 and 0 < abs(b) <= 24 and 0 < abs(c) <= 15,
            "Coefficients outside bounds")
    if level == 1:
        require(a == 1 and b % 2 == 0 and abs(b) <= 12,
                "Expected an integer monic shift")
    elif level == 2:
        require(a == 1 and b % 2 != 0 and abs(b) <= 11,
                "Expected a half-integer monic shift")
    elif level == 3:
        require(2 <= abs(a) <= 4 and b % a == 0,
                "Expected a manageable non-monic square")
    else:
        require(1 <= a <= 3, "Leading coefficient outside bounds")
        discriminant = b * b - 4 * a * c
        require(0 < discriminant <= 200 and not is_perfect_square(discriminant),
                "Expected two manageable irrational roots")


class CompletingSquare:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        nonzero = [v for v in range(-12, 13) if v]
        for attempt in range(300):
            c = rng.choice(nonzero)
            if difficulty == 1:
                a, b = 1, 2 * rng.choice([v for v in range(-6, 7) if v])
            elif difficulty == 2:
                a, b = 1, rng.choice(list(range(-11, 12, 2)))
            elif difficulty == 3:
                a = rng.choice((-4, -3, -2, 2, 3, 4))
                b = a * rng.choice([v for v in range(-5, 6) if v])
            else:
                a, b = rng.randint(1, 3), rng.choice(nonzero)
            p = {"coefficients": [a, b, c]}
            try:
                check_parameters(p, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a completing-square question")
        answer = answer_for(p, difficulty)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(p, difficulty),
            answer=answer, answer_display=display_for(answer, difficulty),
            worked_solution=(), marks=3 if difficulty <= 2 else 5,
            tags=self.info.tags, layout_hint=LayoutHint(working_lines=5),
            parameters=p,
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        require(type(q.difficulty) is int and q.difficulty in (1, 2, 3, 4),
                "Invalid difficulty")
        require(q.settings == {}, "Unsupported settings")
        check_parameters(q.parameters, q.difficulty)
        expected = answer_for(q.parameters, q.difficulty)
        require(q.answer == expected, "Incorrect completed form or answer")
        require(q.prompt == prompt_for(q.parameters, q.difficulty), "Prompt mismatch")
        require(q.answer_display == display_for(expected, q.difficulty),
                "Display mismatch")
        require(not q.visual_assets("questions") and not q.visual_assets("answers"),
                "Unexpected visuals")
        return True

    def validate_independently(self, q):
        """Expand the submitted square; check vertex and roots independently."""
        a, b, c = map(Fraction, q.parameters["coefficients"])
        form = q.answer["form"]
        scale, shift, offset = (
            Fraction(form["a"]), Fraction(form["shift"]), Fraction(form["offset"])
        )
        require((scale, 2 * scale * shift, scale * shift * shift + offset)
                == (a, b, c), "Expansion differs from the original polynomial")
        if q.difficulty == 3:
            x, y = map(Fraction, q.answer["vertex"])
            require(2 * a * x + b == 0, "Vertex is not the stationary point")
            require(a * x * x + b * x + c == y, "Wrong vertex height")
            require(q.answer["extremum"] == ("minimum" if a > 0 else "maximum"),
                    "Wrong extremum type")
        elif q.difficulty == 4:
            n, k, radicand, denominator = q.answer["roots"]
            require(all(type(v) is int for v in (n, k, radicand, denominator))
                    and k > 0 and radicand > 1 and denominator > 0,
                    "Invalid surd representation")
            require(all(radicand % (factor * factor) != 0
                        for factor in range(2, radicand + 1)
                        if factor * factor <= radicand),
                    "Radicand is not squarefree")
            require(gcd(gcd(abs(n), k), denominator) == 1,
                    "Surd fraction is not reduced")
            require(Fraction(2 * n, denominator) == -b / a,
                    "Root sum is incorrect")
            require(Fraction(n * n - k * k * radicand, denominator ** 2) == c / a,
                    "Root product is incorrect")
        return True