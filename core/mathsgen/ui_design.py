"""Shared Ivory app palette. PDF styling remains in theme.py.

Use green for selection and primary actions, neutral cream surfaces for
content, and terracotta sparingly. Subject identity comes from its label.
"""
from .topic_browser import topic_style as original_topic_style

PAPER = "#F6F1E6"
SURFACE = "#FFFCF5"
GROUP = "#EEE9DD"
BORDER = "#DCD5C6"
INK = "#202420"
MUTED = "#697267"
GREEN = "#164D39"
SELECTED = "#E3EBDD"
PRESSED = "#D7E2CF"
TERRACOTTA = "#A35435"
DANGER = "#A33D32"
HEADING_FONT = "Georgia-Bold"


def topic_style(topic):
    """Keep the established subject names with one consistent app palette."""
    title = original_topic_style(topic)[0]
    return title, GREEN, SELECTED