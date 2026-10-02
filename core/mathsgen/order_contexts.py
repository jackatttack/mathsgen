"""Applied forms for number.operations.order: brackets and misconceptions.

L1 insert_brackets       three numbers: place one pair of brackets so the
                         calculation equals the target
L2 spot_error            a worked answer that added first; explain and correct
L3 insert_brackets_four  four numbers, including division
L4 power_error           squaring or left-to-right mistakes; explain and correct

Bracket puzzles are built from a chosen placement, then checked by trying
every placement: exactly one may reach the target, and it must differ from
the unbracketed value. Error forms render the correct and the mistaken
calculation from templates and evaluate both exactly.

check() uses number_operations' own rendering and exact evaluation;
solve() re-parses the displayed text with SymPy and, for bracket puzzles,
re-checks that the placement is unique.
"""
from collections import namedtuple

from .core import Content, rational_text, require
from . import rich_blocks as rb
from . import worded
from .worded import NAMES, Context
from .number_operations import evaluate_display, python_form, render, tex_of


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {1: 0.3, 2: 0.3, 3: 0.35, 4: 0.35}
MARKS = {1: 1, 2: 2, 3: 2, 4: 2}
WORKING_LINES = {1: 2, 2: 3, 3: 3, 4: 3}

TARGET_LOW, TARGET_HIGH = 1, 200
NUMBER_COUNTS = {"insert_brackets": 3, "insert_brackets_four": 4}
OPERATORS = {"insert_brackets": ("+", "-", "×"),
             "insert_brackets_four": ("+", "-", "×", "÷")}

# plain: the calculation; wrong: how the mistake works it out;
# mistake: completes "<name> ..." in the answer.
ErrorForm = namedtuple("ErrorForm", "plain wrong mistake")
ERROR_FORMS = {
    "add_multiply": ErrorForm(
        "{a} + {b} × {c}", "({a} + {b}) × {c}", "added before multiplying"),
    "subtract_add": ErrorForm(
        "{a} - {b} + {c}", "{a} - ({b} + {c})",
        "added before subtracting; + and - are worked from left to right"),
    "multiply_square": ErrorForm(
        "{a} × {b}^2", "({a} × {b})^2", "multiplied before squaring"),
    "add_square": ErrorForm(
        "{a} + {b}^2", "({a} + {b})^2", "added before squaring"),
    "divide_multiply": ErrorForm(
        "{a} ÷ {b} × {c}", "{a} ÷ ({b} × {c})",
        "multiplied before dividing; × and ÷ are worked from left to right"),
}
ERROR_CONTEXT_FORMS = {
    "spot_error": ("add_multiply", "subtract_add"),
    "power_error": ("multiply_square", "add_square", "divide_multiply"),
}


def context_share(level):
    return CONTEXT_SHARE.get(level, 0.0)


# ------------------------------------------------------ bracket puzzles

def calculation(numbers, operators, span=None):
    """Plain text of the calculation, with brackets around span if given."""
    pieces = []
    for index, number in enumerate(numbers):
        text = str(number)
        if span is not None and index == span[0]:
            text = "(" + text
        if span is not None and index == span[1]:
            text = text + ")"
        if index:
            pieces.append(operators[index - 1])
        pieces.append(text)
    return " ".join(pieces)


def placements(count):
    """Every pair of brackets around two or more numbers, except all of them."""
    return [(start, end) for start in range(count) for end in range(start + 1, count)
            if (start, end) != (0, count - 1)]


def value_or_none(plain):
    try:
        value = evaluate_display(plain)
    except ValueError:
        return None
    return value if value.denominator == 1 else None


def puzzle(p):
    """(numbers, operators, span) after checking their shape."""
    count = NUMBER_COUNTS[p["context"]]
    numbers, operators, span = p["numbers"], p["operators"], p["span"]
    require(isinstance(numbers, list) and len(numbers) == count, "Number count")
    require(all(type(n) is int and 1 <= n <= 12 for n in numbers), "Numbers out of bounds")
    require(isinstance(operators, list) and len(operators) == count - 1, "Operator count")
    require(all(o in OPERATORS[p["context"]] for o in operators), "Unknown operator")
    require(isinstance(span, list) and tuple(span) in placements(count), "Invalid brackets")
    return numbers, operators, tuple(span)


def check_insert(p):
    numbers, operators, span = puzzle(p)
    plain_value = value_or_none(calculation(numbers, operators))
    require(plain_value is not None, "The calculation must work out exactly")
    target = value_or_none(calculation(numbers, operators, span))
    require(target is not None and TARGET_LOW <= target <= TARGET_HIGH, "Target out of bounds")
    require(target != plain_value, "The brackets must change the answer")
    reaching = [placement for placement in placements(len(numbers))
                if value_or_none(calculation(numbers, operators, placement)) == target]
    require(reaching == [span], "Exactly one placement may reach the target")
    return int(target)


def build_insert(rng, context):
    count = NUMBER_COUNTS[context]
    operators = [rng.choice(OPERATORS[context]) for _ in range(count - 1)]
    return {
        "context": context,
        "numbers": [rng.randint(2, 12 if count == 4 else 9) for _ in range(count)],
        "operators": operators,
        "span": list(rng.choice(placements(count))),
    }


def parts_insert(p):
    target = check_insert(p)
    numbers, operators, span = puzzle(p)
    shown = calculation(numbers, operators) + " = " + str(target)
    solved = calculation(numbers, operators, span) + " = " + str(target)
    lead = "Insert one pair of brackets to make this calculation correct."
    return {
        "prompt": Content(lead + " " + shown,
                          blocks=(rb.prose(lead), rb.equation(tex_of(shown), shown))),
        "answer": {"kind": "brackets", "calculation": solved, "value": rational_text(target)},
        "answer_display": Content(solved, tex_of(solved)),
    }


def solve_insert(p, sympy):
    numbers, operators, span = p["numbers"], p["operators"], tuple(p["span"])

    def evaluated(placement):
        return sympy.sympify(python_form(calculation(numbers, operators, placement)))

    target = evaluated(span)
    reaching = [placement for placement in placements(len(numbers))
                if evaluated(placement) == target]
    require(reaching == [span], "SymPy finds another placement reaching the target")
    return target


# ---------------------------------------------------- misconception forms

def build_error(rng, context):
    form = rng.choice(ERROR_CONTEXT_FORMS[context])
    if form == "add_multiply":
        values = {"a": rng.randint(2, 20), "b": rng.randint(2, 9), "c": rng.randint(2, 9)}
    elif form == "subtract_add":
        values = {"a": rng.randint(15, 40), "b": rng.randint(2, 12), "c": rng.randint(2, 12)}
    elif form in ("multiply_square", "add_square"):
        values = {"a": rng.randint(2, 9), "b": rng.randint(2, 9)}
    else:
        b, c = rng.randint(2, 6), rng.randint(2, 5)
        values = {"a": b * c * rng.randint(1, 5), "b": b, "c": c}
    return {"context": context, "form": form, "name": rng.choice(NAMES), "values": values}


def check_error(p):
    require(p["form"] in ERROR_CONTEXT_FORMS[p["context"]], "Form outside this level")
    require(p["name"] in NAMES, "Unknown name")
    form = ERROR_FORMS[p["form"]]
    correct = evaluate_display(render(form.plain, p["values"]))
    wrong = evaluate_display(render(form.wrong, p["values"]))
    for value in (correct, wrong):
        require(value.denominator == 1 and 1 <= value <= 999, "Value out of bounds")
    require(correct != wrong, "The mistake must change the answer")
    return int(correct), int(wrong)


def parts_error(p):
    correct, wrong = check_error(p)
    plain = render(ERROR_FORMS[p["form"]].plain, p["values"])
    prompt = worded.rich_prompt(
        (p["name"] + " works out ", (tex_of(plain), plain), " and gets {}.".format(wrong)),
        ("Explain the mistake and work out the correct answer.",),
    )
    explanation = "{} {}. The correct answer is {}.".format(
        p["name"], ERROR_FORMS[p["form"]].mistake, correct)
    return {
        "prompt": prompt,
        "answer": {"kind": "rational", "value": rational_text(correct)},
        "answer_display": Content(explanation),
    }


def solve_error(p, sympy):
    return sympy.sympify(python_form(render(ERROR_FORMS[p["form"]].plain, p["values"])))


# ----------------------------------------------------------------- registry

PUZZLE_KEYS = frozenset({"context", "numbers", "operators", "span"})
ERROR_KEYS = frozenset({"context", "form", "name", "values"})

CONTEXTS = {
    "insert_brackets": Context(
        1, PUZZLE_KEYS, lambda rng: build_insert(rng, "insert_brackets"),
        check_insert, parts_insert, solve_insert),
    "spot_error": Context(
        2, ERROR_KEYS, lambda rng: build_error(rng, "spot_error"),
        check_error, parts_error, solve_error),
    "insert_brackets_four": Context(
        3, PUZZLE_KEYS, lambda rng: build_insert(rng, "insert_brackets_four"),
        check_insert, parts_insert, solve_insert),
    "power_error": Context(
        4, ERROR_KEYS, lambda rng: build_error(rng, "power_error"),
        check_error, parts_error, solve_error),
}


# ------------------------------------------------ generate and validate

def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    import sympy
    p = q.parameters
    expected = CONTEXTS[p["context"]].solve(p, sympy)
    require(sympy.Rational(q.answer["value"]) == expected,
            "Independent evaluation disagrees")
    return True