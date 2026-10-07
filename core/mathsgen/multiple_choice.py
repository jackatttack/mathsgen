"""Misconception-based options, independent of UI and PDF rendering.

Providers explicitly opt in by generator and question form. They supply exact
candidates with a named mistake; this engine never invents random answers.
Each answer domain has its own exact comparison contract (key): rationals
compare as Fractions, polynomials as collected canonical terms. Nothing is
compared by display string or by numerical substitution.

Original answer data is retained in the teacher-only answer object. Student
Choice objects contain only opaque position IDs and visible content.
"""
from dataclasses import dataclass, replace
from fractions import Fraction
import hashlib
import random

from .core import (
    Choice, Content, canonical_json, rational_text, rational_tex, require,
)


ENGINE_VERSION = 2
MINIMUM_OPTIONS = 3
MAXIMUM_OPTIONS = 4


@dataclass(frozen=True)
class RationalCandidate:
    """A rational value and the misconception that produces it.

    Optional raw numerator/denominator preserve meaningful error notation,
    such as 2/6 from adding the tops and bottoms of 1/3 + 1/3.
    Equality always uses the exact value, never the displayed spelling.
    """
    value: Fraction
    mistake: str
    explanation: str
    raw: tuple = ()

    def content(self):
        value = Fraction(self.value)
        if not self.raw:
            return Content(rational_text(value), rational_tex(value))
        numerator, denominator = self.raw
        require(type(numerator) is int and type(denominator) is int,
                "Raw fraction requires integer components")
        require(denominator > 0, "Raw denominator must be positive")
        require(Fraction(numerator, denominator) == value,
                "Raw fraction disagrees with its exact value")
        sign = "-" if numerator < 0 else ""
        return Content(
            "{}/{}".format(numerator, denominator),
            sign + r"\frac{" + str(abs(numerator)) + "}{" + str(denominator) + "}",
        )

    def key(self):
        """Exact identity used for distinctness and for finding the answer."""
        return Fraction(self.value)

    def metadata(self):
        """Teacher-only record. Unchanged since engine version 2, so existing
        identities and action links still reproduce exactly."""
        return {"value": rational_text(self.value)}


@dataclass(frozen=True)
class PolynomialCandidate:
    """A polynomial, as [coefficient, monomial] terms, and the mistake behind it.

    Equality uses the collected canonical form from algebra_basics, so 3ab and
    3ba, or x + x and 2x, are the same option. A "mistake" that is secretly
    equivalent to the correct answer is therefore discarded, never shown.
    Display is always the collected form a student would write as a final answer.
    """
    terms: list
    mistake: str
    explanation: str

    def collected(self):
        from .algebra_basics import collect
        return collect([[coefficient, list(monomial)] for coefficient, monomial in self.terms])

    def key(self):
        from .algebra_basics import monomial_key
        return tuple(
            (monomial_key(monomial), Fraction(coefficient))
            for coefficient, monomial in self.collected()
        )

    def content(self):
        from .algebra_basics import expression_text
        terms = self.collected()
        return Content(expression_text(terms), expression_text(terms, True))

    def metadata(self):
        """Exact collected terms; value is display text for readers only."""
        return {"terms": self.collected(), "value": self.content().text}


CANDIDATE_TYPES = (RationalCandidate, PolynomialCandidate)


def providers():
    """Explicit provider registry shared by capability checks and generation."""
    from . import mcq_algebra, mcq_angles, mcq_area, mcq_basics, mcq_bearings
    from . import mcq_equations, mcq_fdp, mcq_fractions, mcq_negatives
    from . import mcq_order, mcq_percent_change, mcq_polygons, mcq_pythagoras
    from . import mcq_rounding, mcq_units
    return (mcq_fractions, mcq_basics, mcq_negatives, mcq_order,
            mcq_rounding, mcq_area, mcq_fdp, mcq_algebra, mcq_bearings,
            mcq_percent_change, mcq_angles, mcq_equations, mcq_polygons,
            mcq_units, mcq_pythagoras)


def supported_levels(generator_id):
    """Explicit capability list; individual forms may still be unsupported."""
    for provider in providers():
        if generator_id in provider.SUPPORTED_LEVELS:
            return provider.SUPPORTED_LEVELS[generator_id]
    return ()


def candidates_for(question):
    """Return authored candidates, or None for an unsupported question form."""
    for provider in providers():
        levels = provider.SUPPORTED_LEVELS.get(question.generator_id, ())
        if question.difficulty in levels:
            return provider.candidates(question)
    return None


def format_candidate(question, candidate):
    """Let an explicit provider choose notation without changing exact values."""
    for provider in providers():
        if question.generator_id in provider.SUPPORTED_LEVELS:
            formatter = getattr(provider, "format_candidate", None)
            if formatter is not None:
                return formatter(question, candidate)
            break
    return candidate.content()


def choose_candidates(correct, candidates):
    """Keep up to three distinct wrong options, in provider priority order.

    correct is the answer as a candidate. A bare rational is still accepted
    and treated as a RationalCandidate (the original contract, used by tests).
    Every distractor must be in the answer's domain; distinctness uses that
    domain's exact key.
    """
    if not isinstance(correct, CANDIDATE_TYPES):
        correct = RationalCandidate(Fraction(correct), "", "")
    seen = {correct.key()}
    selected = []
    for candidate in candidates:
        require(isinstance(candidate, CANDIDATE_TYPES), "Invalid MCQ candidate")
        require(type(candidate) is type(correct),
                "Distractor and answer are in different answer domains")
        require(bool(candidate.mistake) and bool(candidate.explanation),
                "A distractor must explain a specific mistake")
        candidate.content()
        key = candidate.key()
        if key in seen:
            continue
        seen.add(key)
        selected.append(candidate)
        if len(selected) == MAXIMUM_OPTIONS - 1:
            break
    return selected


def numeric_answer(question):
    """Read exact numeric answer data, normalising percentage notation.

    A converted percentage such as 50% is the value 1/2, not 50.
    Units remain the provider's responsibility; unlike units are never mixed
    within one option set.
    """
    answer = question.answer
    kind = answer.get("kind")
    if kind == "converted_value":
        require(answer.get("form") in ("fraction", "decimal", "percentage"),
                "Unsupported conversion answer form")
        value = answer["value"]
        if answer["form"] == "percentage":
            require(isinstance(value, str) and value.endswith("%"),
                    "Percentage answer requires a percent sign")
            return Fraction(value[:-1]) / 100
        return Fraction(value)
    if kind == "multiplier":
        return Fraction(answer["multiplier"])
    if kind == "solve":
        require("largest" not in answer, "Two-part solve answers have no single value")
        return Fraction(answer["x"])
    if kind == "variable_values":
        require(set(answer["values"]) == {"x"}, "Only single-unknown answers have one value")
        return Fraction(answer["values"]["x"])
    require(kind in ("rational", "rounded_value", "measure", "decimal",
                     "money", "bearing", "integer", "angle", "converted_quantity",
                     "length"),
            "Numeric MCQ provider requires an explicit exact numeric answer")
    return Fraction(answer["value"])


def correct_candidate(question):
    """The original answer as a candidate in its own exact answer domain."""
    if question.answer.get("kind") == "polynomial_terms":
        return PolynomialCandidate(question.answer["terms"], "", "")
    return RationalCandidate(numeric_answer(question), "", "")


def option_key(option):
    """Exact key rebuilt from stored teacher metadata, never from display text."""
    if "terms" in option:
        return PolynomialCandidate(option["terms"], "", "").key()
    return Fraction(option["value"])


def make_multiple_choice(question):
    """Adapt a supported ordinary question, or return None.

    None means this form has no provider or too few distinct misconceptions.
    Callers must retry or report the limitation, never silently emit a written
    question when multiple choice was requested. Existing native MCQs are
    outside this adapter's contract.
    """
    if question.choices:
        raise ValueError("Question already has choices")
    candidates = candidates_for(question)
    if candidates is None:
        return None
    correct_entry = correct_candidate(question)
    selected = choose_candidates(correct_entry, candidates)
    if len(selected) < MINIMUM_OPTIONS - 1:
        return None
    entries = [correct_entry] + selected
    seed_material = canonical_json(["multiple_choice", ENGINE_VERSION, question.id])
    digest = hashlib.sha256(seed_material.encode("utf-8")).hexdigest()
    random.Random(int(digest, 16)).shuffle(entries)
    choices = tuple(
        Choice("option_" + str(index), format_candidate(question, entry))
        for index, entry in enumerate(entries)
    )
    correct_index = next(
        index for index, entry in enumerate(entries)
        if entry.key() == correct_entry.key()
    )
    correct = choices[correct_index]
    letter = chr(65 + correct_index)
    answer = {
        "kind": "choice",
        "choice_id": correct.id,
        "multiple_choice": {
            "engine_version": ENGINE_VERSION,
            "original_id": question.id,
            "original_answer": question.answer,
            "original_display": {
                "text": question.answer_display.text,
                "math_tex": question.answer_display.math_tex,
                "display_text": question.answer_display.display_text,
                "blocks": question.answer_display.blocks,
            },
            "options": [
                dict(entry.metadata(), choice_id=choice.id,
                     mistake=entry.mistake, explanation=entry.explanation)
                for choice, entry in zip(choices, entries)
            ],
        },
    }
    identity = hashlib.sha256(canonical_json({
        "base": question.id, "engine": ENGINE_VERSION,
        "choices": [
            [choice.id, choice.content.text, choice.content.math_tex]
            for choice in choices
        ],
        "answer": answer,
    }).encode("utf-8")).hexdigest()
    return replace(
        question,
        id=identity,
        choices=choices,
        answer=answer,
        answer_display=Content(
            letter + ": " + correct.content.text,
            r"\mathrm{" + letter + r"}:\quad " + correct.content.math_tex,
        ),
    )


def original_question(question):
    """Recover the written question for the original generator's validator."""
    metadata = question.answer.get("multiple_choice")
    require(isinstance(metadata, dict), "Missing multiple-choice metadata")
    require(metadata.get("engine_version") == ENGINE_VERSION,
            "Unsupported multiple-choice engine version")
    return replace(
        question,
        id=metadata["original_id"],
        choices=(),
        answer=metadata["original_answer"],
        answer_display=Content(**metadata["original_display"]),
    )


def validate_multiple_choice(question, generator, independent=False):
    """Validate the original mathematics and every emitted option/key field.

    Rebuilding also checks mistake attribution, raw display, deterministic
    order and the adapted identity. Exact values establish uniqueness.
    """
    original = original_question(question)
    generator.validate(original)
    if independent:
        generator.validate_independently(original)
    expected = make_multiple_choice(original)
    require(expected is not None, "Unsupported multiple-choice form")
    require(question.to_dict() == expected.to_dict(),
            "Multiple-choice content, identity or answer metadata mismatch")
    values = [
        option_key(option)
        for option in question.answer["multiple_choice"]["options"]
    ]
    require(MINIMUM_OPTIONS <= len(values) <= MAXIMUM_OPTIONS,
            "Invalid option count")
    require(len(set(values)) == len(values), "Equivalent options")
    correct_key = correct_candidate(original).key()
    require(sum(value == correct_key for value in values) == 1,
            "Expected exactly one correct option")
    return True