"""IB AI SL arithmetic and geometric sequences in context.

Level 1 arithmetic term and sum; level 2 geometric term and sum (growth
or decay); level 3 the first term or total to pass a target; level 4 an
arithmetic plan racing a geometric plan to a daily distance.

Terms and sums are exact Fractions from the closed forms. Searches step
term by term; the independent check solves the same questions with a
quadratic or logarithms instead.
"""
from fractions import Fraction

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from . import common as ib


# --- Editable pools ---------------------------------------------------------
ROW_SEATS, ROW_STEPS, ROW_COUNTS = tuple(range(12, 31)), (1, 2, 3, 4), tuple(range(15, 41))
WEEK_START, WEEK_STEPS, WEEK_COUNTS = tuple(range(5, 21)), (1, 2, 3, 4, 5), tuple(range(20, 53))
GEOMETRIC = {
    "training": {"starts": tuple(range(2, 9)), "percents": ("5", "6", "8", "10", "12.5", "15"),
                 "counts": tuple(range(8, 21))},
    "sales": {"starts": tuple(range(120, 901, 20)), "percents": ("3", "4", "5", "6", "7.5", "8"),
              "counts": tuple(range(6, 19))},
    "bounce": {"starts": tuple(range(80, 241, 10)), "percents": ("60", "65", "70", "75", "80", "85"),
               "counts": tuple(range(4, 11))},
}
READ_START, READ_STEPS = tuple(range(5, 21)), (2, 3, 4, 5, 6)
FOLLOW_START, FOLLOW_PERCENTS = tuple(range(50, 501, 10)), ("5", "8", "10", "12", "15", "20")
RACE_STARTS = (2, 3, 4, 5, 6)
RACE_STEPS = ("1", "1.5", "2", "2.5", "3")
RACE_PERCENTS = ("8", "10", "12", "13", "15", "18", "20")
RACE_TARGETS = ("21.1", "25", "30", "42.2", "50")

LEVEL_FORMS = {1: ("rows", "savings"), 2: tuple(GEOMETRIC), 3: ("reading", "followers"),
               4: ("race",)}
FORM_KEYS = {
    "rows": {"form", "a", "d", "n"},
    "savings": {"form", "name", "currency", "a", "d", "n"},
    "training": {"form", "name", "a", "percent", "n"},
    "sales": {"form", "a", "percent", "n"},
    "bounce": {"form", "a", "percent", "n"},
    "reading": {"form", "name", "a", "d", "target"},
    "followers": {"form", "a", "percent", "target"},
    "race": {"form", "name_a", "name_b", "a", "d", "percent", "target"},
}


# ------------------------------------------------------------ mathematics

def arithmetic_term(a, d, n):
    return Fraction(a) + (n - 1) * Fraction(d)


def arithmetic_sum(a, d, n):
    return Fraction(n, 2) * (2 * Fraction(a) + (n - 1) * Fraction(d))


def ratio(form, percent):
    """Growth multiplier; a bounce keeps a percentage of the previous height."""
    if form == "bounce":
        return Fraction(percent) / 100
    return 1 + Fraction(percent) / 100


def geometric_term(a, r, n):
    return Fraction(a) * r ** (n - 1)


def geometric_sum(a, r, n):
    return Fraction(a) * (r ** n - 1) / (r - 1)


def first_index(passes, limit=200):
    """The first n = 1, 2, ... for which passes(n) is true."""
    for n in range(1, limit + 1):
        if passes(n):
            return n
    raise ValueError("Target never reached")


def reading_day(p):
    return first_index(lambda n: arithmetic_sum(p["a"], p["d"], n) > p["target"])


def followers_week(p):
    r = ratio("followers", p["percent"])
    return first_index(lambda n: geometric_term(p["a"], r, n) > p["target"])


def race_days(p):
    target, r = Fraction(p["target"]), ratio("race", p["percent"])
    day_a = first_index(lambda n: arithmetic_term(p["a"], p["d"], n) >= target)
    day_b = first_index(lambda n: geometric_term(p["a"], r, n) >= target)
    return day_a, day_b


def linear_rule(a, d):
    """u_n = dn + (a - d), for an arithmetic sequence with integer terms."""
    constant = a - d
    text = "u_n = {}n".format(d)
    if constant > 0:
        text += " + {}".format(constant)
    elif constant < 0:
        text += " - {}".format(-constant)
    return text


# ------------------------------------------------------------ generator

class SequenceModels(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.number.sequences",
        version=1,
        topic=ib.TOPIC,
        subtopic="sequences_and_series",
        title="Arithmetic and geometric sequences in context",
        difficulty_descriptions={
            1: "Arithmetic sequence in context: a term and a sum.",
            2: "Geometric growth or decay: a term and a sum.",
            3: "Write the nth term, then find when a total or term first passes a target.",
            4: "Arithmetic against geometric: who first reaches a daily target, and when.",
        },
        tags=ib.BASE_TAGS + ("sequences", "series", "arithmetic", "geometric"),
    )

    def expected_keys(self, parameters, level):
        form = parameters.get("form")
        require(form in LEVEL_FORMS[level], "Unknown form for this level")
        return FORM_KEYS[form]

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def candidate(self, level, rng):
        form = rng.choice(LEVEL_FORMS[level])
        if form == "rows":
            return {"form": form, "a": rng.choice(ROW_SEATS), "d": rng.choice(ROW_STEPS),
                    "n": rng.choice(ROW_COUNTS)}
        if form == "savings":
            return {"form": form, "name": rng.choice(ib.NAMES),
                    "currency": rng.choice(tuple(ib.CURRENCIES)), "a": rng.choice(WEEK_START),
                    "d": rng.choice(WEEK_STEPS), "n": rng.choice(WEEK_COUNTS)}
        if form in GEOMETRIC:
            pool = GEOMETRIC[form]
            p = {"form": form, "a": rng.choice(pool["starts"]),
                 "percent": rng.choice(pool["percents"]), "n": rng.choice(pool["counts"])}
            if form == "training":
                p["name"] = rng.choice(ib.NAMES)
            return p
        if form == "reading":
            p = {"form": form, "name": rng.choice(ib.NAMES), "a": rng.choice(READ_START),
                 "d": rng.choice(READ_STEPS)}
            total = arithmetic_sum(p["a"], p["d"], rng.randint(8, 30))
            p["target"] = int(total // 50) * 50
            return p
        if form == "followers":
            p = {"form": form, "a": rng.choice(FOLLOW_START),
                 "percent": rng.choice(FOLLOW_PERCENTS)}
            value = geometric_term(p["a"], ratio(form, p["percent"]), rng.randint(8, 30))
            step = 100 if value >= 1000 else 10
            p["target"] = int(value // step) * step
            return p
        name_a, name_b = rng.sample(ib.NAMES, 2)
        return {"form": form, "name_a": name_a, "name_b": name_b,
                "a": rng.choice(RACE_STARTS), "d": rng.choice(RACE_STEPS),
                "percent": rng.choice(RACE_PERCENTS), "target": rng.choice(RACE_TARGETS)}

    def check_rules(self, p, level):
        form = p["form"]
        require(form in LEVEL_FORMS[level], "Unknown form for this level")
        if form == "rows":
            require(p["a"] in ROW_SEATS and p["d"] in ROW_STEPS and p["n"] in ROW_COUNTS,
                    "Theatre outside pools")
        elif form == "savings":
            require(p["name"] in ib.NAMES and p["currency"] in ib.CURRENCIES, "Unknown context")
            require(p["a"] in WEEK_START and p["d"] in WEEK_STEPS and p["n"] in WEEK_COUNTS,
                    "Savings outside pools")
        elif form in GEOMETRIC:
            pool = GEOMETRIC[form]
            require(p["a"] in pool["starts"] and p["percent"] in pool["percents"]
                    and p["n"] in pool["counts"], "Geometric values outside pools")
            if form == "training":
                require(p["name"] in ib.NAMES, "Unknown name")
        elif form == "reading":
            require(p["name"] in ib.NAMES, "Unknown name")
            require(p["a"] in READ_START and p["d"] in READ_STEPS, "Reading outside pools")
            require(type(p["target"]) is int and p["target"] > 0 and p["target"] % 50 == 0,
                    "Target outside rules")
            day = reading_day(p)
            require(6 <= day <= 40, "Day outside bounds")
            require(all(arithmetic_sum(p["a"], p["d"], n) != p["target"] for n in range(1, day + 1)),
                    "Target hit exactly")
        elif form == "followers":
            require(p["a"] in FOLLOW_START and p["percent"] in FOLLOW_PERCENTS,
                    "Followers outside pools")
            require(type(p["target"]) is int and p["target"] > p["a"], "Target outside rules")
            week = followers_week(p)
            r = ratio(form, p["percent"])
            require(6 <= week <= 40, "Week outside bounds")
            require(all(geometric_term(p["a"], r, n) != p["target"] for n in range(1, week + 1)),
                    "Target hit exactly")
        else:
            require(p["name_a"] in ib.NAMES and p["name_b"] in ib.NAMES
                    and p["name_a"] != p["name_b"], "Names must differ")
            require(p["a"] in RACE_STARTS and p["d"] in RACE_STEPS
                    and p["percent"] in RACE_PERCENTS and p["target"] in RACE_TARGETS,
                    "Race outside pools")
            day_a, day_b = race_days(p)
            require(day_a != day_b, "Both reach the target on the same day")
            require(3 <= min(day_a, day_b) and max(day_a, day_b) <= 60, "Days outside bounds")

    def parts(self, p, level):
        form = p["form"]
        if form == "rows":
            last = arithmetic_term(p["a"], p["d"], p["n"])
            total = arithmetic_sum(p["a"], p["d"], p["n"])
            context = ["A lecture theatre has {} rows of seats. The first row has {} seats, and "
                       "each row after the first has {} more {} than the row in front of "
                       "it.".format(p["n"], p["a"], p["d"], "seat" if p["d"] == 1 else "seats")]
            return ib.assemble(context, [
                ib.part("a", "Find the number of seats in the last row.", 2,
                        "{} seats".format(ib.exact_text(last)), last),
                ib.part("b", "Find the total number of seats in the theatre.", 2,
                        "{} seats".format(ib.exact_text(total)), total),
            ])
        if form == "savings":
            cur, name = p["currency"], p["name"]
            last = arithmetic_term(p["a"], p["d"], p["n"])
            total = arithmetic_sum(p["a"], p["d"], p["n"])
            context = ["{} saves {}{} in the first week of the year. Each week after that, {} "
                       "saves {}{} more than in the week before.".format(
                           name, cur, p["a"], name, cur, p["d"])]
            return ib.assemble(context, [
                ib.part("a", "Find the amount {} saves in week {}.".format(name, p["n"]), 2,
                        cur + ib.exact_text(last), last),
                ib.part("b", "Find the total amount {} saves in the first {} weeks.".format(
                    name, p["n"]), 2, cur + ib.exact_text(total), total),
            ])
        if form in GEOMETRIC:
            r = ratio(form, p["percent"])
            term = geometric_term(p["a"], r, p["n"])
            total = geometric_sum(p["a"], r, p["n"])
            if form == "training":
                name = p["name"]
                context = ["{} runs {} km on the first day of a training plan. Each day after "
                           "that, the distance increases by {}%.".format(name, p["a"], p["percent"])]
                tasks = ("Find the distance {} runs on day {}.".format(name, p["n"]),
                         "Find the total distance {} runs in the first {} days.".format(name, p["n"]))
                unit = " km"
            elif form == "sales":
                context = ["A company sells {} copies of a new game in its first month. Each "
                           "month after that, sales increase by {}%.".format(p["a"], p["percent"])]
                tasks = ("Find the number of copies sold in month {}.".format(p["n"]),
                         "Find the total number of copies sold in the first {} months.".format(p["n"]))
                unit = " copies"
            else:
                context = ["A ball is dropped, and its first bounce reaches a height of {} cm. "
                           "Each bounce after that reaches {}% of the height of the bounce "
                           "before.".format(p["a"], p["percent"])]
                tasks = ("Find the height reached on bounce {}.".format(p["n"]),
                         "Find the total of the heights reached on the first {} bounces.".format(p["n"]))
                unit = " cm"
            return ib.assemble(context, [
                ib.part("a", tasks[0], 2, ib.sf3(term) + unit, term),
                ib.part("b", tasks[1], 3, ib.sf3(total) + unit, total),
            ])
        if form == "reading":
            name, day = p["name"], reading_day(p)
            context = ["{} starts a reading challenge. On day 1, {} reads {} pages, and each "
                       "day after that, {} reads {} more pages than the day before.".format(
                           name, name, p["a"], name, p["d"])]
            return ib.assemble(context, [
                ib.part("a", "Write down an expression for the number of pages {} reads on "
                        "day n.".format(name), 2, linear_rule(p["a"], p["d"])),
                ib.part("b", "Find the first day on which the total number of pages read is "
                        "greater than {}.".format(p["target"]), 3, "Day {}".format(day), day),
            ])
        if form == "followers":
            r, week = ratio(form, p["percent"]), followers_week(p)
            context = ["A new social media account has {} followers at the end of week 1. The "
                       "number of followers then increases by {}% each week.".format(
                           p["a"], p["percent"])]
            return ib.assemble(context, [
                ib.part("a", "Write down an expression for the number of followers at the end "
                        "of week n.", 2, "u_n = {} × {}^(n - 1)".format(p["a"], ib.exact_text(r))),
                ib.part("b", "Find the first week in which the number of followers is greater "
                        "than {}.".format(p["target"]), 3, "Week {}".format(week), week),
            ])

        day_a, day_b = race_days(p)
        if day_a < day_b:
            winner, loser, day, later = p["name_a"], p["name_b"], day_a, day_b
            total = arithmetic_sum(p["a"], p["d"], day_a)
        else:
            winner, loser, day, later = p["name_b"], p["name_a"], day_b, day_a
            total = geometric_sum(p["a"], ratio("race", p["percent"]), day_b)
        context = [
            "{} and {} are training for a long-distance run. On day 1, each of them runs "
            "{} km.".format(p["name_a"], p["name_b"], p["a"]),
            "Each day after that, {} runs {} km more than the day before, and {} runs {}% "
            "further than the day before.".format(p["name_a"], p["d"], p["name_b"], p["percent"]),
        ]
        return ib.assemble(context, [
            ib.part("a", "Determine who is first to run at least {} km in a single day, and "
                    "state on which day this happens.".format(p["target"]), 5,
                    "{}, on day {} ({} first does so on day {})".format(winner, day, loser, later),
                    day),
            ib.part("b", "Find the total distance run by that person up to and including that "
                    "day.", 2, ib.sf3(total) + " km", total),
        ])

    def validate_independently(self, question):
        """Add terms one at a time; solve targets with a quadratic or logarithms."""
        import math
        p, form = question.parameters, question.parameters["form"]
        values, shown = ib.answer_values(question), ib.answer_shown(question)

        def running(first, step=0.0, multiplier=1.0, count=1):
            term, total = float(first), 0.0
            for _ in range(count):
                total += term
                last = term
                term = term * multiplier + step
            return last, total

        if form in ("rows", "savings"):
            last, total = running(p["a"], step=p["d"], count=p["n"])
            require(Fraction(values["a"]) == round(last) and Fraction(values["b"]) == round(total),
                    "Independent arithmetic failed")
        elif form in GEOMETRIC:
            last, total = running(p["a"], multiplier=float(ratio(form, p["percent"])), count=p["n"])
            require(ib.close(values["a"], last) and ib.close(values["b"], total),
                    "Independent geometric failed")
        elif form == "reading":
            a, d, target = p["a"], p["d"], p["target"]
            linear = 2 * a - d
            root = (-linear + math.sqrt(linear * linear + 8 * d * target)) / (2 * d)
            require(Fraction(values["b"]) == math.floor(root) + 1, "Independent day failed")
            require(shown["a"] == linear_rule(a, d), "Independent rule failed")
        elif form == "followers":
            r = float(ratio(form, p["percent"]))
            power = math.log(p["target"] / p["a"]) / math.log(r)
            require(Fraction(values["b"]) == math.floor(power) + 2, "Independent week failed")
        else:
            a, d = p["a"], float(Fraction(p["d"]))
            target, r = float(Fraction(p["target"])), float(ratio("race", p["percent"]))
            day_a = math.ceil((target - a) / d - 1e-9) + 1
            day_b = math.ceil(math.log(target / a) / math.log(r) - 1e-9) + 1
            winner = p["name_a"] if day_a < day_b else p["name_b"]
            require(shown["a"].startswith(winner + ","), "Independent winner failed")
            require(Fraction(values["a"]) == min(day_a, day_b), "Independent day failed")
            if day_a < day_b:
                _, total = running(a, step=d, count=day_a)
            else:
                _, total = running(a, multiplier=r, count=day_b)
            require(ib.close(values["b"], total), "Independent total failed")
        return True