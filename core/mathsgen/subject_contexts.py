"""Worded contexts for algebra.rearranging.changing_subject.

Each context is "(a) make the subject, (b) use your formula":
L1 taxi fare C = pm + f        L2 candle h = L - rt
L3 F = 9C/5 + 32; v = u + at   L4 E = (1/2)mv^2; s = 5t^2 (positive roots)

check() computes the value exactly from the displayed numbers.
solve() rearranges the original formula with SymPy, proves the stated
formula equivalent, and solves the numerical case from the original formula.
"""
from fractions import Fraction
from math import isqrt

from .core import Content, rational_tex, rational_text, require
from . import worded
from .worded import Context, exact, integers, rich_prompt, whole


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {1: 0.35, 2: 0.4, 3: 0.5, 4: 0.5}
MARKS = {1: 3, 2: 3, 3: 4, 4: 4}
WORKING_LINES = {1: 5, 2: 5, 3: 7, 4: 7}


def maths(text, tex=None):
    return (tex if tex is not None else text, text)


def formula_answer(subject, formula, value, unit):
    return {"kind": "formula_and_value", "subject": subject, "formula": formula,
            "value": rational_text(exact(value)), "unit": unit}


def formula_display(subject, formula, formula_tex, value, unit):
    value = exact(value)
    tail = " " + unit if unit else ""
    tex_tail = r"\ \mathrm{" + unit.replace(" ", r"\ ") + "}" if unit else ""
    return Content("{}; {} = {}{}".format(formula, subject, rational_text(value), tail),
                   formula_tex + r",\quad " + subject + " = " + rational_tex(value) + tex_tail)


def equivalent(sympy, solutions, stated):
    require(any(sympy.simplify(solution - stated) == 0 for solution in solutions),
            "Stated formula is not an independent rearrangement")


# ------------------------------------------------------------ L1 taxi

def build_taxi(rng):
    p, f, miles = rng.randint(2, 4), rng.randint(2, 8), rng.randint(3, 20)
    return {"context": "taxi", "p": p, "f": f, "cost": p * miles + f}


def check_taxi(p):
    integers(p, "p f cost")
    require(2 <= p["p"] <= 4 and 2 <= p["f"] <= 8, "Formula bounds")
    return whole(Fraction(p["cost"] - p["f"], p["p"]), 3, 20, "Miles must be whole")


def taxi_formula(p):
    return ("m = (C - {})/{}".format(p["f"], p["p"]),
            r"m = \frac{C - " + str(p["f"]) + "}{" + str(p["p"]) + "}")


def parts_taxi(p):
    miles = check_taxi(p)
    plain, tex = taxi_formula(p)
    formula = "C = {}m + {}".format(p["p"], p["f"])
    prompt = rich_prompt(
        ("The cost, £", maths("C"), ", of a taxi journey of ", maths("m"),
         " miles is given by the formula ", maths(formula), "."),
        ("(a) Make ", maths("m"), " the subject of the formula.",),
        ("(b) Use your formula to find ", maths("m"), " when ",
         maths("C = {}".format(p["cost"])), "."),
    )
    return {"prompt": prompt, "answer": formula_answer("m", plain, miles, "miles"),
            "answer_display": formula_display("m", plain, tex, miles, "miles")}


def solve_taxi(p, sympy):
    C, m = sympy.symbols("C m")
    equivalent(sympy, sympy.solve(sympy.Eq(C, p["p"] * m + p["f"]), m), (C - p["f"]) / p["p"])
    (value,) = sympy.solve(sympy.Eq(p["cost"], p["p"] * m + p["f"]), m)
    return formula_answer("m", taxi_formula(p)[0], value, "miles")


# ------------------------------------------------------------ L2 candle

def build_candle(rng):
    length, rate, hours = rng.randint(15, 40), rng.randint(2, 5), rng.randint(2, 10)
    return {"context": "candle", "length": length, "rate": rate,
            "height": length - rate * hours}


def check_candle(p):
    integers(p, "length rate height")
    require(15 <= p["length"] <= 40 and 2 <= p["rate"] <= 5, "Formula bounds")
    require(1 <= p["height"] < p["length"], "Height bounds")
    return whole(Fraction(p["length"] - p["height"], p["rate"]), 2, 10, "Hours must be whole")


def candle_formula(p):
    return ("t = ({} - h)/{}".format(p["length"], p["rate"]),
            r"t = \frac{" + str(p["length"]) + " - h}{" + str(p["rate"]) + "}")


def parts_candle(p):
    hours = check_candle(p)
    plain, tex = candle_formula(p)
    formula = "h = {} - {}t".format(p["length"], p["rate"])
    prompt = rich_prompt(
        ("A candle is {} cm tall when it is lit. After ".format(p["length"]), maths("t"),
         " hours, its height ", maths("h"), " cm is given by ", maths(formula), "."),
        ("(a) Make ", maths("t"), " the subject of the formula.",),
        ("(b) Use your formula to find ", maths("t"), " when ",
         maths("h = {}".format(p["height"])), "."),
    )
    return {"prompt": prompt, "answer": formula_answer("t", plain, hours, "hours"),
            "answer_display": formula_display("t", plain, tex, hours, "hours")}


def solve_candle(p, sympy):
    h, t = sympy.symbols("h t")
    equivalent(sympy, sympy.solve(sympy.Eq(h, p["length"] - p["rate"] * t), t),
               (p["length"] - h) / sympy.Integer(p["rate"]))
    (value,) = sympy.solve(sympy.Eq(p["height"], p["length"] - p["rate"] * t), t)
    return formula_answer("t", candle_formula(p)[0], value, "hours")


# ------------------------------------------------------- L3 temperature

TEMPERATURE_FORMULA = ("C = 5(F - 32)/9", r"C = \frac{5(F - 32)}{9}")


def build_temperature(rng):
    return {"context": "temperature",
            "fahrenheit": 32 + 9 * rng.choice([k for k in range(-5, 13) if k])}


def check_temperature(p):
    integers(p, "fahrenheit")
    require(-13 <= p["fahrenheit"] <= 140 and p["fahrenheit"] != 32, "Temperature bounds")
    return whole(Fraction(5 * (p["fahrenheit"] - 32), 9), -25, 60, "Celsius must be whole")


def parts_temperature(p):
    celsius = check_temperature(p)
    plain, tex = TEMPERATURE_FORMULA
    prompt = rich_prompt(
        ("The formula ", maths("F = 9C/5 + 32", r"F = \frac{9C}{5} + 32"),
         " converts a temperature of ", maths("C"), " degrees Celsius into ", maths("F"),
         " degrees Fahrenheit."),
        ("(a) Make ", maths("C"), " the subject of the formula.",),
        ("(b) Use your formula to find ", maths("C"), " when ",
         maths("F = {}".format(p["fahrenheit"])), "."),
    )
    return {"prompt": prompt, "answer": formula_answer("C", plain, celsius, "°C"),
            "answer_display": formula_display("C", plain, tex, celsius, "°C")}


def solve_temperature(p, sympy):
    C, F = sympy.symbols("C F")
    equivalent(sympy, sympy.solve(sympy.Eq(F, sympy.Rational(9, 5) * C + 32), C),
               sympy.Rational(5, 9) * (F - 32))
    (value,) = sympy.solve(sympy.Eq(p["fahrenheit"], sympy.Rational(9, 5) * C + 32), C)
    return formula_answer("C", TEMPERATURE_FORMULA[0], value, "°C")


# ------------------------------------------------------------ L3 motion

MOTION_FORMULA = ("t = (v - u)/a", r"t = \frac{v - u}{a}")


def build_motion(rng):
    u, a, t = rng.randint(0, 20), rng.randint(2, 10), rng.randint(2, 12)
    return {"context": "motion", "u": u, "a": a, "v": u + a * t}


def check_motion(p):
    integers(p, "u a v")
    require(0 <= p["u"] <= 20 and 2 <= p["a"] <= 10, "Bounds")
    return whole(Fraction(p["v"] - p["u"], p["a"]), 2, 12, "Time must be whole")


def parts_motion(p):
    seconds = check_motion(p)
    plain, tex = MOTION_FORMULA
    prompt = rich_prompt(
        ("The formula ", maths("v = u + at"), " gives the final speed ", maths("v"),
         " m/s of an object that starts at ", maths("u"), " m/s and accelerates at ",
         maths("a"), " m/s² for ", maths("t"), " seconds."),
        ("(a) Make ", maths("t"), " the subject of the formula.",),
        ("(b) Use your formula to find ", maths("t"), " when ",
         maths("v = {}, u = {}".format(p["v"], p["u"])), " and ",
         maths("a = {}".format(p["a"])), "."),
    )
    return {"prompt": prompt, "answer": formula_answer("t", plain, seconds, "seconds"),
            "answer_display": formula_display("t", plain, tex, seconds, "seconds")}


def solve_motion(p, sympy):
    u, a, t, v = sympy.symbols("u a t v", positive=True)
    equivalent(sympy, sympy.solve(sympy.Eq(v, u + a * t), t), (v - u) / a)
    t_plain = sympy.Symbol("t")
    (value,) = sympy.solve(sympy.Eq(p["v"], p["u"] + p["a"] * t_plain), t_plain)
    return formula_answer("t", MOTION_FORMULA[0], value, "seconds")


# ------------------------------------------------------------ L4 energy

ENERGY_FORMULA = ("v = sqrt(2E/m)", r"v = \sqrt{\frac{2E}{m}}")


def build_energy(rng):
    mass, speed = rng.randint(2, 20), rng.randint(2, 15)
    product = mass * speed * speed
    return {"context": "energy", "m": mass, "E": product // 2 if product % 2 == 0 else 0}


def check_energy(p):
    integers(p, "m E")
    require(2 <= p["m"] <= 20 and p["E"] >= 4, "Bounds")
    squared = whole(Fraction(2 * p["E"], p["m"]), 4, 225, "v squared must be whole")
    root = isqrt(squared)
    require(root * root == squared, "Speed must be whole")
    return root


def parts_energy(p):
    speed = check_energy(p)
    plain, tex = ENERGY_FORMULA
    prompt = rich_prompt(
        ("An object of mass ", maths("m"), " kg moving at ", maths("v"),
         " m/s has kinetic energy ", maths("E"), " joules, where ",
         maths("E = (1/2)mv^2", r"E = \frac{1}{2}mv^{2}"), "."),
        ("(a) Make ", maths("v"), " the subject of the formula, where ", maths("v > 0"), "."),
        ("(b) Use your formula to find ", maths("v"), " when ",
         maths("E = {}".format(p["E"])), " and ", maths("m = {}".format(p["m"])), "."),
    )
    return {"prompt": prompt, "answer": formula_answer("v", plain, speed, "m/s"),
            "answer_display": formula_display("v", plain, tex, speed, "m/s")}


def solve_energy(p, sympy):
    E, m, v = sympy.symbols("E m v", positive=True)
    equivalent(sympy, sympy.solve(sympy.Eq(E, m * v ** 2 / 2), v), sympy.sqrt(2 * E / m))
    (value,) = sympy.solve(sympy.Eq(p["E"], sympy.Integer(p["m"]) * v ** 2 / 2), v)
    return formula_answer("v", ENERGY_FORMULA[0], value, "m/s")


# ------------------------------------------------------------ L4 falling

FALLING_FORMULA = ("t = sqrt(s/5)", r"t = \sqrt{\frac{s}{5}}")


def build_falling(rng):
    return {"context": "falling", "s": 5 * rng.randint(1, 8) ** 2}


def check_falling(p):
    integers(p, "s")
    squared = whole(Fraction(p["s"], 5), 1, 64, "t squared must be whole")
    root = isqrt(squared)
    require(root * root == squared, "Time must be whole")
    return root


def parts_falling(p):
    seconds = check_falling(p)
    plain, tex = FALLING_FORMULA
    prompt = rich_prompt(
        ("An object is dropped. After ", maths("t"), " seconds it has fallen ", maths("s"),
         " metres, where ", maths("s = 5t^2", "s = 5t^{2}"), "."),
        ("(a) Make ", maths("t"), " the subject of the formula, where ", maths("t > 0"), "."),
        ("(b) Use your formula to find ", maths("t"), " when ",
         maths("s = {}".format(p["s"])), "."),
    )
    return {"prompt": prompt, "answer": formula_answer("t", plain, seconds, "seconds"),
            "answer_display": formula_display("t", plain, tex, seconds, "seconds")}


def solve_falling(p, sympy):
    s, t = sympy.symbols("s t", positive=True)
    equivalent(sympy, sympy.solve(sympy.Eq(s, 5 * t ** 2), t), sympy.sqrt(s / 5))
    (value,) = sympy.solve(sympy.Eq(p["s"], 5 * t ** 2), t)
    return formula_answer("t", FALLING_FORMULA[0], value, "seconds")


# ------------------------------------------------------------ registry

CONTEXTS = {
    "taxi": Context(1, frozenset({"context", "p", "f", "cost"}),
                    build_taxi, check_taxi, parts_taxi, solve_taxi),
    "candle": Context(2, frozenset({"context", "length", "rate", "height"}),
                      build_candle, check_candle, parts_candle, solve_candle),
    "temperature": Context(3, frozenset({"context", "fahrenheit"}),
                           build_temperature, check_temperature, parts_temperature,
                           solve_temperature),
    "motion": Context(3, frozenset({"context", "u", "a", "v"}),
                      build_motion, check_motion, parts_motion, solve_motion),
    "energy": Context(4, frozenset({"context", "m", "E"}),
                      build_energy, check_energy, parts_energy, solve_energy),
    "falling": Context(4, frozenset({"context", "s"}),
                       build_falling, check_falling, parts_falling, solve_falling),
}


def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    import sympy
    expected = CONTEXTS[q.parameters["context"]].solve(q.parameters, sympy)
    require(expected == q.answer, "Independent rearrangement disagrees")
    return True