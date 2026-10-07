"""Changing ratios: recover original amounts from exact, sufficient data.

Four structures progress from one equal increase to two successive changes.
Stored parameters contain the givens only; validators recover the answer.
"""
from fractions import Fraction
from math import gcd

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)


INFO = GeneratorInfo(
    id="ratio.changing.algebra", version=1, topic="ratio", subtopic="changing_ratios",
    title="Ratio: algebra and changing ratios",
    difficulty_descriptions={
        1: "Find original amounts when both increase by the same known amount.",
        2: "Find original wages after unequal increases or an increase and a deduction.",
        3: "Three-person ratios with a fixed transfer and a fractional transfer.",
        4: "Two successive ratio changes: find original amounts and an unknown equal increase.",
    },
    tags=("ratio", "algebra", "changing_ratios", "reasoning", "wages"),
)
FORMS = {1: "equal_increase", 2: "wages", 3: "three_transfers", 4: "two_changes"}
KEYS = {
    1: {"a", "b", "c", "d", "increase"},
    2: {"a", "b", "c", "d", "change_a", "change_b"},
    3: {"a", "b", "c", "transfer", "fraction_num", "fraction_den", "u", "v"},
    4: {"a", "b", "c", "d", "e", "f", "transfer"},
}


def reduced(first, second):
    common = gcd(first, second)
    return first // common, second // common


def whole_positive(value, name):
    require(value.denominator == 1 and 0 < value <= 10000,
            name + " must be a positive whole amount within bounds")
    return value.numerator


def originals(p, level):
    """Recover originals by elimination, rejecting singular ratio equations."""
    if level in (1, 2):
        change_a = p["increase"] if level == 1 else p["change_a"]
        change_b = p["increase"] if level == 1 else p["change_b"]
        determinant = p["a"] * p["d"] - p["b"] * p["c"]
        require(determinant != 0, "Ratio change does not determine original amounts")
        scale = Fraction(p["c"] * change_b - p["d"] * change_a, determinant)
        a, b = p["a"] * scale, p["b"] * scale
        require(a + change_a > 0 and b + change_b > 0, "Final amounts must be positive")
        return {"A": whole_positive(a, "A"), "B": whole_positive(b, "B")}
    if level == 3:
        fraction = Fraction(p["fraction_num"], p["fraction_den"])
        coefficient = p["v"] * p["a"] - p["u"] * (p["c"] + fraction * p["b"])
        require(coefficient != 0, "Transfers do not determine original amounts")
        scale = p["v"] * p["transfer"] / coefficient
        values = {label: whole_positive(p[key] * scale, label)
                  for label, key in zip("ABC", ("a", "b", "c"))}
        given = fraction * values["B"]
        whole_positive(given, "Fractional transfer")
        require(values["A"] > p["transfer"]
                and values["B"] + p["transfer"] > given, "Transfer exceeds available counters")
        return values
    determinant = p["c"] * p["f"] - p["d"] * p["e"]
    require(determinant != 0 and p["a"] != p["b"], "Two changes must determine both unknowns")
    middle_scale = Fraction(p["transfer"] * (p["e"] + p["f"]), determinant)
    original_scale = Fraction(p["c"] - p["d"], p["a"] - p["b"]) * middle_scale
    a, b = p["a"] * original_scale, p["b"] * original_scale
    increase = p["c"] * middle_scale - a
    require(p["c"] * middle_scale > p["transfer"], "Transfer exceeds available amount")
    return {"A": whole_positive(a, "A"), "B": whole_positive(b, "B"),
            "increase": whole_positive(increase, "Increase")}


def check_parameters(p, level):
    require(isinstance(p, dict) and set(p) == KEYS[level] | {"context"},
            "Unexpected ratio parameters")
    require(p["context"] == FORMS[level], "Wrong ratio form for level")
    require(all(type(p[key]) is int for key in KEYS[level]), "Integer givens required")
    pairs = (("a", "b"), ("c", "d")) if level <= 2 else (
        (("u", "v"),) if level == 3 else (("a", "b"), ("c", "d"), ("e", "f")))
    for left, right in pairs:
        require(1 <= p[left] <= 80 and 1 <= p[right] <= 80
                and gcd(p[left], p[right]) == 1, "Ratio must be positive and simplified")
    if level == 1:
        require(1 <= p["increase"] <= 40, "Increase bounds")
    elif level == 2:
        require(5 <= p["change_a"] <= 250 and 5 <= abs(p["change_b"]) <= 250
                and p["change_a"] != p["change_b"], "Unequal wage changes required")
    elif level == 3:
        require(all(1 <= p[key] <= 9 for key in ("a", "b", "c"))
                and gcd(gcd(p["a"], p["b"]), p["c"]) == 1, "Three-part ratio bounds")
        require(1 <= p["fraction_num"] < p["fraction_den"] <= 5
                and gcd(p["fraction_num"], p["fraction_den"]) == 1, "Transfer fraction bounds")
        require(1 <= p["transfer"] <= 100, "Transfer bounds")
    else:
        require(1 <= p["transfer"] <= 100, "Transfer bounds")
    return originals(p, level)


def prompt_for(p, level):
    if level == 1:
        return Content(
            "Two positive amounts A and B are in the ratio {a} : {b}. "
            "Both amounts increase by {increase}. The ratio A : B is now "
            "{c} : {d}. Find the original values of A and B.".format(**p))
    if level == 2:
        second = ("increases by £{}".format(p["change_b"]) if p["change_b"] > 0
                  else "decreases by £{}".format(-p["change_b"]))
        return Content(
            "Asha and Ben's original weekly wages are in the ratio {a} : {b}. "
            "Asha's weekly wage increases by £{change_a}. Ben's weekly wage "
            "{second}. Their new weekly wages are in the ratio {c} : {d}. "
            "Find each person's original weekly wage.".format(second=second, **p))
    if level == 3:
        return Content(
            "A, B and C initially have counters in the ratio {a} : {b} : {c}. "
            "A gives {transfer} counters to B. B then gives {fraction_num}/{fraction_den} "
            "of B's ORIGINAL number of counters to C. The final ratio of A's counters "
            "to C's counters is {u} : {v}. Find how many counters each person had "
            "originally.".format(**p))
    return Content(
        "A and B initially have money in the ratio {a} : {b}. Each receives the same "
        "unknown amount of money, making the ratio {c} : {d}. A then gives £{transfer} "
        "to B, making the ratio {e} : {f}. Find their original amounts and the "
        "amount each received.".format(**p))


def answer_for(values, level):
    unit = "GBP" if level in (2, 4) else "counters" if level == 3 else "amount"
    answer = {"kind": "labelled_quantities", "unit": unit,
              "values": {key: str(value) for key, value in values.items()}}
    labels = {"A": "Asha" if level == 2 else "A",
              "B": "Ben" if level == 2 else "B", "C": "C",
              "increase": "Each received"}
    def shown(value):
        return "£" + str(value) if unit == "GBP" else str(value) + (" counters" if level == 3 else "")
    display = Content("; ".join(labels[key] + ": " + shown(value)
                                for key, value in values.items()))
    return answer, display


def draw(rng, level):
    a, b = reduced(*rng.sample(range(1, 10), 2))
    scale = rng.randint(2, 20)
    p = {"context": FORMS[level], "a": a, "b": b}
    if level == 1:
        increase = rng.randint(1, 30)
        c, d = reduced(a * scale + increase, b * scale + increase)
        p.update(c=c, d=d, increase=increase)
    elif level == 2:
        scale *= 25
        change_a = 5 * rng.randint(1, 30)
        change_b = 5 * rng.randint(1, 30) * rng.choice((-1, 1))
        if b * scale + change_b <= 0:
            return None
        c, d = reduced(a * scale + change_a, b * scale + change_b)
        p.update(c=c, d=d, change_a=change_a, change_b=change_b)
    elif level == 3:
        c = rng.randint(1, 9)
        fraction = rng.choice((Fraction(1, 2), Fraction(1, 3), Fraction(2, 3),
                               Fraction(1, 4), Fraction(3, 4), Fraction(2, 5)))
        scale *= fraction.denominator
        transfer = rng.randint(1, min(a * scale - 1, 60))
        given = b * scale * fraction
        u, v = reduced(a * scale - transfer, int(c * scale + given))
        p.update(c=c, transfer=transfer, fraction_num=fraction.numerator,
                 fraction_den=fraction.denominator, u=u, v=v)
    else:
        increase = rng.randint(1, 40)
        middle_a, middle_b = a * scale + increase, b * scale + increase
        transfer = rng.randint(1, min(middle_a - 1, 60))
        c, d = reduced(middle_a, middle_b)
        e, f = reduced(middle_a - transfer, middle_b + transfer)
        p.update(c=c, d=d, e=e, f=f, transfer=transfer)
    return p


class RatioAlgebra:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "Changing ratios accepts no settings")
        for _ in range(2000):
            parameters = draw(context.rng, difficulty)
            if parameters is None:
                continue
            try:
                values = check_parameters(parameters, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a suitable changing-ratio problem")
        answer, display = answer_for(values, difficulty)
        question = Question(
            id=context.identity, generator_id=self.info.id, generator_version=self.info.version,
            topic=self.info.topic, subtopic=self.info.subtopic, difficulty=difficulty,
            seed=seed, settings=context.settings, prompt=prompt_for(parameters, difficulty),
            answer=answer, answer_display=display, worked_solution=(),
            marks={1: 3, 2: 4, 3: 5, 4: 6}[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines={1: 6, 2: 7, 3: 9, 4: 10}[difficulty]),
            parameters=parameters,
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id
                and question.generator_version == self.info.version, "Generator mismatch")
        level = question.difficulty
        require(type(level) is int and level in FORMS, "Invalid level")
        require(question.settings == {}, "Unsupported settings")
        values = check_parameters(question.parameters, level)
        answer, display = answer_for(values, level)
        require(question.answer == answer, "Incorrect original amounts")
        require(question.answer_display == display, "Answer display mismatch")
        require(question.prompt == prompt_for(question.parameters, level), "Prompt mismatch")
        return True

    def validate_independently(self, question):
        """Solve simultaneous equations in the original amounts using SymPy."""
        import sympy
        p, level = question.parameters, question.difficulty
        A, B, C, h = sympy.symbols("A B C h")
        equations = [p["b"] * A - p["a"] * B]
        symbols, labels = [A, B], ["A", "B"]
        if level in (1, 2):
            da = p["increase"] if level == 1 else p["change_a"]
            db = p["increase"] if level == 1 else p["change_b"]
            equations.append(p["d"] * (A + da) - p["c"] * (B + db))
        elif level == 3:
            symbols, labels = [A, B, C], ["A", "B", "C"]
            equations.append(p["c"] * A - p["a"] * C)
            given = sympy.Rational(p["fraction_num"], p["fraction_den"]) * B
            equations.append(p["v"] * (A - p["transfer"]) - p["u"] * (C + given))
        else:
            symbols, labels = [A, B, h], ["A", "B", "increase"]
            equations.extend([
                p["d"] * (A + h) - p["c"] * (B + h),
                p["f"] * (A + h - p["transfer"]) - p["e"] * (B + h + p["transfer"]),
            ])
        solved = sympy.solve(equations, symbols, dict=True)
        require(len(solved) == 1 and set(solved[0]) == set(symbols), "Originals are not unique")
        require(all(solved[0][symbol] == sympy.Rational(question.answer["values"][label])
                    for symbol, label in zip(symbols, labels)), "Independent originals disagree")
        return True