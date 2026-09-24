"""Geometric sequences: terms, ratios, nth terms, surd sequences and unknowns.

Terms are exact (integers or Fractions). Surd sequences 1, sqrt(k), k, ...
have n-th term k^((n-1)/2), stored as a whole-number coefficient times sqrt(k)
or a whole number. The algebraic form builds x + a, x + b, x + c from a real
geometric sequence, so x is recovered exactly by a linear equation.
"""
import math
from fractions import Fraction

from . import rich_blocks as rb
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .iteration import join_terms


INFO = GeneratorInfo(
    id="algebra.sequences.geometric", version=1,
    topic="algebra", subtopic="geometric_sequences",
    title="Geometric sequences: ratios, nth terms and unknowns",
    difficulty_descriptions={
        1: "Continue a geometric sequence, or find its common ratio.",
        2: "Write the nth term as a times r to the power n - 1, or find a term.",
        3: "Find the first term from two terms, or a term of a surd sequence.",
        4: "Find x when x + a, x + b, x + c are geometric, or the first term above a limit.",
    },
    tags=("algebra", "sequences", "geometric"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("next_terms", "ratio"),
    2: ("nth_expression", "find_term"),
    3: ("from_two_terms", "surd_terms"),
    4: ("algebraic_terms", "first_exceeding"),
}
COMMON_RATIOS = (Fraction(2), Fraction(3), Fraction(4), Fraction(1, 2), Fraction(1, 3),
                 Fraction(2, 3), Fraction(3, 2))
ROOTS = (2, 3, 5, 7)
LIMITS = (500, 1000, 2000, 5000, 10000, 50000, 100000)
MARKS = {1: 2, 2: 2, 3: 3, 4: 3}
WORKING_LINES = {1: 3, 2: 4, 3: 5, 4: 6}

KEYS = {
    "next_terms": {"first", "ratio"},
    "ratio": {"first", "ratio_num", "ratio_den"},
    "nth_expression": {"first", "ratio"},
    "find_term": {"first", "ratio", "position"},
    "from_two_terms": {"first", "ratio", "earlier", "later"},
    "surd_terms": {"root", "position"},
    "algebraic_terms": {"x", "offset", "ratio"},
    "first_exceeding": {"first", "ratio", "limit"},
}


# ------------------------------------------------------------ mathematics

def term(first, ratio, n):
    return first * Fraction(ratio) ** (n - 1)


def ordinal(n):
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return "{}{}".format(n, suffix)


def surd_term(root, position):
    """(coefficient, root or 1) for the position-th term of 1, sqrt(k), k, ..."""
    power = position - 1
    if power % 2 == 0:
        return root ** (power // 2), 1
    return root ** (power // 2), root


def algebraic_offsets(par):
    """(a, b, c): terms x + a, x + b, x + c of a geometric sequence."""
    first = par["x"] + par["offset"]
    r = par["ratio"]
    return par["offset"], first * r - par["x"], first * r * r - par["x"]


def exceeding_position(par):
    n = 1
    while term(par["first"], par["ratio"], n) <= par["limit"]:
        n += 1
    return n


def check_parameters(par, level):
    require(isinstance(par, dict), "Parameters must be a dictionary")
    form = par.get("form")
    require(level in FORMS and form in FORMS[level], "Unexpected form for this level")
    require(set(par) == KEYS[form] | {"form"}, "Unexpected parameters")
    require(all(type(par[k]) is int for k in KEYS[form]), "Integer parameters required")

    if form == "next_terms":
        require(1 <= par["first"] <= 6 and 2 <= par["ratio"] <= 5, "Values outside bounds")
        require(term(par["first"], par["ratio"], 6) <= 20000, "Terms too large")
    elif form == "ratio":
        den = par["ratio_den"]
        require(den > 0 and math.gcd(par["ratio_num"], den) == 1
                and Fraction(par["ratio_num"], den) in COMMON_RATIOS, "Unexpected ratio")
        require(par["first"] % den ** 3 == 0 and 1 <= par["first"] // den ** 3 <= 5,
                "First term must keep four whole-number terms")
    elif form == "nth_expression":
        require(1 <= par["first"] <= 9 and 2 <= par["ratio"] <= 5, "Values outside bounds")
    elif form == "find_term":
        require(1 <= par["first"] <= 9 and 2 <= par["ratio"] <= 4 and 5 <= par["position"] <= 9,
                "Values outside bounds")
        require(term(par["first"], par["ratio"], par["position"]) <= 10 ** 6, "Term too large")
    elif form == "from_two_terms":
        require(1 <= par["first"] <= 6 and 2 <= par["ratio"] <= 4, "Values outside bounds")
        require(1 <= par["earlier"] <= 3 and par["later"] - par["earlier"] in (2, 3),
                "Positions outside bounds")
        require(term(par["first"], par["ratio"], par["later"]) <= 50000, "Terms too large")
    elif form == "surd_terms":
        require(par["root"] in ROOTS and 6 <= par["position"] <= 11, "Values outside bounds")
    elif form == "algebraic_terms":
        require(1 <= par["x"] <= 12 and -5 <= par["offset"] <= 8 and par["offset"] != 0,
                "Values outside bounds")
        require(1 <= par["x"] + par["offset"] <= 9 and par["ratio"] in (2, 3),
                "First term or ratio outside bounds")
        a, b, c = algebraic_offsets(par)
        require(len({a, b, c}) == 3, "Offsets must differ")
    else:
        # A first term of 1 would print as "1 x 2^(n-1)".
        require(2 <= par["first"] <= 9 and par["ratio"] in (2, 3) and par["limit"] in LIMITS,
                "Values outside bounds")
        n = exceeding_position(par)
        require(n >= 4 and term(par["first"], par["ratio"], n - 1) != par["limit"],
                "Threshold too early or exactly hit")


# ------------------------------------------------------------ wording

def terms_text(values):
    return ", ".join(rational_text(v) for v in values)


def content(runs):
    return Content("".join(run["text"] for run in runs), blocks=(rb.paragraph(*runs),))


def prompt_for(par):
    form = par["form"]
    if form in ("next_terms", "nth_expression"):
        shown = terms_text([term(par["first"], par["ratio"], n) for n in range(1, 5)])
        task = ("Write down the next two terms." if form == "next_terms"
                else "Find an expression, in terms of n, for the nth term.")
        return content([rb.text("The first four terms of a geometric sequence are {}. {}"
                                .format(shown, task))])
    if form == "ratio":
        r = Fraction(par["ratio_num"], par["ratio_den"])
        shown = terms_text([term(par["first"], r, n) for n in range(1, 5)])
        return content([rb.text("Here are the first four terms of a geometric sequence: {}. "
                                "Find the common ratio.".format(shown))])
    if form == "find_term":
        return content([rb.text("The first term of a geometric sequence is {} and the common "
                                "ratio is {}. Work out the {} term.".format(
                                    par["first"], par["ratio"], ordinal(par["position"])))])
    if form == "from_two_terms":
        first, r = par["first"], par["ratio"]
        return content([rb.text(
            "In a geometric sequence, the {} term is {} and the {} term is {}. The common "
            "ratio is a positive whole number. Work out the first term of the sequence.".format(
                ordinal(par["earlier"]), term(first, r, par["earlier"]),
                ordinal(par["later"]), term(first, r, par["later"])))])
    if form == "surd_terms":
        k = par["root"]
        return content([
            rb.text("The first four terms of a geometric sequence are "),
            rb.maths(r"1,\ \sqrt{%d},\ %d,\ %d\sqrt{%d}" % (k, k, k, k),
                     "1, √{0}, {0}, {0}√{0}".format(k)),
            rb.text(". Work out the {} term. Give your answer in its simplest form.".format(
                ordinal(par["position"]))),
        ])
    if form == "algebraic_terms":
        pieces = [join_terms([(1, "x", "x"), (offset, "", "")])
                  for offset in algebraic_offsets(par)]
        return content([
            rb.text("The first three terms of a geometric sequence are "),
            rb.maths(r",\ ".join(p[0] for p in pieces), ", ".join(p[1] for p in pieces)),
            rb.text(". Work out the value of x."),
        ])
    return content([
        rb.text("The nth term of a geometric sequence is "),
        rb.maths(r"%d \times %d^{n-1}" % (par["first"], par["ratio"]),
                 "{} x {}^(n-1)".format(par["first"], par["ratio"])),
        rb.text(". Work out the position of the first term that is greater than {}."
                .format(par["limit"])),
    ])


def answer_for(par):
    form = par["form"]
    if form == "next_terms":
        values = [term(par["first"], par["ratio"], n) for n in (5, 6)]
        return ({"kind": "terms", "values": [rational_text(v) for v in values]},
                Content(terms_text(values)))
    if form == "ratio":
        r = Fraction(par["ratio_num"], par["ratio_den"])
        return {"kind": "rational", "value": rational_text(r)}, Content(rational_text(r))
    if form == "nth_expression":
        a, r = par["first"], par["ratio"]
        tex = (r"%d^{n-1}" % r) if a == 1 else (r"%d \times %d^{n-1}" % (a, r))
        text = ("{}^(n-1)".format(r)) if a == 1 else ("{} x {}^(n-1)".format(a, r))
        return {"kind": "geometric_nth", "first": str(a), "ratio": str(r)}, Content(text, tex)
    if form == "find_term":
        value = term(par["first"], par["ratio"], par["position"])
        return {"kind": "integer", "value": rational_text(value)}, Content(rational_text(value))
    if form == "from_two_terms":
        return ({"kind": "integer", "value": str(par["first"]), "ratio": str(par["ratio"])},
                Content("Common ratio {}, so the first term is {}.".format(
                    par["ratio"], par["first"])))
    if form == "surd_terms":
        coefficient, root = surd_term(par["root"], par["position"])
        if root == 1:
            return ({"kind": "surd", "coefficient": str(coefficient), "root": "1"},
                    Content(str(coefficient), str(coefficient)))
        return ({"kind": "surd", "coefficient": str(coefficient), "root": str(root)},
                Content("{}√{}".format(coefficient, root), r"%d\sqrt{%d}" % (coefficient, root)))
    if form == "algebraic_terms":
        return {"kind": "integer", "value": str(par["x"])}, Content("x = {}".format(par["x"]))
    n = exceeding_position(par)
    return ({"kind": "integer", "value": str(n)},
            Content("The {} term, {}, is the first greater than {}.".format(
                ordinal(n), rational_text(term(par["first"], par["ratio"], n)), par["limit"])))


def draw_parameters(rng, form):
    par = {"form": form}
    if form in ("next_terms", "nth_expression"):
        par.update(first=rng.randint(1, 6 if form == "next_terms" else 9),
                   ratio=rng.randint(2, 5))
    elif form == "ratio":
        r = rng.choice(COMMON_RATIOS)
        par.update(first=r.denominator ** 3 * rng.randint(1, 5),
                   ratio_num=r.numerator, ratio_den=r.denominator)
    elif form == "find_term":
        par.update(first=rng.randint(1, 9), ratio=rng.randint(2, 4), position=rng.randint(5, 9))
    elif form == "from_two_terms":
        earlier = rng.randint(1, 3)
        par.update(first=rng.randint(1, 6), ratio=rng.randint(2, 4), earlier=earlier,
                   later=earlier + rng.choice((2, 3)))
    elif form == "surd_terms":
        par.update(root=rng.choice(ROOTS), position=rng.randint(6, 11))
    elif form == "algebraic_terms":
        par.update(x=rng.randint(1, 12), offset=rng.choice([v for v in range(-5, 9) if v]),
                   ratio=rng.choice((2, 3)))
    else:
        par.update(first=rng.randint(2, 9), ratio=rng.choice((2, 3)), limit=rng.choice(LIMITS))
    return par


# ------------------------------------------------------------ generator

class GeometricSequences:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        form = rng.choice(FORMS[difficulty])
        for attempt in range(1000):
            par = draw_parameters(rng, form)
            try:
                check_parameters(par, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a geometric sequence question")
        answer, display = answer_for(par)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(par),
            answer=answer, answer_display=display, worked_solution=(),
            marks=MARKS[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=WORKING_LINES[difficulty]),
            parameters=par,
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        require(type(q.difficulty) is int and q.difficulty in (1, 2, 3, 4), "Invalid difficulty")
        require(q.settings == {}, "Unsupported settings")
        check_parameters(q.parameters, q.difficulty)
        answer, display = answer_for(q.parameters)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Answer display mismatch")
        require(q.prompt == prompt_for(q.parameters), "Prompt mismatch")
        return True

    def validate_independently(self, q):
        """Repeated multiplication, a search for the ratio, and the closed form for x."""
        par, answer = q.parameters, q.answer
        form = par.get("form")

        def by_steps(first, ratio, count):
            values, value = [], Fraction(first)
            for _ in range(count):
                values.append(value)
                value *= ratio
            return values

        if form == "next_terms":
            values = by_steps(par["first"], par["ratio"], 6)
            require([Fraction(v) for v in answer["values"]] == values[4:], "Next terms disagree")
        elif form == "ratio":
            r = Fraction(par["ratio_num"], par["ratio_den"])
            values = by_steps(par["first"], r, 4)
            stated = Fraction(answer["value"])
            require(all(values[i + 1] == values[i] * stated for i in range(3)), "Ratio disagrees")
        elif form == "nth_expression":
            a, r = int(answer["first"]), int(answer["ratio"])
            require(by_steps(par["first"], par["ratio"], 4) == [a * r ** (n - 1) for n in range(1, 5)],
                    "Expression does not generate the terms")
        elif form == "find_term":
            require(Fraction(answer["value"]) == by_steps(par["first"], par["ratio"],
                                                          par["position"])[-1], "Term disagrees")
        elif form == "from_two_terms":
            earlier = by_steps(par["first"], par["ratio"], par["earlier"])[-1]
            later = by_steps(par["first"], par["ratio"], par["later"])[-1]
            found = [r for r in range(2, 11)
                     if earlier * r ** (par["later"] - par["earlier"]) == later]
            require(len(found) == 1, "Ratio is not unique")
            first = earlier / found[0] ** (par["earlier"] - 1)
            require(Fraction(answer["value"]) == first, "First term disagrees")
        elif form == "surd_terms":
            stated = int(answer["coefficient"]) * math.sqrt(int(answer["root"]))
            expected = math.sqrt(par["root"]) ** (par["position"] - 1)
            require(abs(stated - expected) <= 1e-9 * expected, "Surd term disagrees")
        elif form == "algebraic_terms":
            a, b, c = algebraic_offsets(par)
            x = Fraction(a * c - b * b, 2 * b - a - c)
            require(Fraction(answer["value"]) == x, "x disagrees with the closed form")
            require((x + b) * (x + b) == (x + a) * (x + c), "Terms are not geometric")
        else:
            n, value = 1, par["first"]
            while value <= par["limit"]:
                value *= par["ratio"]
                n += 1
            require(int(answer["value"]) == n, "Position disagrees")
        return True