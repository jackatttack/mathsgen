"""IB AI SL Venn diagrams, tree diagrams and conditional probability.

Level 1 two sets; level 2 three sets given by region; level 3 a test with
false positives and negatives (tree diagram); level 4 independent failures
repeated over time. Every probability is an exact Fraction.
"""
from fractions import Fraction

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from . import common as ib


# --- Editable pools ---------------------------------------------------------
TWO_SETS = {
    "languages": {"group": "students", "person": "student", "a": ("F", "study French"),
                  "b": ("S", "study Spanish")},
    "sports": {"group": "club members", "person": "member", "a": ("T", "play tennis"),
               "b": ("G", "play golf")},
    "pets": {"group": "households", "person": "household", "a": ("C", "own a cat"),
             "b": ("D", "own a dog")},
}
THREE_SETS = {
    "absences": {"intro": "A school has {} students. In one week, the numbers absent with "
                          "headlice (H), influenza (I) or chickenpox (C) are given below.",
                 "person": "student", "letters": ("H", "I", "C"),
                 "words": ("had headlice", "had influenza", "had chickenpox")},
    "clubs": {"intro": "A school has {} students. The numbers in the chess (P), drama (D) and "
                       "music (M) clubs are given below.",
              "person": "student", "letters": ("P", "D", "M"),
              "words": ("is in the chess club", "is in the drama club", "is in the music club")},
}
REGION_NAMES = ("{0} only", "{1} only", "{2} only", "{0} and {1} but not {2}",
                "{0} and {2} but not {1}", "{1} and {2} but not {0}", "all three")
TESTS = {
    "athletes": {"intro": "Athletes are tested for a banned substance. The probability that an "
                          "athlete uses the substance is {}. If an athlete uses it, the test is "
                          "positive with probability {}. If an athlete does not, the test is "
                          "negative with probability {}.",
                 "condition": "uses the substance", "people": "athletes",
                 "item": "athlete", "positive": "tests positive"},
    "screening": {"intro": "A screening test is used for a disease. The probability that a "
                           "person has the disease is {}. If a person has it, the test is "
                           "positive with probability {}. If a person does not, the test is "
                           "negative with probability {}.",
                  "condition": "has the disease", "people": "people",
                  "item": "person", "positive": "tests positive"},
    "factory": {"intro": "A scanner checks items from a factory for faults. The probability "
                         "that an item is faulty is {}. A faulty item is flagged with "
                         "probability {}. An item without a fault passes with probability {}.",
                "condition": "is faulty", "people": "items",
                "item": "item", "positive": "is flagged"},
}
PREVALENCE = ("0.02", "0.04", "0.05", "0.06", "0.1", "0.15")
SENSITIVITY = ("0.71", "0.8", "0.85", "0.9", "0.95")
SPECIFICITY = ("0.9", "0.92", "0.95", "0.98")
SCREENED = (500, 800, 1000, 1300, 2000)
SYSTEMS = {
    "generator": {"intro": "A generator has a main switch A and a backup switch B. In any month, "
                           "A fails with probability {} and B fails with probability {}, "
                           "independently. The generator shuts down only if both fail.",
                  "event": "the generator shuts down", "once": "in a given month",
                  "none": "in none of {} months",
                  "count": "the number of months in which the generator shuts down, out of {}"},
    "alarms": {"intro": "A building has two smoke alarms, A and B. When there is smoke, A fails "
                        "to sound with probability {} and B fails with probability {}, "
                        "independently. A fire goes undetected only if both fail.",
               "event": "a fire goes undetected", "once": "on an occasion with smoke",
               "none": "on none of {} occasions with smoke",
               "count": "the number of undetected fires in {} occasions with smoke"},
}
FAILURES = ("0.05", "0.1", "0.15", "0.2", "0.25", "0.3")
PERIODS = (3, 4, 6, 12)
HORIZONS = (12, 24, 36, 60, 120)


# ------------------------------------------------------------ helpers

def shown(value):
    value = Fraction(value)
    text = ib.probability_text(value)
    return text if "/" not in text else "{} ({})".format(text, ib.sf3(value))


def tree_values(p):
    prevalence = Fraction(p["prevalence"])
    sensitivity, specificity = Fraction(p["sensitivity"]), Fraction(p["specificity"])
    positive = prevalence * sensitivity + (1 - prevalence) * (1 - specificity)
    incorrect = prevalence * (1 - sensitivity) + (1 - prevalence) * (1 - specificity)
    given_positive = prevalence * sensitivity / positive
    return positive, incorrect, given_positive


# ------------------------------------------------------------ generator

class VennAndTrees(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.probability.venn_and_trees",
        version=1,
        topic=ib.TOPIC,
        subtopic="statistics_and_probability",
        title="Venn diagrams, trees and conditional probability",
        difficulty_descriptions={
            1: "Two-set Venn diagram: neither, a probability and a conditional probability.",
            2: "Three-set Venn diagram from its regions, with a conditional probability.",
            3: "Test results on a tree: positives, incorrect results and P(condition | positive).",
            4: "Independent failures: both, exactly one, and repeated over time.",
        },
        tags=ib.BASE_TAGS + ("venn_diagrams", "tree_diagrams", "conditional_probability",
                             "independent_events"),
    )
    keys = {
        1: {"context", "total", "a", "b", "both"},
        2: {"context", "total", "regions"},
        3: {"context", "prevalence", "sensitivity", "specificity", "screened"},
        4: {"context", "fail_a", "fail_b", "periods", "horizon"},
    }

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def candidate(self, level, rng):
        if level == 1:
            total = rng.randint(50, 150)
            both = rng.randint(3, total // 6)
            a = both + rng.randint(5, total // 3)
            b = both + rng.randint(5, total // 3)
            return {"context": rng.choice(tuple(TWO_SETS)), "total": total, "a": a, "b": b,
                    "both": both}
        if level == 2:
            regions = [rng.randint(5, 40), rng.randint(5, 40), rng.randint(2, 30),
                       rng.randint(1, 8), rng.randint(1, 8), rng.randint(1, 8), rng.randint(0, 4)]
            return {"context": rng.choice(tuple(THREE_SETS)),
                    "total": sum(regions) + rng.randint(100, 400), "regions": regions}
        if level == 3:
            return {"context": rng.choice(tuple(TESTS)), "prevalence": rng.choice(PREVALENCE),
                    "sensitivity": rng.choice(SENSITIVITY), "specificity": rng.choice(SPECIFICITY),
                    "screened": rng.choice(SCREENED)}
        return {"context": rng.choice(tuple(SYSTEMS)), "fail_a": rng.choice(FAILURES),
                "fail_b": rng.choice(FAILURES), "periods": rng.choice(PERIODS),
                "horizon": rng.choice(HORIZONS)}

    def check_rules(self, p, level):
        if level == 1:
            require(p["context"] in TWO_SETS, "Unknown context")
            for key in ("total", "a", "b", "both"):
                require(type(p[key]) is int and p[key] >= 0, "Counts must be whole numbers")
            require(p["both"] >= 1 and p["both"] < min(p["a"], p["b"]), "Overlap outside rules")
            require(p["a"] + p["b"] - p["both"] < p["total"], "Someone must be in neither set")
        elif level == 2:
            require(p["context"] in THREE_SETS, "Unknown context")
            regions = p["regions"]
            require(isinstance(regions, list) and len(regions) == 7
                    and all(type(v) is int and 0 <= v <= 60 for v in regions), "Regions outside rules")
            require(regions[0] + regions[3] + regions[4] + regions[6] > 0, "First set is empty")
            require(type(p["total"]) is int and p["total"] > sum(regions), "Total outside rules")
        elif level == 3:
            require(p["context"] in TESTS, "Unknown context")
            require(p["prevalence"] in PREVALENCE and p["sensitivity"] in SENSITIVITY
                    and p["specificity"] in SPECIFICITY and p["screened"] in SCREENED,
                    "Values outside pools")
        else:
            require(p["context"] in SYSTEMS, "Unknown context")
            require(p["fail_a"] in FAILURES and p["fail_b"] in FAILURES, "Probabilities outside pool")
            require(p["periods"] in PERIODS and p["horizon"] in HORIZONS, "Periods outside pool")

    def parts(self, p, level):
        if level == 1:
            c = TWO_SETS[p["context"]]
            (la, wa), (lb, wb) = c["a"], c["b"]
            neither = p["total"] - p["a"] - p["b"] + p["both"]
            context = ["In a group of {} {}, {} {}, {} {} and {} {} both.".format(
                p["total"], c["group"], p["a"], wa, p["b"], wb, p["both"], "do")]
            only_a = Fraction(p["a"] - p["both"], p["total"])
            given = Fraction(p["both"], p["b"])
            return ib.assemble(context, [
                ib.part("a", "Find the number of {} who do neither.".format(c["group"]), 2,
                        str(neither), neither),
                ib.part("b", "A {} is chosen at random. Find the probability that they {} but do "
                        "not {}.".format(c["person"], wa, wb.split(" ", 1)[0] + " " + wb.split(" ", 1)[1]),
                        2, shown(only_a), only_a),
                ib.part("c", "Given that the {} chosen {}, find the probability that they also "
                        "{}.".format(c["person"], wb.replace("study", "studies").replace("play", "plays")
                                     .replace("own", "owns"), wa), 2, shown(given), given),
            ])
        if level == 2:
            c = THREE_SETS[p["context"]]
            letters, regions = c["letters"], p["regions"]
            context = [c["intro"].format(p["total"])]
            for name, count in zip(REGION_NAMES, regions):
                context.append("{}: {}".format(name.format(*letters), count))
            none = p["total"] - sum(regions)
            first = regions[0] + regions[3] + regions[4] + regions[6]
            first_and_second = regions[3] + regions[6]
            chance = Fraction(first, p["total"])
            given = Fraction(first_and_second, first)
            return ib.assemble(context, [
                ib.part("a", "Find the number of students in none of the three groups.", 2,
                        str(none), none),
                ib.part("b", "A student is chosen at random. Find the probability that the "
                        "student {}.".format(c["words"][0]), 2, shown(chance), chance),
                ib.part("c", "Given that the student {}, find the probability that the student "
                        "also {}.".format(c["words"][0], c["words"][1]), 2, shown(given), given),
            ])
        if level == 3:
            c = TESTS[p["context"]]
            positive, incorrect, given_positive = tree_values(p)
            expected = p["screened"] * incorrect
            context = [c["intro"].format(p["prevalence"], p["sensitivity"], p["specificity"])]
            return ib.assemble(context, [
                ib.part("a", "Find the probability that a randomly chosen {} {}.".format(
                    c["item"], c["positive"]), 2, ib.sf3(positive), positive),
                ib.part("b", "Find the probability that the result is incorrect.", 2,
                        ib.sf3(incorrect), incorrect),
                ib.part("c", "{} {} are checked. Find the expected number of incorrect "
                        "results.".format(p["screened"], c["people"]), 1, ib.sf3(expected), expected),
                ib.part("d", "Given that a randomly chosen {} {}, find the probability that the "
                        "{} {}.".format(c["item"], c["positive"], c["item"], c["condition"]), 2,
                        ib.sf3(given_positive), given_positive),
            ])
        c = SYSTEMS[p["context"]]
        a, b = Fraction(p["fail_a"]), Fraction(p["fail_b"])
        both = a * b
        exactly_one = a * (1 - b) + (1 - a) * b
        never = (1 - both) ** p["periods"]
        expected = p["horizon"] * both
        context = [c["intro"].format(p["fail_a"], p["fail_b"])]
        return ib.assemble(context, [
            ib.part("a", "Find the probability that {} {}.".format(c["event"], c["once"]), 1,
                    ib.nice(both), both),
            ib.part("b", "Find the probability that exactly one of A and B fails.", 2,
                    ib.nice(exactly_one), exactly_one),
            ib.part("c", "Find the probability that {} {}.".format(
                c["event"], c["none"].format(p["periods"])), 2, ib.sf3(never), never),
            ib.part("d", "Find the expected value of {}.".format(
                c["count"].format(p["horizon"])), 1, ib.nice(expected), expected),
        ])

    def validate_independently(self, question):
        """Count explicit individuals, or enumerate every branch of the tree."""
        from itertools import product
        p, level = question.parameters, question.difficulty
        values = ib.answer_values(question)
        if level == 1:
            people = ([(True, True)] * p["both"] + [(True, False)] * (p["a"] - p["both"])
                      + [(False, True)] * (p["b"] - p["both"]))
            people += [(False, False)] * (p["total"] - len(people))
            require(Fraction(values["a"]) == sum(1 for x in people if x == (False, False)),
                    "Independent neither failed")
            require(ib.close(values["b"], sum(1 for x in people if x == (True, False)) / p["total"]),
                    "Independent probability failed")
            in_b = [x for x in people if x[1]]
            require(ib.close(values["c"], sum(1 for x in in_b if x[0]) / len(in_b)),
                    "Independent conditional failed")
        elif level == 2:
            r = p["regions"]
            memberships = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)]
            people = [m for m, count in zip(memberships, r) for _ in range(count)]
            in_first = [m for m in people if m[0]]
            require(Fraction(values["a"]) == p["total"] - len(people), "Independent none failed")
            require(ib.close(values["b"], len(in_first) / p["total"]), "Independent P(first) failed")
            require(ib.close(values["c"], sum(1 for m in in_first if m[1]) / len(in_first)),
                    "Independent conditional failed")
        elif level == 3:
            prevalence = float(Fraction(p["prevalence"]))
            sensitivity = float(Fraction(p["sensitivity"]))
            specificity = float(Fraction(p["specificity"]))
            branches = {}
            for has, positive in product((True, False), repeat=2):
                first = prevalence if has else 1 - prevalence
                second = (sensitivity if positive else 1 - sensitivity) if has else (
                    1 - specificity if positive else specificity)
                branches[(has, positive)] = first * second
            positive = branches[(True, True)] + branches[(False, True)]
            incorrect = branches[(True, False)] + branches[(False, True)]
            require(ib.close(values["a"], positive) and ib.close(values["b"], incorrect),
                    "Independent tree failed")
            require(ib.close(values["c"], p["screened"] * incorrect), "Independent expectation failed")
            require(ib.close(values["d"], branches[(True, True)] / positive), "Independent Bayes failed")
        else:
            a, b = float(Fraction(p["fail_a"])), float(Fraction(p["fail_b"]))
            outcomes = {(x, y): (a if x else 1 - a) * (b if y else 1 - b)
                        for x, y in product((True, False), repeat=2)}
            both = outcomes[(True, True)]
            require(ib.close(values["a"], both), "Independent both failed")
            require(ib.close(values["b"], outcomes[(True, False)] + outcomes[(False, True)]),
                    "Independent exactly one failed")
            never = 1.0
            for _ in range(p["periods"]):
                never *= 1 - both
            require(ib.close(values["c"], never) and ib.close(values["d"], p["horizon"] * both),
                    "Independent repetition failed")
        return True