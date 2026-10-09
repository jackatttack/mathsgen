"""IB AI SL optimisation in context.

Level 1 a given model (profit or a thrown ball); level 2 the open box from
a sheet of card; level 3 a fence against a wall or a running-track shape
(exact answer in pi); level 4 a closed cylinder of fixed volume or profit
from linear demand. Exact algebra with Fractions; square and cube roots and
pi come from mpmath. The independent check uses SymPy.
"""
from fractions import Fraction

import mpmath

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from .. import rich_blocks as rb
from . import common as ib
from . import distributions as dist
from .tangents import poly_text


# --- Editable pools ---------------------------------------------------------
PROFIT_RATES = (2, 4, 5, 10, 20, 50)
PROFIT_PEAKS = tuple(range(8, 41))
BALL_SPEEDS = tuple(range(8, 26))
BALL_STARTS = ("1", "1.5", "2", "2.5")
SHEETS = tuple(range(20, 61, 2))
WALL_FENCES = tuple(range(20, 201, 4))
TRACK_PERIMETERS = (20, 30, 40, 50, 60, 80, 100)
CYLINDER_VOLUMES = (250, 330, 500, 750, 1000, 1500, 2000)
DEMAND_STARTS = tuple(range(10000, 30001, 1000))
DEMAND_SLOPES = (500, 1000, 2000)
UNIT_COSTS = tuple(range(4, 13))
FIXED_COSTS = tuple(range(5000, 20001, 1000))


# ------------------------------------------------------------ mathematics

def mp_fraction(expression):
    with mpmath.workdps(dist.PRECISION):
        return dist.fraction(expression())


def pi():
    return mp_fraction(lambda: mpmath.pi)


def box_volume(width, height, x):
    return x * (width - 2 * x) * (height - 2 * x)


def box_best(width, height):
    """Smaller root of 12x^2 - 4(W + H)x + WH = 0."""
    root = dist.square_root(width * width - width * height + height * height)
    return (width + height - root) / 6


def cylinder_best(volume):
    """r minimising S = 2 pi r^2 + 2V/r: r = (V / (2 pi))^(1/3)."""
    return mp_fraction(lambda: mpmath.cbrt(dist.mp(volume) / (2 * mpmath.pi)))


def demand_profit_terms(p):
    """P(x) = (x - c)(N - m x) - F as [(coefficient, power)]."""
    n, m, c, f = p["start"], p["slope"], p["unit_cost"], p["fixed"]
    return [(-m, 2), (n + m * c, 1), (-(c * n + f), 0)]


def evaluate(terms, x):
    return sum(Fraction(c) * Fraction(x) ** power for c, power in terms)


def runs(label, terms):
    return rb.maths(label + " = " + poly_text(terms, True), label + " = " + poly_text(terms))


# ------------------------------------------------------------ generator

class Optimisation(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.calculus.optimisation",
        version=1,
        topic=ib.TOPIC,
        subtopic="differentiation",
        title="Optimisation in context",
        difficulty_descriptions={
            1: "A given model: derivative, the optimum and its value.",
            2: "Open box from a sheet: largest x, dV/dx, maximum volume.",
            3: "Show an area formula, then maximise it (wall fence or running track).",
            4: "Closed cylinder of fixed volume, or profit from linear demand.",
        },
        tags=ib.BASE_TAGS + ("optimisation", "differentiation", "stationary_points"),
    )
    keys = {
        1: {"form", "rate", "peak", "fixed", "speed", "start"},
        2: {"width", "height"},
        3: {"form", "length"},
        4: {"form", "volume", "start", "slope", "unit_cost", "fixed", "trial"},
    }

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def candidate(self, level, rng):
        if level == 1:
            rate, peak = rng.choice(PROFIT_RATES), rng.choice(PROFIT_PEAKS)
            fixed = int(rate * peak * peak * rng.uniform(0.3, 0.8)) // 10 * 10
            return {"form": rng.choice(("profit", "ball")), "rate": rate, "peak": peak,
                    "fixed": fixed, "speed": rng.choice(BALL_SPEEDS), "start": rng.choice(BALL_STARTS)}
        if level == 2:
            return {"width": rng.choice(SHEETS), "height": rng.choice(SHEETS)}
        if level == 3:
            form = rng.choice(("wall", "track"))
            return {"form": form, "length": rng.choice(WALL_FENCES if form == "wall" else TRACK_PERIMETERS)}
        p = {"form": rng.choice(("cylinder", "demand")), "volume": rng.choice(CYLINDER_VOLUMES),
             "start": rng.choice(DEMAND_STARTS), "slope": rng.choice(DEMAND_SLOPES),
             "unit_cost": rng.choice(UNIT_COSTS), "fixed": rng.choice(FIXED_COSTS)}
        best = Fraction(p["start"] + p["slope"] * p["unit_cost"], 2 * p["slope"])
        p["trial"] = int(best) + rng.choice((-3, -2, 2, 3))
        return p

    def check_rules(self, p, level):
        if level == 1:
            require(p["form"] in ("profit", "ball"), "Unknown form")
            require(p["rate"] in PROFIT_RATES and p["peak"] in PROFIT_PEAKS, "Profit outside pools")
            require(type(p["fixed"]) is int and 0 < p["fixed"] < p["rate"] * p["peak"] ** 2
                    and p["fixed"] % 10 == 0, "Fixed cost outside rules")
            require(p["speed"] in BALL_SPEEDS and p["start"] in BALL_STARTS, "Ball outside pools")
        elif level == 2:
            require(p["width"] in SHEETS and p["height"] in SHEETS, "Sheet outside pool")
        elif level == 3:
            require(p["form"] in ("wall", "track"), "Unknown form")
            require(p["length"] in (WALL_FENCES if p["form"] == "wall" else TRACK_PERIMETERS),
                    "Length outside pool")
        else:
            require(p["form"] in ("cylinder", "demand"), "Unknown form")
            require(p["volume"] in CYLINDER_VOLUMES, "Volume outside pool")
            require(p["start"] in DEMAND_STARTS and p["slope"] in DEMAND_SLOPES
                    and p["unit_cost"] in UNIT_COSTS and p["fixed"] in FIXED_COSTS, "Demand outside pools")
            terms = demand_profit_terms(p)
            best = Fraction(p["start"] + p["slope"] * p["unit_cost"], 2 * p["slope"])
            require(p["unit_cost"] < best < Fraction(p["start"], p["slope"]), "Optimum outside range")
            require(evaluate(terms, best) > 0, "Maximum profit must be positive")
            require(type(p["trial"]) is int and p["trial"] > p["unit_cost"] and p["trial"] != best,
                    "Trial price outside rules")
            require(evaluate(terms, p["trial"]) > 0, "Trial profit must be positive")

    def parts(self, p, level):
        if level == 1:
            if p["form"] == "profit":
                a, peak, fixed = p["rate"], p["peak"], p["fixed"]
                terms = [(-a, 2), (2 * a * peak, 1), (-fixed, 0)]
                best_value = evaluate(terms, peak)
                context = [[rb.text("A company's weekly profit, P dollars, from selling an item at "
                                    "x dollars is modelled by "), runs("P(x)", terms), rb.text(".")]]
                return ib.assemble(context, [
                    ib.part("a", "Find P'(x).", 2, "P'(x) = " + poly_text([(-2 * a, 1), (2 * a * peak, 0)])),
                    ib.part("b", "Find the price that maximises the profit.", 2,
                            "${}".format(peak), peak),
                    ib.part("c", "Find the maximum weekly profit.", 2,
                            ib.cash_whole("$", best_value), best_value),
                ])
            speed, start = p["speed"], Fraction(p["start"])
            gravity = Fraction(49, 10)
            terms = [(-gravity, 2), (speed, 1), (start, 0)]
            best = Fraction(speed) / (2 * gravity)
            top = evaluate(terms, best)
            context = [[rb.text("The height, h metres, of a ball t seconds after it is thrown is "
                                "modelled by "), runs("h(t)", terms).copy(), rb.text(".")]]
            context[0][1] = rb.maths(("h(t) = " + poly_text(terms, True)).replace("x", "t"),
                                     ("h(t) = " + poly_text(terms)).replace("x", "t"))
            return ib.assemble(context, [
                ib.part("a", "Find h'(t).", 2, "h'(t) = -9.8t + {}".format(speed)),
                ib.part("b", "Find the time at which the ball reaches its maximum height.", 2,
                        "{} s".format(ib.sf3(best)), best),
                ib.part("c", "Find the maximum height of the ball.", 2, "{} m".format(ib.sf3(top)), top),
            ])
        if level == 2:
            w, h = p["width"], p["height"]
            cubic = [(4, 3), (-2 * (w + h), 2), (w * h, 1)]
            slope = [(12, 2), (-4 * (w + h), 1), (w * h, 0)]
            best = box_best(Fraction(w), Fraction(h))
            volume = box_volume(w, h, best)
            context = ["An open box is made from a rectangular sheet of card {} cm by {} cm. A square "
                       "of side x cm is cut from each corner and the sides are folded up.".format(w, h)]
            return ib.assemble(context, [
                ib.part("a", "Write down the greatest possible value of x.", 1,
                        "x < {}".format(ib.nice(Fraction(min(w, h), 2))), Fraction(min(w, h), 2)),
                ib.part("b", [rb.text("Show that the volume is "), runs("V", cubic),
                              rb.text(" cm^3, and find dV/dx.")], 3,
                        "V = x({} - 2x)({} - 2x); dV/dx = {}".format(w, h, poly_text(slope))),
                ib.part("c", "Find the value of x that maximises the volume.", 2,
                        "x = {} cm".format(ib.sf3(best)), best),
                ib.part("d", "Find the maximum volume.", 2, "{} cm^3".format(ib.sf3(volume)), volume),
            ])
        if level == 3:
            length = p["length"]
            if p["form"] == "wall":
                terms = [(-2, 2), (length, 1)]
                best, area = Fraction(length, 4), Fraction(length * length, 8)
                context = ["A farmer uses {} m of fencing to make a rectangular pen against a long "
                           "wall. The wall forms one side; the fence forms the other three. The two "
                           "sides at right angles to the wall are each x m long.".format(length)]
                return ib.assemble(context, [
                    ib.part("a", [rb.text("Show that the area of the pen is "), runs("A", terms),
                                  rb.text(" m^2.")], 2,
                            "The side parallel to the wall is {} - 2x, so A = x({} - 2x).".format(length, length)),
                    ib.part("b", "Find dA/dx.", 1, "dA/dx = " + poly_text([(-4, 1), (length, 0)])),
                    ib.part("c", "Find the value of x that maximises the area.", 2,
                            "x = {} m".format(ib.nice(best)), best),
                    ib.part("d", "Find the maximum area.", 2, "{} m^2".format(ib.nice(area)), area),
                ])
            half = Fraction(length, 2)
            best = length / pi()
            area = length * length / (4 * pi())
            text = "A = {}x - (pi/4)x^2".format(ib.nice(half))
            tex = "A={}x-\\frac{{\\pi}}{{4}}x^{{2}}".format(ib.nice(half))
            context = ["A running track is a rectangle with a semicircle on each end. The rectangle "
                       "has length y m and each semicircle has diameter x m. The perimeter of the "
                       "track is {} m.".format(length)]
            return ib.assemble(context, [
                ib.part("a", "Write an equation for the perimeter in terms of x and y.", 1,
                        "pi x + 2y = {}".format(length)),
                ib.part("b", [rb.text("Show that the area enclosed is "), rb.maths(tex, text),
                              rb.text(" m^2.")], 3,
                        "y = ({} - pi x)/2 and A = xy + pi x^2/4, which simplifies to {}".format(length, text)),
                ib.part("c", "Find dA/dx.", 1, "dA/dx = {} - (pi/2)x".format(ib.nice(half))),
                ib.part("d", "Find the exact value of x that maximises the area.", 2,
                        "x = {}/pi ({} m)".format(length, ib.sf3(best)), best),
                ib.part("e", "Find the maximum area.", 1, "{} m^2".format(ib.sf3(area)), area),
            ])
        if p["form"] == "cylinder":
            volume = p["volume"]
            best = cylinder_best(volume)
            surface = 2 * pi() * best * best + 2 * volume / best
            text = "S = 2 pi r^2 + {}/r".format(2 * volume)
            tex = "S=2\\pi r^{{2}}+\\frac{{{}}}{{r}}".format(2 * volume)
            context = ["A closed cylindrical can has radius r cm, height h cm and volume {} cm^3.".format(volume)]
            return ib.assemble(context, [
                ib.part("a", "Write h in terms of r.", 2, "h = {}/(pi r^2)".format(volume)),
                ib.part("b", [rb.text("Show that the surface area is "), rb.maths(tex, text),
                              rb.text(" cm^2.")], 2,
                        "S = 2 pi r^2 + 2 pi r h, with h = {}/(pi r^2).".format(volume)),
                ib.part("c", "Find dS/dr.", 2, "dS/dr = 4 pi r - {}/r^2".format(2 * volume)),
                ib.part("d", "Find the radius that minimises the surface area.", 2,
                        "r = {} cm".format(ib.sf3(best)), best),
                ib.part("e", "Find the minimum surface area.", 2, "{} cm^2".format(ib.sf3(surface)), surface),
            ])
        terms = demand_profit_terms(p)
        best = Fraction(p["start"] + p["slope"] * p["unit_cost"], 2 * p["slope"])
        context = ["A company sells travel mugs. At a price of x euros, it expects to sell "
                   "n = {} - {}x mugs a month. Each mug costs {} euros to buy, and fixed costs are "
                   "{} euros a month.".format(p["start"], p["slope"], p["unit_cost"], p["fixed"])]
        trial_profit = evaluate(terms, p["trial"])
        top = evaluate(terms, best)
        return ib.assemble(context, [
            ib.part("a", "Find the monthly profit at a price of {} euros.".format(p["trial"]), 2,
                    "€" + ib.exact_text(trial_profit), trial_profit),
            ib.part("b", [rb.text("Show that the monthly profit is "), runs("P(x)", terms), rb.text(".")], 2,
                    "P = (x - {})({} - {}x) - {}".format(p["unit_cost"], p["start"], p["slope"], p["fixed"])),
            ib.part("c", "Find P'(x).", 2, "P'(x) = " + poly_text([(-2 * p["slope"], 1), (terms[1][0], 0)])),
            ib.part("d", "Find the price that maximises the monthly profit.", 2,
                    "€" + ib.money(best), best),
            ib.part("e", "Find the maximum monthly profit.", 2, ib.cash("€", top), top),
        ])

    def validate_independently(self, question):
        """SymPy differentiates each model and solves for the stationary point."""
        import sympy
        p, level = question.parameters, question.difficulty
        values = ib.answer_values(question)
        x = sympy.Symbol("x", positive=True)
        if level == 1:
            if p["form"] == "profit":
                model = -p["rate"] * x ** 2 + 2 * p["rate"] * p["peak"] * x - p["fixed"]
            else:
                model = -sympy.Rational(49, 10) * x ** 2 + p["speed"] * x + sympy.Rational(p["start"])
            best = sympy.solve(sympy.diff(model, x), x)[0]
            require(ib.close(values["b"], float(best)) and ib.close(values["c"], float(model.subs(x, best))),
                    "Independent optimum failed")
        elif level == 2:
            model = x * (p["width"] - 2 * x) * (p["height"] - 2 * x)
            best = min(sympy.solve(sympy.diff(model, x), x))
            require(ib.close(values["c"], float(best)) and ib.close(values["d"], float(model.subs(x, best))),
                    "Independent box failed")
        elif level == 3:
            length = p["length"]
            if p["form"] == "wall":
                model = x * (length - 2 * x)
                label_x, label_area = "c", "d"
            else:
                y = (length - sympy.pi * x) / 2
                model = x * y + sympy.pi * x ** 2 / 4
                label_x, label_area = "d", "e"
            best = sympy.solve(sympy.diff(model, x), x)[0]
            require(ib.close(values[label_x], float(best), 1e-8)
                    and ib.close(values[label_area], float(model.subs(x, best)), 1e-8),
                    "Independent area failed")
        elif p["form"] == "cylinder":
            model = 2 * sympy.pi * x ** 2 + 2 * p["volume"] / x
            best = sympy.solve(sympy.diff(model, x), x)[0]
            require(ib.close(values["d"], float(best), 1e-8)
                    and ib.close(values["e"], float(model.subs(x, best)), 1e-8), "Independent can failed")
        else:
            model = (x - p["unit_cost"]) * (p["start"] - p["slope"] * x) - p["fixed"]
            best = sympy.solve(sympy.diff(model, x), x)[0]
            require(ib.close(values["a"], float(model.subs(x, p["trial"]))), "Independent trial failed")
            require(ib.close(values["d"], float(best)) and ib.close(values["e"], float(model.subs(x, best))),
                    "Independent profit failed")
        return True