"""Algebraic proof: show-that identities and proofs about multiples, odd and even.

Every question is an exact integer polynomial in n (or x). The answer is the
written proof: expand, refactor, conclude. Each claim is one of

    identity   the two sides are equal for every x
    multiple   E(n) = m * Q(n) + r for every integer n (r = 0: a multiple of m)
    constant   E(n) is the same positive number for every n

Level 4 uses classic results that need one more idea: n(n + 1) is a product of
consecutive integers, so it is even; three consecutive integers include a
multiple of 2 and a multiple of 3.
"""
import math

from . import rich_blocks as rb
from .core import Content, GeneratorInfo, LayoutHint, Question, make_context, require
from .iteration import join_terms


INFO = GeneratorInfo(
    id="algebra.proof.algebraic", version=1,
    topic="algebra", subtopic="proof",
    title="Algebraic proof: identities, multiples, odd and even",
    difficulty_descriptions={
        1: "Prove a sum of consecutive numbers is a multiple, or show a linear identity.",
        2: "Prove a difference of two squares is always a multiple of a number.",
        3: "Prove an expression is always positive, or a squares difference is odd or a multiple.",
        4: "Classic proofs needing 'n(n + 1) is even' or three consecutive integers.",
    },
    tags=("algebra", "proof", "reasoning"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("consecutive_sum", "show_identity"),
    2: ("difference_squares", "shifted_squares"),
    3: ("constant_difference", "consecutive_gap"),
    4: ("classic",),
}
# (kind, how many consecutive numbers) -> the multiple that is always true.
CONSECUTIVE = {("integers", 3): 3, ("integers", 5): 5, ("integers", 7): 7,
               ("evens", 3): 6, ("evens", 5): 10, ("odds", 2): 4, ("odds", 4): 8}
WORDS = {"integers": "integers", "evens": "even numbers", "odds": "odd numbers"}
CLASSICS = ("odd_square", "even_product", "odd_squares_sum", "cube_minus",
            "three_squares", "odd_product_plus")
MARKS = {1: 2, 2: 3, 3: 3, 4: 4}
WORKING_LINES = {1: 5, 2: 6, 3: 6, 4: 8}

KEYS = {
    "consecutive_sum": {"kind", "count"},
    "show_identity": {"a", "b", "c", "d"},
    "difference_squares": {"a", "b"},
    "shifted_squares": {"a", "b"},
    "constant_difference": {"a", "d"},
    "consecutive_gap": {"d"},
    "classic": {"statement"},
}


# ------------------------------------------------------------ polynomials
# Ascending integer coefficient lists: [c0, c1, c2] is c0 + c1 n + c2 n^2.

def trim(p):
    p = list(p)
    while len(p) > 1 and p[-1] == 0:
        p.pop()
    return p


def add(p, q):
    size = max(len(p), len(q))
    return trim([(p[i] if i < len(p) else 0) + (q[i] if i < len(q) else 0) for i in range(size)])


def scale(c, p):
    return trim([c * x for x in p])


def mul(p, q):
    out = [0] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        for j, b in enumerate(q):
            out[i + j] += a * b
    return trim(out)


def linear(a, b):
    return trim([b, a])


def parts(p, var="n"):
    terms = []
    for power in range(len(p) - 1, -1, -1):
        if power == 0:
            terms.append((p[0], "", ""))
        elif power == 1:
            terms.append((p[1], var, var))
        else:
            terms.append((p[power], "%s^{%d}" % (var, power), "%s^%d" % (var, power)))
    return join_terms(terms)


def bracketed(p, var="n"):
    tex, text = parts(p, var)
    return "(" + tex + ")", "(" + text + ")"


def squared(p, var="n"):
    tex, text = bracketed(p, var)
    return tex + "^{2}", text + "^2"


def divided(p, m):
    require(all(c % m == 0 for c in p), "Expression is not a multiple as claimed")
    return [c // m for c in p]


# ------------------------------------------------------------ classic results

def classic(name):
    """(prompt, expanded polynomial, claim, proof) for one classic statement."""
    if name == "odd_square":
        return ("Prove that the square of any odd number is always 1 more than a multiple of 8.",
                [1, 4, 4], ("multiple", 8, 1),
                "An odd number is 2n + 1, where n is an integer. (2n + 1)^2 = 4n^2 + 4n + 1 "
                "= 4n(n + 1) + 1. n(n + 1) is a product of two consecutive integers, so it is "
                "even, and 4n(n + 1) is a multiple of 8. So the square is 1 more than a "
                "multiple of 8.")
    if name == "even_product":
        return ("Prove that the product of any two consecutive even numbers is always a "
                "multiple of 8.",
                [0, 4, 4], ("multiple", 8, 0),
                "The numbers are 2n and 2n + 2. 2n(2n + 2) = 4n^2 + 4n = 4n(n + 1). "
                "n(n + 1) is a product of two consecutive integers, so it is even, and "
                "4n(n + 1) is a multiple of 8.")
    if name == "odd_squares_sum":
        return ("Prove that the sum of the squares of any two consecutive odd numbers is "
                "always 2 more than a multiple of 8.",
                [2, 0, 8], ("multiple", 8, 2),
                "The numbers are 2n - 1 and 2n + 1. (2n - 1)^2 + (2n + 1)^2 = 4n^2 - 4n + 1 "
                "+ 4n^2 + 4n + 1 = 8n^2 + 2, which is 2 more than a multiple of 8.")
    if name == "cube_minus":
        return ("Prove that n^3 - n is always a multiple of 6 for any integer n.",
                [0, -1, 0, 1], ("multiple", 6, 0),
                "n^3 - n = n(n^2 - 1) = (n - 1)n(n + 1), a product of three consecutive "
                "integers. At least one of them is even and exactly one is a multiple of 3, "
                "so the product is a multiple of 2 x 3 = 6.")
    if name == "three_squares":
        return ("Prove that the sum of the squares of any three consecutive integers is always "
                "2 more than a multiple of 3.",
                [2, 0, 3], ("multiple", 3, 2),
                "The integers are n - 1, n and n + 1. (n - 1)^2 + n^2 + (n + 1)^2 = n^2 - 2n + 1 "
                "+ n^2 + n^2 + 2n + 1 = 3n^2 + 2, which is 2 more than a multiple of 3.")
    return ("Prove that the product of any two consecutive odd numbers, plus 1, is always a "
            "multiple of 4.",
            [0, 0, 4], ("multiple", 4, 0),
            "The numbers are 2n - 1 and 2n + 1. (2n - 1)(2n + 1) + 1 = 4n^2 - 1 + 1 = 4n^2 "
            "= 4 x n^2, which is a multiple of 4.")


# ------------------------------------------------------------ building each form

def build(par):
    """{"runs", "expanded", "claim", "proof"} for the parameters."""
    form = par["form"]
    if form == "consecutive_sum":
        kind, k = par["kind"], par["count"]
        m = CONSECUTIVE[(kind, k)]
        lead = 1 if kind == "integers" else 2
        step = 1 if kind == "integers" else 2
        start = 1 if kind == "odds" else 0
        numbers = [linear(lead, start + step * i) for i in range(k)]
        expanded = [0]
        for number in numbers:
            expanded = add(expanded, number)
        quotient = divided(expanded, m)
        proof = ("Let the numbers be {}, where n is an integer. Their sum is {} = {}({}), "
                 "which is a multiple of {}.").format(
            ", ".join(parts(number)[1] for number in numbers), parts(expanded)[1], m,
            parts(quotient)[1], m)
        runs = [rb.text("Prove that the sum of any {} consecutive {} is always a multiple of "
                        "{}.".format(k, WORDS[kind], m))]
        return {"runs": runs, "expanded": expanded, "claim": ("multiple", m, 0), "proof": proof}

    if form == "show_identity":
        a, b, c, d = par["a"], par["b"], par["c"], par["d"]
        first, second = scale(a, linear(1, b)), scale(c, linear(1, d))
        expanded = add(first, scale(-1, second))
        left_tex = "%d%s - %d%s" % (a, bracketed(linear(1, b), "x")[0], c,
                                    bracketed(linear(1, d), "x")[0])
        left_text = "%d%s - %d%s" % (a, bracketed(linear(1, b), "x")[1], c,
                                     bracketed(linear(1, d), "x")[1])
        right_tex, right_text = parts(expanded, "x")
        runs = [rb.text("Show that "),
                rb.maths(left_tex + r" \equiv " + right_tex, left_text + " ≡ " + right_text),
                rb.text(".")]
        proof = "{} = {} - ({}) = {}".format(left_text, parts(first, "x")[1],
                                             parts(second, "x")[1], right_text)
        return {"runs": runs, "expanded": expanded, "claim": ("identity",), "proof": proof}

    if form == "difference_squares":
        a, b = par["a"], par["b"]
        up, down = linear(a, b), linear(a, -b)
        first, second = mul(up, up), mul(down, down)
        expanded = add(first, scale(-1, second))
        m = 4 * a * b
        sq_up, sq_down = squared(up), squared(down)
        runs = [rb.text("Prove that "), rb.maths(sq_up[0] + " - " + sq_down[0],
                                                sq_up[1] + " - " + sq_down[1]),
                rb.text(" is always a multiple of {} for any integer n.".format(m))]
        proof = "{} - {} = ({}) - ({}) = {}, which is a multiple of {}.".format(
            sq_up[1], sq_down[1], parts(first)[1], parts(second)[1], parts(expanded)[1], m)
        return {"runs": runs, "expanded": expanded, "claim": ("multiple", m, 0), "proof": proof}

    if form == "shifted_squares":
        a, b = par["a"], par["b"]
        up, down = linear(1, a), linear(1, -b)
        first, second = mul(up, up), mul(down, down)
        expanded = add(first, scale(-1, second))
        m = a + b
        quotient = divided(expanded, m)
        sq_up, sq_down = squared(up), squared(down)
        runs = [rb.text("Prove that "), rb.maths(sq_up[0] + " - " + sq_down[0],
                                                sq_up[1] + " - " + sq_down[1]),
                rb.text(" is always a multiple of {} for any integer n.".format(m))]
        proof = "{} - {} = ({}) - ({}) = {} = {}({}), which is a multiple of {}.".format(
            sq_up[1], sq_down[1], parts(first)[1], parts(second)[1], parts(expanded)[1],
            m, parts(quotient)[1], m)
        return {"runs": runs, "expanded": expanded, "claim": ("multiple", m, 0), "proof": proof}

    if form == "constant_difference":
        a, d = par["a"], par["d"]
        square = mul(linear(1, a), linear(1, a))
        product = mul(linear(1, a - d), linear(1, a + d))
        expanded = add(square, scale(-1, product))
        sq = squared(linear(1, a))
        low, high = bracketed(linear(1, a - d)), bracketed(linear(1, a + d))
        expression_tex = sq[0] + " - " + low[0] + high[0]
        expression_text = sq[1] + " - " + low[1] + high[1]
        runs = [rb.text("Prove that "), rb.maths(expression_tex, expression_text),
                rb.text(" is always positive.")]
        proof = "{} = ({}) - ({}) = {}, which is always positive.".format(
            expression_text, parts(square)[1], parts(product)[1], parts(expanded)[1])
        return {"runs": runs, "expanded": expanded, "claim": ("constant", d * d), "proof": proof}

    if form == "consecutive_gap":
        d = par["d"]
        first = mul(linear(1, d), linear(1, d))
        expanded = add(first, [0, 0, -1])
        if d == 1:
            runs = [rb.text("Prove that the difference between the squares of any two "
                            "consecutive integers is always odd.")]
            proof = ("Let the integers be n and n + 1. (n + 1)^2 - n^2 = n^2 + 2n + 1 - n^2 "
                     "= 2n + 1, which is odd.")
            return {"runs": runs, "expanded": expanded, "claim": ("multiple", 2, 1),
                    "proof": proof}
        quotient = divided(expanded, d)
        runs = [rb.text("Prove that the difference between the squares of two integers that "
                        "differ by {0} is always a multiple of {0}.".format(d))]
        proof = ("Let the integers be n and n + {0}. (n + {0})^2 - n^2 = {1} - n^2 = {2} "
                 "= {0}({3}), which is a multiple of {0}.").format(
            d, parts(first)[1], parts(expanded)[1], parts(quotient)[1])
        return {"runs": runs, "expanded": expanded, "claim": ("multiple", d, 0), "proof": proof}

    prompt, expanded, claim, proof = classic(par["statement"])
    return {"runs": [rb.text(prompt)], "expanded": expanded, "claim": claim, "proof": proof}


def check_parameters(par, level):
    require(isinstance(par, dict), "Parameters must be a dictionary")
    form = par.get("form")
    require(level in FORMS and form in FORMS[level], "Unexpected form for this level")
    require(set(par) == KEYS[form] | {"form"}, "Unexpected parameters")
    if form == "consecutive_sum":
        require((par["kind"], par["count"]) in CONSECUTIVE and type(par["count"]) is int,
                "Unexpected consecutive sum")
    elif form == "classic":
        require(par["statement"] in CLASSICS, "Unknown statement")
    else:
        require(all(type(par[k]) is int for k in KEYS[form]), "Integer parameters required")
    if form == "show_identity":
        require(2 <= par["a"] <= 9 and 2 <= par["c"] <= 9 and par["a"] != par["c"],
                "Multipliers outside bounds")
        require(all(-9 <= par[k] <= 9 and par[k] != 0 for k in ("b", "d")),
                "Constants outside bounds")
        require(par["a"] * par["b"] != par["c"] * par["d"], "Constant term cancels")
    elif form == "difference_squares":
        require(1 <= par["a"] <= 4 and 1 <= par["b"] <= 5, "Coefficients outside bounds")
    elif form == "shifted_squares":
        require(1 <= par["a"] <= 6 and 1 <= par["b"] <= 6 and par["a"] + par["b"] >= 3,
                "Shifts outside bounds")
    elif form == "constant_difference":
        require(2 <= par["a"] <= 8 and 1 <= par["d"] <= 4 and par["d"] != par["a"],
                "Values outside bounds")
    elif form == "consecutive_gap":
        require(1 <= par["d"] <= 6, "Gap outside bounds")
    build(par)


def content(runs):
    return Content("".join(run["text"] for run in runs), blocks=(rb.paragraph(*runs),))


def answer_for(par):
    built = build(par)
    answer = {"kind": "proof", "expanded": [str(c) for c in built["expanded"]],
              "claim": list(built["claim"])}
    return answer, Content(built["proof"])


def draw_parameters(rng, form):
    par = {"form": form}
    if form == "consecutive_sum":
        kind, count = rng.choice(sorted(CONSECUTIVE))
        par.update(kind=kind, count=count)
    elif form == "show_identity":
        par.update(a=rng.randint(2, 9), b=rng.choice([v for v in range(-9, 10) if v]),
                   c=rng.randint(2, 9), d=rng.choice([v for v in range(-9, 10) if v]))
    elif form == "difference_squares":
        par.update(a=rng.randint(1, 4), b=rng.randint(1, 5))
    elif form == "shifted_squares":
        par.update(a=rng.randint(1, 6), b=rng.randint(1, 6))
    elif form == "constant_difference":
        par.update(a=rng.randint(2, 8), d=rng.randint(1, 4))
    elif form == "consecutive_gap":
        par["d"] = rng.randint(1, 6)
    else:
        par["statement"] = rng.choice(CLASSICS)
    return par


# ------------------------------------------------------------ generator

class AlgebraicProof:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        form = rng.choice(FORMS[difficulty])
        for attempt in range(500):
            par = draw_parameters(rng, form)
            try:
                check_parameters(par, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct an algebraic proof question")
        answer, display = answer_for(par)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=content(build(par)["runs"]),
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
        require(q.prompt == content(build(q.parameters)["runs"]), "Prompt mismatch")
        return True

    def validate_independently(self, q):
        """Evaluate each expression directly for n = -25..25; check the stated expansion
        agrees at every point and the claim holds at every point."""
        par, answer = q.parameters, q.answer
        form = par.get("form")

        def direct(n):
            if form == "consecutive_sum":
                lead = 1 if par["kind"] == "integers" else 2
                step = 1 if par["kind"] == "integers" else 2
                start = 1 if par["kind"] == "odds" else 0
                return sum(lead * n + start + step * i for i in range(par["count"]))
            if form == "show_identity":
                return par["a"] * (n + par["b"]) - par["c"] * (n + par["d"])
            if form == "difference_squares":
                return (par["a"] * n + par["b"]) ** 2 - (par["a"] * n - par["b"]) ** 2
            if form == "shifted_squares":
                return (n + par["a"]) ** 2 - (n - par["b"]) ** 2
            if form == "constant_difference":
                a, d = par["a"], par["d"]
                return (n + a) ** 2 - (n + a - d) * (n + a + d)
            if form == "consecutive_gap":
                return (n + par["d"]) ** 2 - n ** 2
            return {
                "odd_square": lambda: (2 * n + 1) ** 2,
                "even_product": lambda: 2 * n * (2 * n + 2),
                "odd_squares_sum": lambda: (2 * n - 1) ** 2 + (2 * n + 1) ** 2,
                "cube_minus": lambda: n ** 3 - n,
                "three_squares": lambda: (n - 1) ** 2 + n ** 2 + (n + 1) ** 2,
                "odd_product_plus": lambda: (2 * n - 1) * (2 * n + 1) + 1,
            }[par["statement"]]()

        expanded = [int(c) for c in answer["expanded"]]
        claim = answer["claim"]
        for n in range(-25, 26):
            value = direct(n)
            require(sum(c * n ** i for i, c in enumerate(expanded)) == value,
                    "Stated expansion disagrees at n = {}".format(n))
            if claim[0] == "multiple":
                require((value - claim[2]) % claim[1] == 0,
                        "Claim fails at n = {}".format(n))
            elif claim[0] == "constant":
                require(value == claim[1] > 0, "Not the stated positive constant")
        return True