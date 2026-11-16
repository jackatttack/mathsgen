"""Joins between a mathsgen question and the other mathskit blocks.

    from mathskit import joins

    joins.equations(question)   # plain-text equations found in the question
    joins.solvable(question)    # one Your move can play (text), or None
    joins.graph_for(question)   # a graph.Graph of it, or None

Equations come from the prompt's equation blocks (their plain-text
fallback) and from its text, cut into runs of maths between words of two
or more letters ("Solve 3(x + 2) = 2x - 5." gives "3(x + 2) = 2x - 5").
No generator names are needed, so new mathsgen skills join in by
themselves.

solvable: the first equation linear.solve can solve to one answer.
graph_for: the first equation whose sides are expressions in x: y = left
and y = right (a y = ... equation draws its right side), centred on where
they meet. Needs sympy for graphs; solvable is pure Python.
"""
from . import linear

import re

TRIM = '.,;:?!'
TIMES_X = re.compile(r'\d\s+x\s+\d')    # an x between two numbers is a times sign
GRAPH_MARGIN = 5          # x units either side of the solutions
GRAPH_RANGE = (-10, 10)   # when there is nothing to centre on


def equations(question):
    prompt = question.prompt
    found = [block['text'] for block in prompt.blocks if block.get('kind') == 'equation']
    words = prompt.display_text or ''
    if prompt.math_tex and words and prompt.text.startswith(words):
        found += prompt.text[len(words):].split(';')     # mathsgen's own split: words, then maths
    found += maths_runs(prompt.text)
    unique = []
    for text in found:
        text = text.strip().strip(TRIM).strip()
        if text.count('=') == 1 and text not in unique:
            unique.append(text)
    return unique


def maths_runs(text):
    """Runs of tokens between words, kept when they hold an '='."""
    runs, current = [], []
    for token in str(text).split():
        bare = token.strip(TRIM + '()')
        if (len(bare) >= 2 and bare.isalpha()) or token.endswith(':'):
            runs.append(current)                 # a word, or a label like "x:"
            current = []
        elif token.endswith(';'):
            current.append(token[:-1])           # "x + y = -6; 3x + 4y = -16": two equations
            runs.append(current)
            current = []
        else:
            current.append(token)
    runs.append(current)
    return [' '.join(run) for run in runs if run and '=' in ' '.join(run)]


def solvable(question):
    for text in equations(question):
        if TIMES_X.search(text):
            continue                     # 55 x 26 = 1430: x means times here
        try:
            solution = linear.solve(text)
        except (linear.NotLinear, ZeroDivisionError):
            continue
        if solution.kind == 'one' and len(solution.steps) > 1:
            return text
    return None


def graph_for(question):
    try:
        import sympy
        from . import graph
    except ImportError:
        return None
    x = sympy.Symbol('x')
    for text in equations(question):
        left, right = [part.strip() for part in text.split('=')]
        try:
            if left.replace(' ', '').lower() == 'y':
                sides = [(right, graph.parse(right))]
            else:
                sides = [(left, graph.parse(left)), (right, graph.parse(right))]
        except graph.GraphError:
            continue
        expressions = [expression for _, expression in sides]
        if any(expression.free_symbols - {x} for expression in expressions):
            continue
        if not any(expression.free_symbols for expression in expressions):
            continue
        low, high = centre(expressions, x, sympy)
        title = text if len(sides) == 1 else 'y = each side of ' + text
        figure = graph.Graph(x=(low, high), title=title)
        try:
            for side_text, expression in sides:
                if expression != 0:
                    figure.curve(side_text)
        except graph.GraphError:
            continue
        if figure.curves:
            return figure
    return None


def centre(expressions, x, sympy):
    """An x range around where the sides meet (or the x-intercepts of one)."""
    difference = expressions[0] - (expressions[1] if len(expressions) > 1 else 0)
    try:
        roots = [float(root) for root in sympy.solve(difference, x) if root.is_real]
    except Exception:
        roots = []
    if not roots:
        return GRAPH_RANGE
    low, high = min(roots) - GRAPH_MARGIN, max(roots) + GRAPH_MARGIN
    return (round(low), round(high))
