"""Solving linear equations: one lesson, from one step to the stretch stage.

Each stage draws equations from mathskit.generate by kind and solves them
with mathskit.linear, so the worked steps, the Question button and Your
move all match the stage on screen. Edit the ladder below.
"""
from .. import generate
from ..lesson import Fact, Lesson, Problem, Stage


def equations(*kinds):
    """make_problem for a stage: an equation of one of these kinds, solved."""
    def make_problem(rng):
        return Problem.from_equation(generate.equation(rng.choice(kinds), rng=rng))
    return make_problem


# --- Facts (editable) ---------------------------------------------------------

BALANCE = (
    '<svg viewBox="0 0 240 110" width="240" height="110" xmlns="http://www.w3.org/2000/svg" '
    'fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" '
    'stroke-linejoin="round">'
    '<path d="M120 28 L120 96 M96 96 L144 96"/>'
    '<path d="M40 28 L200 28"/>'
    '<path d="M40 28 L24 60 M40 28 L56 60 M200 28 L184 60 M200 28 L216 60"/>'
    '<path d="M16 60 Q40 78 64 60 Z M176 60 Q200 78 224 60 Z"/>'
    '<text x="40" y="96" text-anchor="middle" fill="currentColor" stroke="none" '
    'font-size="17" font-family="-apple-system, sans-serif">x + 3</text>'
    '<text x="200" y="96" text-anchor="middle" fill="currentColor" stroke="none" '
    'font-size="17" font-family="-apple-system, sans-serif">7</text>'
    '</svg>')

FACTS = [
    Fact('The golden rule',
         'Whatever you do to one side, do to the other. The equation stays '
         'balanced, like a pair of scales.', BALANCE),
    Fact('Inverse operations',
         r'Adding and subtracting undo each other. Multiplying and dividing undo '
         r'each other: $3x$ divided by $3$ is $x$.'),
    Fact('Undo in reverse order',
         r'Deal with adding or subtracting first, then multiplying or dividing: '
         r'$2x + 3 = 11$, so $2x = 8$, so $x = 4$.'),
    Fact('Expanding brackets',
         r'Multiply every term inside by the number outside: $3(x + 4) = 3x + 12$. '
         r'A minus outside changes every sign: $-(x - 5) = -x + 5$.'),
    Fact('Unknowns on both sides',
         r'Take the smaller $x$ term away from both sides, so the $x$ term left is '
         r'positive: $5x + 1 = 2x + 10$ gives $3x + 1 = 10$.'),
    Fact('Clearing fractions',
         r'Multiply both sides by the denominator: $\frac{x}{4} = 3$ gives $x = 12$. '
         r'With a fraction on each side, cross multiply: $\frac{a}{b} = \frac{c}{d}$ '
         r'gives $ad = bc$.'),
    Fact('Dividing by a negative',
         r'$-3x = 12$ gives $x = -4$. Dividing both sides by a negative changes the '
         r'sign of the answer.'),
    Fact('Check your answer',
         r'Put the answer back into the original equation. If both sides come to the '
         r'same number, it is right: $x = 4$ in $2x + 3 = 11$ gives $11 = 11$.'),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='linear',
    title='Solving linear equations',
    area='Algebra',
    keywords=('equations', 'solve', 'unknown', 'balance'),
    intro='Do the same thing to both sides until $x$ is on its own.',
    facts=FACTS,
    stages=[
        Stage('one_step', 'One step',
              'One operation stands between $x$ and the answer. Undo it on both '
              'sides: take away what was added, divide what was multiplied.',
              equations('one_step')),
        Stage('two_step', 'Two steps',
              'Two operations. Undo them in reverse order: the adding or '
              'subtracting first, then the multiplying or dividing.',
              equations('two_step')),
        Stage('both_sides', 'Unknowns on both sides',
              'Get the $x$ terms together on one side first. Then it is a '
              'two-step equation.',
              equations('both_sides')),
        Stage('brackets', 'Brackets',
              'Expand the brackets first, multiplying every term inside. Then '
              'collect like terms and solve as before.',
              equations('brackets', 'two_brackets')),
        Stage('fractions', 'Fractions',
              'Clear the fraction: multiply both sides by the denominator. With '
              'a fraction on each side, cross multiply.',
              equations('fraction_one_side', 'fractions')),
        Stage('stretch', 'Stretch',
              'Negative $x$ terms and answers that are fractions. Move the $x$ '
              'terms so they stay positive, and leave the answer as a fraction '
              'in its simplest form.',
              equations('stretch')),
    ])
