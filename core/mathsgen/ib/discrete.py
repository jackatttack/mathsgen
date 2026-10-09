"""IB AI SL discrete probability distributions and expected value.

Level 1 a table with one unknown k; level 2 P(X = x) = k f(x); level 3 a
dice game and the cost that makes it fair; level 4 a distribution built
from a two-stage experiment. Probabilities are exact Fractions.
"""
from fractions import Fraction
from itertools import product

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from ..rounding import decimal_text
from .. import rich_blocks as rb
from . import common as ib


# --- Editable pools ---------------------------------------------------------
VALUE_SETS = ((0, 1, 2, 3), (1, 2, 3, 4), (1, 2, 3, 4, 5), (0, 1, 2, 3, 4), (2, 4, 6, 8))
# rule -> (plain, TeX, weight function)
RULES = {
    "linear": ("kx", "kx", lambda x: x),
    "shifted": ("k(x + 1)", "k(x+1)", lambda x: x + 1),
    "square": ("kx^2", "kx^{2}", lambda x: x * x),
}
RULE_VALUES = ((1, 2, 3, 4), (1, 2, 3, 4, 5), (0, 1, 2, 3), (2, 3, 4, 5))
COSTS = tuple(range(2, 11))
PRIZES = tuple(range(5, 41, 5))
EXPERIMENTS = {
    "coin_die": "A fair coin is tossed and a fair six-sided die is rolled. If the coin shows "
                "tails, X is the score on the die. If it shows heads, X is the score plus one.",
    "two_dice_max": "Two fair six-sided dice are rolled. X is the larger of the two scores "
                    "(or the common score if they are equal).",
    "spinners_sum": "A fair spinner numbered 1 to 3 and a fair spinner numbered 1 to 4 are "
                    "spun. X is the sum of the two scores.",
    "dice_difference": "Two fair six-sided dice are rolled. X is the positive difference "
                       "between the scores (0 if they are equal).",
}


# ------------------------------------------------------------ mathematics

def experiment(name):
    """{value: probability} for a two-stage experiment."""
    if name == "coin_die":
        outcomes = [(face + bonus) for bonus, face in product((0, 1), range(1, 7))]
    elif name == "two_dice_max":
        outcomes = [max(a, b) for a, b in product(range(1, 7), repeat=2)]
    elif name == "spinners_sum":
        outcomes = [a + b for a, b in product(range(1, 4), range(1, 5))]
    else:
        outcomes = [abs(a - b) for a, b in product(range(1, 7), repeat=2)]
    distribution = {}
    for value in outcomes:
        distribution[value] = distribution.get(value, 0) + Fraction(1, len(outcomes))
    return dict(sorted(distribution.items()))


def expectation(distribution):
    return sum(value * chance for value, chance in distribution.items())


def table_text(distribution):
    return "; ".join("P(X = {}) = {}".format(v, ib.probability_text(c))
                     for v, c in distribution.items())


def game(p):
    """{gain: probability} for one play of the dice game."""
    top, middle = p["top_faces"], p["middle_faces"]
    return {
        p["top_prize"] - p["cost"]: Fraction(top, 6),
        p["middle_prize"] - p["cost"]: Fraction(middle, 6),
        -p["cost"]: Fraction(6 - top - middle, 6),
    }


def face_words(first, count):
    faces = list(range(first, first + count))
    if count == 1:
        return "a {}".format(faces[0])
    return "a {} or {}".format(", ".join(str(f) for f in faces[:-1]), faces[-1])


# ------------------------------------------------------------ generator

class DiscreteDistributions(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.probability.discrete_distributions",
        version=1,
        topic=ib.TOPIC,
        subtopic="statistics_and_probability",
        title="Discrete distributions and expected value",
        difficulty_descriptions={
            1: "Find a missing probability k, then E(X).",
            2: "P(X = x) = k f(x): find k, a probability and E(X).",
            3: "A dice game: the gain table, expected gain and the fair cost.",
            4: "Build the distribution of a two-stage experiment, then E(X).",
        },
        tags=ib.BASE_TAGS + ("discrete_distributions", "expected_value", "fair_games"),
    )
    keys = {
        1: {"values", "probabilities", "missing"},
        2: {"rule", "values", "threshold"},
        3: {"cost", "top_prize", "middle_prize", "top_faces", "middle_faces"},
        4: {"experiment", "asked"},
    }

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def candidate(self, level, rng):
        if level == 1:
            values = list(rng.choice(VALUE_SETS))
            twentieths = [1] * len(values)
            for _ in range(20 - len(values)):
                twentieths[rng.randrange(len(values))] += 1
            return {"values": values,
                    "probabilities": [decimal_text(Fraction(t, 20)) for t in twentieths],
                    "missing": rng.randrange(len(values))}
        if level == 2:
            values = list(rng.choice(RULE_VALUES))
            return {"rule": rng.choice(tuple(RULES)), "values": values,
                    "threshold": rng.choice(values[1:])}
        if level == 3:
            top = rng.choice((1, 2))
            return {"cost": rng.choice(COSTS), "top_prize": rng.choice(PRIZES),
                    "middle_prize": rng.choice(PRIZES), "top_faces": top,
                    "middle_faces": rng.randint(1, 4 - top)}
        name = rng.choice(tuple(EXPERIMENTS))
        return {"experiment": name, "asked": rng.choice(tuple(experiment(name)))}

    def check_rules(self, p, level):
        if level == 1:
            values = p["values"]
            require(isinstance(values, list) and tuple(values) in VALUE_SETS, "Values outside pool")
            chances = p["probabilities"]
            require(isinstance(chances, list) and len(chances) == len(values)
                    and all(isinstance(c, str) for c in chances), "Probabilities outside rules")
            numbers = [Fraction(c) for c in chances]
            require(all(c > 0 and (c * 20).denominator == 1 for c in numbers), "Use twentieths")
            require(sum(numbers) == 1, "Probabilities must sum to 1")
            ib.require_int(p["missing"], 0, len(values) - 1, "Missing entry outside table")
        elif level == 2:
            require(p["rule"] in RULES, "Unknown rule")
            values = p["values"]
            require(isinstance(values, list) and tuple(values) in RULE_VALUES, "Values outside pool")
            weight = RULES[p["rule"]][2]
            require(all(weight(v) > 0 for v in values), "Every probability must be positive")
            require(p["threshold"] in values[1:], "Threshold outside table")
        elif level == 3:
            require(p["cost"] in COSTS and p["top_prize"] in PRIZES and p["middle_prize"] in PRIZES,
                    "Amounts outside pools")
            require(p["top_prize"] > p["middle_prize"] > p["cost"], "Prizes must beat the cost")
            require(p["top_faces"] in (1, 2) and type(p["middle_faces"]) is int
                    and 1 <= p["middle_faces"] <= 4 - p["top_faces"], "Faces outside rules")
            require(expectation(game(p)) != 0, "The game must not already be fair")
        else:
            require(p["experiment"] in EXPERIMENTS, "Unknown experiment")
            require(p["asked"] in experiment(p["experiment"]), "Value not possible")

    def parts(self, p, level):
        if level == 1:
            values, chances = p["values"], p["probabilities"]
            shown_chances = list(chances)
            shown_chances[p["missing"]] = "k"
            k = Fraction(chances[p["missing"]])
            distribution = {v: Fraction(c) for v, c in zip(values, chances)}
            mean = expectation(distribution)
            context = ["The probability distribution of a discrete random variable X is:",
                       "x: " + ", ".join(str(v) for v in values),
                       "P(X = x): " + ", ".join(shown_chances)]
            return ib.assemble(context, [
                ib.part("a", "Find the value of k.", 2, "k = " + ib.exact_text(k), k),
                ib.part("b", "Find E(X).", 2, "E(X) = " + ib.nice(mean), mean),
            ])
        if level == 2:
            plain, tex, weight = RULES[p["rule"]]
            values = p["values"]
            k = Fraction(1, sum(weight(v) for v in values))
            distribution = {v: k * weight(v) for v in values}
            at_least = sum(c for v, c in distribution.items() if v >= p["threshold"])
            mean = expectation(distribution)
            listing = ", ".join(str(v) for v in values)
            context = [[rb.text("The probability distribution of X is given by "),
                        rb.maths("P(X=x)=" + tex, "P(X = x) = " + plain),
                        rb.text(", for x = {}.".format(listing))]]
            return ib.assemble(context, [
                ib.part("a", "Find the value of k.", 2, "k = " + ib.probability_text(k), k),
                ib.part("b", "Find P(X ≥ {}).".format(p["threshold"]).replace("≥", ">="), 2,
                        ib.probability_text(at_least), at_least),
                ib.part("c", "Find E(X).", 2, "E(X) = " + ib.nice(mean), mean),
            ])
        if level == 3:
            gains = game(p)
            mean = expectation(gains)
            fair_cost = p["cost"] + mean
            top, middle = p["top_faces"], p["middle_faces"]
            context = ["A game costs ${} to play. A fair six-sided die is rolled once.".format(p["cost"]),
                       "Rolling {} wins ${}. Rolling {} wins ${}. Any other score wins nothing.".format(
                           face_words(7 - top, top), p["top_prize"],
                           face_words(7 - top - middle, middle), p["middle_prize"]),
                       "Let X be the player's gain in dollars (the prize minus the cost)."]
            table = "; ".join("P(X = {}) = {}".format(g, ib.probability_text(c))
                              for g, c in sorted(gains.items()))
            verdict = "the player expects to {} {} per game".format(
                "gain" if mean > 0 else "lose", ib.cash("$", abs(mean)))
            return ib.assemble(context, [
                ib.part("a", "Write down the probability distribution of X.", 2, table),
                ib.part("b", "Find E(X) and interpret it.", 2,
                        "E(X) = {}: {}".format(ib.nice(mean), verdict), mean),
                ib.part("c", "The cost is changed so that the game is fair. Find the new cost.", 2,
                        ib.cash("$", fair_cost), fair_cost),
            ])
        distribution = experiment(p["experiment"])
        chance = distribution[p["asked"]]
        mean = expectation(distribution)
        return ib.assemble([EXPERIMENTS[p["experiment"]]], [
            ib.part("a", "Find P(X = {}).".format(p["asked"]), 2, ib.probability_text(chance), chance),
            ib.part("b", "Write down the probability distribution of X.", 3, table_text(distribution)),
            ib.part("c", "Find E(X).", 2, "E(X) = " + ib.nice(mean), mean),
        ])

    def validate_independently(self, question):
        """Recount outcomes by brute force; check sums and expectations in floats."""
        p, level = question.parameters, question.difficulty
        values = ib.answer_values(question)
        if level == 1:
            known = sum(float(Fraction(c)) for i, c in enumerate(p["probabilities"]) if i != p["missing"])
            k = 1 - known
            chances = [k if i == p["missing"] else float(Fraction(c))
                       for i, c in enumerate(p["probabilities"])]
            require(ib.close(values["a"], k), "Independent k failed")
            require(ib.close(values["b"], sum(v * c for v, c in zip(p["values"], chances))),
                    "Independent E(X) failed")
        elif level == 2:
            weight = RULES[p["rule"]][2]
            weights = [weight(v) for v in p["values"]]
            k = 1 / sum(weights)
            require(ib.close(values["a"], k), "Independent k failed")
            require(ib.close(values["b"], sum(k * w for v, w in zip(p["values"], weights)
                                            if v >= p["threshold"])), "Independent tail failed")
            require(ib.close(values["c"], sum(k * w * v for v, w in zip(p["values"], weights))),
                    "Independent E(X) failed")
        elif level == 3:
            total = 0
            for face in range(1, 7):
                if face > 6 - p["top_faces"]:
                    prize = p["top_prize"]
                elif face > 6 - p["top_faces"] - p["middle_faces"]:
                    prize = p["middle_prize"]
                else:
                    prize = 0
                total += prize - p["cost"]
            require(ib.close(values["b"], total / 6), "Independent expected gain failed")
            require(ib.close(values["c"], p["cost"] + total / 6), "Independent fair cost failed")
        else:
            counts, size = {}, 0
            for first in range(1, 7):
                for second in range(1, 7):
                    if p["experiment"] == "coin_die":
                        if second > 2:
                            continue
                        value = first + (second - 1)
                    elif p["experiment"] == "two_dice_max":
                        value = first if first >= second else second
                    elif p["experiment"] == "spinners_sum":
                        if first > 3 or second > 4:
                            continue
                        value = first + second
                    else:
                        value = first - second if first >= second else second - first
                    counts[value] = counts.get(value, 0) + 1
                    size += 1
            require(ib.close(values["a"], counts[p["asked"]] / size), "Independent probability failed")
            require(ib.close(values["c"], sum(v * c for v, c in counts.items()) / size),
                    "Independent E(X) failed")
        return True