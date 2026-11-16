"""Maths: a Toolbox tool for teaching maths, one lesson at a time.

Pages:
    Lessons   every lesson (mathskit.lessons); Open teaches it
    Lesson    the lesson as a ladder of stages: the idea, a worked example,
              Question, and Your move where it fits
    Facts     the lesson's key facts and formulae, tap Show to reveal
    Bank      mathsgen's question bank, for anything no lesson covers yet

Built for a shared screen: a teacher and a student look at it together, so
answers stay hidden until revealed. Opened from the hub through
Toolbox/tools/maths.json, or run this file by hand.
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
# While mathskit is young: always load the latest edit of it.
for name in list(sys.modules):
    if name == 'mathskit' or name.startswith('mathskit.'):
        del sys.modules[name]

import editorkit as ek  # noqa: E402
from editorkit.web import cards, prose  # noqa: E402
from editorkit.web import tiles as web_tiles  # noqa: E402

from mathskit import blocks, explore, graph, joins, lessons, questions, typeset  # noqa: E402

TITLE = 'Maths'
EMOJI = '\U0001f9ee'
WINDOW_KEY = 'mathskit'
FIRST_PAGE = 'Lesson'
AREA_ORDER = ('Number', 'Algebra', 'Graphs', 'Geometry', 'Probability', 'Statistics')
SEARCH_BOX = ('<input class="mk-search" type="search" placeholder="Search lessons" '
              'autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" '
              'style="width:100%;box-sizing:border-box;font-size:17px;padding:10px 12px;'
              'border-radius:10px;border:1px solid rgba(128,128,128,0.4);'
              'background:transparent;color:inherit;margin:4px 0 8px">')


def button_row(go, buttons, scroll=False):
    """A row of page buttons. buttons are (label, item, highlighted); each
    tap comes back to the page's on_pick as item. scroll brings the row
    into view after a redraw."""
    spans = ['<span class="mk-btn%s" %s>%s</span>'
             % (' mk-go' if highlighted else '', go(item), blocks.escape(label))
             for label, item, highlighted in buttons]
    mark = ' data-mk-scroll="1"' if scroll else ''
    return '<div class="mk-controls"%s>%s</div>' % (mark, ''.join(spans))


def figure_html(figure):
    """A problem's figure: inline SVG, or a lesson.Plot drawn as a graph."""
    if figure is None:
        return ''
    if isinstance(figure, str):
        return '<div class="mk-fact-figure" style="margin:10px 0">%s</div>' % figure
    drawn = graph.Graph(**figure.window())
    for curve in figure.curves:
        drawn.curve(curve)
    return blocks.graph(drawn)


# --- Lessons ------------------------------------------------------------------

class LessonsPage:
    """The Lessons page: every lesson with its ladder of stages. Open hands
    the lesson to on_open, which teaches it on the Lesson and Facts pages."""

    def __init__(self, window, extras, on_open):
        self.tile = web_tiles.Cards(window, on_pick=self.picked,
                                    zoom_key='mathskit-lessons', extra_css=extras)
        self.on_open = on_open

    def picked(self, item):
        if isinstance(item, tuple) and item[0] == 'open':
            self.on_open(lessons.find(item[1]))

    def show(self, teaching):
        page = cards.Page()
        parts = [prose.heading('Lessons', 1), SEARCH_BOX]
        areas = []
        for lesson in lessons.ALL:
            if (lesson.area or 'Other') not in areas:
                areas.append(lesson.area or 'Other')
        areas.sort(key=lambda area: AREA_ORDER.index(area) if area in AREA_ORDER
                   else len(AREA_ORDER))
        for area in areas:
            area_cards = [self.card(page, lesson, lesson is teaching)
                          for lesson in lessons.ALL if (lesson.area or 'Other') == area]
            parts.append('<div class="mk-area">%s%s</div>'
                         % (prose.heading(area, 2), ''.join(area_cards)))
        page.prose(*parts)
        self.tile.show(page)

    def card(self, page, lesson, now):
        """One lesson: title, its ladder, Open. data-search holds every word
        the search box matches (title, area, keywords, stage titles)."""
        words = [lesson.title, lesson.area] + list(lesson.keywords)
        words += [stage.title for stage in lesson.stages]
        ladder = ' \u00b7 '.join(stage.title for stage in lesson.stages)
        button = button_row(page.go, [('Teaching now' if now else 'Open \u25b6',
                                       ('open', lesson.key), not now)])
        return ('<div class="mk-lesson" data-search="%s" style="margin:4px 0 16px">%s%s%s</div>'
                % (blocks.escape(' '.join(words).lower()), blocks.text('**%s**' % lesson.title),
                   blocks.text(ladder), button))


# --- Lesson -------------------------------------------------------------------

class LessonPage:
    """The Lesson page: one lesson as a ladder of stages (mathskit.lessons).

    Pick a stage, read its idea, step through a worked example, and grab a
    question at the same stage any time. A question shows only its first
    line until Next or Show all, so the answer stays hidden until you
    choose. Your move opens under a question when the stage allows it.
    Every example and question is a fresh draw from the stage's generator.
    """

    def __init__(self, window, extras, lesson):
        self.tile = web_tiles.Cards(window, on_pick=self.picked,
                                    zoom_key='mathskit-lesson', extra_css=extras)
        self.rng = random.Random()
        self.lesson = None
        self.stage = None
        self.example = None
        self.question = None
        self.game = None           # Your move on the question, while open
        self.question_figure = False   # the question's graph, once asked for
        self.set_lesson(lesson)

    # --- What the buttons do --------------------------------------------------

    def set_lesson(self, lesson):
        self.lesson = lesson
        self.go_to(lesson.stages[0])

    def go_to(self, stage):
        self.stage = stage
        self.question = None
        self.game = None
        self.new_example()

    def new_example(self):
        self.example = self.stage.problem(rng=self.rng)
        self.show()

    def new_question(self):
        self.question = self.stage.problem(rng=self.rng)
        self.game = None
        self.question_figure = False
        self.show(scroll_to_question=True)

    def toggle_your_move(self):
        if self.game is None and self.question is not None and self.question.equation:
            self.game = explore.Explorer(self.question.equation)
        else:
            self.game = None
        self.show(scroll_to_question=True)

    def picked(self, item):
        if isinstance(item, tuple) and item[0] == 'stage':
            self.go_to(self.lesson.stage(item[1]))
        elif item == 'easier':
            self.go_to(self.lesson.easier(self.stage))
        elif item == 'harder':
            self.go_to(self.lesson.harder(self.stage))
        elif item == 'example':
            self.new_example()
        elif item == 'question':
            self.new_question()
        elif item == 'your_move':
            self.toggle_your_move()
        elif item == 'figure':
            self.question_figure = not self.question_figure
            self.show(scroll_to_question=True)
        elif isinstance(item, tuple) and item[0] == 'move' and self.game is not None:
            self.show(fresh=self.game.play(item[1]), keep_bottom=True)
        elif item in ('undo', 'restart') and self.game is not None:
            getattr(self.game, item)()
            self.show(keep_bottom=True)

    # --- The page -------------------------------------------------------------

    def show(self, fresh=False, scroll_to_question=False, keep_bottom=False):
        page = cards.Page()
        stage_buttons = [(stage.title, ('stage', stage.key), stage is self.stage)
                         for stage in self.lesson.stages]
        parts = [prose.heading(self.lesson.title, 1),
                 button_row(page.go, stage_buttons),
                 prose.heading(self.stage.title, 2),
                 blocks.text(self.stage.idea),
                 blocks.text('**Worked example**'),
                 blocks.steps(self.example.solution),
                 figure_html(self.example.figure),
                 button_row(page.go, [('New example', 'example', False),
                                      ('Easier', 'easier', False),
                                      ('Harder', 'harder', False),
                                      ('Question \u25b6', 'question', True)])]
        if self.question is not None:
            parts += self.question_parts(page, fresh, scroll_to_question)
        if keep_bottom:
            parts.append('<div data-mk-bottom="1"></div>')
        page.prose(*parts)
        self.tile.show(page)

    def question_parts(self, page, fresh, scroll):
        buttons = [('Another question', 'question', False)]
        if self.question.figure is not None:
            buttons.append(('Hide graph' if self.question_figure else 'Show graph',
                            'figure', False))
        if self.question.equation:
            buttons.append(('Close Your move' if self.game else 'Your move',
                            'your_move', self.game is None))
        landing = '<div data-mk-land="1"></div>' if scroll and not fresh else ''
        parts = [landing + prose.heading('Question', 2),
                 blocks.steps(self.question.solution),
                 figure_html(self.question.figure) if self.question_figure else '',
                 button_row(page.go, buttons)]
        if self.game is not None:
            parts.append(blocks.explore(self.game, page.go, fresh=fresh, offer_new=False))
        return parts


# --- Facts --------------------------------------------------------------------

class FactsPage:
    """The Facts page: the lesson's key facts and formulae (lesson.Fact).
    Show reveals a card in the page and Show all reveals every card, with
    no Python round trip, so the page stays where it is."""

    def __init__(self, window, extras):
        self.tile = web_tiles.Cards(window, zoom_key='mathskit-facts', extra_css=extras)

    def show(self, lesson):
        page = cards.Page()
        parts = [prose.heading(lesson.title, 1), blocks.text('**Key facts**')]
        if not lesson.facts:
            parts.append(blocks.text('No facts written for this lesson yet.'))
        else:
            parts.append('<div class="mk-controls">'
                         '<span class="mk-btn" data-mk="flip_all">Show all</span></div>')
            parts += [blocks.fact(item) for item in lesson.facts]
        page.prose(*parts)
        self.tile.show(page)


# --- Bank ---------------------------------------------------------------------

class Questions:
    """The Bank page: a mathsgen question card. Each button comes back
    through picked(), moves the deck on, and shows the card again."""

    def __init__(self, window, extras):
        self.tile = web_tiles.Cards(window, on_pick=self.picked,
                                    zoom_key='mathskit-questions', extra_css=extras)
        self.deck = questions.Deck()
        self.extra = None          # 'solve' or 'graph' while one is open under the card
        self.game = None           # the Your move game for Solve it here
        self.joined = (None, None, None)   # (question id, solvable text, graph) for the card
        self.show()

    def joins(self):
        """(solvable text, graph) for the question showing, worked out once."""
        question = self.deck.question
        key = question.id if question is not None else None
        if self.joined[0] != key:
            text = joins.solvable(question) if question is not None else None
            figure = joins.graph_for(question) if question is not None else None
            self.joined = (key, text, figure)
        return self.joined[1], self.joined[2]

    def open_extra(self, kind):
        if self.extra == kind:
            self.extra = None
            return
        text, figure = self.joins()
        if kind == 'solve' and text:
            self.game = explore.Explorer(text)
            self.extra = 'solve'
        elif kind == 'graph' and figure is not None:
            self.extra = 'graph'

    def picked(self, item):
        deck = self.deck
        moves = {'another': deck.another, 'harder': deck.harder, 'easier': deck.easier,
                 'random': deck.random}
        menu = {'all': deck.clear, 'all_grades': deck.clear_bands}
        if item in moves:
            moves[item]()
            self.extra = None
            self.show()
        elif item in ('solve', 'graph'):
            self.open_extra(item)
            self.show()
        elif isinstance(item, tuple) and item[0] == 'move' and self.game is not None:
            self.show(fresh=self.game.play(item[1]))
        elif item in ('undo', 'restart') and self.game is not None:
            getattr(self.game, item)()
            self.show()
        elif item in menu:
            menu[item]()
            self.pool_changed()
        elif isinstance(item, tuple) and item[0] == 'toggle':
            deck.toggle(item[1])
            self.pool_changed()
        elif isinstance(item, tuple) and item[0] == 'band':
            deck.toggle_band(item[1])
            self.pool_changed()

    def pool_changed(self):
        """The page has already flipped the chip; only the pool line needs
        the new name and count. No redraw, so the page stays where it is."""
        self.tile.run('window.qcPool && qcPool(%s, %d)'
                      % (json.dumps(self.deck.pool_name()), len(self.deck.pool())))

    def show(self, menu_open=False, fresh=False):
        page = cards.Page()
        text, figure = self.joins()
        buttons = []
        if text:
            buttons.append(('Close solver' if self.extra == 'solve' else 'Solve it here', 'solve'))
        if figure is not None:
            buttons.append(('Close graph' if self.extra == 'graph' else 'Graph it', 'graph'))
        below = ''
        if self.extra == 'solve' and self.game is not None:
            below = blocks.explore(self.game, page.go, fresh=fresh, offer_new=False)
        elif self.extra == 'graph' and figure is not None:
            below = blocks.graph(figure)
        page.prose(blocks.question(self.deck, page.go, menu_open, buttons, below))
        self.tile.show(page)


# --- Not on a tab: kept to reuse in a graphs lesson ----------------------------

def graphs_page():
    """Graphs to play with: lines, completed square form, stretching, and
    two lines meeting at an equation's answer."""
    lines = graph.Graph(x=(-10, 10), square=True, title='Straight lines')
    lines.curve('m x + c')
    lines.slider('m', -5, 5, value=2, step=0.5)
    lines.slider('c', -10, 10, value=1, step=1)

    vertex = graph.Graph(x=(-6, 6), y=(-8, 10), title='Completed square form')
    vertex.curve('a (x - h)^2 + k')
    vertex.slider('a', -3, 3, value=1, step=0.25)
    vertex.slider('h', -5, 5, value=0, step=0.5)
    vertex.slider('k', -6, 6, value=0, step=0.5)

    waves = graph.Graph(x=(-6.3, 6.3), y=(-4, 4), title='Stretching sin x')
    waves.transform('sin(x)')

    meet = graph.Graph(x=(-8, 4), title='Where the lines meet')
    meet.curve('2x - 24')
    meet.curve('5x - 15')

    page = cards.Page()
    page.prose(
        prose.heading('Graphs', 1),
        blocks.text('Drag a slider and the graph follows. Tap a graph to trace it.'),
        blocks.graph(lines),
        blocks.text('$m$ is the gradient: how far up for one step across. $c$ is where the '
                    'line crosses the $y$ axis.'),
        blocks.graph(vertex),
        blocks.text('The turning point is at $(h, k)$. A negative $a$ turns it upside down.'),
        blocks.graph(waves),
        blocks.text('$a$ stretches it up and down; $b$ squashes it across.'),
        prose.heading('Solving with a graph', 2),
        blocks.text('$2x - 24 = 5x - 15$ is true where the two lines meet. Tap near the '
                    'crossing: it is at $x = -3$.'),
        blocks.graph(meet))
    return page


# --- The window ---------------------------------------------------------------

def main():
    """Open the Maths window over the code (or bring it back)."""
    window = ek.Window(TITLE, emoji=EMOJI, key=WINDOW_KEY)
    extras = typeset.page_extras()
    first = lessons.ALL[0]
    lesson_page = LessonPage(window, extras, first)
    facts_page = FactsPage(window, extras)
    bank = Questions(window, extras)

    def open_lesson(lesson):
        """Teach lesson: the Lesson and Facts pages follow it."""
        lesson_page.set_lesson(lesson)
        facts_page.show(lesson)
        lessons_page.show(lesson)
        window.set_page('Lesson')

    lessons_page = LessonsPage(window, extras, open_lesson)
    lessons_page.show(first)
    facts_page.show(first)
    window.add_page('Lessons', lessons_page.tile)
    window.add_page('Lesson', lesson_page.tile)
    window.add_page('Facts', facts_page.tile)
    window.add_page('Bank', bank.tile)
    window.set_page(FIRST_PAGE)
    window.show()
    return window


if __name__ == '__main__':
    ek.run_tool(main)
