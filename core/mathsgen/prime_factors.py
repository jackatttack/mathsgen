"""Prime decomposition, HCF and LCM constructed from controlled factors."""
from functools import reduce
from math import gcd

from .core import Content, GeneratorInfo, LayoutHint, Question, make_context, require


def factorise(number):
    """Independent-of-generation trial division for small positive integers."""
    factors = {}
    divisor = 2
    while divisor * divisor <= number:
        while number % divisor == 0:
            factors[divisor] = factors.get(divisor, 0) + 1
            number //= divisor
        divisor += 1
    if number > 1:
        factors[number] = factors.get(number, 0) + 1
    return factors


def product(factors):
    result = 1
    for prime, power in factors.items():
        result *= int(prime) ** power
    return result


def factor_text(factors, tex=False):
    pieces = []
    for prime, power in sorted((int(p), e) for p, e in factors.items()):
        term = str(prime)
        if power != 1:
            term += "^{" + str(power) + "}" if tex else "^" + str(power)
        pieces.append(term)
    return (r" \times " if tex else " × ").join(pieces) or "1"


def common_value(numbers, operation):
    if operation == "hcf":
        return reduce(gcd, numbers)
    return reduce(lambda a, b: a // gcd(a, b) * b, numbers, 1)


def make_prompt(numbers, operation, level):
    if operation == "prime":
        return Content(
            "Express {} as a product of prime factors. Use index notation where appropriate.".format(numbers[0])
        )
    name = "highest common factor (HCF)" if operation == "hcf" else "lowest common multiple (LCM)"
    if level < 4:
        return Content("Find the {} of {}.".format(name, ", ".join(map(str, numbers))))
    labels = "ABC"[:len(numbers)]
    definitions = [
        "{} = {}".format(label, factor_text(factorise(number)))
        for label, number in zip(labels, numbers)
    ]
    return Content(
        "Given {}. Find the {} of {}. Give your answer as a product of prime factors.".format(
            "; ".join(definitions), name, ", ".join(labels)
        ),
        r",\quad ".join(
            label + "=" + factor_text(factorise(number), True)
            for label, number in zip(labels, numbers)
        ),
        display_text="Find the {} of A, B and C. Give your answer as a product of prime factors.".format(name),
    )


class FactorQuestion:
    """Shared exact-number checks, with separate registered question families."""

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        if self.operation in ("hcf", "lcm"):
            from . import factor_contexts as worded_forms
            if rng.random() < worded_forms.CONTEXT_SHARE.get(difficulty, 0.0):
                return worded_forms.generate(self, context)
        if self.operation == "prime":
            if difficulty == 1:
                primes = rng.sample((2, 3, 5, 7, 11), 2)
                powers = [1, 1]
            elif difficulty == 2:
                primes = rng.sample((2, 3, 5, 7), 2)
                powers = [rng.randint(2, 4), 1]
            elif difficulty == 3:
                primes = rng.sample((2, 3, 5, 7), 3)
                powers = [2, rng.choice((1, 2)), 1]
            else:
                primes = [rng.choice((11, 13)), rng.choice((2, 3, 5))]
                powers = [rng.choice((1, 2)), rng.choice((2, 3))]
            numbers = [product(dict(zip(primes, powers)))]
            answer_value = numbers[0]
        else:
            if difficulty == 1:
                smaller = rng.randint(4, 24)
                numbers = [smaller, smaller * rng.randint(2, 6)]
            elif difficulty == 2:
                shared = rng.randint(2, 12)
                first, second = rng.sample((2, 3, 5, 7), 2)
                numbers = [shared * first, shared * second]
            elif difficulty == 3:
                shared = rng.randint(2, 9)
                first, second, third = rng.sample((2, 3, 5, 7), 3)
                numbers = [
                    shared * first * second,
                    shared * first * third,
                    shared * second * third,
                ]
            else:
                # Unequal exponents and absent factors require choosing
                # minima/maxima, not simply multiplying the given numbers.
                a, b, c = rng.sample((2, 3, 5), 3)
                numbers = [
                    a ** rng.randint(2, 3) * b,
                    a * b ** rng.randint(2, 3) * c,
                    a ** 2 * c ** rng.randint(2, 3),
                ]
            rng.shuffle(numbers)
            answer_value = common_value(numbers, self.operation)

        factors = {str(prime): power for prime, power in factorise(answer_value).items()}
        show_factors = self.operation == "prime" or difficulty == 4
        answer = (
            {"kind": "prime_factorisation", "factors": factors}
            if show_factors else {"kind": "integer", "value": answer_value}
        )
        display = Content(
            factor_text(factors) if show_factors else str(answer_value),
            factor_text(factors, True) if show_factors else str(answer_value),
        )
        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=make_prompt(numbers, self.operation, difficulty),
            answer=answer,
            answer_display=display,
            worked_solution=(),
            marks=2 if difficulty <= 2 else 3,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=5),
            parameters={"numbers": numbers},
        )
        self.validate(question)
        return question

    def validate(self, question):
        from .worded import is_worded
        if self.operation in ("hcf", "lcm") and is_worded(question):
            from .factor_contexts import validate as validate_worded
            return validate_worded(self, question)
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in (1, 2, 3, 4), "Invalid difficulty")
        numbers = question.parameters["numbers"]
        size = 1 if self.operation == "prime" else (2 if level <= 2 else 3)
        require(len(numbers) == size, "Incorrect number of inputs")
        require(all(type(n) is int and 2 <= n <= 25000 for n in numbers), "Input outside bounds")
        require(len(set(numbers)) == size, "Repeated inputs")
        if self.operation == "prime":
            factors = factorise(numbers[0])
            powers = list(factors.values())
            if level == 1:
                require(len(factors) == 2 and powers == [1, 1], "Expected square-free semiprime")
            elif level == 2:
                require(len(factors) == 2 and sorted(powers)[0] == 1
                        and 2 <= max(powers) <= 4, "Expected one repeated prime")
            elif level == 3:
                require(len(factors) == 3 and max(powers) == 2, "Expected three prime factors")
            else:
                require(len(factors) == 2 and any(p in factors for p in (11, 13))
                        and max(powers) >= 2, "Expected less familiar repeated factors")
            expected = numbers[0]
        else:
            if level == 1:
                require(max(numbers) % min(numbers) == 0, "Expected divisibility")
            elif level == 2:
                require(max(numbers) % min(numbers) != 0 and gcd(*numbers) > 1,
                        "Expected overlapping factors without divisibility")
            expected = common_value(numbers, self.operation)

        show_factors = self.operation == "prime" or level == 4
        require(
            isinstance(question.answer, dict) and question.answer.get("kind") == (
                "prime_factorisation" if show_factors else "integer"),
            "Unexpected answer shape",
        )
        if show_factors:
            submitted = question.answer["factors"]
            require(submitted == {str(p): e for p, e in factorise(expected).items()},
                    "Incorrect prime factorisation")
            require(product(submitted) == expected, "Factor product disagrees")
            text, tex = factor_text(submitted), factor_text(submitted, True)
        else:
            require(type(question.answer["value"]) is int
                    and question.answer["value"] == expected, "Incorrect numerical answer")
            text = tex = str(expected)
        require(question.prompt == make_prompt(numbers, self.operation, level), "Prompt mismatch")
        require(question.answer_display == Content(text, tex), "Displayed answer mismatch")
        return True

    def validate_independently(self, question):
        from .worded import is_worded
        if self.operation in ("hcf", "lcm") and is_worded(question):
            from .factor_contexts import validate_independently as independent_worded
            return independent_worded(self, question)
        import sympy

        numbers = question.parameters["numbers"]
        if self.operation == "prime":
            expected = numbers[0]
        elif self.operation == "hcf":
            expected = int(sympy.igcd(*numbers))
        else:
            expected = int(sympy.ilcm(*numbers))
        if question.answer["kind"] == "prime_factorisation":
            expected_factors = {str(p): int(e) for p, e in sympy.factorint(expected).items()}
            require(question.answer["factors"] == expected_factors, "Independent factors disagree")
        else:
            require(question.answer["value"] == expected, "Independent HCF/LCM disagrees")
        return True


# ------------------------------------------------------------ prime factorisation v2
#
# PrimeFactorisation has its own forms and flow. FactorQuestion's "prime"
# branches are now unused and kept only so HCF and LCM stay untouched;
# remove them in a later tidy-up.

PRIME_FORMS = {1: ("express", "from_product"), 2: ("express", "from_product"),
               3: ("express", "square_root"), 4: ("express", "smallest_multiplier")}
SMALL_PRIMES = (2, 3, 5, 7)


def expanded_text(factors):
    """2 × 2 × 3 × 7: every factor written out, no indices."""
    pieces = []
    for prime, power in sorted((int(p), e) for p, e in factors.items()):
        pieces += [str(prime)] * power
    return " × ".join(pieces)


def prime_value(p):
    form = p["form"]
    if form == "express":
        return p["numbers"][0]
    if form == "from_product":
        return product(p["factors"])
    if form == "square_root":
        return product(p["root_factors"])
    n, power = p["number"], 2 if p["target"] == "square" else 3
    multiplier = 1
    for prime, exponent in factorise(n).items():
        multiplier *= prime ** ((-exponent) % power)
    return multiplier


def prime_prompt(p, level):
    form = p["form"]
    if form == "express":
        return make_prompt(p["numbers"], "prime", level)
    if form == "from_product":
        factors = p["factors"]
        if level == 1:
            return Content("Work out {}.".format(expanded_text(factors)))
        return Content("Work out {}.".format(factor_text(factors)), factor_text(factors, True),
                       display_text="Work out the value of this product of prime factors.")
    if form == "square_root":
        square = {prime: 2 * e for prime, e in p["root_factors"].items()}
        n = product(square)
        return Content(
            "{} = {}. Use this to find the square root of {}.".format(n, factor_text(square), n),
            "{} = {}".format(n, factor_text(square, True)),
            display_text="Use the prime factorisation below to find the square root of {}.".format(n),
        )
    return Content(
        "Find the smallest whole number that {} can be multiplied by to give a {} number.".format(
            p["number"], p["target"]))


def prime_answer(p):
    value = prime_value(p)
    if p["form"] == "express":
        factors = {str(prime): power for prime, power in factorise(value).items()}
        return ({"kind": "prime_factorisation", "factors": factors},
                Content(factor_text(factors), factor_text(factors, True)))
    return {"kind": "integer", "value": value}, Content(str(value), str(value))


def check_factor_dict(factors):
    require(isinstance(factors, dict) and factors, "Invalid factors")
    for prime, power in factors.items():
        require(prime.isdigit() and int(prime) in SMALL_PRIMES, "Unexpected prime")
        require(type(power) is int and power >= 1, "Invalid power")


def check_prime_parameters(p, level):
    require(isinstance(p, dict), "Parameters must be a dictionary")
    form = p.get("form")
    require(form in PRIME_FORMS[level], "Unexpected form for this level")
    keys = {"express": {"numbers"}, "from_product": {"factors"},
            "square_root": {"root_factors"}, "smallest_multiplier": {"number", "target"}}[form]
    require(set(p) == keys | {"form"}, "Unexpected parameters")
    if form == "express":
        numbers = p["numbers"]
        require(isinstance(numbers, list) and len(numbers) == 1
                and type(numbers[0]) is int and 2 <= numbers[0] <= 25000, "Input outside bounds")
        factors = factorise(numbers[0])
        powers = list(factors.values())
        if level == 1:
            require(len(factors) == 2 and powers == [1, 1], "Expected square-free semiprime")
        elif level == 2:
            require(len(factors) == 2 and sorted(powers)[0] == 1
                    and 2 <= max(powers) <= 4, "Expected one repeated prime")
        elif level == 3:
            require(len(factors) == 3 and max(powers) == 2, "Expected three prime factors")
        else:
            require(len(factors) == 2 and any(q in factors for q in (11, 13))
                    and max(powers) >= 2, "Expected less familiar repeated factors")
    elif form == "from_product":
        factors = p["factors"]
        check_factor_dict(factors)
        require(2 <= len(factors) <= 3, "Use two or three different primes")
        biggest = 2 if level == 1 else 4
        require(max(factors.values()) <= biggest and product(factors) <= 3000,
                "Product outside bounds")
        if level == 2:
            require(max(factors.values()) >= 2, "Expected index notation")
    elif form == "square_root":
        check_factor_dict(p["root_factors"])
        require(2 <= len(p["root_factors"]) <= 3 and max(p["root_factors"].values()) <= 2
                and 10 <= product(p["root_factors"]) <= 200, "Root outside bounds")
    else:
        require(p["target"] in ("square", "cube"), "Unknown target")
        n = p["number"]
        require(type(n) is int and 12 <= n <= 2000, "Number outside bounds")
        factors = factorise(n)
        require(2 <= len(factors) <= 3 and all(q in SMALL_PRIMES for q in factors),
                "Use two or three small primes")
        require(prime_value(p) > 1, "The number must not already qualify")


def draw_prime(rng, level):
    form = rng.choice(PRIME_FORMS[level])
    if form == "express":
        if level == 1:
            primes, powers = rng.sample((2, 3, 5, 7, 11), 2), [1, 1]
        elif level == 2:
            primes, powers = rng.sample((2, 3, 5, 7), 2), [rng.randint(2, 4), 1]
        elif level == 3:
            primes, powers = rng.sample((2, 3, 5, 7), 3), [2, rng.choice((1, 2)), 1]
        else:
            primes = [rng.choice((11, 13)), rng.choice((2, 3, 5))]
            powers = [rng.choice((1, 2)), rng.choice((2, 3))]
        return {"form": form, "numbers": [product(dict(zip(primes, powers)))]}
    primes = rng.sample(SMALL_PRIMES, rng.choice((2, 3)))
    if form == "from_product":
        biggest = 2 if level == 1 else 4
        return {"form": form, "factors": {str(q): rng.randint(1, biggest) for q in primes}}
    if form == "square_root":
        return {"form": form, "root_factors": {str(q): rng.randint(1, 2) for q in primes}}
    return {"form": form, "target": rng.choice(("square", "square", "cube")),
            "number": product({q: rng.randint(1, 3) for q in primes})}


class PrimeFactorisation(FactorQuestion):
    operation = "prime"
    info = GeneratorInfo(
        id="number.primes.factorisation", version=2, topic="number",
        subtopic="prime_factors", title="Prime factors: express, rebuild and use",
        difficulty_descriptions={
            1: "Two distinct prime factors, or multiply prime factors back out.",
            2: "A repeated prime factor with index notation, either direction.",
            3: "Three primes, or a square root from a prime factorisation.",
            4: "Factors involving 11 or 13, or the smallest multiplier for a square or cube.",
        },
        tags=("prime_factors", "indices"),
    )

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        for attempt in range(300):
            p = draw_prime(rng, difficulty)
            try:
                check_prime_parameters(p, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a prime-factor question")
        answer, display = prime_answer(p)
        marks = 3 if p["form"] in ("square_root", "smallest_multiplier") else (
            2 if difficulty <= 2 else 3)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prime_prompt(p, difficulty),
            answer=answer, answer_display=display, worked_solution=(),
            marks=marks, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=5), parameters=p,
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in (1, 2, 3, 4), "Invalid difficulty")
        p = question.parameters
        check_prime_parameters(p, level)
        answer, display = prime_answer(p)
        require(question.answer == answer, "Incorrect answer")
        require(question.answer_display == display, "Displayed answer mismatch")
        require(question.prompt == prime_prompt(p, level), "Prompt mismatch")
        return True

    def validate_independently(self, question):
        """SymPy factorint, a direct product, an integer root, or a brute-force search."""
        import sympy

        p, answer = question.parameters, question.answer
        form = p["form"]
        if form == "express":
            expected = {str(q): int(e) for q, e in sympy.factorint(p["numbers"][0]).items()}
            require(answer["factors"] == expected, "Independent factors disagree")
        elif form == "from_product":
            value = sympy.prod([sympy.Integer(q) ** e for q, e in p["factors"].items()])
            require(answer["value"] == int(value), "Independent product disagrees")
        elif form == "square_root":
            square = sympy.prod([sympy.Integer(q) ** (2 * e) for q, e in p["root_factors"].items()])
            root, exact = sympy.integer_nthroot(int(square), 2)
            require(exact and answer["value"] == root, "Independent square root disagrees")
        else:
            power = 2 if p["target"] == "square" else 3
            k = 1
            while not sympy.integer_nthroot(p["number"] * k, power)[1]:
                k += 1
            require(answer["value"] == k, "Independent smallest multiplier disagrees")
        return True


class HighestCommonFactor(FactorQuestion):
    operation = "hcf"
    info = GeneratorInfo(
        id="number.factors.hcf", version=2, topic="number",
        subtopic="hcf_lcm", title="Highest common factor",
        difficulty_descriptions={
            1: "Two numbers where one divides the other.",
            2: "Two numbers with shared factors; or cut two lengths into equal pieces.",
            3: "Three numbers with different common factors; or cut three lengths.",
            4: "Three supplied prime decompositions; or the greatest number of identical bags.",
        },
        tags=("hcf", "prime_factors"),
    )


class LowestCommonMultiple(FactorQuestion):
    operation = "lcm"
    info = GeneratorInfo(
        id="number.multiples.lcm", version=2, topic="number",
        subtopic="hcf_lcm", title="Lowest common multiple",
        difficulty_descriptions={
            1: "Two numbers where one divides the other.",
            2: "Two numbers with shared factors; or when two buses next leave together.",
            3: "Three numbers with overlapping factors; or three flashing lights.",
            4: "Three supplied prime decompositions; or the least packs to match two items.",
        },
        tags=("lcm", "prime_factors"),
    )