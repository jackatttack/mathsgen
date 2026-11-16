"""KaTeX for maths pages: the extras a page needs to typeset blocks.

    tile = tiles.Cards(window, extra_css=typeset.page_extras())

The page shell (editorkit.web.codeview.page_html) has no head of its own
to add to, only extra_css inside its style tag. So page_extras() is
KaTeX's stylesheet plus blocks.CSS, then it closes the style tag, adds
KaTeX, auto-render and blocks.SCRIPT in a script tag, and opens an empty
style tag for the shell to close. The page is loaded from a string, so it
cannot reach files by relative path: KaTeX's fonts go in as data URIs.

Built once per run and cached (about 0.8 MB). KaTeX itself lives in
library/katex (tools/utils/katex_install.py fetches it).

Stopgap: once editorkit.web grows a proper head hook, this moves there
and the style-tag trick goes.
"""
import base64
import os
import re

from . import blocks, card_page, graph_page, question_page

# Each page part brings CSS and SCRIPT; all of them ride in every page's extras.
PAGE_PARTS = (blocks, graph_page, question_page, card_page)

# KaTeX: bundled beside the tool in a release (katex/), else the shared
# library copy (library/katex) while developing.
KATEX_CANDIDATES = (
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'katex'),
    os.path.join(os.path.expanduser('~'), 'Documents', 'library', 'katex'))


def find_katex():
    for folder in KATEX_CANDIDATES:
        if os.path.isfile(os.path.join(folder, 'katex.min.js')):
            return folder
    return KATEX_CANDIDATES[-1]


KATEX_FOLDER = find_katex()
FONT_URL = re.compile(r'url\((["\']?)fonts/([^)"\']+?\.woff2)\1\)')

_cached = None


class MissingKatex(RuntimeError):
    """KaTeX is not where KATEX_FOLDER says."""


def page_extras():
    """extra_css for a page that shows mathskit blocks (cached)."""
    global _cached
    if _cached is None:
        _cached = build_extras()
    return _cached


def build_extras(folder=KATEX_FOLDER):
    css = read_text(folder, 'katex.min.css')
    css = FONT_URL.sub(lambda match: font_data_url(folder, match), css)
    scripts = [read_text(folder, 'katex.min.js'), read_text(folder, 'auto-render.min.js')]
    scripts += [part.SCRIPT for part in PAGE_PARTS]
    script = '\n;\n'.join(safe_script(part) for part in scripts)
    styles = '\n'.join(part.CSS for part in PAGE_PARTS)
    return '%s\n%s\n</style><script>%s</script><style>' % (css, styles, script)


def read_text(folder, name):
    path = os.path.join(folder, name)
    if not os.path.exists(path):
        raise MissingKatex('%s is missing: run tools/utils/katex_install.py first.' % path)
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def font_data_url(folder, match):
    path = os.path.join(folder, 'fonts', match.group(2))
    if not os.path.exists(path):
        return match.group(0)
    with open(path, 'rb') as handle:
        data = base64.b64encode(handle.read()).decode('ascii')
    return 'url(data:font/woff2;base64,%s)' % data


def safe_script(source):
    """A script that cannot end its script tag early."""
    return source.replace('</script', '<\\/script')
