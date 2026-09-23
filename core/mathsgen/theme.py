"""Worksheet themes: every colour and font the PDF chrome uses, in one place.

A worksheet chooses a theme with specification["theme"]; "calm" is the
default (chosen 2026-09-23) and "classic" is the original look. Themes cover the page chrome (title, labels,
body text, maths ink, links, grid, footer, source line). Diagram colours stay
in visuals.py and plots.py for now.

Only the built-in PDF fonts (Helvetica family, Times, Courier) are used, so
nothing needs embedding. A custom TTF font would need registering with
reportlab.pdfbase.pdfmetrics and shipping the font file with the project.
"""
from dataclasses import dataclass

from .core import require


@dataclass(frozen=True)
class Theme:
    name: str
    body_font: str
    bold_font: str
    title_ink: str        # worksheet title and maths
    body_ink: str         # question text
    muted_ink: str        # subtitle and footer
    source_ink: str       # the generator line under each heading
    link_ink: str         # + New | Answer | Flag | Options
    grid_ink: str
    grid_width: float
    accent: str           # question heading colour when topic colours are off
    topic_colours: bool   # colour each heading by its topic


THEMES = {
    "classic": Theme(
        name="classic", body_font="Helvetica", bold_font="Helvetica-Bold",
        title_ink="#17212B", body_ink="#000000", muted_ink="#596572",
        source_ink="#8A94A0", link_ink="#24658A", grid_ink="#D0BDE7",
        grid_width=0.35, accent="#334B62", topic_colours=True,
    ),
    "calm": Theme(
        name="calm", body_font="Helvetica", bold_font="Helvetica-Bold",
        title_ink="#1F2937", body_ink="#1F2937", muted_ink="#6B7280",
        source_ink="#9CA3AF", link_ink="#4F46E5", grid_ink="#E3E7EE",
        grid_width=0.3, accent="#4F46E5", topic_colours=False,
    ),
    "contrast": Theme(
        name="contrast", body_font="Helvetica", bold_font="Helvetica-Bold",
        title_ink="#000000", body_ink="#000000", muted_ink="#374151",
        source_ink="#4B5563", link_ink="#0B3D91", grid_ink="#BFC5CC",
        grid_width=0.5, accent="#000000", topic_colours=False,
    ),
}
DEFAULT_THEME = "calm"


def theme_for(specification):
    """The theme a worksheet asks for; unknown names are refused, not ignored."""
    name = (specification or {}).get("theme", DEFAULT_THEME)
    require(name in THEMES, "Unknown worksheet theme: {}".format(name))
    return THEMES[name]