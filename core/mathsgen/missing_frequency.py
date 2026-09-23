"""Recover one frequency from a stated exact mean."""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .rounding import decimal_text


INFO = GeneratorInfo(
    id="data.mean.missing_frequency", version=1, topic="data", subtopic="mean",
    title="Find a missing frequency from the mean",
    difficulty_descriptions={
        1: "Three whole-number values and an integer mean.",
        2: "Three whole-number values and a decimal mean.",
        3: "Four values, with the missing frequency on an interior row.",
        4: "Decimal values of both signs and a decimal mean.",
    },
    tags=("mean", "frequency_table", "missing_frequency", "equations"),
)


def presentation(values, frequencies, mean):
    instruction = (
        "The mean of the values in the frequency table is {}. "
        "Find the missing frequency f."
    ).format(decimal_text(mean))
    rows = [
        [decimal_text(value), "f" if frequency is None else str(frequency)]
        for value, frequency in zip(values, frequencies)
    ]
    prompt = Content(
        instruction + " Value: frequency — "
        + "; ".join(": ".join(row) for row in rows) + ".",
        display_text=instruction,
    )
    return prompt, {
        "kind": "table", "version": 1,
        "headers": ["Value", "Frequency"], "rows": rows,
    }


class MissingFrequency:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        count = 3 if difficulty <= 2 else 4
        for _ in range(1000):
            if difficulty == 4:
                values = sorted(Fraction(v, 2) for v in rng.sample(range(-12, 17), count))
                if not (values[0] < 0 < values[-1]):
                    continue
                if not any(v.denominator == 2 for v in values):
                    continue
            else:
                values = list(map(Fraction, sorted(rng.sample(range(0, 13), count))))
            full = [rng.randint(1, 9) for _ in values]
            mean = sum(v * f for v, f in zip(values, full)) / sum(full)
            if difficulty == 1:
                if mean.denominator != 1:
                    continue
            elif mean.denominator not in (2, 4, 5, 10, 20):
                continue
            possible = [
                i for i, value in enumerate(values)
                if value != mean and (difficulty != 3 or 0 < i < count - 1)
            ]
            if not possible:
                continue
            missing = rng.choice(possible)
            result = full[missing]
            frequencies = [None if i == missing else f for i, f in enumerate(full)]
            break
        else:
            raise ValueError("Could not construct a unique missing frequency")

        prompt, table = presentation(values, frequencies, mean)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt,
            answer={"kind": "integer", "value": result},
            answer_display=Content("f = " + str(result), "f = " + str(result)),
            worked_solution=(), marks=3 if difficulty <= 2 else 4,
            tags=self.info.tags, layout_hint=LayoutHint(working_lines=5),
            parameters={
                "values": [rational_text(v) for v in values],
                "frequencies": frequencies, "mean": rational_text(mean),
            },
            question_visuals=(table,),
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")
        raw = question.parameters["values"]
        frequencies = question.parameters["frequencies"]
        require(isinstance(raw, list) and isinstance(frequencies, list),
                "Expected lists")
        require(len(raw) == len(frequencies) == (3 if level <= 2 else 4),
                "Unexpected row count")
        values = list(map(Fraction, raw))
        require(raw == [rational_text(v) for v in values], "Non-canonical values")
        require(all(a < b for a, b in zip(values, values[1:])),
                "Values must increase strictly")
        require(frequencies.count(None) == 1, "Exactly one missing frequency required")
        require(all(f is None or (type(f) is int and 1 <= f <= 9)
                    for f in frequencies), "Invalid known frequency")
        result = question.answer["value"]
        require(type(result) is int and 1 <= result <= 9, "Invalid answer frequency")
        require(question.answer == {"kind": "integer", "value": result},
                "Unexpected answer structure")
        mean = Fraction(question.parameters["mean"])
        require(question.parameters["mean"] == rational_text(mean),
                "Non-canonical mean")
        require(mean.denominator == 1 if level == 1
                else mean.denominator in (2, 4, 5, 10, 20),
                "Mean precision mismatch")
        missing = frequencies.index(None)
        require(values[missing] != mean, "Missing frequency is not uniquely determined")
        if level == 3:
            require(0 < missing < len(values) - 1, "Expected an interior missing row")
        if level == 4:
            require(all(-6 <= v <= 8 and (v * 2).denominator == 1 for v in values),
                    "Decimal values outside bounds")
            require(values[0] < 0 < values[-1]
                    and any(v.denominator == 2 for v in values),
                    "Expected signed decimal data")
        else:
            require(all(v.denominator == 1 and 0 <= v <= 12 for v in values),
                    "Expected bounded whole-number values")
        full = [result if f is None else f for f in frequencies]
        require(sum(v * f for v, f in zip(values, full)) == mean * sum(full),
                "Answer fails the stated mean")
        prompt, table = presentation(values, frequencies, mean)
        require(question.prompt == prompt, "Prompt mismatch")
        require(question.visual_assets("questions") == (table,), "Table mismatch")
        require(not question.visual_assets("answers"), "Unexpected answer assets")
        require(question.answer_display == Content("f = " + str(result), "f = " + str(result)),
                "Answer display mismatch")
        return True

    def validate_independently(self, question):
        """Recover the unknown by balancing deviations from the stated mean."""
        import sympy

        mean = sympy.Rational(question.parameters["mean"])
        deviations = []
        known_balance = sympy.Integer(0)
        for value, frequency in zip(
            question.parameters["values"], question.parameters["frequencies"]
        ):
            deviation = sympy.Rational(value) - mean
            if frequency is None:
                deviations.append(deviation)
            else:
                known_balance += frequency * deviation
        require(len(deviations) == 1 and deviations[0] != 0,
                "Independent check found no unique frequency")
        recovered = -known_balance / deviations[0]
        require(recovered == question.answer["value"],
                "Independent frequency disagrees")
        return True