"""Every lesson stage makes problems that are right and render.

For each stage, SEEDS problems:
- equations (problem.equation): one answer, equal to the equation's own
  root (read from its a*x + b = 0 form, not from the steps); Your move can
  start on it; linear's whole-number stages stay whole.
- worked problems: every line has words; meta 'got' (from the working)
  equals meta 'expected' (straight from the formula).
- all: no unescaped % in any TeX (KaTeX would read a comment), and
  blocks.steps renders the solution.
Prints one example per stage.
"""
import os
import random
import re
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
for name in list(sys.modules):
    if name == 'mathskit' or name.startswith('mathskit.'):
        del sys.modules[name]

from mathskit import blocks, explore, lessons, linear  # noqa: E402

SEEDS = 60
LINEAR_WHOLE_STAGES = ('one_step', 'two_step', 'both_sides', 'brackets', 'fractions')
BARE_PERCENT = re.compile(r'(?<!\\)%')


def root(text):
    a, b = linear.read(text).form()
    return Fraction(-b) / Fraction(a)


def check_equation(lesson, stage, problem):
    """Returns True when the answer is a fraction."""
    solution = problem.solution
    if solution.kind != 'one':
        raise AssertionError('no single answer: %s' % solution.verdict)
    expected = root(problem.equation)
    if Fraction(solution.answer) != expected:
        raise AssertionError('steps give %s, equation says %s' % (solution.answer, expected))
    if lesson.key == 'linear' and stage.key in LINEAR_WHOLE_STAGES and expected.denominator != 1:
        raise AssertionError('answer %s should be whole' % expected)
    explore.Explorer(problem.equation)
    return expected.denominator != 1


FORM_LETTERS = 'abmnpqxy'
FORM_RNG = random.Random(1)


def check_forms(forms):
    """Every form of the problem (question, working, answer) is the same
    expression: evaluate them all at random fractional values."""
    for _ in range(3):
        values = {letter: Fraction(FORM_RNG.randint(-7, 7), FORM_RNG.choice((1, 2, 3)))
                  for letter in FORM_LETTERS}
        results = [eval(form, {'__builtins__': {}}, values) for form in forms]
        if any(result != results[0] for result in results):
            raise AssertionError('forms disagree: %s' % ' | '.join(forms))


def check_worked(problem):
    for line in problem.solution.steps:
        if not line.say:
            raise AssertionError('a line with no words')
    meta = problem.meta
    if 'expected' in meta and meta['got'] != meta['expected']:
        raise AssertionError('working gives %s, formula gives %s'
                             % (meta['got'], meta['expected']))
    if 'forms' in meta:
        check_forms(meta['forms'])
    if 'roots' in meta:
        form, roots = meta['roots']
        for root in roots:
            value = eval(form, {'__builtins__': {}}, {'x': float(root)})
            if abs(value) > 1e-6:
                raise AssertionError('x = %s gives %s, not 0, in %s' % (root, value, form))


def check_figure(problem):
    """A Plot must build as a graph (sympy parses every curve)."""
    figure = getattr(problem, 'figure', None)
    if figure is None or isinstance(figure, str):
        return
    from mathskit import graph
    drawn = graph.Graph(**figure.window())
    for curve in figure.curves:
        drawn.curve(curve)


def check_problem(lesson, stage, problem):
    for line in problem.solution.steps:
        if line.tex and BARE_PERCENT.search(line.tex):
            raise AssertionError('unescaped %% in %r' % line.tex)
    blocks.steps(problem.solution)
    check_figure(problem)
    if problem.equation:
        return check_equation(lesson, stage, problem)
    check_worked(problem)
    return False


def main():
    failures = []
    for lesson in lessons.ALL:
        print('LESSON %s: %d stages, %d facts' % (lesson.key, len(lesson.stages), len(lesson.facts)))
        for stage in lesson.stages:
            fractional = 0
            for seed in range(SEEDS):
                problem = None
                try:
                    problem = stage.problem(seed=seed)
                    fractional += check_problem(lesson, stage, problem)
                except Exception as error:
                    failures.append('%s/%s seed %d (%s): %s: %s' % (
                        lesson.key, stage.key, seed,
                        getattr(problem, 'statement', '?'), type(error).__name__, error))
            try:
                sample = stage.problem(seed=7)
                print('  %-14s %s' % (stage.key, sample.answer))
            except Exception as error:
                print('  %-14s (no sample: %s)' % (stage.key, error))
            if lesson.key == 'linear' and stage.key == 'stretch' and fractional == 0:
                failures.append('linear/stretch: no fractional answers in %d seeds' % SEEDS)
        first, last = lesson.stages[0], lesson.stages[-1]
        if lesson.easier(first) is not first or lesson.harder(last) is not last:
            failures.append('%s: Easier/Harder run off the ends' % lesson.key)

    if failures:
        print('FAILED %d:' % len(failures))
        for line in failures[:15]:
            print('  ' + line)
        raise SystemExit(1)
    print('smoke_lessons: all stages passed')


main()
