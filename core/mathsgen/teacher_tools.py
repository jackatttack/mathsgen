"""Question-specific teaching resources for the MathsGen teacher toolbox.

The registry is portable: it does not import Pythonista UI or clipboard modules.

Every tool has:
- A stable ID and a visible label.
- An explicit rule determining which questions it supports.
- Default options and optional configurable settings.
- A builder producing a resource for the shared rendering pipeline.

Tools build mathematical resources. They do not display interfaces, write
files or manipulate the clipboard.

The existing SupportCard is currently the shared resource contract:
title, Content and optional visual assets. This lets the teacher toolbox
reuse the tested card renderer while its interface develops independently.
"""

from dataclasses import dataclass
import math

from .core import require
from .question_support import SupportCard, equation, make_card


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ToolOption:
    """One editable setting exposed by a tool's optional interface.

    choices contains the accepted values. The default must be one of them.
    An empty set of choices is deliberately unsupported.
    """

    name: str
    label: str
    choices: tuple
    default: object


@dataclass(frozen=True)
class TeacherTool:
    """A registered teaching resource with a quick-copy default.

    supports(question) decides whether the resource is applicable.
    build(question, options) returns a SupportCard-compatible resource.

    Options are defined centrally so quick actions and interactive
    interfaces use the same defaults and validation.
    """

    id: str
    label: str
    kind: str
    supports: object
    build: object
    options: tuple = ()


_TOOLS = {}


def register_tool(tool):
    """Register a tool without silently replacing an existing definition."""

    require(isinstance(tool, TeacherTool), "Invalid teacher tool")
    require(bool(tool.id.strip()), "Teacher tool needs an ID")
    require(bool(tool.label.strip()), "Teacher tool needs a label")
    require(tool.kind in ("formula", "diagram", "question"),
            "Unknown teacher tool kind")
    require(tool.id not in _TOOLS, "Duplicate teacher tool: " + tool.id)
    require(callable(tool.supports), "Teacher tool needs a support rule")
    require(callable(tool.build), "Teacher tool needs a resource builder")

    names = set()

    for option in tool.options:
        require(isinstance(option, ToolOption), "Invalid tool option")
        require(option.name not in names, "Duplicate tool option")
        require(bool(option.choices), "Tool option needs choices")
        require(
            option.default in option.choices,
            "Tool option default is not an accepted choice",
        )
        names.add(option.name)

    _TOOLS[tool.id] = tool
    return tool


def available_tools(question):
    """Return the tools applicable to this exact question.

    A generator-specific tool must explicitly check the generator version.
    Unsupported tools are omitted rather than offered with a fallback.
    """

    return tuple(
        tool for tool in _TOOLS.values()
        if tool.supports(question)
    )


def get_tool(question, tool_id):
    """Resolve a tool while enforcing its question-specific support rule."""

    require(tool_id in _TOOLS, "Unknown teacher tool: " + str(tool_id))
    tool = _TOOLS[tool_id]

    require(
        tool.supports(question),
        "Teacher tool {} is not available for this question".format(tool_id),
    )

    return tool


def default_options(tool):
    """Return fresh editable defaults for one tool."""

    return {
        option.name: option.default
        for option in tool.options
    }


def resolve_options(tool, changes=None):
    """Merge optional changes with the tool's validated defaults.

    Reject unknown names and unsupported values rather than silently
    changing a diagram or formula's intended meaning.
    """

    resolved = default_options(tool)
    changes = {} if changes is None else changes

    require(isinstance(changes, dict), "Tool options must be a dictionary")

    definitions = {
        option.name: option
        for option in tool.options
    }

    for name, value in changes.items():
        require(name in definitions, "Unknown tool option: " + str(name))
        require(
            any(
                type(value) is type(choice) and value == choice
                for choice in definitions[name].choices
            ),
            "Unsupported value for tool option: " + name,
        )
        resolved[name] = value

    return resolved


def build_resource(question, tool_id, options=None):
    """Build one resource for quick copy or interactive preview.

    Both routes call this function. The caller decides whether to render
    a PNG, show a preview or place the result on the clipboard.
    """

    tool = get_tool(question, tool_id)
    selected_options = resolve_options(tool, options)

    resource = tool.build(question, selected_options)

    require(
        isinstance(resource, SupportCard),
        "Teacher tool must return a teaching resource",
    )

    resource.content.validate_blocks()

    return resource


# ---------------------------------------------------------------------------
# Reusable resource builders
# ---------------------------------------------------------------------------

def formula_resource(title, formulas):
    """Build a compact formula card without instructional prose.

    Each formula is a pair of plain text and supported MathText TeX.
    Plain text remains available independently of image rendering.
    """

    require(bool(formulas), "A formula resource needs at least one formula")

    blocks = [
        equation(plain_text, math_tex)
        for plain_text, math_tex in formulas
    ]

    return make_card(title, blocks)


def quadratic_formula(question, options):
    """Return the general quadratic formula without substituting answers."""

    return formula_resource(
        "Quadratic formula",
        (
            (
                "x = (-b +/- sqrt(b^2 - 4ac)) / (2a)",
                r"x=\frac{-b\pm\sqrt{b^{2}-4ac}}{2a}",
            ),
        ),
    )


def trigonometry_formulas(question, options):
    """Return the three SOHCAHTOA relationships."""

    return formula_resource(
        "SOHCAHTOA",
        (
            ("sin(theta) = O/H", r"\sin\theta=\frac{O}{H}"),
            ("cos(theta) = A/H", r"\cos\theta=\frac{A}{H}"),
            ("tan(theta) = O/A", r"\tan\theta=\frac{O}{A}"),
        ),
    )


def quadratic_graph(question, options):
    """Graph the reduced quadratic, using the question's coefficients.

    For an equation L(x) = R(x), its solutions occur where
    y = L(x) - R(x) crosses the x-axis.

    The default graph does not mark the roots. The optional marked
    version adds crosses at the intercepts, without numerical labels.
    """
    from .core import Content

    left = question.parameters["left"]
    right = question.parameters["right"]

    require(
        len(left) == len(right) == 3,
        "Expected quadratic coefficient triples",
    )
    a, b, c = [l - r for l, r in zip(left, right)]
    require(a == 1, "This graph tool expects a monic quadratic")

    discriminant = b * b - 4 * a * c
    require(discriminant > 0, "Expected two distinct real roots")
    square_root = math.isqrt(discriminant)
    require(
        square_root * square_root == discriminant,
        "Expected exact integer roots",
    )

    roots = sorted((
        (-b - square_root) // (2 * a),
        (-b + square_root) // (2 * a),
    ))
    require(
        all(a * root * root + b * root + c == 0 for root in roots),
        "Calculated intercept does not solve the equation",
    )

    view = options["view"]
    margin = 2 if view == "standard" else 5

    # Include the y-axis as well as both roots. The viewing window
    # comes from this particular question, not fixed example data.
    x_low = min(0, roots[0] - margin)
    x_high = max(0, roots[1] + margin)
    x_step = 1 if x_high - x_low <= 10 else 2

    # Use an even pair of bounds for the wider viewing range.
    if x_step == 2:
        x_low = 2 * math.floor(x_low / 2)
        x_high = 2 * math.ceil(x_high / 2)

    def y_at(x):
        return a * x * x + b * x + c

    vertex_x = -b / (2 * a)
    extrema = [
        0,
        y_at(x_low),
        y_at(x_high),
        y_at(vertex_x),
    ]
    minimum, maximum = min(extrema), max(extrema)
    padding = max(1, (maximum - minimum) * 0.08)

    # Choose readable major tick intervals. The existing renderer
    # validates both tick spacing and the total grid-line count.
    y_span = maximum - minimum + 2 * padding
    y_step = next(
        step for step in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000)
        if y_span / step <= 8
    )
    y_low = y_step * math.floor((minimum - padding) / y_step)
    y_high = y_step * math.ceil((maximum + padding) / y_step)

    samples = 240
    continuous = [
        [
            x_low + (x_high - x_low) * index / samples,
            y_at(x_low + (x_high - x_low) * index / samples),
        ]
        for index in range(samples + 1)
    ]

    plot = {
        "kind": "plot",
        "version": 1,
        "x_range": [x_low, x_high],
        "y_range": [y_low, y_high],
        "x_step": x_step,
        "y_step": y_step,
        "minor_divisions": 1,
        "equal_units": False,
        "x_label": "x",
        "y_label": "y",
        "curves": [{
            "segments": [continuous],
            "dashed": False,
        }],
        "points": (
            [[root, 0] for root in roots]
            if options["show_roots"] else []
        ),
    }

    return SupportCard(
        title="Graph of the quadratic",
        content=Content(""),
        visuals=(plot,),
    )


def question_answer(question, options):
    """Render the answer belonging to this exact question.

    Reuse the same answer content and answer-only visual assets as the
    worksheet answer pages. Never include student-facing question visuals
    or worked-solution steps in the quick-copy answer.
    """
    return SupportCard(
        title="Answer",
        content=question.answer_display,
        visuals=question.visual_assets("answers"),
    )


# ---------------------------------------------------------------------------
# Built-in tool registrations
# ---------------------------------------------------------------------------

# Register generator-specific tools against reviewed generator versions.
# A changed generator version must be inspected before support is extended.

register_tool(TeacherTool(
    id="quadratic.formula",
    label="Quadratic formula",
    kind="formula",
    supports=lambda question: (
        question.generator_id == "algebra.quadratic.factorisable_monic"
        and question.generator_version == 1
    ),
    build=quadratic_formula,
))

register_tool(TeacherTool(
    id="trigonometry.sohcahtoa",
    label="SOHCAHTOA",
    kind="formula",
    supports=lambda question: (
        question.generator_id == "geometry.trigonometry.right_angled"
        and question.generator_version == 4
    ),
    build=trigonometry_formulas,
))

register_tool(TeacherTool(
    id="quadratic.graph",
    label="Graph",
    kind="diagram",
    supports=lambda question: (
        question.generator_id == "algebra.quadratic.factorisable_monic"
        and question.generator_version == 1
    ),
    build=quadratic_graph,
    options=(
        ToolOption(
            name="show_roots",
            label="Mark the roots",
            choices=(False, True),
            default=False,
        ),
        ToolOption(
            name="view",
            label="Viewing range",
            choices=("standard", "wide"),
            default="standard",
        ),
    ),
))

register_tool(TeacherTool(
    id="question.answer",
    label="Answer",
    kind="question",
    supports=lambda question: True,
    build=question_answer,
))