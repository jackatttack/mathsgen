"""Two-way tables and expected/relative frequency.

Two-way tables are stored as a count matrix plus the positions left blank in
the full table (row and column totals included). A propagation solver decides
difficulty by counting deduction rounds; the independent check solves the
row/column equations with SymPy and requires a unique solution, proving the
blanks are fully determined by what is shown.
"""
from fractions import Fraction

from .core import Content, GeneratorInfo, rational_tex, rational_text, require
from .family import GeneratorFamily
from .rounding import decimal_text


# =============================================================== two-way tables

CONTEXTS = {
    "travel": {
        "intro": "Some students were asked how they travel to school.",
        "noun": "student",
        "rows": ["Year 10", "Year 11"], "row_phrases": ["is in Year 10", "is in Year 11"],
        "columns": ["Walk", "Bus", "Car"],
        "column_phrases": ["walks to school", "travels by bus", "travels by car"],
    },
    "lunch": {
        "intro": "Some students recorded what they usually have for lunch.",
        "noun": "student",
        "rows": ["Year 7", "Year 8"], "row_phrases": ["is in Year 7", "is in Year 8"],
        "columns": ["Packed", "Hot meal"],
        "column_phrases": ["has a packed lunch", "has a hot meal"],
    },
    "club": {
        "intro": "Members of a leisure centre each chose one activity.",
        "noun": "member",
        "rows": ["Adult", "Child"], "row_phrases": ["is an adult", "is a child"],
        "columns": ["Swim", "Gym", "Tennis"],
        "column_phrases": ["chose swimming", "chose the gym", "chose tennis"],
    },
    "pets": {
        "intro": "Some people were asked where they live and which pet they own.",
        "noun": "person",
        "rows": ["Flat", "House"], "row_phrases": ["lives in a flat", "lives in a house"],
        "columns": ["Cat", "Dog", "No pet"],
        "column_phrases": ["owns a cat", "owns a dog", "owns no pet"],
    },
}
COUNT_RANGE = (3, 30)
BLANK_COUNTS = {1: (2, 3), 2: (4, 6), 4: (2, 3)}


def shape(context):
    return len(CONTEXTS[context]["rows"]), len(CONTEXTS[context]["columns"])


def full_grid(counts):
    """{(r, c): value} including row totals (c = C), column totals (r = R)."""
    rows, columns = len(counts), len(counts[0])
    grid = {(r, c): counts[r][c] for r in range(rows) for c in range(columns)}
    for r in range(rows):
        grid[(r, columns)] = sum(counts[r])
    for c in range(columns + 1):
        grid[(rows, c)] = sum(grid[(r, c)] for r in range(rows))
    return grid


def table_lines(rows, columns):
    """Each line is (parts, total): the parts sum to the total cell."""
    lines = [([(r, c) for c in range(columns)], (r, columns)) for r in range(rows + 1)]
    lines += [([(r, c) for r in range(rows)], (rows, c)) for c in range(columns + 1)]
    return lines


def propagate(grid, blanks, rows, columns):
    """Rounds of single-unknown deductions needed, or None if it stalls."""
    unknown = set(blanks)
    known = {pos: value for pos, value in grid.items() if pos not in unknown}
    rounds = 0
    while unknown:
        found = {}
        for parts, total in table_lines(rows, columns):
            missing = [pos for pos in parts + [total] if pos in unknown]
            if len(missing) != 1:
                continue
            pos = missing[0]
            if pos == total:
                found[pos] = sum(known[p] for p in parts)
            else:
                found[pos] = known[total] - sum(known[p] for p in parts if p != pos)
        if not found:
            return None
        known.update(found)
        unknown -= set(found)
        rounds += 1
    return rounds


def choose_blanks(rng, grid, rows, columns, level):
    low, high = BLANK_COUNTS[level]
    positions = sorted(grid)
    for _ in range(500):
        blanks = rng.sample(positions, rng.randint(low, high))
        rounds = propagate(grid, blanks, rows, columns)
        if rounds is None:
            continue
        if (level == 2 and rounds >= 2) or (level != 2 and rounds == 1):
            return sorted([list(pos) for pos in blanks])
    raise ValueError("Could not choose determinable blanks")


def table_spec(context, grid, blanks):
    ctx = CONTEXTS[context]
    rows, columns = shape(context)
    hidden = {tuple(pos) for pos in blanks}
    labels = ctx["rows"] + ["Total"]
    body = []
    for r in range(rows + 1):
        body.append([labels[r]] + [
            "" if (r, c) in hidden else str(grid[(r, c)]) for c in range(columns + 1)
        ])
    return {
        "kind": "table", "version": 1,
        "headers": [""] + ctx["columns"] + ["Total"],
        "weights": [1.5] + [1] * columns + [1.1],
        "rows": body,
    }


def table_text(context, grid, blanks):
    """Plain CLI rendering of the table; blanks shown as ?."""
    spec = table_spec(context, grid, blanks)
    headers = spec["headers"][1:]
    lines = []
    for row in spec["rows"]:
        cells = ", ".join("{} {}".format(h, v or "?") for h, v in zip(headers, row[1:]))
        lines.append("{}: {}".format(row[0], cells))
    return "Table — " + "; ".join(lines) + "."


def cell_label(context, pos):
    ctx = CONTEXTS[context]
    r, c = pos
    row = (ctx["rows"] + ["Total"])[r]
    column = (ctx["columns"] + ["Total"])[c]
    return "{}, {}".format(row, column)


def event_text(context, event):
    ctx = CONTEXTS[context]
    kind = event[0]
    if kind == "cell":
        return "{} and {}".format(ctx["row_phrases"][event[1]], ctx["column_phrases"][event[2]])
    if kind == "row":
        return ctx["row_phrases"][event[1]]
    return ctx["column_phrases"][event[1]]


def event_probability(grid, rows, columns, event):
    grand = grid[(rows, columns)]
    kind = event[0]
    if kind == "cell":
        return Fraction(grid[(event[1], event[2])], grand)
    if kind == "row":
        return Fraction(grid[(event[1], columns)], grand)
    if kind == "column":
        return Fraction(grid[(rows, event[1])], grand)
    r, c = event[1], event[2]
    if kind == "given_row":
        return Fraction(grid[(r, c)], grid[(r, columns)])
    return Fraction(grid[(r, c)], grid[(rows, c)])


def fraction_answer(value):
    return (
        {"kind": "rational", "value": rational_text(value)},
        Content(rational_text(value), rational_tex(value)),
    )


class TwoWayTables(GeneratorFamily):
    info = GeneratorInfo(
        id="probability.two_way.tables",
        version=1,
        topic="probability",
        subtopic="two_way_tables",
        title="Two-way tables",
        difficulty_descriptions={
            1: "Complete a two-way table; each blank takes one step.",
            2: "Complete a two-way table that needs a chain of deductions.",
            3: "Find a probability from a completed two-way table.",
            4: "Complete a table, then find a conditional probability.",
        },
        tags=("probability", "two_way_tables", "conditional_probability"),
    )
    keys = {
        1: {"context", "counts", "blanks"}, 2: {"context", "counts", "blanks"},
        3: {"context", "counts", "event"}, 4: {"context", "counts", "blanks", "event"},
    }

    def build(self, level, rng):
        context = rng.choice(sorted(CONTEXTS))
        rows, columns = shape(context)
        counts = [[rng.randint(*COUNT_RANGE) for _ in range(columns)] for _ in range(rows)]
        p = {"context": context, "counts": counts}
        grid = full_grid(counts)
        if level != 3:
            p["blanks"] = choose_blanks(rng, grid, rows, columns, level)
        if level == 3:
            kind = rng.choice(("cell", "cell", "row", "column"))
            if kind == "cell":
                p["event"] = ["cell", rng.randrange(rows), rng.randrange(columns)]
            elif kind == "row":
                p["event"] = ["row", rng.randrange(rows)]
            else:
                p["event"] = ["column", rng.randrange(columns)]
        if level == 4:
            kind = rng.choice(("given_row", "given_column"))
            p["event"] = [kind, rng.randrange(rows), rng.randrange(columns)]
        return p

    def check_rules(self, p, level):
        require(p["context"] in CONTEXTS, "Unknown context")
        rows, columns = shape(p["context"])
        counts = p["counts"]
        require(isinstance(counts, list) and len(counts) == rows
                and all(isinstance(row, list) and len(row) == columns for row in counts),
                "Count matrix has the wrong shape")
        require(all(type(v) is int and COUNT_RANGE[0] <= v <= COUNT_RANGE[1]
                    for row in counts for v in row), "Count outside bounds")
        grid = full_grid(counts)
        if level != 3:
            blanks = p["blanks"]
            require(isinstance(blanks, list) and all(
                isinstance(pos, list) and len(pos) == 2 and tuple(pos) in grid for pos in blanks),
                "Invalid blank positions")
            require(len({tuple(pos) for pos in blanks}) == len(blanks), "Repeated blank")
            low, high = BLANK_COUNTS[level]
            require(low <= len(blanks) <= high, "Blank count outside this level")
            rounds = propagate(grid, [tuple(pos) for pos in blanks], rows, columns)
            require(rounds is not None, "Blanks cannot be deduced")
            require(rounds >= 2 if level == 2 else rounds == 1, "Deduction depth outside this level")
        if level in (3, 4):
            event = p["event"]
            require(isinstance(event, list) and bool(event), "Invalid event")
            kind = event[0]
            if level == 3:
                require(kind in ("cell", "row", "column"), "Event outside this level")
                if kind == "cell":
                    require(len(event) == 3 and event[1] in range(rows) and event[2] in range(columns),
                            "Invalid cell event")
                elif kind == "row":
                    require(len(event) == 2 and event[1] in range(rows), "Invalid row event")
                else:
                    require(len(event) == 2 and event[1] in range(columns), "Invalid column event")
            else:
                require(kind in ("given_row", "given_column") and len(event) == 3
                        and event[1] in range(rows) and event[2] in range(columns),
                        "Invalid conditional event")

    def parts(self, p, level):
        context = p["context"]
        ctx = CONTEXTS[context]
        rows, columns = shape(context)
        grid = full_grid(p["counts"])
        blanks = p.get("blanks", [])
        noun = ctx["noun"]
        if level in (1, 2):
            instruction = "Complete the two-way table."
        elif level == 3:
            instruction = "One {} is chosen at random. Find the probability that the {} {}.".format(
                noun, noun, event_text(context, p["event"]))
        else:
            kind, r, c = p["event"]
            given, target = (
                (ctx["row_phrases"][r], ctx["column_phrases"][c]) if kind == "given_row"
                else (ctx["column_phrases"][c], ctx["row_phrases"][r])
            )
            instruction = (
                "Complete the two-way table. A {} who {} is chosen at random. "
                "Find the probability that the {} {}."
            ).format(noun, given, noun, target)
        prose = ctx["intro"] + " " + instruction
        prompt = Content(
            ctx["intro"] + " " + table_text(context, grid, blanks) + " " + instruction,
            display_text=prose,
        )
        result = {
            "prompt": prompt,
            "question_visuals": [table_spec(context, grid, blanks)],
            "marks": {1: 2, 2: 3, 3: 2, 4: 3}[level],
            "working_lines": {1: 2, 2: 3, 3: 3, 4: 4}[level],
        }
        if level in (1, 2):
            values = [[r, c, grid[(r, c)]] for r, c in blanks]
            result["answer"] = {"kind": "table_completion", "values": values}
            result["answer_display"] = Content("; ".join(
                "{}: {}".format(cell_label(context, (r, c)), v) for r, c, v in values))
        else:
            probability = event_probability(grid, rows, columns, p["event"])
            result["answer"], result["answer_display"] = fraction_answer(probability)
        if level != 3:
            result["answer_visuals"] = [table_spec(context, grid, [])]
        return result

    def validate_independently(self, question):
        """Solve the displayed table's equations; the solution must be unique."""
        import sympy
        p, level = question.parameters, question.difficulty
        rows, columns = shape(p["context"])
        grid = full_grid(p["counts"])
        blanks = [tuple(pos) for pos in p.get("blanks", [])]
        symbols = {pos: sympy.Symbol("cell_{}_{}".format(*pos)) for pos in blanks}

        def cell(pos):
            return symbols.get(pos, grid[pos])

        # Fully shown lines simplify to True or False: check them directly
        # and pass only lines containing an unknown to the solver.
        equations = []
        for parts, total in table_lines(rows, columns):
            equation = sympy.Eq(sum(cell(pos) for pos in parts), cell(total))
            if equation is sympy.true:
                continue
            require(equation is not sympy.false, "Displayed table is inconsistent")
            equations.append(equation)
        solved = dict(grid)
        if blanks:
            solutions = sympy.linsolve(equations, [symbols[pos] for pos in blanks])
            require(len(solutions) == 1, "Blanks are not uniquely determined")
            (solution,) = solutions
            require(all(value.is_Integer for value in solution), "Blanks are not uniquely determined")
            for pos, value in zip(blanks, solution):
                require(int(value) == grid[pos], "Independent table solution disagrees")

        if level in (1, 2):
            require(question.answer["values"] == [[r, c, grid[(r, c)]] for r, c in blanks],
                    "Answer values disagree")
        else:
            event = p["event"]
            kind = event[0]
            grand = sum(p["counts"][r][c] for r in range(rows) for c in range(columns))
            if kind == "cell":
                expected = sympy.Rational(p["counts"][event[1]][event[2]], grand)
            elif kind == "row":
                expected = sympy.Rational(sum(p["counts"][event[1]]), grand)
            elif kind == "column":
                expected = sympy.Rational(sum(row[event[1]] for row in p["counts"]), grand)
            elif kind == "given_row":
                expected = sympy.Rational(p["counts"][event[1]][event[2]], sum(p["counts"][event[1]]))
            else:
                expected = sympy.Rational(p["counts"][event[1]][event[2]],
                                          sum(row[event[2]] for row in p["counts"]))
            require(expected == sympy.Rational(question.answer["value"]), "Independent probability disagrees")
        return True


# =================================================== expected / relative frequency

TRIAL_CONTEXTS = {
    "spinner": {"object": "a spinner", "verb": "spun", "lands": "lands on red", "event": "landing on red"},
    "coin": {"object": "a biased coin", "verb": "flipped", "lands": "lands on heads", "event": "landing on heads"},
    "dice": {"object": "a biased dice", "verb": "rolled", "lands": "lands on a six", "event": "landing on a six"},
    "pin": {"object": "a drawing pin", "verb": "dropped", "lands": "lands point up", "event": "landing point up"},
}
PROBABILITIES = tuple(Fraction(k, 20) for k in range(1, 20))
EXPECTED_TRIALS = (50, 100, 200, 300, 400, 500, 1000)
RELATIVE_TRIALS = (20, 25, 40, 50, 80, 100, 200)
FUTURE_TRIALS = (100, 200, 300, 400, 500, 600, 1000)
COLOURS = ("Red", "Blue", "Green", "Yellow")
SPINNER_TRIALS = (200, 400, 500, 1000)


def capitalised(text):
    return text[0].upper() + text[1:]


def whole(value):
    return Fraction(value).denominator == 1


class ExpectedFrequency(GeneratorFamily):
    info = GeneratorInfo(
        id="probability.frequency.expected",
        version=1,
        topic="probability",
        subtopic="relative_frequency",
        title="Expected and relative frequency",
        difficulty_descriptions={
            1: "Expected frequency from a given probability.",
            2: "Relative frequency from experimental results.",
            3: "Estimate a future count from earlier results.",
            4: "Find a missing probability in a table, then an expected count.",
        },
        tags=("probability", "expected_frequency", "relative_frequency"),
    )
    keys = {
        1: {"context", "probability", "trials"},
        2: {"context", "trials", "successes"},
        3: {"context", "trials", "successes", "future_trials"},
        4: {"probabilities", "missing", "trials"},
    }

    def build(self, level, rng):
        context = rng.choice(sorted(TRIAL_CONTEXTS))
        if level == 1:
            for _ in range(200):
                probability, trials = rng.choice(PROBABILITIES), rng.choice(EXPECTED_TRIALS)
                if whole(probability * trials):
                    return {"context": context, "probability": rational_text(probability), "trials": trials}
        if level == 2:
            trials = rng.choice(RELATIVE_TRIALS)
            return {"context": context, "trials": trials, "successes": rng.randint(1, trials - 1)}
        if level == 3:
            for _ in range(200):
                trials = rng.choice(RELATIVE_TRIALS)
                successes = rng.randint(1, trials - 1)
                future = rng.choice(FUTURE_TRIALS)
                if future > trials and whole(Fraction(successes, trials) * future):
                    return {"context": context, "trials": trials, "successes": successes,
                            "future_trials": future}
        if level == 4:
            for _ in range(500):
                shown = [rng.choice(PROBABILITIES[:10]) for _ in range(3)]
                missing_value = 1 - sum(shown)
                if Fraction(1, 20) <= missing_value <= Fraction(1, 2):
                    missing = rng.randrange(4)
                    values = shown[:missing] + [missing_value] + shown[missing:]
                    return {"probabilities": [rational_text(v) for v in values],
                            "missing": missing, "trials": rng.choice(SPINNER_TRIALS)}
        raise ValueError("Could not build a frequency question")

    def check_rules(self, p, level):
        if level == 4:
            values = p["probabilities"]
            require(isinstance(values, list) and len(values) == 4, "Expected four probabilities")
            fractions = [Fraction(v) for v in values]
            require(all(rational_text(f) == v for f, v in zip(fractions, values)), "Non-canonical value")
            require(all(f in PROBABILITIES[:10] for f in fractions), "Probability outside bounds")
            require(sum(fractions) == 1, "Probabilities must total 1")
            require(p["missing"] in range(4), "Invalid missing position")
            require(p["trials"] in SPINNER_TRIALS, "Trials outside bounds")
            require(whole(fractions[p["missing"]] * p["trials"]), "Expected count must be whole")
            return
        require(p["context"] in TRIAL_CONTEXTS, "Unknown context")
        if level == 1:
            probability = Fraction(p["probability"])
            require(rational_text(probability) == p["probability"] and probability in PROBABILITIES,
                    "Probability outside bounds")
            require(p["trials"] in EXPECTED_TRIALS and whole(probability * p["trials"]),
                    "Expected count must be whole")
            return
        require(p["trials"] in RELATIVE_TRIALS, "Trials outside bounds")
        require(type(p["successes"]) is int and 1 <= p["successes"] < p["trials"], "Successes outside bounds")
        if level == 3:
            future = p["future_trials"]
            require(future in FUTURE_TRIALS and future > p["trials"], "Future trials outside bounds")
            require(whole(Fraction(p["successes"], p["trials"]) * future), "Estimate must be whole")

    def parts(self, p, level):
        if level == 4:
            fractions = [Fraction(v) for v in p["probabilities"]]
            missing = p["missing"]
            colour = COLOURS[missing]
            cells = ["" if i == missing else decimal_text(f) for i, f in enumerate(fractions)]
            instruction = (
                "The table shows the probability that a spinner lands on each colour. "
                "The probability for {} is missing. The spinner is spun {} times. "
                "Estimate the number of times it lands on {}."
            ).format(colour.lower(), p["trials"], colour.lower())
            table_plain = "Table — " + ", ".join(
                "{} {}".format(name, cell or "?") for name, cell in zip(COLOURS, cells)) + "."
            value = fractions[missing] * p["trials"]
            completed = [decimal_text(f) for f in fractions]
            spec = {"kind": "table", "version": 1, "headers": ["Colour"] + list(COLOURS),
                    "weights": [1.6, 1, 1, 1, 1], "rows": [["Probability"] + cells]}
            answer = {"kind": "rational", "value": rational_text(value)}
            return {
                "prompt": Content(instruction + " " + table_plain, display_text=instruction),
                "question_visuals": [spec],
                "answer_visuals": [dict(spec, rows=[["Probability"] + completed])],
                "answer": answer,
                "answer_display": Content("{} = {}; about {} times".format(
                    colour, decimal_text(fractions[missing]), rational_text(value))),
                "marks": 3, "working_lines": 4,
            }
        ctx = TRIAL_CONTEXTS[p["context"]]
        subject = capitalised(ctx["object"])
        if level == 1:
            probability = Fraction(p["probability"])
            text = (
                "The probability that {} {} is {}. It is {} {} times. "
                "Estimate the number of times it {}."
            ).format(ctx["object"], ctx["lands"], decimal_text(probability), ctx["verb"],
                     p["trials"], ctx["lands"])
            value = probability * p["trials"]
        elif level == 2:
            text = (
                "{} is {} {} times. It {} {} times. "
                "Find the relative frequency of it {}."
            ).format(subject, ctx["verb"], p["trials"], ctx["lands"], p["successes"], ctx["event"])
            value = Fraction(p["successes"], p["trials"])
        else:
            text = (
                "{} is {} {} times. It {} {} times. "
                "Estimate how many times it {} if it is {} {} times."
            ).format(subject, ctx["verb"], p["trials"], ctx["lands"], p["successes"],
                     ctx["lands"], ctx["verb"], p["future_trials"])
            value = Fraction(p["successes"], p["trials"]) * p["future_trials"]
        shown = decimal_text(value) if level == 2 else rational_text(value)
        return {
            "prompt": Content(text),
            "answer": {"kind": "rational", "value": rational_text(value)},
            "answer_display": Content(shown),
            "marks": {1: 1, 2: 2, 3: 2}[level],
            "working_lines": {1: 2, 2: 2, 3: 3}[level],
        }

    def validate_independently(self, question):
        import sympy
        p, level = question.parameters, question.difficulty
        answer = sympy.Rational(question.answer["value"])
        if level == 1:
            expected = sympy.Rational(p["probability"]) * p["trials"]
        elif level == 2:
            expected = sympy.Rational(p["successes"], p["trials"])
        elif level == 3:
            expected = sympy.Rational(p["successes"], p["trials"]) * p["future_trials"]
        else:
            shown = [sympy.Rational(v) for i, v in enumerate(p["probabilities"]) if i != p["missing"]]
            expected = (1 - sum(shown)) * p["trials"]
        require(expected == answer, "Independent frequency check failed")
        if level != 2:
            require(answer.q == 1, "Expected counts must be whole")
        return True