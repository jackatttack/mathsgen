"""Applied forms for inverse proportion (ratio.proportion.inverse): workers.

L1 workers_days      n workers take d days; how long would m workers take?
L2 workers_deadline  n workers take d days (halves allowed); show that W
                     workers finish in less than T days
L3 workers_join      n workers start a d-day job; j more join after k days;
                     how many days does the job take altogether?
L4 workers_needed    the job must be done in T days; least number of workers

These live in the InverseProportion source, so the registered family
ratio.proportion.direct shows them through its dispatcher. Bare questions
store a wording dict under "context", so applied questions are recognised
by is_applied(): a context string naming one of the CONTEXTS below.

check() counts worker-days with exact Fractions. validate_independently()
solves the worker-day equations with SymPy, or searches for the least
number of workers.
"""
from fractions import Fraction

from .core import Content, rational_text, require
from . import worded
from .worded import NAMES, Context, quantity


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {1: 0.5, 2: 0.5, 3: 0.5, 4: 0.5}
MARKS = {1: 3, 2: 3, 3: 4, 4: 4}
WORKING_LINES = {1: 4, 2: 5, 3: 6, 4: 6}

JOBS = (("builders", "build a wall"), ("painters", "paint a school"),
        ("cleaners", "clean an office block"), ("gardeners", "clear a park"))


def context_share(level):
    return CONTEXT_SHARE.get(level, 0.0)


def is_applied(question):
    p = question.parameters
    return isinstance(p, dict) and isinstance(p.get("context"), str) \
        and p.get("context") in CONTEXTS


# ------------------------------------------------------------------ helpers

def days_text(value):
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    require(value.denominator == 2, "Days are whole or halves")
    return "{}.5".format(value.numerator // 2)


def two_places(value):
    scaled = Fraction(value) * 100
    whole, rest = divmod(int((scaled * 2 + 1) // 2), 100)
    return "{}.{:02d}".format(whole, rest)


def whole_in(value, low, high, message):
    require(type(value) is int and low <= value <= high, message)
    return value


def job(p):
    whole_in(p["job"], 0, len(JOBS) - 1, "Unknown job")
    return JOBS[p["job"]]


def stored_days(p, key, low, high):
    value = Fraction(p[key])
    require(p[key] == rational_text(value) and value.denominator in (1, 2)
            and low <= value <= high, "Days out of bounds")
    return value


# --------------------------------------------------- L1: how long would it take

def build_days(rng):
    workers, new = rng.sample(range(2, 13), 2)
    return {"context": "workers_days", "job": rng.randrange(len(JOBS)),
            "workers": workers, "days": rng.randint(3, 30), "new_workers": new}


def check_days(p):
    job(p)
    workers = whole_in(p["workers"], 2, 12, "Workers out of bounds")
    days = whole_in(p["days"], 3, 30, "Days out of bounds")
    new = whole_in(p["new_workers"], 2, 12, "Workers out of bounds")
    require(new != workers, "A different number of workers")
    time = Fraction(workers * days, new)
    require(time.denominator == 1, "Whole days")
    return int(time)


def parts_days(p):
    time = check_days(p)
    people, task = job(p)
    text = ("{n} {people} take {d} days to {task}. Working at the same rate, how many "
            "days would {m} {people} take?").format(
        n=p["workers"], people=people, d=p["days"], task=task, m=p["new_workers"])
    return {"prompt": Content(text), "answer": quantity(time, "days"),
            "answer_display": Content("{} days".format(time))}


# ----------------------------------------------- L2: show it beats a deadline

def build_deadline(rng):
    workers = rng.randint(3, 8)
    days = Fraction(rng.randint(12, 40), 2)
    available = workers + rng.randint(3, 9)
    time = workers * days / available
    return {"context": "workers_deadline", "job": rng.randrange(len(JOBS)),
            "name": rng.choice(NAMES), "workers": workers, "days": rational_text(days),
            "available": available, "limit": int(time) + 1}


def check_deadline(p):
    job(p)
    require(p["name"] in NAMES, "Unknown name")
    workers = whole_in(p["workers"], 2, 10, "Workers out of bounds")
    days = stored_days(p, "days", 3, 30)
    available = whole_in(p["available"], workers + 1, 25, "Available workers")
    limit = whole_in(p["limit"], 1, 40, "Deadline out of bounds")
    time = workers * days / available
    require(limit - time >= Fraction(1, 10), "The deadline must be beaten clearly")
    require(limit == int(time) + 1, "The deadline is the next whole day")
    return time


def parts_deadline(p):
    time = check_deadline(p)
    people, task = job(p)
    text = ("{name} has {w} {people} available for a job. {name} knows that {n} {people} "
            "would take {d} days to {task}. Show that {name} has enough {people} to finish "
            "the job in less than {t} days.").format(
        name=p["name"], w=p["available"], people=people, n=p["workers"],
        d=days_text(Fraction(p["days"])), task=task, t=p["limit"])
    work = p["workers"] * Fraction(p["days"])
    shown = ("{n} × {d} = {work} worker-days. {work} ÷ {w} = {t} days (2 d.p.), which is "
             "less than {limit} days.").format(
        n=p["workers"], d=days_text(Fraction(p["days"])), work=days_text(work),
        w=p["available"], t=two_places(time), limit=p["limit"])
    return {"prompt": Content(text),
            "answer": {"kind": "show", "days": rational_text(time), "limit": p["limit"]},
            "answer_display": Content(shown)}


# --------------------------------------------- L3: more workers join partway

def build_join(rng):
    workers, extra = rng.randint(2, 8), rng.randint(1, 6)
    left = (workers + extra) * rng.randint(1, 6) // workers
    after = rng.randint(1, 8)
    return {"context": "workers_join", "job": rng.randrange(len(JOBS)), "workers": workers,
            "days": after + max(left, 1), "after": after, "extra": extra}


def check_join(p):
    job(p)
    workers = whole_in(p["workers"], 2, 10, "Workers out of bounds")
    days = whole_in(p["days"], 3, 40, "Days out of bounds")
    after = whole_in(p["after"], 1, days - 1, "Join day out of bounds")
    extra = whole_in(p["extra"], 1, 8, "Extra workers out of bounds")
    remaining = Fraction(workers * (days - after), workers + extra)
    require(remaining.denominator == 1, "The rest of the job takes whole days")
    return after + int(remaining)


def parts_join(p):
    total = check_join(p)
    people, task = job(p)
    joining = ("1 more {} joins".format(people[:-1]) if p["extra"] == 1
               else "{} more {} join".format(p["extra"], people))
    waited = "1 day" if p["after"] == 1 else "{} days".format(p["after"])
    text = ("{n} {people} would take {d} days to {task}. They start the job, and after "
            "{waited}, {joining} them. Working at the same rate, how many days does the "
            "job take altogether?").format(
        n=p["workers"], people=people, d=p["days"], task=task, waited=waited,
        joining=joining)
    return {"prompt": Content(text), "answer": quantity(total, "days"),
            "answer_display": Content("{} days".format(total))}


# ------------------------------------------------ L4: least number of workers

def build_needed(rng):
    workers, days = rng.randint(3, 10), rng.randint(8, 30)
    return {"context": "workers_needed", "job": rng.randrange(len(JOBS)),
            "workers": workers, "days": days, "limit": rng.randint(3, days - 2)}


def check_needed(p):
    job(p)
    workers = whole_in(p["workers"], 2, 12, "Workers out of bounds")
    days = whole_in(p["days"], 5, 30, "Days out of bounds")
    limit = whole_in(p["limit"], 2, days - 1, "Deadline out of bounds")
    exact = Fraction(workers * days, limit)
    require(exact.denominator != 1, "The answer should need rounding up")
    needed = int(exact) + 1
    require(needed > workers, "More workers must be needed")
    return needed


def parts_needed(p):
    needed = check_needed(p)
    people, task = job(p)
    text = ("{n} {people} take {d} days to {task}. The job must now be finished in {t} "
            "days. Working at the same rate, what is the least number of {people} "
            "needed?").format(n=p["workers"], people=people, d=p["days"], task=task,
                              t=p["limit"])
    return {"prompt": Content(text), "answer": quantity(needed, people),
            "answer_display": Content("{} {}".format(needed, people))}


# ----------------------------------------------------------------- registry

CONTEXTS = {
    "workers_days": Context(
        1, frozenset({"context", "job", "workers", "days", "new_workers"}),
        build_days, check_days, parts_days, None),
    "workers_deadline": Context(
        2, frozenset({"context", "job", "name", "workers", "days", "available", "limit"}),
        build_deadline, check_deadline, parts_deadline, None),
    "workers_join": Context(
        3, frozenset({"context", "job", "workers", "days", "after", "extra"}),
        build_join, check_join, parts_join, None),
    "workers_needed": Context(
        4, frozenset({"context", "job", "workers", "days", "limit"}),
        build_needed, check_needed, parts_needed, None),
}


# ------------------------------------------------ generate and validate

def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    """Worker-day equations with SymPy; the least workforce by searching."""
    import sympy
    p, answer = q.parameters, q.answer
    t = sympy.Symbol("t", positive=True)
    work = p["workers"] * sympy.Rational(p["days"])
    if p["context"] == "workers_days":
        found = sympy.solve(sympy.Eq(p["new_workers"] * t, work), t)
        require(found == [sympy.Rational(answer["value"])], "Independent time disagrees")
    elif p["context"] == "workers_deadline":
        found = sympy.solve(sympy.Eq(p["available"] * t, work), t)
        require(found == [sympy.Rational(answer["days"])] and found[0] < p["limit"],
                "Independent deadline check disagrees")
    elif p["context"] == "workers_join":
        found = sympy.solve(sympy.Eq(p["workers"] * p["after"]
                                     + (p["workers"] + p["extra"]) * t, work), t)
        require(len(found) == 1 and p["after"] + found[0] == sympy.Rational(answer["value"]),
                "Independent total time disagrees")
    else:
        crew = 1
        while crew * p["limit"] < work:
            crew += 1
        require(crew == sympy.Rational(answer["value"]), "Independent workforce disagrees")
    return True