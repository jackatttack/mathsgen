"""IB AI SL loans and amortisation: monthly payments, total repaid, down
payments, and repaying early with a larger payment.

Every loan here is monthly: a nominal annual rate of r% compounded monthly
and equal payments at the end of each month. The annuity formula is not in
the formula booklet, so the expected route is the GDC TVM solver
(N, I%, PV, PMT, FV = 0, P/Y = C/Y = 12). Later parts reuse the rounded
payment from part (a), as IB mark schemes do.
"""
from fractions import Fraction

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from . import common as ib


# --- Editable pools ---------------------------------------------------------
LOAN_RATES = ("3.6", "4.2", "4.8", "5.5", "6", "6.5", "7.2", "8", "9.5", "10.8", "12.6")
MORTGAGE_RATES = ("2.5", "3", "3.2", "3.6", "4", "4.5", "4.8", "5", "5.5", "6")
LOANS = tuple(range(5000, 60001, 500))
TERMS = (2, 3, 4, 5, 6, 8, 10)
PURPOSES = ("to buy a car", "to buy a boat", "to pay for home improvements",
            "to start a business")
PRICES = tuple(range(150000, 600001, 5000))
DOWN_PAYMENTS = (10, 15, 20, 25)
PROPERTIES = ("house", "flat", "holiday cottage")
MORTGAGES = tuple(range(80000, 400001, 5000))
MORTGAGE_TERMS = (15, 20, 25, 30)
EXTRA_STEP = 50
EXTRA_STEPS = 8


# ------------------------------------------------------------ mathematics

def monthly_rate(rate):
    return Fraction(rate) / 1200


def monthly_payment(loan, rate, months):
    """The equal end-of-month payment that clears the loan exactly."""
    i = monthly_rate(rate)
    return loan * i / (1 - (1 + i) ** -months)


def pay_off(loan, rate, instalment):
    """(number of payments, final payment) when paying a fixed instalment."""
    i = monthly_rate(rate)
    balance, count = Fraction(loan), 0
    while True:
        count += 1
        owed = balance * (1 + i)
        if owed <= instalment:
            return count, owed
        balance = owed - instalment
        require(count <= 1200, "The instalment never repays the loan")


# ------------------------------------------------------------ generator

class Loans(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.finance.loans",
        version=1,
        topic=ib.TOPIC,
        subtopic="financial_mathematics",
        title="Loans and amortisation",
        difficulty_descriptions={
            1: "Monthly payment on a loan, to two decimal places.",
            2: "Monthly payment, total repaid and total interest.",
            3: "Amount borrowed after a down payment, monthly payment and total interest.",
            4: "Pay more each month: number of payments, final payment and the saving.",
        },
        tags=ib.BASE_TAGS + ("loans", "amortisation", "tvm"),
    )
    keys = {
        1: {"name", "currency", "loan", "rate", "years", "purpose"},
        2: {"name", "currency", "loan", "rate", "years", "purpose"},
        3: {"name", "currency", "price", "down", "rate", "years", "property"},
        4: {"name", "currency", "loan", "rate", "years", "instalment"},
    }

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def candidate(self, level, rng):
        p = {"name": rng.choice(ib.NAMES), "currency": rng.choice(tuple(ib.CURRENCIES))}
        if level in (1, 2):
            p.update(loan=rng.choice(LOANS), rate=rng.choice(LOAN_RATES),
                     years=rng.choice(TERMS), purpose=rng.choice(PURPOSES))
        elif level == 3:
            p.update(price=rng.choice(PRICES), down=rng.choice(DOWN_PAYMENTS),
                     rate=rng.choice(MORTGAGE_RATES), years=rng.choice(MORTGAGE_TERMS),
                     property=rng.choice(PROPERTIES))
        else:
            p.update(loan=rng.choice(MORTGAGES), rate=rng.choice(MORTGAGE_RATES),
                     years=rng.choice(MORTGAGE_TERMS))
            base = monthly_payment(p["loan"], p["rate"], 12 * p["years"])
            p["instalment"] = (int(base // EXTRA_STEP) + rng.randint(1, EXTRA_STEPS)) * EXTRA_STEP
        return p

    def check_rules(self, p, level):
        require(p["name"] in ib.NAMES, "Unknown name")
        require(p["currency"] in ib.CURRENCIES, "Unknown currency")
        if level in (1, 2):
            require(p["loan"] in LOANS, "Loan outside pool")
            require(p["rate"] in LOAN_RATES, "Rate outside pool")
            require(p["years"] in TERMS, "Term outside pool")
            require(p["purpose"] in PURPOSES, "Unknown purpose")
        elif level == 3:
            require(p["price"] in PRICES, "Price outside pool")
            require(p["down"] in DOWN_PAYMENTS, "Down payment outside pool")
            require(p["rate"] in MORTGAGE_RATES, "Rate outside pool")
            require(p["years"] in MORTGAGE_TERMS, "Term outside pool")
            require(p["property"] in PROPERTIES, "Unknown property")
        else:
            require(p["loan"] in MORTGAGES, "Loan outside pool")
            require(p["rate"] in MORTGAGE_RATES, "Rate outside pool")
            require(p["years"] in MORTGAGE_TERMS, "Term outside pool")
            require(type(p["instalment"]) is int and p["instalment"] % EXTRA_STEP == 0,
                    "Instalment outside rules")
            months = 12 * p["years"]
            base = monthly_payment(p["loan"], p["rate"], months)
            require(base < p["instalment"] <= base + (EXTRA_STEPS + 1) * EXTRA_STEP,
                    "Instalment outside bounds")
            count, final = pay_off(p["loan"], p["rate"], p["instalment"])
            require(2 <= count < months, "Payment count outside bounds")
            require(ib.to_cents(final) > 0 and final < p["instalment"],
                    "Final payment outside bounds")

    def parts(self, p, level):
        cur, unit = p["currency"], ib.CURRENCIES[p["currency"]]
        months = 12 * p["years"]
        if level in (1, 2):
            context = ["{} borrows {}{} {}. The loan is repaid over {} years with equal "
                       "payments at the end of each month. The nominal annual interest rate is "
                       "{}%, compounded monthly.".format(
                           p["name"], cur, p["loan"], p["purpose"], p["years"], p["rate"])]
            payment = monthly_payment(p["loan"], p["rate"], months)
            parts = [ib.part("a", "Find the monthly payment. Give your answer to two decimal "
                             "places.", 3, ib.cash(cur, payment), payment)]
            if level == 2:
                total = ib.round_whole(ib.to_cents(payment) * months)
                parts.append(ib.part(
                    "b", "Find the total amount {} repays over the life of the loan, to the "
                    "nearest {}.".format(p["name"], unit), 2, ib.cash_whole(cur, total), total))
                parts.append(ib.part("c", "Find the total interest paid.", 1,
                                     ib.cash_whole(cur, total - p["loan"]), total - p["loan"]))
            return ib.assemble(context, parts)

        if level == 3:
            loan = p["price"] * (100 - p["down"]) // 100
            context = ["{} buys a {} for {}{}. The bank requires a down payment of {}% and "
                       "lends the rest. The loan is repaid over {} years with equal payments "
                       "at the end of each month, at a nominal annual interest rate of {}%, "
                       "compounded monthly.".format(
                           p["name"], p["property"], cur, p["price"], p["down"], p["years"],
                           p["rate"])]
            payment = monthly_payment(loan, p["rate"], months)
            interest = ib.round_whole(ib.to_cents(payment) * months - loan)
            return ib.assemble(context, [
                ib.part("a", "Write down the amount borrowed.", 1, ib.cash_whole(cur, loan), loan),
                ib.part("b", "Find the monthly payment. Give your answer to two decimal "
                        "places.", 3, ib.cash(cur, payment), payment),
                ib.part("c", "Find the total interest paid over the life of the loan, to the "
                        "nearest {}.".format(unit), 2, ib.cash_whole(cur, interest), interest),
            ])

        instalment = p["instalment"]
        payment = monthly_payment(p["loan"], p["rate"], months)
        count, final = pay_off(p["loan"], p["rate"], instalment)
        original = ib.to_cents(payment) * months
        faster = (count - 1) * instalment + ib.to_cents(final)
        saving = ib.round_whole(original - faster)
        context = ["{} takes out a mortgage of {}{}, to be repaid over {} years with equal "
                   "payments at the end of each month. The nominal annual interest rate is "
                   "{}%, compounded monthly.".format(
                       p["name"], cur, p["loan"], p["years"], p["rate"])]
        return ib.assemble(context, [
            ib.part("a", "Find the monthly payment. Give your answer to two decimal places.",
                    3, ib.cash(cur, payment), payment),
            ib.part("b", "Instead, {} decides to pay {}{} each month. Find the number of "
                    "monthly payments needed to repay the mortgage.".format(
                        p["name"], cur, instalment), 2, "{} payments".format(count), count),
            ib.part("c", "The final payment is less than {}{}. Find the final payment. Give "
                    "your answer to two decimal places.".format(cur, instalment), 3,
                    ib.cash(cur, final), final),
            ib.part("d", "Find how much {} saves by paying {}{} each month instead of the "
                    "payment in part (a), to the nearest {}.".format(
                        p["name"], cur, instalment, unit), 2, ib.cash_whole(cur, saving), saving),
        ])

    def validate_independently(self, question):
        """Run payments month by month, and count payments with logarithms."""
        import math
        p, level = question.parameters, question.difficulty
        values = ib.answer_values(question)
        i = float(Fraction(p["rate"])) / 1200
        months = 12 * p["years"]

        def left_after(loan, instalment, count):
            balance = float(loan)
            for _ in range(count):
                balance = balance * (1 + i) - instalment
            return balance

        if level == 3:
            loan = p["price"] * (100 - p["down"]) / 100
            require(Fraction(values["a"]) == Fraction(p["price"] * (100 - p["down"]), 100),
                    "Independent loan amount failed")
            payment_label = "b"
        else:
            loan = p["loan"]
            payment_label = "a"
        payment = float(Fraction(values[payment_label]))
        require(abs(left_after(loan, payment, months)) < 1e-3, "Payment does not clear the loan")

        if level == 2:
            total = math.floor(round(payment, 2) * months + 0.5)
            require(Fraction(values["b"]) == total, "Independent total failed")
            require(Fraction(values["c"]) == total - p["loan"], "Independent interest failed")
        if level == 3:
            interest = round(payment, 2) * months - loan
            require(abs(float(Fraction(values["c"])) - interest) <= 0.51,
                    "Independent interest failed")
        if level == 4:
            x = p["instalment"]
            count = math.ceil(-math.log(1 - loan * i / x) / math.log(1 + i) - 1e-9)
            require(Fraction(values["b"]) == count, "Independent payment count failed")
            growth = (1 + i) ** (count - 1)
            before_last = loan * growth - x * (growth - 1) / i
            final = before_last * (1 + i)
            require(ib.close(values["c"], final, 1e-7), "Independent final payment failed")
            saving = round(payment, 2) * months - ((count - 1) * x + round(final, 2))
            require(abs(float(Fraction(values["d"])) - saving) <= 0.51,
                    "Independent saving failed")
        return True