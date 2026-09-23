"""Find a missing data value in a frequency table from its exact mean."""
from dataclasses import replace
from fractions import Fraction

from .core import Content, GeneratorInfo, LayoutHint, make_context, rational_text, require
from .frequency_mean import FrequencyMean, presentation as complete_presentation
from .rounding import decimal_text


INFO = GeneratorInfo(
    id="data.mean.frequency_missing_value", version=1, topic="data", subtopic="mean",
    title="Find a missing value in a frequency table",
    difficulty_descriptions={
        1: "Whole-number data with a stated integer mean.",
        2: "Whole-number data with a stated decimal mean.",
        3: "A known zero-frequency row alongside the missing value.",
        4: "A missing decimal value among data of both signs.",
    },
    tags=("mean", "frequency_table", "missing_value", "equations"),
)


def presentation(values, frequencies, mean):
    instruction = (
        "The mean of the values in the frequency table is {}. "
        "Find the missing value x."
    ).format(decimal_text(mean))
    rows = [
        ["x" if v is None else decimal_text(Fraction(v)), str(f)]
        for v, f in zip(values, frequencies)
    ]
    return Content(
        instruction + " Value: frequency — "
        + "; ".join(": ".join(row) for row in rows) + ".",
        display_text=instruction,
    ), {
        "kind": "table", "version": 1,
        "headers": ["Value", "Frequency"], "rows": rows,
    }


class FrequencyMissingValue:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        # Reuse the bounded plain-table construction, not its question identity.
        # FrequencyMean v2 sometimes returns a reverse "form" question at levels
        # 3 and 4, whose missing frequency is None; draw again until the table is
        # complete. The first draw is unchanged, so earlier working seeds match.
        for _ in range(100):
            base = FrequencyMean().generate(context.rng.getrandbits(63), difficulty)
            if "form" not in base.parameters:
                break
        else:
            raise ValueError("Could not draw a complete frequency table")
        values = list(base.parameters["values"])
        frequencies = list(base.parameters["frequencies"])
        eligible = [
            i for i, frequency in enumerate(frequencies)
            if frequency > 0 and (
                difficulty != 4 or Fraction(values[i]).denominator != 1
            )
        ]
        require(bool(eligible), "No suitable missing value")
        index = context.rng.choice(eligible)
        result = Fraction(values[index])
        values[index] = None
        mean = Fraction(base.answer["value"])
        prompt, table = presentation(values, frequencies, mean)
        display = "x = " + decimal_text(result)
        question = replace(
            base, id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, seed=seed,
            settings=context.settings, prompt=prompt, tags=self.info.tags,
            answer={"kind": "rational", "value": rational_text(result)},
            answer_display=Content(display, display),
            parameters={
                "values": values, "frequencies": frequencies,
                "mean": rational_text(mean),
            },
            layout_hint=LayoutHint(working_lines=5), marks=3,
            question_visuals=(table,),
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        values = question.parameters["values"]
        frequencies = question.parameters["frequencies"]
        require(isinstance(values, list) and isinstance(frequencies, list),
                "Expected lists")
        require(len(values) == len(frequencies) and values.count(None) == 1,
                "Exactly one missing value required")
        index = values.index(None)
        require(type(frequencies[index]) is int and frequencies[index] > 0,
                "Missing value has no observations and is not determined")
        result = Fraction(question.answer["value"])
        require(question.answer == {"kind": "rational", "value": rational_text(result)},
                "Non-canonical answer")
        mean = Fraction(question.parameters["mean"])
        require(question.parameters["mean"] == rational_text(mean), "Non-canonical mean")
        if question.difficulty == 4:
            require(result.denominator != 1, "Expected a missing decimal value")

        # Reconstruct the complete table and apply its mathematical and
        # structural checks, including sorted distinct values and exact mean.
        full = [rational_text(result) if v is None else v for v in values]
        numeric = list(map(Fraction, full))
        base_prompt, base_table = complete_presentation(numeric, frequencies)
        display_mean = decimal_text(mean)
        complete = replace(
            question, generator_id=FrequencyMean.info.id,
            generator_version=FrequencyMean.info.version,
            parameters={"values": full, "frequencies": frequencies},
            prompt=base_prompt, question_visuals=(base_table,),
            answer={"kind": "rational", "value": rational_text(mean)},
            answer_display=Content(display_mean, display_mean),
        )
        FrequencyMean().validate(complete)

        prompt, table = presentation(values, frequencies, mean)
        require(question.prompt == prompt, "Prompt mismatch")
        require(question.visual_assets("questions") == (table,), "Table mismatch")
        require(not question.visual_assets("answers"), "Unexpected answer assets")
        display = "x = " + decimal_text(result)
        require(question.answer_display == Content(display, display), "Display mismatch")
        return True

    def validate_independently(self, question):
        """Expand known observations and recover the missing repeated value."""
        import sympy

        known = []
        missing_counts = []
        for value, frequency in zip(
            question.parameters["values"], question.parameters["frequencies"]
        ):
            if value is None:
                missing_counts.append(frequency)
            else:
                known.extend([sympy.Rational(value)] * frequency)
        require(len(missing_counts) == 1 and missing_counts[0] > 0,
                "Independent check found no unique missing value")
        count = missing_counts[0]
        total_count = len(known) + count
        target = sympy.Rational(question.parameters["mean"]) * total_count
        recovered = (target - sum(known, sympy.Integer(0))) / count
        require(recovered == sympy.Rational(question.answer["value"]),
                "Independent missing value disagrees")
        return True