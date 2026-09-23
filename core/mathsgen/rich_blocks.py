"""Shared builders for schema-5 rich Content blocks.

Author blocks from exact parameters; never parse prose into maths.
Every maths run carries a plain-text fallback, so Content.text stays a
complete CLI rendering. Adjacent runs without whitespace render as one
unbreakable group, which keeps punctuation attached to maths.

No renderer imports: generators can use this module freely.
"""


def prose(value):
    """A paragraph of plain prose."""
    return {"kind": "paragraph", "text": value}


def text(value):
    """A prose run inside a paragraph."""
    return {"text": value}


def maths(tex, fallback):
    """An inline maths run with its plain-text fallback."""
    return {"tex": tex, "text": fallback}


def paragraph(*runs):
    """A paragraph built from text and maths runs."""
    return {"kind": "paragraph", "runs": list(runs)}


def equation(tex, fallback):
    """A display equation on its own line."""
    return {"kind": "equation", "tex": tex, "text": fallback}


def unit_tex(name, power=1):
    """Upright unit: unit_tex("cm", 3) gives \\mathrm{cm}^{3}."""
    tex = r"\mathrm{" + name + "}"
    return tex if power == 1 else tex + "^{" + str(power) + "}"


def unit_text(name, power=1):
    """Plain fallback matching unit_tex: unit_text("cm", 3) gives cm^3."""
    return name if power == 1 else name + "^" + str(power)


def degrees_tex(expression_tex):
    """Append a degree sign. Bracket compound expressions first."""
    return expression_tex + r"^{\circ}"