"""Lessons: a ladder of stages, each making problems from one generator.

    from mathskit import lessons
    lesson = lessons.find('linear')
    stage = lesson.stages[0]
    problem = stage.problem(seed=4)
    problem.statement      # TeX of the question
    problem.solution       # worked steps (linear.Solution), or None
    problem.answer         # the answer in words
    problem.equation       # text Your move plays, or None where it doesn't fit
    lesson.harder(stage)   # the next stage up (the same one at the top)

A lesson knows nothing about the screen showing it: the Lesson page, the
Questions tab and (later) a student screen all read these same objects.
Pure Python (Pythonista, PythonIDE, Juno).
"""
import random

from . import linear


class Line:
    """One line of working: say (plain words above it) and tex (the maths,
    or None for a line of words only, such as a worded question)."""

    def __init__(self, say, tex=None):
        self.say = say
        self.tex = tex


class Worked:
    """Worked steps in the shape blocks.steps reads, like linear.Solution:
    steps (Lines), kind 'one', and verdict (the answer in words). The last
    line should show the answer, since kind 'one' adds no verdict line."""

    def __init__(self, lines, verdict):
        self.steps = list(lines)
        self.kind = 'one'
        self.verdict = verdict


class Plot:
    """A graph to show with the working: curves as text graph.py reads
    ('x^2 - 2x - 8') and the window. Pure data: the page builds the
    graph.Graph, so lessons need no sympy."""

    def __init__(self, curves, x=(-10, 10), y=None, title='', square=False):
        self.curves = list(curves)
        self.x = x
        self.y = y
        self.title = title
        self.square = square       # equal scales, so right angles look right

    def window(self):
        options = {'x': self.x, 'title': self.title}
        if self.square:
            options['square'] = True
        elif self.y is not None:
            options['y'] = self.y
        return options


class Problem:
    """One question, with everything needed to teach it."""

    def __init__(self, statement, answer, solution=None, equation=None, meta=None,
                 figure=None):
        self.statement = statement
        self.answer = answer
        self.solution = solution
        self.equation = equation
        self.meta = meta or {}     # for tests: e.g. got/expected worked two ways
        self.figure = figure       # a Plot or inline SVG shown with the working

    @classmethod
    def from_equation(cls, text, your_move=True):
        """A linear equation solved as taught. Your move can play it when
        your_move is true."""
        solution = linear.solve(text)
        return cls(statement=solution.steps[0].tex, answer=solution.verdict,
                   solution=solution, equation=text if your_move else None)


class Fact:
    """A key fact or formula for a lesson's Facts page. front is a short
    title; back is maths prose ($...$); figure is optional inline SVG,
    drawn with currentColor so it suits light and dark themes."""

    def __init__(self, front, back, figure=None, tex=None):
        self.front = front
        self.back = back
        self.figure = figure
        self.tex = tex             # optional display maths (a table) under the back


class Stage:
    """One rung of a lesson: the idea in words and a way to make problems.

    idea is maths prose ($...$). make_problem(rng) returns a Problem; the
    rng is the only source of variety, so a seed always gives the same one.
    """

    def __init__(self, key, title, idea, make_problem):
        self.key = key
        self.title = title
        self.idea = idea
        self.make_problem = make_problem

    def problem(self, seed=None, rng=None):
        return self.make_problem(rng or random.Random(seed))


class Lesson:
    """A topic as a ladder of stages, easiest first. Start anywhere; Easier
    and Harder step one rung and stop at the ends."""

    def __init__(self, key, title, intro, stages, facts=(), area='', keywords=()):
        keys = [stage.key for stage in stages]
        if len(set(keys)) != len(keys):
            raise ValueError('%s: two stages share a key' % key)
        self.key = key
        self.title = title
        self.intro = intro
        self.stages = list(stages)
        self.facts = list(facts)
        self.area = area                  # Number, Algebra, Geometry, ...: groups the Lessons page
        self.keywords = tuple(keywords)   # extra words the Lessons search matches

    def stage(self, key):
        for stage in self.stages:
            if stage.key == key:
                return stage
        raise KeyError('%s has no stage %r' % (self.key, key))

    def position(self, stage):
        return self.stages.index(stage)

    def easier(self, stage):
        return self.stages[max(self.position(stage) - 1, 0)]

    def harder(self, stage):
        return self.stages[min(self.position(stage) + 1, len(self.stages) - 1)]
