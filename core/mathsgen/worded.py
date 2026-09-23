"""Shared machinery for worded forms mixed into existing generators.

A host module supplies CONTEXTS {name: Context}, MARKS {level: marks} and
WORKING_LINES {level: lines}. Its generator draws once from the RNG to
decide whether a question is worded, then dispatches here. Worded
questions are recognised afterwards by the "context" key in parameters.

Context fields:
    level   the difficulty this context belongs to
    keys    the exact set of parameter names
    build   rng -> parameters (may break the rules; generation retries)
    check   parameters -> solution, or raises ValueError
    parts   parameters -> dict(prompt, answer, answer_display)
    solve   the host module's independent check (its contract is local)
"""
from collections import namedtuple
from fractions import Fraction

from .core import Content, LayoutHint, Question, rational_text, require
from . import rich_blocks as rb


Context = namedtuple("Context", "level keys build check parts solve")

BUILD_ATTEMPTS = 2000


def is_worded(question):
    return isinstance(question.parameters, dict) and "context" in question.parameters


def generate(generator, context, contexts, marks, working_lines):
    rng, level = context.rng, context.difficulty
    names = sorted(name for name, spec in contexts.items() if spec.level == level)
    require(bool(names), "No worded contexts at this level")
    spec = contexts[rng.choice(names)]
    for _ in range(BUILD_ATTEMPTS):
        p = spec.build(rng)
        try:
            spec.check(p)
        except ValueError:
            continue
        break
    else:
        raise ValueError("Could not construct a suitable worded problem")
    parts = spec.parts(p)
    info = generator.info
    q = Question(
        id=context.identity, generator_id=info.id, generator_version=info.version,
        topic=info.topic, subtopic=info.subtopic, difficulty=level,
        seed=context.seed, settings=context.settings,
        prompt=parts["prompt"], answer=parts["answer"],
        answer_display=parts["answer_display"],
        worked_solution=(), marks=marks[level], tags=info.tags,
        layout_hint=LayoutHint(working_lines=working_lines[level]),
        parameters=p,
    )
    generator.validate(q)
    return q


def validate(generator, q, contexts, marks, working_lines):
    require(q.generator_id == generator.info.id, "Generator mismatch")
    require(q.generator_version == generator.info.version, "Version mismatch")
    require(q.settings == {}, "Unsupported settings")
    p = q.parameters
    require(isinstance(p, dict) and p.get("context") in contexts, "Unknown context")
    spec = contexts[p["context"]]
    require(q.difficulty == spec.level, "Context used at the wrong level")
    require(set(p) == spec.keys, "Unexpected parameters")
    spec.check(p)
    parts = spec.parts(p)
    require(q.prompt == parts["prompt"], "Prompt mismatch")
    require(q.answer == parts["answer"], "Answer mismatch")
    require(q.answer_display == parts["answer_display"], "Displayed answer mismatch")
    require(q.marks == marks[q.difficulty], "Marks mismatch")
    require(q.layout_hint.working_lines == working_lines[q.difficulty],
            "Working space mismatch")
    return True


# ------------------------------------------------------ prose helpers

def article(noun):
    return ("an " if noun[0] in "aeiou" else "a ") + noun


def sentence_case(text):
    return text[0].upper() + text[1:]


def rich_prompt(*sentences):
    """Each sentence is a sequence of prose strings and (tex, plain) pieces."""
    blocks, plain = [], []
    for pieces in sentences:
        runs, words = [], []
        for piece in pieces:
            if isinstance(piece, str):
                runs.append(rb.text(piece))
                words.append(piece)
            else:
                tex, fallback = piece
                runs.append(rb.maths(tex, fallback))
                words.append(fallback)
        blocks.append(rb.paragraph(*runs))
        plain.append("".join(words))
    return Content(" ".join(plain), blocks=tuple(blocks))


# ------------------------------------------------ shared story helpers

NAMES = (
    "Amir", "Beth", "Chloe", "Dev", "Ella", "Finn", "Grace", "Hassan",
    "Isla", "Jay", "Kofi", "Lena", "Maya", "Noah", "Omar", "Priya",
    "Rosa", "Sam", "Tariq", "Zara",
)


def exact(value):
    """Exact Fraction from an int, Fraction or SymPy rational."""
    return Fraction(str(value))


def integers(p, names):
    for name in names.split():
        require(type(p[name]) is int, "Expected an integer " + name)


def whole(value, low, high, message):
    """Require an exact whole number within bounds and return it as int."""
    value = exact(value)
    require(value.denominator == 1 and low <= value <= high, message)
    return int(value)


def distinct_names(*names):
    require(all(name in NAMES for name in names) and len(set(names)) == len(names),
            "Names must be distinct known names")


def quantity(value, unit):
    return {"kind": "quantity", "value": rational_text(exact(value)), "unit": unit}


def money_answer(pence):
    value = exact(pence)
    require(value.denominator == 1, "Money must be whole pence")
    return {"kind": "money", "currency": "GBP", "pence": int(value)}


def pounds(pence):
    """£1,234 or £12.50 from exact whole pence."""
    value = exact(pence)
    require(value.denominator == 1 and value >= 0, "Money must be whole pence")
    whole_pounds, rest = divmod(int(value), 100)
    text = "£{:,}".format(whole_pounds)
    return text if rest == 0 else text + ".{:02d}".format(rest)


def sympy_solve(sympy, equations, symbols):
    """Solve story equations with SymPy; require exactly one solution."""
    solutions = sympy.solve(equations, symbols, dict=True)
    require(len(solutions) == 1, "Story equations must have exactly one solution")
    return [exact(solutions[0][symbol]) for symbol in symbols]