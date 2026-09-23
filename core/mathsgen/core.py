"""Shared contracts. This module has no UI, PDF or SymPy dependency."""
from dataclasses import asdict, dataclass, field
from fractions import Fraction
import hashlib
import json
import random


SCHEMA_VERSION = 5


def canonical_json(value):
    """Stable JSON for identities, exports and deterministic seed material."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    )


def rational_text(value):
    """Exact plain-text representation of an integer or rational."""
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return "{}/{}".format(value.numerator, value.denominator)


def rational_tex(value):
    """Exact TeX representation; rendering is delegated to consumers."""
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    sign = "-" if value < 0 else ""
    return sign + r"\frac{" + str(abs(value.numerator)) + "}{" + str(
        value.denominator
    ) + "}"


@dataclass(frozen=True)
class Content:
    """Human-readable content with optional display mathematics.

    text remains useful in a plain CLI. math_tex is presentation markup,
    never an executable expression or the authoritative answer.
    """
    text: str
    math_tex: str = ""
    # Optional prose for visual rendering when text already includes the
    # equation as a complete plain-text fallback.
    display_text: str = None
    blocks: tuple = ()

    def __post_init__(self):
        self.validate_blocks()

    def validate_blocks(self):
        """Validate optional rich presentation without importing a renderer.

        Empty blocks retain legacy text/math_tex/display_text behaviour.
        Nonempty blocks supply the PDF presentation; text remains the full
        CLI fallback. Lists are accepted for JSON reconstruction.
        """
        require(isinstance(self.blocks, (tuple, list)), "Content blocks must be a sequence")
        if not self.blocks:
            return True
        require(isinstance(self.text, str) and bool(self.text.strip()),
                "Rich content requires a complete plain-text fallback")
        require(not self.math_tex and self.display_text is None,
                "Rich blocks cannot be combined with legacy display fields")
        for block in self.blocks:
            require(isinstance(block, dict), "Content block must be an object")
            kind = block.get("kind")
            if kind == "equation":
                require(set(block) == {"kind", "tex", "text"}, "Invalid equation block")
                require(isinstance(block["tex"], str) and bool(block["tex"].strip()),
                        "Equation requires nonempty TeX")
                require(isinstance(block["text"], str) and bool(block["text"].strip()),
                        "Equation requires a plain-text fallback")
            elif kind == "paragraph":
                require(set(block) in ({"kind", "text"}, {"kind", "runs"}),
                        "Paragraph requires either text or runs")
                if "text" in block:
                    require(isinstance(block["text"], str) and bool(block["text"].strip()),
                            "Paragraph must contain text")
                else:
                    runs = block["runs"]
                    require(isinstance(runs, (tuple, list)) and bool(runs),
                            "Paragraph runs must be nonempty")
                    visible = False
                    for run in runs:
                        require(isinstance(run, dict) and set(run) in (
                            {"text"}, {"text", "tex"},
                        ), "Invalid paragraph run")
                        require(isinstance(run["text"], str), "Run fallback must be text")
                        visible = visible or bool(run["text"].strip())
                        if "tex" in run:
                            require(
                                isinstance(run["tex"], str) and bool(run["tex"].strip())
                                and bool(run["text"].strip()),
                                "Math run requires TeX and plain fallback",
                            )
                    require(visible, "Paragraph has no visible content")
            else:
                raise ValueError("Unknown content block: " + str(kind))
        canonical_json(self.blocks)
        return True


@dataclass(frozen=True)
class Choice:
    """A student-visible option. Correctness belongs in Question.answer."""
    id: str
    content: Content


@dataclass(frozen=True)
class LayoutHint:
    working_lines: int = 5
    keep_together: bool = True


@dataclass(frozen=True)
class Question:
    id: str
    generator_id: str
    generator_version: int
    topic: str
    subtopic: str
    difficulty: int
    seed: int
    settings: dict
    prompt: Content
    answer: dict
    answer_display: Content
    worked_solution: tuple
    marks: int
    tags: tuple
    layout_hint: LayoutHint
    parameters: dict
    diagram: object = None
    schema_version: int = SCHEMA_VERSION
    choices: tuple = ()
    question_visuals: tuple = ()
    answer_visuals: tuple = ()

    def visual_assets(self, mode="questions"):
        """Return only the assets intended for the requested audience.

        Legacy diagram remains supported, but cannot be combined with
        question_visuals. Answer assets are complete drawings, not overlays.
        Worked sheets display question assets followed by answer assets.
        """
        require(mode in ("questions", "answers", "worked"), "Unknown visual mode")
        for name, assets in (
            ("question_visuals", self.question_visuals),
            ("answer_visuals", self.answer_visuals),
        ):
            require(isinstance(assets, (tuple, list)), name + " must be a sequence")
            require(all(isinstance(asset, dict) for asset in assets),
                    name + " must contain visual specifications")
            canonical_json(assets)
        require(self.diagram is None or isinstance(self.diagram, dict),
                "diagram must be a visual specification")
        require(self.diagram is None or not self.question_visuals,
                "Use diagram or question_visuals, not both")
        student = (
            (self.diagram,) if self.diagram is not None
            else tuple(self.question_visuals)
        )
        if mode == "questions":
            return student
        if mode == "answers":
            return tuple(self.answer_visuals)
        return student + tuple(self.answer_visuals)

    def to_dict(self):
        """Full teacher/machine export, including answers and parameters."""
        return asdict(self)


@dataclass(frozen=True)
class GeneratorInfo:
    id: str
    version: int
    topic: str
    subtopic: str
    title: str
    difficulty_descriptions: dict
    tags: tuple = field(default_factory=tuple)

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class GenerationContext:
    seed: int
    difficulty: int
    settings: dict
    identity: str
    rng: object


def make_context(info, seed, difficulty, settings=None):
    """Create an isolated RNG without touching global random state.

    Settings must be JSON-compatible. Reproduction requires the same
    generator version and implementation.
    """
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(difficulty) is not int:
        raise ValueError("difficulty must be an integer")
    if difficulty not in info.difficulty_descriptions:
        raise ValueError("Unsupported difficulty: {}".format(difficulty))
    settings = {} if settings is None else settings
    if not isinstance(settings, dict):
        raise ValueError("settings must be an object")
    settings = json.loads(canonical_json(settings))
    payload = {
        "generator": info.id,
        "version": info.version,
        "seed": seed,
        "difficulty": difficulty,
        "settings": settings,
    }
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return GenerationContext(
        seed, difficulty, settings, digest,
        random.Random(int(digest, 16)),
    )


class Registry:
    """Explicit catalogue; registration never silently replaces a generator."""

    def __init__(self):
        self._generators = {}

    def register(self, generator):
        generator_id = generator.info.id
        if generator_id in self._generators:
            raise ValueError("Duplicate generator: " + generator_id)
        self._generators[generator_id] = generator

    def get(self, generator_id):
        if generator_id not in self._generators:
            raise ValueError("Unknown generator: " + generator_id)
        return self._generators[generator_id]

    def list(self, topic=None):
        return [
            generator.info
            for key, generator in sorted(self._generators.items())
            if topic is None or generator.info.topic == topic
        ]


def require(condition, message):
    """Validation that remains active even when Python assertions are disabled."""
    if not condition:
        raise ValueError(message)