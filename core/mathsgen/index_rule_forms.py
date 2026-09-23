"""Comparison and two-step exact index questions for number.indices.rules."""
from fractions import Fraction

from .core import Content, LayoutHint, Question, rational_text, rational_tex, require
from .index_rules import exact_value, integer_root, power_text
from .worded import rich_prompt


FORMS = {"compare_roots": 3, "combined_powers": 4}
ROOT_LIMITS = {2: 5, 3: 5, 4: 4}
FRACTIONAL_NUMERATORS = {2: 3, 3: 2, 4: 3}


def build(rng, form):
    if form == "compare_roots":
        first_d, second_d = rng.choice((2, 3, 4)), rng.choice((2, 3, 4))
        first_root = rng.randint(2, ROOT_LIMITS[first_d])
        second_root = (
            first_root if rng.random() < 0.3
            and first_root <= ROOT_LIMITS[second_d]
            else rng.randint(2, ROOT_LIMITS[second_d])
        )
        return {
            "form": form,
            "first": {"base": first_root ** first_d,
                      "exponent": rational_text(Fraction(1, first_d))},
            "second": {"base": second_root ** second_d,
                       "exponent": rational_text(Fraction(1, second_d))},
        }
    first_d, second_d = rng.choice((2, 3, 4)), rng.choice((2, 3))
    first_root, second_root = rng.randint(2, 4), rng.randint(2, 5)
    return {
        "form": form,
        "first": {"base": first_root ** first_d,
                  "exponent": rational_text(Fraction(
                      FRACTIONAL_NUMERATORS[first_d], first_d
                  ))},
        "second": {"base": second_root ** second_d,
                   "exponent": rational_text(Fraction(-1, second_d))},
        "operator": rng.choice(("multiply", "divide")),
    }


def checked_power(power, role, form):
    require(isinstance(power, dict) and set(power) == {"base", "exponent"},
            "Invalid index power")
    base = power["base"]
    require(type(base) is int and base >= 2, "Invalid base")
    exponent = Fraction(power["exponent"])
    require(power["exponent"] == rational_text(exponent),
            "Non-canonical exponent")
    denominator = exponent.denominator
    if form == "compare_roots":
        require(denominator in ROOT_LIMITS and exponent.numerator == 1,
                "Comparison needs unit fractional indices")
        limit = ROOT_LIMITS[denominator]
    elif role == "first":
        require(denominator in FRACTIONAL_NUMERATORS
                and exponent.numerator == FRACTIONAL_NUMERATORS[denominator],
                "Expected a non-unit fractional index")
        limit = 4
    else:
        require(denominator in (2, 3) and exponent.numerator == -1,
                "Expected a negative unit fractional index")
        limit = 5
    root = integer_root(base, denominator)
    require(2 <= root <= limit, "Root outside difficulty bounds")
    return exact_value(base, exponent)


def check(p):
    form = p.get("form")
    require(form in FORMS, "Unknown index form")
    expected = ({"form", "first", "second", "operator"}
                if form == "combined_powers" else
                {"form", "first", "second"})
    require(set(p) == expected, "Unexpected index parameters")
    first = checked_power(p["first"], "first", form)
    second = checked_power(p["second"], "second", form)
    if form == "compare_roots":
        require(p["first"] != p["second"],
                "Do not compare identical powers")
        return first, second
    require(p["operator"] in ("multiply", "divide"), "Unknown operation")
    result = first * second if p["operator"] == "multiply" else first / second
    require(result > 0 and result.numerator <= 1000
            and result.denominator <= 1000, "Combined answer outside bounds")
    return first, second


def parts(p):
    first, second = check(p)
    first_power = p["first"]
    second_power = p["second"]
    first_plain = power_text(first_power["base"], Fraction(first_power["exponent"]))
    second_plain = power_text(second_power["base"], Fraction(second_power["exponent"]))
    first_tex = power_text(first_power["base"], Fraction(first_power["exponent"]), True)
    second_tex = power_text(second_power["base"], Fraction(second_power["exponent"]), True)
    if p["form"] == "compare_roots":
        prompt = rich_prompt((
            "Compare ", (first_tex, first_plain), " and ",
            (second_tex, second_plain),
            ". Which is greater, or are they equal? Give the difference "
            "between their exact values.",
        ))
        greater = "first" if first > second else "second" if second > first else "equal"
        difference = abs(first - second)
        answer = {"kind": "index_comparison", "greater": greater,
                  "difference": rational_text(difference)}
        if greater == "equal":
            display = Content("They are equal; the difference is 0.")
        else:
            display = Content(
                "The {} is greater by {}.".format(
                    greater, rational_text(difference)
                )
            )
        return prompt, answer, display

    symbol = "×" if p["operator"] == "multiply" else "÷"
    tex_symbol = r"\times" if p["operator"] == "multiply" else r"\div"
    instruction = "Work out the exact value, showing how you use the indices."
    prompt = Content(
        "{} {} {} {}".format(instruction, first_plain, symbol, second_plain),
        "{} {} {}".format(first_tex, tex_symbol, second_tex),
        display_text=instruction,
    )
    result = first * second if p["operator"] == "multiply" else first / second
    answer = {"kind": "exact_value", "value": rational_text(result)}
    return prompt, answer, Content(rational_text(result), rational_tex(result))


def generate(generator, context, form):
    rng = context.rng
    for _ in range(100):
        p = build(rng, form)
        try:
            check(p)
        except ValueError:
            continue
        break
    else:
        raise ValueError("Could not construct an index follow-up")
    prompt, answer, display = parts(p)
    info = generator.info
    q = Question(
        id=context.identity, generator_id=info.id, generator_version=info.version,
        topic=info.topic, subtopic=info.subtopic, difficulty=context.difficulty,
        seed=context.seed, settings=context.settings, prompt=prompt,
        answer=answer, answer_display=display, worked_solution=(),
        marks=3 if form == "compare_roots" else 4, tags=info.tags,
        layout_hint=LayoutHint(
            working_lines=4 if form == "compare_roots" else 5
        ),
        parameters=p,
    )
    generator.validate(q)
    return q


def validate(generator, q):
    p = q.parameters
    form = p.get("form")
    require(q.generator_id == generator.info.id
            and q.generator_version == generator.info.version
            and q.settings == {} and q.difficulty == FORMS.get(form),
            "Wrong index family or level")
    prompt, answer, display = parts(p)
    require(q.prompt == prompt and q.answer == answer
            and q.answer_display == display, "Incorrect index question")
    require(q.marks == (3 if form == "compare_roots" else 4)
            and q.layout_hint.working_lines ==
            (4 if form == "compare_roots" else 5),
            "Marks or working space mismatch")
    require(q.visual_assets("questions") == ()
            and q.visual_assets("answers") == (),
            "Unexpected index visual")
    return True


def validate_independently(q):
    """Evaluate both printed powers directly with SymPy."""
    import sympy
    p = q.parameters
    first, second = (
        sympy.simplify(
            sympy.Integer(p[key]["base"]) ** sympy.Rational(p[key]["exponent"])
        )
        for key in ("first", "second")
    )
    require(first.is_rational and second.is_rational,
            "Expected exact rational powers")
    if p["form"] == "compare_roots":
        greater = "first" if first > second else "second" if second > first else "equal"
        require(q.answer == {
            "kind": "index_comparison", "greater": greater,
            "difference": rational_text(Fraction(abs(first - second))),
        }, "Independent index comparison disagrees")
    else:
        expected = (first * second if p["operator"] == "multiply"
                    else first / second)
        require(expected == sympy.Rational(q.answer["value"]),
                "Independent two-step index calculation disagrees")
    return True