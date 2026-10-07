"""Exact fraction MCQ checks; no native UI or PDF dependency."""
import copy
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
for name in list(sys.modules):
    if name == "mathsgen" or name.startswith("mathsgen."):
        del sys.modules[name]

from mathsgen.catalogue import build_registry
from mathsgen.core import Content, require
from mathsgen.multiple_choice import (
    RationalCandidate, choose_candidates, make_multiple_choice,
    original_question, validate_multiple_choice,
)
from mathsgen.multiple_choice import (
    providers, numeric_answer, correct_candidate, option_key,
)

SUPPORTED_LEVELS = {}
for provider in providers():
    require(not (set(SUPPORTED_LEVELS) & set(provider.SUPPORTED_LEVELS)),
            "Duplicate MCQ provider registration")
    SUPPORTED_LEVELS.update(provider.SUPPORTED_LEVELS)


def must_reject(action, label):
    try:
        action()
    except ValueError:
        return
    raise AssertionError("Accepted corruption: " + label)


def main():
    registry = build_registry()
    tested = 0
    skipped = 0
    positions = set()
    example_seen = False
    for generator_id, levels in SUPPORTED_LEVELS.items():
        generator = registry.get(generator_id)
        for level in levels:
            accepted = 0
            sample = None
            for seed in range(40):
                original = generator.generate(seed, level)
                question = make_multiple_choice(original)
                if question is None:
                    skipped += 1
                    continue
                validate_multiple_choice(
                    question, generator, independent=accepted < 8)
                require(original_question(question) == original,
                        "Original question did not round-trip")
                require(make_multiple_choice(original) == question,
                        "Options are not reproducible")
                # Exact keys in each option's own answer domain (rational or
                # polynomial), rebuilt from teacher metadata, never display text.
                values = [
                    option_key(item)
                    for item in question.answer["multiple_choice"]["options"]
                ]
                target = correct_candidate(original).key()
                require(len(set(values)) == len(values), "Duplicate exact values")
                correct_index = values.index(target)
                positions.add(correct_index)
                require(question.choices[correct_index].id == question.answer["choice_id"],
                        "Wrong letter mapping")
                bad_answer = copy.deepcopy(question.answer)
                bad_answer["choice_id"] = question.choices[
                    (correct_index + 1) % len(values)
                ].id
                must_reject(
                    lambda: validate_multiple_choice(
                        replace(question, answer=bad_answer), generator),
                    "wrong answer key")
                bad_choices = list(question.choices)
                bad_choices[0] = replace(
                    bad_choices[0], content=Content("999", "999"))
                must_reject(
                    lambda: validate_multiple_choice(
                        replace(question, choices=tuple(bad_choices)), generator),
                    "wrong displayed option")
                if (
                    generator_id.endswith(".addition")
                    and original.parameters == {"left": "1/3", "right": "1/3"}
                ):
                    require(any(choice.content.text == "2/6"
                                for choice in question.choices),
                            "Lost the add-tops-and-bottoms example")
                    example_seen = True
                sample = sample or question
                accepted += 1
                tested += 1
            require(accepted > 0, "No MCQ examples for " + generator_id)
            print(generator_id, "L" + str(level), "checked", accepted)
            print(" ", sample.prompt.text)
            print(" ", " | ".join(
                chr(65 + index) + ": " + choice.content.text
                for index, choice in enumerate(sample.choices)))
            print("  Answer:", sample.answer_display.text)

    # The same wrong number in two forms must occupy only one option.
    selected = choose_candidates(Fraction(2, 3), [
        RationalCandidate(Fraction(1, 3), "one", "First error.", (2, 6)),
        RationalCandidate(Fraction(1, 3), "two", "Equivalent error."),
        RationalCandidate(Fraction(2, 3), "three", "Accidentally correct."),
        RationalCandidate(Fraction(1, 9), "four", "Multiplication error."),
    ])
    require(len(selected) == 2, "Equivalent/correct candidate filtering failed")
    require(selected[0].content().text == "2/6", "Raw mistake notation lost")
    require(len(positions) >= 3, "Correct answer position did not vary")
    print("Checked:", tested, "| unsupported/insufficient forms:", skipped)
    print("Generated 1/3 + 1/3 seen:", example_seen,
          "(raw 2/6 and equivalence checked directly)")
    print("MULTIPLE CHOICE FOUNDATION PASS")


if __name__ == "__main__":
    main()