"""Combine pairwise ratios using exact shared-quantity constraints."""
from fractions import Fraction
from math import gcd

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)


def ratio_text(values):
    return " : ".join(str(value) for value in values)


def prompt_for(first, second, reversed_pair):
    second_names = "C : B" if reversed_pair else "B : C"
    return Content(
        "A : B = {} and {} = {}. "
        "Find A : B : C in its simplest whole-number form.".format(
            ratio_text(first), second_names, ratio_text(second)
        )
    )


def permitted_shared_parts(level):
    if level == 1:
        return [(b, b) for b in range(2, 10)]
    if level == 2:
        return [
            pair for b in range(2, 5) for scale in (2, 3)
            for pair in ((b, b * scale), (b * scale, b))
        ]
    return [
        (b, d) for b in range(2, 10) for d in range(2, 10)
        if b % d != 0 and d % b != 0
    ]


class CombineRatios:
    info = GeneratorInfo(
        id="ratio.combining.three_part",
        version=2,
        topic="ratio",
        subtopic="combining",
        title="Combine two ratios into a three-part ratio",
        difficulty_descriptions={
            1: "The shared quantity already has matching parts.",
            2: "Scale one ratio to match; or combine two ratios from a story.",
            3: "Scale both ratios to match; or combine two ratios from a story.",
            4: "Interpret a reversed pair; or combine, then find a count from a total.",
        },
        tags=("ratio", "combining", "equivalence"),
    )

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        from . import ratio_more_contexts as worded_forms
        if rng.random() < worded_forms.share(self, difficulty):
            return worded_forms.generate(self, context)
        b, d = rng.choice(permitted_shared_parts(difficulty))
        a = rng.choice([n for n in range(1, 13) if gcd(n, b) == 1])
        c = rng.choice([n for n in range(1, 13) if gcd(n, d) == 1])
        common = b * d // gcd(b, d)
        values = [a * (common // b), common, c * (common // d)]
        divisor = gcd(gcd(values[0], values[1]), values[2])
        values = [value // divisor for value in values]
        reversed_pair = difficulty == 4
        first = [a, b]
        second = [c, d] if reversed_pair else [d, c]
        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=prompt_for(first, second, reversed_pair),
            answer={"kind": "ratio", "labels": ["A", "B", "C"], "parts": values},
            answer_display=Content(ratio_text(values)),
            worked_solution=(),
            marks=2 if difficulty < 3 else 3,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=5),
            parameters={
                "first": first, "second": second,
                "reversed_pair": reversed_pair,
            },
        )
        self.validate(question)
        return question

    def validate(self, question):
        from .worded import is_worded
        if is_worded(question):
            from .ratio_more_contexts import validate as validate_worded
            return validate_worded(self, question)
        require(isinstance(question.answer, dict) and question.answer.get("kind") == "ratio"
                and isinstance(question.answer.get("parts"), list), "Unexpected answer shape")
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(not question.settings, "Unexpected settings")
        first = question.parameters["first"]
        second = question.parameters["second"]
        reverse = question.parameters["reversed_pair"]
        require(type(reverse) is bool and reverse == (level == 4), "Wrong pair order")
        require(len(first) == len(second) == 2, "Expected two-part ratios")
        require(all(type(n) is int and n > 0 for n in first + second),
                "Expected positive integer parts")
        a, b = first
        c, d = second if reverse else second[::-1]
        require(1 <= a <= 12 and 1 <= c <= 12, "Outer parts outside bounds")
        require((b, d) in permitted_shared_parts(level), "Wrong scaling structure")
        require(gcd(a, b) == gcd(c, d) == 1, "Input ratios must be simplified")
        values = question.answer["parts"]
        require(len(values) == 3 and all(type(n) is int and 0 < n <= 144
                                        for n in values), "Invalid answer parts")
        require(question.answer == {
            "kind": "ratio", "labels": ["A", "B", "C"], "parts": values,
        }, "Invalid answer structure")
        x, y, z = values
        require(x * b == y * a, "Answer does not preserve A:B")
        require(y * c == z * d, "Answer does not preserve B:C")
        require(gcd(gcd(x, y), z) == 1, "Answer is not fully simplified")
        require(question.prompt == prompt_for(first, second, reverse), "Prompt mismatch")
        require(question.answer_display == Content(ratio_text(values)), "Display mismatch")
        return True

    def validate_independently(self, question):
        """Normalize both supplied ratios to B=1 and compare exact proportions."""
        from .worded import is_worded
        if is_worded(question):
            from .ratio_more_contexts import validate_independently as independent_worded
            return independent_worded(self, question)
        a, b = question.parameters["first"]
        second = question.parameters["second"]
        c, d = second if question.parameters["reversed_pair"] else second[::-1]
        expected = (Fraction(a, b), Fraction(1), Fraction(c, d))
        x, y, z = question.answer["parts"]
        actual = (Fraction(x, y), Fraction(1), Fraction(z, y))
        require(actual == expected, "Independent shared-unit check disagrees")
        require(gcd(gcd(x, y), z) == 1, "Independent simplification check failed")
        return True