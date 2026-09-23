"""Exact means from discrete frequency tables, independently checked by expansion."""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .rounding import decimal_text


INFO = GeneratorInfo(
    id="data.mean.frequency_table", version=2, topic="data", subtopic="mean",
    title="Calculate the mean from a frequency table",
    difficulty_descriptions={
        1: "Whole-number data and an integer mean.",
        2: "Whole-number data and a non-integer mean.",
        3: "Calculate a mean or recover a missing frequency from a stated mean.",
        4: "Work with signed decimal data, a target mean or two combined groups.",
    },
    tags=("mean", "frequency_table", "weighted_mean"),
)


def presentation(values, frequencies):
    instruction = "Calculate the mean of the values in the frequency table."
    pairs = "; ".join(
        "{}: {}".format(decimal_text(value), frequency)
        for value, frequency in zip(values, frequencies)
    )
    prompt = Content(
        instruction + " Value: frequency — " + pairs + ".",
        display_text=instruction,
    )
    table = {
        "kind": "table", "version": 1,
        "headers": ["Value", "Frequency"],
        "rows": [[decimal_text(value), str(frequency)]
                 for value, frequency in zip(values, frequencies)],
    }
    return prompt, table


class FrequencyMean:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        if difficulty == 3 and rng.random() < 0.6:
            from .frequency_mean_forms import generate
            return generate(self, context, "missing_frequency")
        if difficulty == 4 and rng.random() < 0.7:
            from .frequency_mean_forms import generate
            return generate(self, context, rng.choice(
                ("target_observation", "combined_mean")
            ))
        count = 5 if difficulty == 3 else 4
        total = 20 if difficulty == 4 else 10
        active = count - 1 if difficulty == 3 else count

        for _ in range(500):
            cuts = [0] + sorted(rng.sample(range(1, total), active - 1)) + [total]
            frequencies = [b - a for a, b in zip(cuts, cuts[1:])]
            rng.shuffle(frequencies)
            if difficulty == 3:
                frequencies.insert(rng.randrange(count), 0)
            if difficulty == 4:
                values = sorted(Fraction(v, 2) for v in rng.sample(range(-15, 16), count))
                if not (values[0] < 0 < values[-1]):
                    continue
                if not any(v.denominator == 2 for v in values):
                    continue
            else:
                values = list(map(Fraction, sorted(rng.sample(range(0, 13), count))))
            mean = sum(v * f for v, f in zip(values, frequencies)) / total
            if (mean.denominator == 1) != (difficulty == 1):
                continue
            if mean == sum(values) / count:
                continue
            break
        else:
            raise ValueError("Could not construct a suitable frequency table")

        prompt, table = presentation(values, frequencies)
        display = decimal_text(mean)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt,
            answer={"kind": "rational", "value": rational_text(mean)},
            answer_display=Content(display, display), worked_solution=(),
            marks=3, tags=self.info.tags, layout_hint=LayoutHint(working_lines=4),
            parameters={
                "values": [rational_text(v) for v in values],
                "frequencies": frequencies,
            },
            question_visuals=(table,),
        )
        self.validate(question)
        return question

    def validate(self, question):
        if isinstance(question.parameters, dict) and "form" in question.parameters:
            from .frequency_mean_forms import validate
            return validate(self, question)
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        require(type(question.difficulty) is int and question.difficulty in (1, 2, 3, 4),
                "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")
        level = question.difficulty
        raw = question.parameters["values"]
        frequencies = question.parameters["frequencies"]
        require(isinstance(raw, list) and isinstance(frequencies, list),
                "Expected lists of data")
        require(len(raw) == len(frequencies) == (5 if level == 3 else 4),
                "Unexpected row count")
        values = list(map(Fraction, raw))
        require(raw == [rational_text(v) for v in values], "Non-canonical values")
        require(all(a < b for a, b in zip(values, values[1:])),
                "Values must be distinct and increasing")
        require(all(type(f) is int and 0 <= f <= 20 for f in frequencies),
                "Invalid frequency")
        require(sum(frequencies) == (20 if level == 4 else 10),
                "Unexpected total frequency")
        require(frequencies.count(0) == (1 if level == 3 else 0),
                "Zero-frequency structure mismatch")
        if level == 4:
            require(all(-Fraction(15, 2) <= v <= Fraction(15, 2)
                        and (v * 2).denominator == 1 for v in values),
                    "Decimal values outside bounds")
            require(values[0] < 0 < values[-1], "Expected both signs")
            require(any(v.denominator == 2 for v in values), "Expected decimal data")
        else:
            require(all(v.denominator == 1 and 0 <= v <= 12 for v in values),
                    "Expected bounded whole-number data")

        mean = Fraction(question.answer["value"])
        require(question.answer == {"kind": "rational", "value": rational_text(mean)},
                "Non-canonical answer")
        require(sum(v * f for v, f in zip(values, frequencies))
                == mean * sum(frequencies), "Incorrect weighted mean")
        require((mean.denominator == 1) == (level == 1), "Mean precision mismatch")
        require(mean != sum(values) / len(values), "Unweighted shortcut gives the answer")
        prompt, table = presentation(values, frequencies)
        require(question.prompt == prompt, "Prompt mismatch")
        require(question.visual_assets("questions") == (table,), "Table mismatch")
        require(not question.visual_assets("answers"), "Unexpected answer asset")
        display = decimal_text(mean)
        require(question.answer_display == Content(display, display),
                "Displayed answer mismatch")
        return True

    def validate_independently(self, question):
        """Expand the emitted table into observations; no weighted-sum helper."""
        if isinstance(question.parameters, dict) and "form" in question.parameters:
            from .frequency_mean_forms import validate_independently
            return validate_independently(question)
        import sympy

        observations = []
        for value, frequency in zip(
            question.parameters["values"], question.parameters["frequencies"]
        ):
            observations.extend([sympy.Rational(value)] * frequency)
        require(bool(observations), "Empty data set")
        result = sum(observations, sympy.Integer(0)) / len(observations)
        require(result == sympy.Rational(question.answer["value"]),
                "Independent expanded-data mean disagrees")
        return True