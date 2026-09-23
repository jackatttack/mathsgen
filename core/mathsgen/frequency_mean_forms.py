"""Reverse and combined means from the facts printed in frequency tables."""
from fractions import Fraction

from .core import Content, LayoutHint, Question, rational_text, require
from .rounding import decimal_text, terminates


FORMS = {"missing_frequency": 3, "target_observation": 4, "combined_mean": 4}
MARKS = {"missing_frequency": 4, "target_observation": 4, "combined_mean": 4}
LINES = {"missing_frequency": 5, "target_observation": 6, "combined_mean": 6}


def split_total(rng, total):
    cuts = [0] + sorted(rng.sample(range(1, total), 3)) + [total]
    return [b - a for a, b in zip(cuts, cuts[1:])]


def values_for(rng, level):
    if level == 3:
        return sorted(rng.sample(range(0, 13), 4))
    return sorted(Fraction(v, 2) for v in rng.sample(range(-15, 16), 4))


def build(rng, form):
    values = values_for(rng, FORMS[form])
    raw = [rational_text(v) for v in values]
    if form == "missing_frequency":
        frequencies = [rng.randint(1, 6) for _ in values]
        unknown = rng.randrange(4)
        hidden = rng.randint(2, 8)
        frequencies[unknown] = hidden
        target = Fraction(
            sum(v * f for v, f in zip(values, frequencies)), sum(frequencies)
        )
        frequencies[unknown] = None
        return {"form": form, "values": raw, "frequencies": frequencies,
                "mean": rational_text(target)}
    if form == "target_observation":
        frequencies = split_total(rng, 19)
        new_value = Fraction(rng.randint(-16, 16), 2)
        target = (sum(v * f for v, f in zip(values, frequencies))
                  + new_value) / 20
        return {"form": form, "values": raw, "frequencies": frequencies,
                "mean": rational_text(target)}
    return {"form": form, "values": raw,
            "first": split_total(rng, 8), "second": split_total(rng, 12)}


def checked_values(p, level):
    raw = p["values"]
    require(isinstance(raw, list) and len(raw) == 4, "Expected four table values")
    values = [Fraction(v) for v in raw]
    require(raw == [rational_text(v) for v in values]
            and all(left < right for left, right in zip(values, values[1:])),
            "Non-canonical or unordered values")
    if level == 3:
        require(all(v.denominator == 1 and 0 <= v <= 12 for v in values),
                "Missing-frequency values outside bounds")
    else:
        require(all(-Fraction(15, 2) <= v <= Fraction(15, 2)
                    and (2 * v).denominator == 1 for v in values)
                and values[0] < 0 < values[-1]
                and any(v.denominator == 2 for v in values),
                "Expected bounded signed decimal data")
    return values


def checked_frequencies(raw, total=None, allow_missing=False):
    require(isinstance(raw, list) and len(raw) == 4, "Expected four frequencies")
    if allow_missing:
        require(raw.count(None) == 1, "Exactly one frequency must be missing")
    else:
        require(None not in raw, "Frequency is missing")
    require(all(f is None or type(f) is int and 1 <= f <= 19 for f in raw),
            "Invalid frequency")
    if total is not None:
        require(sum(raw) == total, "Wrong group size")


def check(p):
    form = p.get("form")
    require(form in FORMS, "Unknown frequency-mean form")
    expected = ({"form", "values", "first", "second"} if form == "combined_mean"
                else {"form", "values", "frequencies", "mean"})
    require(set(p) == expected, "Unexpected frequency-mean parameters")
    values = checked_values(p, FORMS[form])
    if form == "combined_mean":
        first, second = p["first"], p["second"]
        checked_frequencies(first, 8)
        checked_frequencies(second, 12)
        first_mean = sum(v * f for v, f in zip(values, first)) / 8
        second_mean = sum(v * f for v, f in zip(values, second)) / 12
        require(first_mean != second_mean, "Classes need different means")
        answer = sum(v * (a + b) for v, a, b in zip(values, first, second)) / 20
        require(terminates(answer), "Combined mean must be an exact decimal")
        return answer

    frequencies = p["frequencies"]
    mean = Fraction(p["mean"])
    require(p["mean"] == rational_text(mean) and terminates(mean),
            "Expected a canonical terminating stated mean")
    if form == "missing_frequency":
        checked_frequencies(frequencies, allow_missing=True)
        require(0 <= mean <= 12, "Stated mean outside bounds")
        index = frequencies.index(None)
        known_total = sum(f for f in frequencies if f is not None)
        known_sum = sum(v * f for v, f in zip(values, frequencies) if f is not None)
        require(values[index] != mean, "Mean does not determine the frequency")
        missing = (mean * known_total - known_sum) / (values[index] - mean)
        require(missing.denominator == 1 and 2 <= missing <= 8,
                "Missing frequency outside bounds")
        return missing

    checked_frequencies(frequencies, 19)
    weighted_sum = sum(v * f for v, f in zip(values, frequencies))
    new_value = 20 * mean - weighted_sum
    require((2 * new_value).denominator == 1 and -8 <= new_value <= 8
            and new_value not in values and mean != weighted_sum / 19,
            "New observation outside bounds or adds no change")
    return new_value


def parts(p):
    form = p["form"]
    values = [Fraction(v) for v in p["values"]]
    answer = check(p)
    if form == "combined_mean":
        rows = [[decimal_text(v), str(a), str(b)]
                for v, a, b in zip(values, p["first"], p["second"])]
        headers = ["Change (°C)", "Station A", "Station B"]
        detail = "; ".join("{}: A {}, B {}".format(*row) for row in rows)
        instruction = (
            "Station A recorded 8 temperature changes and Station B recorded "
            "12, all in °C. Find the mean change across all 20 readings."
        )
        display = decimal_text(answer) + " °C"
    else:
        frequencies = p["frequencies"]
        rows = [[decimal_text(v), "x" if f is None else str(f)]
                for v, f in zip(values, frequencies)]
        headers = ["Value", "Frequency"]
        detail = "; ".join("{}: {}".format(*row) for row in rows)
        if form == "missing_frequency":
            instruction = (
                "The mean of this frequency table is {}. "
                "Find the missing frequency x."
            ).format(decimal_text(Fraction(p["mean"])))
        else:
            headers = ["Change (°C)", "Frequency"]
            instruction = (
                "The table shows 19 temperature changes in °C. One more "
                "change x is recorded, making the mean of all 20 changes "
                "{} °C. Find x."
            ).format(decimal_text(Fraction(p["mean"])))
        display = "x = " + decimal_text(answer)
        if form == "target_observation":
            display += " °C"
    columns = ("Change (°C): Station A frequency, Station B frequency"
               if form == "combined_mean" else
               "Change (°C): frequency" if form == "target_observation"
               else "Value: frequency")
    prompt = Content(instruction + " " + columns + " — " + detail + ".",
                     display_text=instruction)
    table = {"kind": "table", "version": 1, "headers": headers, "rows": rows}
    return (prompt, table,
            {"kind": "rational", "value": rational_text(answer)},
            Content(display))


def generate(generator, context, form):
    rng = context.rng
    for _ in range(500):
        p = build(rng, form)
        try:
            check(p)
        except ValueError:
            continue
        break
    else:
        raise ValueError("Could not construct a frequency-mean follow-up")
    prompt, table, answer, display = parts(p)
    info = generator.info
    q = Question(
        id=context.identity, generator_id=info.id, generator_version=info.version,
        topic=info.topic, subtopic=info.subtopic, difficulty=context.difficulty,
        seed=context.seed, settings=context.settings, prompt=prompt,
        answer=answer, answer_display=display, worked_solution=(),
        marks=MARKS[form], tags=info.tags,
        layout_hint=LayoutHint(working_lines=LINES[form]),
        parameters=p, question_visuals=(table,),
    )
    generator.validate(q)
    return q


def validate(generator, q):
    p = q.parameters
    form = p.get("form")
    require(q.generator_id == generator.info.id
            and q.generator_version == generator.info.version
            and q.settings == {} and q.difficulty == FORMS.get(form),
            "Wrong frequency-mean family or level")
    prompt, table, answer, display = parts(p)
    require(q.prompt == prompt and q.answer == answer
            and q.answer_display == display, "Incorrect frequency-mean question")
    require(q.visual_assets("questions") == (table,)
            and not q.visual_assets("answers"), "Frequency table mismatch")
    require(q.marks == MARKS[form]
            and q.layout_hint.working_lines == LINES[form],
            "Marks or working space mismatch")
    return True


def validate_independently(q):
    """Reconstruct the printed data with SymPy; solve missing quantities."""
    import sympy
    p = q.parameters
    values = [sympy.Rational(value) for value in p["values"]]
    form = p["form"]
    if form == "combined_mean":
        observations = []
        for value, a, b in zip(values, p["first"], p["second"]):
            observations.extend([value] * (a + b))
        expected = sum(observations, sympy.Integer(0)) / len(observations)
    else:
        x = sympy.Symbol("x")
        if form == "missing_frequency":
            frequencies = [x if f is None else f for f in p["frequencies"]]
            equation = sympy.Eq(
                sum((value * f for value, f in zip(values, frequencies)),
                    sympy.Integer(0)),
                sympy.Rational(p["mean"]) * sum(frequencies),
            )
        else:
            observations = []
            for value, frequency in zip(values, p["frequencies"]):
                observations.extend([value] * frequency)
            equation = sympy.Eq(
                (sum(observations, sympy.Integer(0)) + x)
                / (len(observations) + 1),
                sympy.Rational(p["mean"]),
            )
        solutions = sympy.solve(equation, x)
        require(len(solutions) == 1, "Follow-up must have one solution")
        expected = solutions[0]
    require(expected == sympy.Rational(q.answer["value"]),
            "Independent frequency-mean follow-up disagrees")
    return True