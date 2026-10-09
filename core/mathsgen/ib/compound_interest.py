"""IB AI SL compound interest: values, time to reach a target, regular
deposits, and comparing two banks.

A nominal annual rate of r% compounded k times a year multiplies the
balance by 1 + r/(100k) each period, as in the formula booklet:
FV = PV(1 + r/(100k))^(kn). The GDC route is the finance (TVM) solver.

Balances are exact Fractions; rounding happens only when an answer is
shown. Targets are taken from a real balance rounded down to a step, and
the answer is then found by stepping period by period.
"""
from fractions import Fraction

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from . import common as ib


# --- Editable pools ---------------------------------------------------------
RATES = ("1.25", "1.5", "1.8", "2", "2.4", "2.75", "3", "3.2", "3.5",
         "4", "4.5", "5", "6")
COMPOUNDING = {1: "annually", 2: "half-yearly", 4: "quarterly", 12: "monthly"}
PRINCIPALS = tuple(range(500, 20001, 250))
DEPOSITS = tuple(range(25, 501, 25))
YEARS = tuple(range(2, 16))
START_YEARS = tuple(range(2025, 2031))
TARGET_STEP = 50


# ------------------------------------------------------------ mathematics

def growth(rate, k):
    """The multiplier for one compounding period."""
    return 1 + Fraction(rate) / (100 * k)


def value_after(principal, rate, k, periods, deposit=0):
    """Closed form. Deposits at the end of each period form a geometric series."""
    g = growth(rate, k)
    value = principal * g ** periods
    if deposit:
        value += deposit * (g ** periods - 1) / (g - 1)
    return value


def periods_to_reach(principal, rate, k, target, step=1):
    """Fewest periods (a multiple of step) for a lump sum to reach target."""
    multiplier = growth(rate, k) ** step
    balance, periods = Fraction(principal), 0
    while balance < target:
        balance *= multiplier
        periods += step
        require(periods <= 1200, "Target out of reach")
    return periods


def bank_values(p):
    """Exact values in Bank A and Bank B after the stated number of years."""
    years = p["years"]
    a = value_after(p["principal"], p["rate_a"], p["k_a"], years * p["k_a"])
    b = value_after(p["principal"], p["rate_b"], p["k_b"], years * p["k_b"])
    return a, b


def years_to_target(p):
    """Complete years for Bank A to reach the target (checked at year ends)."""
    periods = periods_to_reach(p["principal"], p["rate_a"], p["k_a"], p["target"], p["k_a"])
    return periods // p["k_a"]


# ------------------------------------------------------------ generator

class CompoundInterest(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.finance.compound_interest",
        version=1,
        topic=ib.TOPIC,
        subtopic="financial_mathematics",
        title="Compound interest and savings",
        difficulty_descriptions={
            1: "Value of a lump sum after a number of years, to two decimal places.",
            2: "Value after n years, then the years or months needed to reach a target.",
            3: "Monthly deposits: the balance at the start of a later year and the interest earned.",
            4: "Compare two banks, then the complete years needed to reach a target.",
        },
        tags=ib.BASE_TAGS + ("compound_interest", "savings", "tvm"),
    )
    keys = {
        1: {"name", "currency", "principal", "rate", "k", "years"},
        2: {"name", "currency", "principal", "rate", "k", "years", "target"},
        3: {"name", "currency", "principal", "deposit", "rate", "years", "start_year"},
        4: {"name", "currency", "principal", "rate_a", "k_a", "rate_b", "k_b",
            "years", "target"},
    }

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def candidate(self, level, rng):
        p = {
            "name": rng.choice(ib.NAMES),
            "currency": rng.choice(tuple(ib.CURRENCIES)),
            "principal": rng.choice(PRINCIPALS),
            "years": rng.choice(YEARS),
        }
        if level == 1:
            p.update(rate=rng.choice(RATES), k=rng.choice(tuple(COMPOUNDING)))
        elif level == 2:
            p.update(rate=rng.choice(RATES), k=rng.choice((1, 12)), years=rng.randint(2, 8))
            extra = rng.randint(2, 12) if p["k"] == 1 else rng.randint(6, 72)
            aim = value_after(p["principal"], p["rate"], p["k"], p["years"] * p["k"] + extra)
            p["target"] = int(aim // TARGET_STEP) * TARGET_STEP
        elif level == 3:
            p.update(rate=rng.choice(RATES), deposit=rng.choice(DEPOSITS),
                     start_year=rng.choice(START_YEARS), years=rng.randint(2, 6))
        else:
            k_a, k_b = rng.sample(tuple(COMPOUNDING), 2)
            p.update(rate_a=rng.choice(RATES), k_a=k_a, rate_b=rng.choice(RATES), k_b=k_b,
                     years=rng.randint(3, 10))
            later = (p["years"] + rng.randint(2, 15)) * k_a
            aim = value_after(p["principal"], p["rate_a"], k_a, later)
            p["target"] = int(aim // TARGET_STEP) * TARGET_STEP
        return p

    def check_rules(self, p, level):
        require(p["name"] in ib.NAMES, "Unknown name")
        require(p["currency"] in ib.CURRENCIES, "Unknown currency")
        require(p["principal"] in PRINCIPALS, "Principal outside pool")
        if level in (1, 2, 3):
            require(p["rate"] in RATES, "Rate outside pool")
        if level == 1:
            require(p["k"] in COMPOUNDING, "Unknown compounding")
            require(p["years"] in YEARS, "Years outside pool")
        elif level == 2:
            require(p["k"] in (1, 12), "Level 2 compounds annually or monthly")
            ib.require_int(p["years"], 2, 8, "Years outside bounds")
            require(type(p["target"]) is int and p["target"] % TARGET_STEP == 0
                    and p["target"] > p["principal"], "Target outside rules")
            periods = periods_to_reach(p["principal"], p["rate"], p["k"], p["target"])
            require(p["years"] * p["k"] < periods <= p["years"] * p["k"] + 120,
                    "Target too near or too far")
        elif level == 3:
            require(p["deposit"] in DEPOSITS, "Deposit outside pool")
            require(p["start_year"] in START_YEARS, "Start year outside pool")
            ib.require_int(p["years"], 2, 6, "Years outside bounds")
        else:
            require(p["rate_a"] in RATES and p["rate_b"] in RATES, "Rate outside pool")
            require(p["k_a"] in COMPOUNDING and p["k_b"] in COMPOUNDING
                    and p["k_a"] != p["k_b"], "Banks need different compounding")
            ib.require_int(p["years"], 3, 10, "Years outside bounds")
            require(type(p["target"]) is int and p["target"] % TARGET_STEP == 0,
                    "Target outside rules")
            a, b = bank_values(p)
            require(abs(ib.to_cents(a) - ib.to_cents(b)) >= 1, "Banks too close to compare")
            require(p["years"] < years_to_target(p) <= p["years"] + 20, "Target outside bounds")

    def parts(self, p, level):
        cur = p["currency"]
        if level in (1, 2):
            context = ["{} invests {}{} in an account that pays a nominal annual interest "
                       "rate of {}%, compounded {}.".format(
                           p["name"], cur, p["principal"], p["rate"], COMPOUNDING[p["k"]])]
            value = value_after(p["principal"], p["rate"], p["k"], p["years"] * p["k"])
            parts = [ib.part(
                "a", "Find the value of the investment after {} years. Give your answer to "
                "two decimal places.".format(p["years"]), 3, ib.cash(cur, value), value)]
            if level == 2:
                periods = periods_to_reach(p["principal"], p["rate"], p["k"], p["target"])
                unit = "years" if p["k"] == 1 else "months"
                parts.append(ib.part(
                    "b", "Find the number of {} it takes for the investment to be worth at "
                    "least {}{}.".format(unit, cur, p["target"]), 2,
                    "{} {}".format(periods, unit), periods))
            return ib.assemble(context, parts)

        if level == 3:
            months = 12 * p["years"]
            end_year = p["start_year"] + p["years"]
            context = [
                "On 1 January {}, {} opens a savings account with a deposit of {}{}. The "
                "account pays a nominal annual interest rate of {}%, compounded monthly.".format(
                    p["start_year"], p["name"], cur, p["principal"], p["rate"]),
                "At the end of each month, starting with January {}, {} deposits a further "
                "{}{}.".format(p["start_year"], p["name"], cur, p["deposit"]),
            ]
            value = value_after(p["principal"], p["rate"], 12, months, p["deposit"])
            interest = ib.to_cents(value) - p["principal"] - p["deposit"] * months
            return ib.assemble(context, [
                ib.part("a", "Find the amount in the account at the start of {}. Give your "
                        "answer to two decimal places.".format(end_year), 3,
                        ib.cash(cur, value), value),
                ib.part("b", "Hence find the total interest earned by the start of "
                        "{}.".format(end_year), 2, ib.cash(cur, interest), interest),
            ])

        a, b = bank_values(p)
        rounded_a, rounded_b = ib.to_cents(a), ib.to_cents(b)
        winner = "Bank A" if rounded_a > rounded_b else "Bank B"
        difference = abs(rounded_a - rounded_b)
        years = years_to_target(p)
        context = [
            "{} has {}{} to invest for {} years.".format(p["name"], cur, p["principal"], p["years"]),
            "Bank A pays a nominal annual interest rate of {}%, compounded {}.".format(
                p["rate_a"], COMPOUNDING[p["k_a"]]),
            "Bank B pays a nominal annual interest rate of {}%, compounded {}.".format(
                p["rate_b"], COMPOUNDING[p["k_b"]]),
        ]
        return ib.assemble(context, [
            ib.part("a", "Find the value of the investment after {} years in Bank A. Give "
                    "your answer to two decimal places.".format(p["years"]), 2,
                    ib.cash(cur, a), a),
            ib.part("b", "Find the value of the investment after {} years in Bank B. Give "
                    "your answer to two decimal places.".format(p["years"]), 2,
                    ib.cash(cur, b), b),
            ib.part("c", "State which bank gives the greater value after {} years, and by "
                    "how much.".format(p["years"]), 2,
                    "{}, by {}".format(winner, ib.cash(cur, difference)), difference),
            ib.part("d", "{} chooses Bank A. Find the least number of complete years needed "
                    "for the investment to be worth at least {}{}.".format(
                        p["name"], cur, p["target"]), 2, "{} years".format(years), years),
        ])

    def validate_independently(self, question):
        """Step the balance period by period and solve counts with logarithms."""
        import math
        p, level = question.parameters, question.difficulty
        values, shown = ib.answer_values(question), ib.answer_shown(question)

        def stepped(rate, k, periods, deposit=0.0):
            g = 1 + float(Fraction(rate)) / (100 * k)
            balance = float(p["principal"])
            for _ in range(periods):
                balance = balance * g + deposit
            return balance

        if level in (1, 2):
            expected = stepped(p["rate"], p["k"], p["years"] * p["k"])
            require(ib.close(values["a"], expected), "Independent value failed")
        if level == 2:
            g = 1 + float(Fraction(p["rate"])) / (100 * p["k"])
            count = math.ceil(math.log(p["target"] / p["principal"]) / math.log(g) - 1e-9)
            require(Fraction(values["b"]) == count, "Independent period count failed")
        if level == 3:
            months = 12 * p["years"]
            total = stepped(p["rate"], 12, months, float(p["deposit"]))
            require(ib.close(values["a"], total), "Independent deposit balance failed")
            interest = round(total, 2) - p["principal"] - p["deposit"] * months
            require(abs(float(Fraction(values["b"])) - interest) < 0.006,
                    "Independent interest failed")
        if level == 4:
            a = stepped(p["rate_a"], p["k_a"], p["years"] * p["k_a"])
            b = stepped(p["rate_b"], p["k_b"], p["years"] * p["k_b"])
            require(ib.close(values["a"], a) and ib.close(values["b"], b),
                    "Independent bank values failed")
            winner = "Bank A" if round(a, 2) > round(b, 2) else "Bank B"
            require(shown["c"].startswith(winner), "Independent comparison failed")
            require(abs(float(Fraction(values["c"])) - abs(round(a, 2) - round(b, 2))) < 0.006,
                    "Independent difference failed")
            g = 1 + float(Fraction(p["rate_a"])) / (100 * p["k_a"])
            years = math.ceil(math.log(p["target"] / p["principal"])
                              / (p["k_a"] * math.log(g)) - 1e-9)
            require(Fraction(values["d"]) == years, "Independent year count failed")
        return True