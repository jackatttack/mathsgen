"""Graphs you can play with: curves, and sliders for their letters.

    from mathskit import graph

    lines = graph.Graph(x=(-10, 10), square=True, title='Straight lines')
    lines.curve('m x + c')                         # m and c become sliders
    lines.slider('m', -5, 5, value=2, step=0.5)    # ...with these ranges
    page.prose(blocks.graph(lines))

    waves = graph.Graph(x=(-6.3, 6.3), y=(-4, 4))
    waves.transform('sin(x)')                      # faint sin x, plus a f(bx)

x is the variable; every other letter in a curve becomes a slider
(SLIDER_DEFAULTS until slider() says otherwise). sympy reads the text
and writes each curve as JavaScript, so the page draws and redraws it
with no trip to Python (graph_page.py). y=None works out a y range once
from the starting values and keeps it, so a slider visibly moves the
curve; square=True makes one unit the same length on both axes.

Needs sympy (Pythonista has it). The rest of mathskit does not.
"""

# --- Settings (editable) ------------------------------------------------------
DEFAULT_X = (-5.0, 5.0)
SLIDER_DEFAULTS = {'low': -5.0, 'high': 5.0, 'value': 1.0, 'step': 0.1}
TRANSFORM_SLIDERS = {'low': -3.0, 'high': 3.0, 'value': 1.0, 'step': 0.1}
SYMBOLS = {'\u03c0': ' pi ', '\u00d7': '*', '\u2212': '-', '\u00b2': '^2', '\u00b3': '^3'}


class GraphError(ValueError):
    """A curve that cannot be read or drawn."""


class Curve:
    def __init__(self, text, js, tex, faint=False):
        self.text = text          # as written
        self.js = js              # JavaScript for the page
        self.tex = tex            # LaTeX for the legend
        self.faint = faint        # drawn dashed and dim (a base curve)


class Slider:
    def __init__(self, name, low, high, value, step):
        if not low < high:
            raise GraphError('Slider %s needs low < high.' % name)
        self.name = name
        self.low = float(low)
        self.high = float(high)
        self.step = float(step)
        self.value = min(self.high, max(self.low, float(value)))


class Graph:
    def __init__(self, x=DEFAULT_X, y=None, square=False, height=None, title=None):
        if not float(x[0]) < float(x[1]):
            raise GraphError('The x range needs low < high.')
        self.x = (float(x[0]), float(x[1]))
        self.y = None if y is None else (float(y[0]), float(y[1]))
        self.square = square
        self.height = height      # pixels; None fits the width
        self.title = title
        self.curves = []
        self.sliders = []

    def curve(self, text, faint=False, label=None):
        """Draw y = text. label is LaTeX for the legend (worked out if None)."""
        return self.add(parse(text), str(text), faint, label)

    def transform(self, text, sliders=TRANSFORM_SLIDERS):
        """f(x) = text drawn faint, then a f(bx) with sliders a and b."""
        import sympy
        base = parse(text)
        x = sympy.Symbol('x')
        a, b = sympy.Symbol('a'), sympy.Symbol('b')
        self.add(base, str(text), True, None)
        for name in ('a', 'b'):
            self.slider(name, **sliders)
        return self.add(a * base.subs(x, b * x), 'a f(bx)', False, None)

    def slider(self, name, low=None, high=None, value=None, step=None):
        """Set (or add) the slider for the letter name."""
        settings = dict(SLIDER_DEFAULTS)
        settings.update({key: given for key, given in
                         (('low', low), ('high', high), ('value', value), ('step', step))
                         if given is not None})
        new = Slider(name, **settings)
        for index, known in enumerate(self.sliders):
            if known.name == name:
                self.sliders[index] = new
                return self
        self.sliders.append(new)
        return self

    def add(self, expression, text, faint, label):
        import sympy
        js = to_js(expression)
        tex = label if label is not None else readable_tex(text, expression)
        for symbol in sorted(expression.free_symbols, key=str):
            name = str(symbol)
            if name != 'x' and name not in [known.name for known in self.sliders]:
                self.slider(name)
        if any(not isinstance(symbol, sympy.Symbol) for symbol in expression.free_symbols):
            raise GraphError('Cannot draw %r.' % text)
        self.curves.append(Curve(text, js, tex, faint))
        return self

    def spec(self):
        """What the page needs, as JSON-ready data."""
        return {'x': list(self.x), 'y': list(self.y) if self.y else None,
                'square': bool(self.square), 'height': self.height,
                'curves': [{'js': curve.js, 'faint': curve.faint} for curve in self.curves],
                'sliders': [{'name': slider.name, 'value': slider.value}
                            for slider in self.sliders]}


# --- Reading and writing curves -----------------------------------------------

def clean(text):
    text = str(text).strip()
    for symbol, plain in SYMBOLS.items():
        text = text.replace(symbol, plain)
    compact = text.replace(' ', '').lower()
    if compact.startswith('y=') or compact.startswith('f(x)='):
        text = text.split('=', 1)[1]
    # Keep pi whole: sympy's letter splitting reads 3pix as 3*p*i*x.
    return text.replace('pi', ' pi ')


def parse(text, evaluate=True):
    """The sympy expression for text: implicit multiplication (2x, a x),
    ^ for powers, e and pi as the constants."""
    import sympy
    from sympy.parsing.sympy_parser import (convert_xor, implicit_multiplication_application,
                                            parse_expr, standard_transformations)
    transformations = standard_transformations + (implicit_multiplication_application,
                                                  convert_xor)
    names = {'x': sympy.Symbol('x'), 'e': sympy.E, 'pi': sympy.pi}
    try:
        result = parse_expr(clean(text), local_dict=names, transformations=transformations,
                            evaluate=evaluate)
    except Exception as error:
        raise GraphError('Could not read %r: %s' % (text, error))
    if not isinstance(result, sympy.Expr):     # S, N, Q... are sympy's own names, not curves
        raise GraphError('%r is not an expression to draw.' % text)
    return result


def to_js(expression):
    from sympy.printing.jscode import jscode
    js = jscode(expression)
    if '//' in js or 'Not supported' in js:
        raise GraphError('The page cannot draw %s yet.' % expression)
    return js


def readable_tex(text, expression):
    """LaTeX in the order it was written (sympy would sort the terms)."""
    import sympy
    if '/' in text:
        return sympy.latex(expression)   # unevaluated division reads 1 \cdot \frac{1}{x}
    try:
        return sympy.latex(parse(text, evaluate=False), order='none')
    except Exception:
        return sympy.latex(expression)
