"""Money problems: best buys, exchange rates, pay, bills, profit, discounts and budgets.

All money is held as exact pence, so every answer is exact. The contexts follow
common Foundation exam styles, two forms per level. Budget questions set the
budget clearly away from the true cost (BUDGET_GAP_PENCE), so the yes/no
decision never hinges on a penny.
"""
import math
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)


INFO = GeneratorInfo(
    id="ratio.money.problems", version=1,
    topic="ratio", subtopic="money",
    title="Money problems: best buys, pay, bills, profit and budgets",
    difficulty_descriptions={
        1: "Decide the better buy, or convert money with an exchange rate.",
        2: "Work out pay with overtime, or a bill with a standing charge.",
        3: "Find a percentage profit, or check a budget after two discounts.",
        4: "Compare who saves most, or check a budget for paving a path.",
    },
    tags=("ratio", "money", "problem solving", "percentages"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("best_buy", "exchange"),
    2: ("overtime", "bill"),
    3: ("profit", "discounts"),
    4: ("savings", "paving"),
}
NAMES = ("Amir", "Beth", "Chris", "Dana", "Ellis", "Farah", "Gavin", "Hana", "Isaac", "Jade")
PRODUCTS = {"cereal": "g", "washing powder": "g", "orange juice": "ml", "shampoo": "ml"}
CURRENCIES = {"euros": "€", "US dollars": "$"}
OVERTIME = ((Fraction(5, 4), "1.25 times"), (Fraction(3, 2), "1.5 times"), (Fraction(2), "double"))
BILL_DAYS = (30, 31, 90, 91, 92)
BAG_GRAMS = (100, 125, 200, 250, 500)
DISCOUNT_DENOMINATORS = (4, 5, 10)
DISCOUNT_PERCENTS = (10, 15, 20, 25)
SPEND_DENOMINATORS = (3, 4, 5, 8)
STONE_SIDES = (30, 40, 50, 60)
BUDGET_GAP_PENCE = (500, 5000)      # a budget is 5 to 50 pounds away from the cost
MARKS = {1: 3, 2: 3, 3: 4, 4: 4}
WORKING_LINES = {1: 4, 2: 5, 3: 7, 4: 8}

KEYS = {
    "best_buy": {"product", "small_amount", "small_rate", "large_amount", "large_rate"},
    "exchange": {"currency", "rate_cents", "pounds", "direction"},
    "overtime": {"name", "rate_pence", "normal_hours", "multiplier", "hours"},
    "bill": {"standing_pence", "days", "unit_tenths", "units"},
    "profit": {"name", "kilograms", "cost_pounds", "bag_grams", "bag_pence"},
    "discounts": {"name", "price_pounds", "denominator", "percent", "budget_pounds"},
    "savings": {"names", "percent", "spend_num", "spend_den", "save_part", "spend_part"},
    "paving": {"name", "length_cm", "width_cm", "side_cm", "price_pence", "budget_pounds"},
}
TEXT_KEYS = {"product", "currency", "direction", "name", "names"}


# ------------------------------------------------------------ money text

def pounds_text(pence):
    pence = Fraction(pence)
    require(pence.denominator == 1 and pence >= 0, "Not a whole number of pence")
    pence = int(pence)
    return "£{}.{:02d}".format(pence // 100, pence % 100)


def price_text(pence):
    """65p below a pound, otherwise pounds and pence."""
    return "{}p".format(pence) if pence < 100 else pounds_text(pence)


def two_places(hundredths):
    return "{}.{:02d}".format(hundredths // 100, hundredths % 100)


def percent_text(share):
    value = share * 100
    if value.denominator == 1:
        return "{}%".format(value.numerator)
    return "{:.1f}%".format(float(value))


# ------------------------------------------------------------ mathematics

def results(par):
    """Exact working values for each form."""
    form = par["form"]
    if form == "best_buy":
        return {"small_price": par["small_rate"] * par["small_amount"] // 100,
                "large_price": par["large_rate"] * par["large_amount"] // 100}
    if form == "exchange":
        return {"foreign_cents": par["pounds"] * par["rate_cents"]}
    if form == "overtime":
        factor = OVERTIME[par["multiplier"]][0]
        extra = par["hours"] - par["normal_hours"]
        return {"pay": par["rate_pence"] * par["normal_hours"]
                + factor * par["rate_pence"] * extra}
    if form == "bill":
        return {"total": par["standing_pence"] * par["days"]
                + Fraction(par["unit_tenths"] * par["units"], 10)}
    if form == "profit":
        bags = par["kilograms"] * 1000 // par["bag_grams"]
        revenue = bags * par["bag_pence"]
        cost = par["cost_pounds"] * 100
        return {"bags": bags, "revenue": revenue, "profit": revenue - cost,
                "percent": Fraction(revenue - cost, cost) * 100}
    if form == "discounts":
        monday = par["price_pounds"] * 100 * (1 - Fraction(1, par["denominator"]))
        return {"monday": monday, "tuesday": monday * (1 - Fraction(par["percent"], 100))}
    if form == "savings":
        return {"shares": [
            Fraction(par["percent"], 100),
            1 - Fraction(par["spend_num"], par["spend_den"]),
            Fraction(par["save_part"], par["save_part"] + par["spend_part"]),
        ]}
    stones = (par["length_cm"] // par["side_cm"]) * (par["width_cm"] // par["side_cm"])
    return {"stones": stones, "cost": stones * par["price_pence"]}


def check_parameters(par, level):
    require(isinstance(par, dict), "Parameters must be a dictionary")
    form = par.get("form")
    require(level in FORMS and form in FORMS[level], "Unexpected form for this level")
    require(set(par) == KEYS[form] | {"form"}, "Unexpected parameters")
    require(all(type(par[k]) is int for k in KEYS[form] - TEXT_KEYS), "Integer parameters required")

    if form == "best_buy":
        require(par["product"] in PRODUCTS, "Unknown product")
        for key in ("small_amount", "large_amount"):
            require(100 <= par[key] <= 1000 and par[key] % 100 == 0, "Amount outside bounds")
        require(par["small_amount"] < par["large_amount"], "Small pack must be smaller")
        for key in ("small_rate", "large_rate"):
            require(20 <= par[key] <= 150, "Rate outside bounds")
        require(abs(par["small_rate"] - par["large_rate"]) >= 3, "Too close to call")
        # Real packs differ modestly per unit; a large pack at double the unit
        # price makes the comparison trivial.
        require(abs(par["small_rate"] - par["large_rate"]) * 4 <= par["small_rate"],
                "Unit prices unrealistically far apart")
    elif form == "exchange":
        require(par["currency"] in CURRENCIES, "Unknown currency")
        require(105 <= par["rate_cents"] <= 180, "Rate outside bounds")
        require(20 <= par["pounds"] <= 600 and par["pounds"] % 10 == 0, "Amount outside bounds")
        require(par["direction"] in ("to_foreign", "to_pounds"), "Unknown direction")
    elif form == "overtime":
        require(par["name"] in NAMES, "Unknown name")
        # Multiples of 20p read like real pay rates and keep 1.25 times exact.
        require(900 <= par["rate_pence"] <= 1600 and par["rate_pence"] % 20 == 0,
                "Rate outside bounds")
        require(par["normal_hours"] in (7, 8), "Normal hours outside bounds")
        require(par["multiplier"] in range(len(OVERTIME)), "Unknown overtime rate")
        require(par["normal_hours"] < par["hours"] <= par["normal_hours"] + 4,
                "Hours outside bounds")
        require(results(par)["pay"].denominator == 1, "Pay must be whole pence")
    elif form == "bill":
        require(20 <= par["standing_pence"] <= 70, "Standing charge outside bounds")
        require(par["days"] in BILL_DAYS, "Unexpected billing period")
        require(150 <= par["unit_tenths"] <= 350, "Unit price outside bounds")
        require(100 <= par["units"] <= 1500, "Units outside bounds")
        require(results(par)["total"].denominator == 1, "Bill must be whole pence")
    elif form == "profit":
        require(par["name"] in NAMES, "Unknown name")
        require(2 <= par["kilograms"] <= 12, "Mass outside bounds")
        require(par["bag_grams"] in BAG_GRAMS
                and par["kilograms"] * 1000 % par["bag_grams"] == 0, "Bags must fit exactly")
        require(20 <= par["bag_pence"] <= 200 and par["bag_pence"] % 5 == 0,
                "Bag price outside bounds")
        require(5 <= par["cost_pounds"] <= 60, "Cost outside bounds")
        percent = results(par)["percent"]
        require(0 < percent <= 150 and percent.denominator == 1, "Profit must be a whole percentage")
    elif form == "discounts":
        require(par["name"] in NAMES, "Unknown name")
        require(200 <= par["price_pounds"] <= 1000 and par["price_pounds"] % 10 == 0,
                "Price outside bounds")
        require(par["denominator"] in DISCOUNT_DENOMINATORS, "Unexpected fraction")
        require(par["percent"] in DISCOUNT_PERCENTS, "Unexpected percentage")
        final = results(par)["tuesday"]
        require(final.denominator == 1, "Sale price must be whole pence")
        gap = abs(par["budget_pounds"] * 100 - final)
        require(BUDGET_GAP_PENCE[0] <= gap <= BUDGET_GAP_PENCE[1], "Budget too close or too far")
    elif form == "savings":
        names = par["names"]
        require(isinstance(names, list) and len(names) == 3 and len(set(names)) == 3
                and all(name in NAMES for name in names), "Three different names needed")
        require(15 <= par["percent"] <= 45, "Percentage outside bounds")
        require(par["spend_den"] in SPEND_DENOMINATORS and 0 < par["spend_num"] < par["spend_den"]
                and math.gcd(par["spend_num"], par["spend_den"]) == 1, "Spend fraction outside bounds")
        require(1 <= par["save_part"] <= 6 and 1 <= par["spend_part"] <= 6
                and math.gcd(par["save_part"], par["spend_part"]) == 1, "Ratio outside bounds")
        shares = sorted(results(par)["shares"], reverse=True)
        require(Fraction(1, 100) <= shares[0] - shares[1] <= Fraction(1, 10),
                "Savers too close to call, or one saver far ahead")
    else:
        require(par["name"] in NAMES, "Unknown name")
        side = par["side_cm"]
        require(side in STONE_SIDES, "Unexpected stone size")
        require(300 <= par["length_cm"] <= 1500 and par["length_cm"] % side == 0,
                "Length must be whole stones")
        require(60 <= par["width_cm"] <= 300 and par["width_cm"] % side == 0,
                "Width must be whole stones")
        require(150 <= par["price_pence"] <= 600 and par["price_pence"] % 10 == 0,
                "Stone price outside bounds")
        gap = abs(par["budget_pounds"] * 100 - results(par)["cost"])
        require(BUDGET_GAP_PENCE[0] <= gap <= BUDGET_GAP_PENCE[1], "Budget too close or too far")


# ------------------------------------------------------------ wording

def prompt_for(par):
    form = par["form"]
    if form == "best_buy":
        unit = PRODUCTS[par["product"]]
        values = results(par)
        text = ("A shop sells {} in two sizes. A small pack contains {} {} and costs {}. "
                "A large pack contains {} {} and costs {}. Which pack is better value for "
                "money? You must show how you get your answer.").format(
            par["product"], par["small_amount"], unit, price_text(values["small_price"]),
            par["large_amount"], unit, price_text(values["large_price"]))
    elif form == "exchange":
        symbol = CURRENCIES[par["currency"]]
        rate = "The exchange rate is £1 = {}{}. ".format(symbol, two_places(par["rate_cents"]))
        if par["direction"] == "to_foreign":
            text = rate + "Change £{} into {}.".format(par["pounds"], par["currency"])
        else:
            text = rate + "Change {}{} into pounds.".format(
                symbol, two_places(results(par)["foreign_cents"]))
    elif form == "overtime":
        name, words = par["name"], OVERTIME[par["multiplier"]][1]
        text = ("{0} works for a company. {0}'s normal rate of pay is {1} per hour. When {0} "
                "works more than {2} hours in a day, {0} is paid overtime for each extra hour. "
                "The overtime rate is {3} the normal rate. On Monday, {0} worked {4} hours. "
                "Work out the total amount {0} earned on Monday.").format(
            name, pounds_text(par["rate_pence"]), par["normal_hours"], words, par["hours"])
    elif form == "bill":
        unit = "{}.{}".format(par["unit_tenths"] // 10, par["unit_tenths"] % 10).replace(".0", "")
        text = ("An electricity bill has a standing charge of {}p per day. Each unit of "
                "electricity used costs {}p. In {} days, {} units are used. Work out the "
                "total bill.").format(par["standing_pence"], unit, par["days"], par["units"])
    elif form == "profit":
        text = ("{0} buys {1} kg of sweets for £{2}. {0} puts all of the sweets into bags, "
                "with {3} g in each bag, and sells every bag for {4}. Work out {0}'s "
                "percentage profit.").format(
            par["name"], par["kilograms"], par["cost_pounds"], par["bag_grams"],
            price_text(par["bag_pence"]))
    elif form == "discounts":
        text = ("In a shop, a TV has a normal price of £{1}. On Monday, the normal price is "
                "reduced by 1/{2} to give the sale price. On Tuesday, the sale price is reduced "
                "by {3}%. {0} has £{4} to spend on the TV. Does {0} have enough money to buy "
                "the TV on Tuesday? You must show how you get your answer.").format(
            par["name"], par["price_pounds"], par["denominator"], par["percent"],
            par["budget_pounds"])
    elif form == "savings":
        a, b, c = par["names"]
        text = ("{0}, {1} and {2} each earn the same monthly salary. Each month, {0} saves "
                "{3}% of their salary and spends the rest. {1} spends {4}/{5} of their salary "
                "and saves the rest. For {2}, the amount saved : the amount spent = {6} : {7}. "
                "Work out who saves the most of their salary each month. You must show how "
                "you get your answer.").format(
            a, b, c, par["percent"], par["spend_num"], par["spend_den"],
            par["save_part"], par["spend_part"])
    else:
        text = ("A rectangular garden path is {1} cm long and {2} cm wide. {0} is going to "
                "cover the path with square paving stones of side {3} cm. Each paving stone "
                "costs {4}. {0} has £{5} to spend on paving stones. Does {0} have enough "
                "money to buy all the stones needed? You must show how you get your "
                "answer.").format(
            par["name"], par["length_cm"], par["width_cm"], par["side_cm"],
            price_text(par["price_pence"]), par["budget_pounds"])
    return Content(text)


def answer_for(par):
    form = par["form"]
    values = results(par)
    if form == "best_buy":
        unit = PRODUCTS[par["product"]]
        better = "small" if par["small_rate"] < par["large_rate"] else "large"
        return ({"kind": "choice", "value": better,
                 "small_per_100": str(par["small_rate"]), "large_per_100": str(par["large_rate"])},
                Content("Small: {} per 100 {u}. Large: {} per 100 {u}. The {} pack is better "
                        "value.".format(price_text(par["small_rate"]),
                                        price_text(par["large_rate"]), better, u=unit)))
    if form == "exchange":
        symbol = CURRENCIES[par["currency"]]
        if par["direction"] == "to_foreign":
            return ({"kind": "money", "currency": par["currency"],
                     "cents": str(values["foreign_cents"])},
                    Content("{}{}".format(symbol, two_places(values["foreign_cents"]))))
        return ({"kind": "money", "currency": "pounds", "pence": str(par["pounds"] * 100)},
                Content("£{}".format(par["pounds"])))
    if form in ("overtime", "bill"):
        total = values["pay" if form == "overtime" else "total"]
        return {"kind": "money", "currency": "pounds", "pence": rational_text(total)}, \
            Content(pounds_text(total))
    if form == "profit":
        return ({"kind": "percentage", "value": rational_text(values["percent"])},
                Content("{} bags sell for {}. Profit {}, so the percentage profit is {}."
                        .format(values["bags"], pounds_text(values["revenue"]),
                                pounds_text(values["profit"]), percent_text(values["percent"] / 100))))
    if form == "discounts":
        final = values["tuesday"]
        enough = final <= par["budget_pounds"] * 100
        return ({"kind": "yes_no", "value": "yes" if enough else "no",
                 "final_pence": rational_text(final)},
                Content("Monday: {}. Tuesday: {}. {} {}, so {}.".format(
                    pounds_text(values["monday"]), pounds_text(final),
                    "This is within" if enough else "This is more than",
                    "£{}".format(par["budget_pounds"]),
                    "yes, {} has enough".format(par["name"]) if enough
                    else "no, {} does not have enough".format(par["name"]))))
    if form == "savings":
        shares = values["shares"]
        best = par["names"][shares.index(max(shares))]
        listing = "; ".join("{} saves {}".format(name, percent_text(share))
                            for name, share in zip(par["names"], shares))
        return ({"kind": "choice", "value": best, "shares": [rational_text(s) for s in shares]},
                Content("{}. {} saves the most.".format(listing, best)))
    enough = values["cost"] <= par["budget_pounds"] * 100
    return ({"kind": "yes_no", "value": "yes" if enough else "no",
             "stones": str(values["stones"]), "cost_pence": str(values["cost"])},
            Content("{} stones cost {}, which is {} £{}, so {}.".format(
                values["stones"], pounds_text(values["cost"]),
                "within" if enough else "more than", par["budget_pounds"],
                "yes" if enough else "no")))


def draw_parameters(rng, form):
    par = {"form": form}
    if form == "best_buy":
        small, large = sorted(rng.sample(range(100, 1001, 100), 2))
        small_rate = rng.randint(20, 150)
        large_rate = rng.randint(max(20, small_rate * 3 // 4), min(150, small_rate * 5 // 4))
        par.update(product=rng.choice(sorted(PRODUCTS)), small_amount=small, large_amount=large,
                   small_rate=small_rate, large_rate=large_rate)
    elif form == "exchange":
        par.update(currency=rng.choice(sorted(CURRENCIES)), rate_cents=rng.randint(105, 180),
                   pounds=rng.randrange(20, 601, 10),
                   direction=rng.choice(("to_foreign", "to_pounds")))
    elif form == "overtime":
        normal = rng.choice((7, 8))
        par.update(name=rng.choice(NAMES), rate_pence=rng.randrange(900, 1601, 20),
                   normal_hours=normal, multiplier=rng.randrange(len(OVERTIME)),
                   hours=normal + rng.randint(1, 4))
    elif form == "bill":
        par.update(standing_pence=rng.randint(20, 70), days=rng.choice(BILL_DAYS),
                   unit_tenths=rng.randint(150, 350), units=rng.randrange(100, 1501, 10))
    elif form == "profit":
        par.update(name=rng.choice(NAMES), kilograms=rng.randint(2, 12),
                   bag_grams=rng.choice(BAG_GRAMS), bag_pence=rng.randrange(20, 201, 5),
                   cost_pounds=rng.randint(5, 60))
    elif form == "discounts":
        price = rng.randrange(200, 1001, 10)
        par.update(name=rng.choice(NAMES), price_pounds=price,
                   denominator=rng.choice(DISCOUNT_DENOMINATORS),
                   percent=rng.choice(DISCOUNT_PERCENTS),
                   budget_pounds=rng.randint(price // 3, price))
    elif form == "savings":
        den = rng.choice(SPEND_DENOMINATORS)
        par.update(names=rng.sample(NAMES, 3), percent=rng.randint(15, 45),
                   spend_num=rng.randint(1, den - 1), spend_den=den,
                   save_part=rng.randint(1, 6), spend_part=rng.randint(1, 6))
    else:
        side = rng.choice(STONE_SIDES)
        length = side * rng.randint(math.ceil(300 / side), 1500 // side)
        width = side * rng.randint(math.ceil(60 / side), 300 // side)
        price = rng.randrange(150, 601, 10)
        cost = (length // side) * (width // side) * price
        par.update(name=rng.choice(NAMES), length_cm=length, width_cm=width, side_cm=side,
                   price_pence=price,
                   budget_pounds=max(1, cost // 100 + rng.choice((-1, 1)) * rng.randint(5, 50)))
    return par


# ------------------------------------------------------------ generator

class MoneyProblems:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        form = rng.choice(FORMS[difficulty])
        for attempt in range(3000):
            par = draw_parameters(rng, form)
            try:
                check_parameters(par, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a money problem")
        answer, display = answer_for(par)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(par),
            answer=answer, answer_display=display, worked_solution=(),
            marks=MARKS[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=WORKING_LINES[difficulty]),
            parameters=par,
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        require(type(q.difficulty) is int and q.difficulty in (1, 2, 3, 4), "Invalid difficulty")
        require(q.settings == {}, "Unsupported settings")
        check_parameters(q.parameters, q.difficulty)
        answer, display = answer_for(q.parameters)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Answer display mismatch")
        require(q.prompt == prompt_for(q.parameters), "Prompt mismatch")
        return True

    def validate_independently(self, q):
        """Recompute each form by a different route: cross-multiplying, hour-by-hour
        pay, day-by-day bills, counting bags, reversed discounts, spending shares
        and stones by area."""
        par, answer = q.parameters, q.answer
        form = par.get("form")
        if form == "best_buy":
            small_price = par["small_rate"] * par["small_amount"] / 100
            large_price = par["large_rate"] * par["large_amount"] / 100
            small_better = small_price * par["large_amount"] < large_price * par["small_amount"]
            require(answer["value"] == ("small" if small_better else "large"),
                    "Independent best buy disagrees")
        elif form == "exchange":
            if par["direction"] == "to_foreign":
                require(Fraction(answer["cents"]) == Fraction(par["pounds"] * par["rate_cents"]),
                        "Independent conversion disagrees")
            else:
                foreign = Fraction(par["pounds"] * par["rate_cents"], 100)
                require(Fraction(answer["pence"]) / 100 == foreign / Fraction(par["rate_cents"], 100),
                        "Independent conversion disagrees")
        elif form == "overtime":
            factor = OVERTIME[par["multiplier"]][0]
            pay = Fraction(0)
            for hour in range(1, par["hours"] + 1):
                pay += par["rate_pence"] * (1 if hour <= par["normal_hours"] else factor)
            require(Fraction(answer["pence"]) == pay, "Independent pay disagrees")
        elif form == "bill":
            total = Fraction(0)
            for day in range(par["days"]):
                total += par["standing_pence"]
            total += Fraction(par["unit_tenths"], 10) * par["units"]
            require(Fraction(answer["pence"]) == total, "Independent bill disagrees")
        elif form == "profit":
            grams, bags = par["kilograms"] * 1000, 0
            while grams >= par["bag_grams"]:
                grams -= par["bag_grams"]
                bags += 1
            require(grams == 0, "Bags do not fit exactly")
            ratio = Fraction(bags * par["bag_pence"], par["cost_pounds"] * 100)
            require(Fraction(answer["value"]) == (ratio - 1) * 100, "Independent profit disagrees")
        elif form == "discounts":
            price = Fraction(par["price_pounds"] * 100)
            price *= Fraction(100 - par["percent"], 100)
            price *= Fraction(par["denominator"] - 1, par["denominator"])
            require(Fraction(answer["final_pence"]) == price, "Independent price disagrees")
            require(answer["value"] == ("yes" if price <= par["budget_pounds"] * 100 else "no"),
                    "Independent decision disagrees")
        elif form == "savings":
            spends = [
                Fraction(100 - par["percent"], 100),
                Fraction(par["spend_num"], par["spend_den"]),
                Fraction(par["spend_part"], par["save_part"] + par["spend_part"]),
            ]
            require(answer["value"] == par["names"][spends.index(min(spends))],
                    "Independent saver disagrees")
        else:
            stones = Fraction(par["length_cm"] * par["width_cm"], par["side_cm"] ** 2)
            require(stones.denominator == 1 and int(answer["stones"]) == stones,
                    "Independent stone count disagrees")
            cost = stones * par["price_pence"]
            require(answer["value"] == ("yes" if cost <= par["budget_pounds"] * 100 else "no"),
                    "Independent decision disagrees")
        return True