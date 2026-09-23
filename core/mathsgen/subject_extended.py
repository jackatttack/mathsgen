"""Fractional and square/root tasks within the changing-subject family."""
from .core import Content, LayoutHint, Question, require

FORMS = {
    3: ("fraction", "reciprocal"),
    4: ("square", "root"),
}


def contents(p):
    form, k = p["form"], p["k"]
    r, a, b = p["letters"]
    instruction = "Make x the subject. All other letters represent positive numbers."
    if form == "fraction":
        equation = "{} = ({}x + {})/{}".format(r, k, a, b)
        tex = r + r" = \frac{" + str(k) + "x + " + a + "}{" + b + "}"
        answer = "({}*{}-{})/{}".format(b, r, a, k)
        plain = "x = ({}{} - {})/{}".format(b, r, a, k)
        result = r"x = \frac{" + b + r + " - " + a + "}{" + str(k) + "}"
    elif form == "reciprocal":
        instruction += " The denominator in the formula is nonzero."
        equation = "{} = {}/({}x + {})".format(r, a, k, b)
        tex = r + r" = \frac{" + a + "}{" + str(k) + "x + " + b + "}"
        answer = "({}-{}*{})/({}*{})".format(a, b, r, k, r)
        plain = "x = ({} - {}{})/({}{})".format(a, b, r, k, r)
        result = r"x = \frac{" + a + " - " + b + r + "}{" + str(k) + r + "}"
    elif form == "square":
        instruction += " Take x >= 0 and assume {}{} >= {}.".format(b, r, a)
        equation = "{} = ({}x^2 + {})/{}".format(r, k, a, b)
        tex = r + r" = \frac{" + str(k) + "x^2 + " + a + "}{" + b + "}"
        answer = "sqrt(({}*{}-{})/{})".format(b, r, a, k)
        plain = "x = sqrt(({}{} - {})/{})".format(b, r, a, k)
        result = r"x = \sqrt{\frac{" + b + r + " - " + a + "}{" + str(k) + "}}"
    else:
        equation = "{} = sqrt(({}x + {})/{})".format(r, k, a, b)
        tex = r + r" = \sqrt{\frac{" + str(k) + "x + " + a + "}{" + b + "}}"
        answer = "({}*{}**2-{})/{}".format(b, r, a, k)
        plain = "x = ({}{}^2 - {})/{}".format(b, r, a, k)
        result = r"x = \frac{" + b + r + "^2 - " + a + "}{" + str(k) + "}"
    return (
        Content(instruction + " " + equation, tex, display_text=instruction),
        Content(plain, result),
        {"kind": "subject_formula", "subject": "x", "expression": answer},
    )


def generate(generator, context):
    from .changing_subject import LETTERS
    rng = context.rng
    p = {
        "form": rng.choice(FORMS[context.difficulty]),
        "k": rng.randint(2, 9),
        "letters": rng.sample(LETTERS, 3),
    }
    prompt, display, answer = contents(p)
    info = generator.info
    q = Question(
        id=context.identity, generator_id=info.id, generator_version=info.version,
        topic=info.topic, subtopic=info.subtopic,
        difficulty=context.difficulty, seed=context.seed, settings=context.settings,
        prompt=prompt, answer=answer, answer_display=display,
        worked_solution=(), marks=3 if context.difficulty == 3 else 4,
        tags=info.tags, layout_hint=LayoutHint(working_lines=7), parameters=p,
    )
    generator.validate(q)
    return q


def validate(generator, q):
    from .changing_subject import LETTERS
    require(q.generator_id == generator.info.id, "Generator mismatch")
    require(q.generator_version == generator.info.version, "Version mismatch")
    require(type(q.difficulty) is int and q.difficulty in FORMS, "Invalid level")
    require(q.settings == {}, "Unsupported settings")
    p = q.parameters
    require(set(p) == {"form", "k", "letters"}, "Unexpected parameters")
    require(p["form"] in FORMS[q.difficulty], "Wrong task for difficulty")
    require(type(p["k"]) is int and 2 <= p["k"] <= 9, "Coefficient bounds")
    require(isinstance(p["letters"], list) and len(p["letters"]) == 3
            and all(s in LETTERS for s in p["letters"])
            and len(set(p["letters"])) == 3, "Invalid formula letters")
    prompt, display, answer = contents(p)
    require(q.prompt == prompt, "Prompt or domain mismatch")
    require(q.answer == answer, "Incorrect subject formula")
    require(q.answer_display == display, "Answer display mismatch")
    return True


def validate_independently(q):
    import sympy as sp
    p = q.parameters
    symbols = {s: sp.Symbol(s, positive=True) for s in p["letters"]}
    r, a, b = (symbols[s] for s in p["letters"])
    x = sp.Symbol("x", real=True)
    k = sp.Integer(p["k"])
    form = p["form"]
    if form == "fraction":
        rhs = (k*x + a)/b
    elif form == "reciprocal":
        rhs = a/(k*x + b)
    elif form == "square":
        rhs = (k*x**2 + a)/b
    else:
        rhs = sp.sqrt((k*x + a)/b)
    proposed = sp.sympify(q.answer["expression"], locals=dict(symbols, sqrt=sp.sqrt))
    require(sp.simplify(rhs.subs(x, proposed) - r) == 0,
            "Independent substitution failed")
    if form == "reciprocal":
        require(sp.simplify((k*x + b).subs(x, proposed)) == a/r,
                "Original denominator restriction failed")
    if form == "square":
        # The explicit nonnegative branch and br >= a exclude the negative root.
        require(proposed == sp.sqrt((b*r-a)/k), "Wrong square-root branch")
    return True