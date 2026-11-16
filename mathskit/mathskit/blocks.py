"""Maths blocks for prose pages: equations, worked steps, maths in words,
and an equation to solve your own way.

Each builder returns HTML for page.prose(...), next to editorkit.web.prose
blocks. KaTeX typesets the maths inside the page, so the page needs
typeset.page_extras() as its extra_css (typeset.py says why and how).

    from editorkit.web import cards, prose
    from mathskit import blocks, linear

    page = cards.Page()
    page.prose(prose.heading('Solving linear equations', 1),
               blocks.text('Solve $3(x + 2) = 2x - 5$ one move at a time.'),
               blocks.steps(linear.solve('3(x + 2) = 2x - 5')))

steps() runs in the page with no trip to Python: SCRIPT reveals one move
per tap of Next, and the terms that move changed light up in the accent
colour. explore() is Python's: its buttons carry the page's go items, so
each tap reaches the tool's on_pick, which plays the move and shows the
page again (fresh=True slides the new line in).

Pure Python: builders only make strings (tests/smoke_blocks.py,
tests/smoke_explore.py).
"""
import html

# --- Words on the page (editable) -------------------------------------------
NEXT_LABEL = 'Next step \u25b6'
BACK_LABEL = '\u25c0 Back'
ALL_LABEL = 'Show all'
ASK_LABEL = 'What will you do?'
HINT_LABEL = 'Hint'
UNDO_LABEL = '\u21b6 Undo'
RESTART_LABEL = 'Restart'
NEW_LABEL = 'New equation \u25b6'
SOLVED_LABEL = 'Solved: %s'
MOVES_LABEL = '%d %s \u00b7 the worked solution takes %d'


def escape(words):
    return html.escape(str(words), quote=True)


def eq(tex):
    """A displayed equation. The raw LaTeX shows until KaTeX typesets it."""
    return '<div class="mk-eq" data-tex="%s">%s</div>' % (escape(tex), escape(tex))


def text(words):
    """prose.text with maths in it: $...$ inline, $$...$$ on its own line.
    prose reads * and _ as markup first, so keep them out of the maths."""
    from editorkit.web import prose
    return '<div class="mk-text">%s</div>' % prose.text(words)


def step_row(classes, say, tex):
    """One line of working: the move in words above the equation."""
    line = ''
    if tex is not None:
        line = '<div class="mk-line" data-tex="%s">%s</div>' % (escape(tex), escape(tex))
    return '<div class="%s"><div class="mk-say">%s</div>%s</div>' % (classes, escape(say), line)


def steps(solution, shown=1):
    """A worked solution (linear.solve's Solution) revealed one move at a
    time. shown is how many lines show to begin with. When there is no
    single answer, the verdict is the last line."""
    rows = [(step.say, step.tex) for step in solution.steps]
    if solution.kind != 'one':
        rows.append((solution.verdict, None))
    shown = max(1, min(int(shown), len(rows)))
    done = ' mk-done' if shown == len(rows) else ''
    out = ['<div class="mk-steps%s" data-shown="%d">' % (done, shown)]
    for index, (say, tex) in enumerate(rows):
        classes = 'mk-step'
        if index < shown:
            classes += ' mk-shown'
        if index == shown - 1:
            classes += ' mk-latest'
        out.append(step_row(classes, say, tex))
    out.append('<div class="mk-controls">'
               '<span class="mk-btn" data-mk="back">%s</span>'
               '<span class="mk-btn mk-go" data-mk="next">%s</span>'
               '<span class="mk-btn" data-mk="all">%s</span></div>'
               % (escape(BACK_LABEL), escape(NEXT_LABEL), escape(ALL_LABEL)))
    out.append('</div>')
    return ''.join(out)


def explore(game, go, fresh=False, offer_new=True):
    """An equation solved your own way (explore.Explorer). go is the page's
    go (cards.Page.go): every button carries an item for the tool's
    on_pick, ('move', say) or 'undo', 'restart', 'new'. fresh slides the
    newest line in and scrolls the buttons into view."""
    from .explore import short_label
    out = ['<div class="mk-explore">']
    last = len(game.history) - 1
    for index, step in enumerate(game.history):
        classes = 'mk-step mk-shown'
        if index == last:
            classes += ' mk-latest' + (' mk-enter' if fresh and index else '')
        out.append(step_row(classes, step.say, step.tex))
    finished = game.verdict()
    if finished:
        moves = game.moves_made
        out.append('<div class="mk-finished"><div class="mk-solved-line">%s</div>'
                   '<div class="mk-count">%s</div></div>'
                   % (escape(SOLVED_LABEL % finished[1]),
                      escape(MOVES_LABEL % (moves, 'move' if moves == 1 else 'moves',
                                            game.worked_moves))))
    else:
        hinted = game.hint()
        out.append('<div class="mk-choices mk-open"><div class="mk-ask">%s</div>'
                   % escape(ASK_LABEL))
        for step in game.options:
            mark = ' data-hint="1"' if step.say == hinted else ''
            out.append('<span class="mk-choice" %s%s>%s</span>'
                       % (go(('move', step.say)), mark, escape(short_label(step.say))))
        out.append('</div>')
    buttons = []
    if game.moves_made:
        buttons.append('<span class="mk-btn" %s>%s</span>' % (go('undo'), escape(UNDO_LABEL)))
    if not finished:
        buttons.append('<span class="mk-btn" data-mk="nudge">%s</span>' % escape(HINT_LABEL))
    if game.moves_made:
        buttons.append('<span class="mk-btn" %s>%s</span>'
                       % (go('restart'), escape(RESTART_LABEL)))
    if offer_new:                        # off when the equation comes from a question card
        buttons.append('<span class="mk-btn mk-go" %s>%s</span>' % (go('new'), escape(NEW_LABEL)))
    scroll = ' data-mk-scroll="1"' if fresh else ''
    out.append('<div class="mk-controls"%s>%s</div>' % (scroll, ''.join(buttons)))
    out.append('</div>')
    return ''.join(out)


def graph(figure):
    """A graph you can play with (graph.Graph): curves on a canvas, a
    slider per letter, tap to trace. Drawn by graph_page's page script."""
    from . import graph_page
    return graph_page.html(figure)


def question(deck, go, menu_open=False, extra_buttons=(), below=''):
    """A question card (questions.Deck) from mathsgen: the question and its
    diagrams, Show answer, Another, Easier, Harder, Random, and a menu of
    grade bands and topics. go is the page's go; the tool's on_pick plays
    the buttons (question_page.py). menu_open keeps the menu open.
    extra_buttons are (label, item) pairs after Random (Solve it here,
    Graph it); below is HTML under the buttons (the solver or the graph)."""
    from . import question_page
    return question_page.html(deck, go, menu_open, extra_buttons, below)


def flashcard(deck, go):
    """A flashcard (flashcards.CardDeck): tap to flip, Got it, Again, Skip,
    and a menu of tiers and tags (card_page.py)."""
    from . import card_page
    return card_page.html(deck, go)


def fact(item):
    """A key fact (lesson.Fact): its front, and a back (maths prose plus an
    optional SVG figure) that Show reveals in the page with no redraw."""
    figure = ''
    if item.figure:
        figure = '<div class="mk-fact-figure" style="margin-top:10px">%s</div>' % item.figure
    return ('<div class="mk-fact" style="border:1px solid rgba(128,128,128,0.35);'
            'border-radius:12px;padding:10px 14px;margin:10px 0">'
            '%s<div class="mk-fact-back" style="display:none">%s%s</div>'
            '<div class="mk-controls"><span class="mk-btn" data-mk="flip">%s</span></div>'
            '</div>' % (text('**%s**' % item.front), text(item.back), figure,
                        escape(FACT_SHOW_LABEL)))


FACT_SHOW_LABEL = 'Show'


# --- The look -----------------------------------------------------------------

CSS = """
.mk-eq { margin: 0.4em 0 1em; overflow-x: auto; overflow-y: hidden; }
.mk-eq .katex-display, .mk-line .katex-display { margin: 0.25em 0; }
.mk-text .katex-display { overflow-x: auto; overflow-y: hidden; }
.mk-steps, .mk-explore { margin: 0.4em 0 1.2em; }
.mk-step { display: none; padding: 6px 0 2px; border-top: 1px solid var(--rule); }
.mk-step:first-child { border-top: none; }
.mk-step.mk-shown { display: block; }
.mk-step.mk-enter { animation: mk-in 0.35s ease-out; }
.mk-say { font: 13px/1.3 -apple-system, sans-serif; color: var(--muted); }
.mk-step.mk-latest .mk-say { color: var(--accent); font-weight: 600; }
.mk-line { overflow-x: auto; overflow-y: hidden; }
.mk-step .mk-hot { transition: color 0.5s; }
.mk-step.mk-latest .mk-hot { color: var(--accent); }
.mk-step.mk-enter .mk-hot { animation: mk-glow 0.9s ease-out; }
.mk-controls { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.mk-btn { padding: 7px 14px; border-radius: 10px; background: var(--wash-strong);
    border: 0.5px solid var(--rule); font: 500 14px/1.3 -apple-system, sans-serif;
    cursor: pointer; -webkit-user-select: none; user-select: none; }
.mk-btn.mk-go { background: var(--accent); color: #111111; font-weight: 600; }
.mk-steps.mk-done .mk-go { opacity: 0.4; }
.mk-choices { display: none; margin-top: 10px; }
.mk-choices.mk-open { display: flex; flex-wrap: wrap; gap: 8px; }
.mk-ask { flex: 0 0 100%; font: 600 13px/1.3 -apple-system, sans-serif; }
.mk-choice { padding: 8px 12px; border-radius: 10px; background: var(--wash-strong);
    border: 0.5px solid var(--rule); font: 14px/1.3 -apple-system, sans-serif;
    cursor: pointer; -webkit-user-select: none; user-select: none; }
.mk-choice.mk-hint { box-shadow: 0 0 0 2px var(--accent); }
.mk-finished { margin-top: 10px; animation: mk-in 0.35s ease-out; }
.mk-solved-line { font: 600 17px -apple-system, sans-serif; color: var(--accent); }
.mk-count { font: 13px -apple-system, sans-serif; color: var(--muted); margin-top: 2px; }
@keyframes mk-in { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: none; } }
@keyframes mk-glow { 0% { opacity: 0.15; } 100% { opacity: 1; } }
"""

# The page's own script: typesets every [data-tex] and .mk-text as it
# appears (a MutationObserver, so set_html, add_html and a rebuild's replay
# all get typeset with no call from Python), keeps a fresh explore's
# buttons in view, and runs the step and hint buttons ([data-mk]). Those
# taps are taken in touchend with preventDefault, so the shell's fast tap
# stands aside (library/guides/web-views.md); click is the fallback.
# Buttons with a go item are left to the shell: they go to Python.
SCRIPT = r"""
(function () {
  var TEX_OPTIONS = {displayMode: true, throwOnError: false, trust: true, strict: false};
  var INLINE_OPTIONS = {displayMode: false, throwOnError: false, trust: true, strict: false};
  var TEXT_OPTIONS = {throwOnError: false, delimiters: [
    {left: '$$', right: '$$', display: true}, {left: '$', right: '$', display: false}]};

  function typeset() {
    if (!window.katex) { return; }
    var maths = document.querySelectorAll('[data-tex]:not([data-mk-done])');
    for (var i = 0; i < maths.length; i++) {
      var element = maths[i];
      element.setAttribute('data-mk-done', '1');
      var options = element.classList.contains('mk-inline') ? INLINE_OPTIONS : TEX_OPTIONS;
      try { katex.render(element.getAttribute('data-tex'), element, options); }
      catch (error) { element.textContent = element.getAttribute('data-tex'); }
    }
    if (window.renderMathInElement) {
      var texts = document.querySelectorAll('.mk-text:not([data-mk-done])');
      for (var j = 0; j < texts.length; j++) {
        texts[j].setAttribute('data-mk-done', '1');
        try { renderMathInElement(texts[j], TEXT_OPTIONS); } catch (error) {}
      }
    }
    var fresh = document.querySelector('[data-mk-scroll]');
    if (fresh) {
      fresh.removeAttribute('data-mk-scroll');
      // The shell puts its own scroll back after a redraw: keep in view again.
      keepInView(fresh);
      setTimeout(function () { keepInView(fresh); }, 60);
      setTimeout(function () { keepInView(fresh); }, 250);
    }
    var land = document.querySelector('[data-mk-land]');
    if (land) { land.removeAttribute('data-mk-land'); landAt(land); }
    var bottom = document.querySelector('[data-mk-bottom]');
    if (bottom) { bottom.removeAttribute('data-mk-bottom'); toBottom(); }
  }

  function setClass(element, name, on) {
    if (on) { element.classList.add(name); } else { element.classList.remove(name); }
  }

  function restart(element, name) {
    element.classList.remove(name);
    void element.offsetWidth;
    element.classList.add(name);
  }

  function keepInView(element) {
    if (!element) { return; }
    var gap = element.getBoundingClientRect().bottom - window.innerHeight + 12;
    if (gap > 0) { window.scrollBy(0, gap); }
  }

  // Scroll to the very bottom of the page (data-mk-bottom), again as the
  // shell puts its own scroll back after a redraw.
  function toBottom() {
    function go() {
      var height = Math.max(document.documentElement.scrollHeight,
                            document.body ? document.body.scrollHeight : 0);
      window.scrollTo(0, height);
    }
    go();
    setTimeout(go, 60);
    setTimeout(go, 250);
    setTimeout(go, 500);
  }

  // Bring an element's top near the top of the screen (data-mk-land). The
  // shell puts its own scroll back after a redraw, so land again a moment
  // later to win.
  function landAt(element) {
    function go() {
      var top = element.getBoundingClientRect().top + window.pageYOffset - 12;
      window.scrollTo(0, Math.max(0, top));
    }
    go();
    setTimeout(go, 60);
    setTimeout(go, 250);
  }

  // --- Worked steps: Next, Back, Show all ---
  function showSteps(box, shown) {
    var rows = box.querySelectorAll('.mk-step');
    shown = Math.max(1, Math.min(rows.length, shown));
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      var on = i < shown;
      var arriving = on && !row.classList.contains('mk-shown');
      setClass(row, 'mk-shown', on);
      setClass(row, 'mk-latest', i === shown - 1);
      row.classList.remove('mk-enter');
      if (arriving) { void row.offsetWidth; row.classList.add('mk-enter'); }
    }
    box.setAttribute('data-shown', String(shown));
    setClass(box, 'mk-done', shown === rows.length);
    keepInView(box.querySelector('.mk-controls'));
  }

  function press(button) {
    var action = button.getAttribute('data-mk');
    if (action === 'nudge') { nudge(button); return; }
    if (action === 'flip') { flipFact(button.closest('.mk-fact')); return; }
    if (action === 'flip_all') { flipAllFacts(button); return; }
    var box = button.closest('.mk-steps');
    if (!box) { return; }
    var shown = parseInt(box.getAttribute('data-shown') || '1', 10);
    if (action === 'next') { shown += 1; }
    else if (action === 'back') { shown -= 1; }
    else if (action === 'all') { shown = box.querySelectorAll('.mk-step').length; }
    showSteps(box, shown);
    // The steps grow downwards: keep the newest line and its buttons in
    // view, again once the slide-in has settled.
    var controls = box.querySelector('.mk-controls');
    keepInView(controls);
    setTimeout(function () { keepInView(controls); }, 280);
  }

  // --- Explore: Hint rings the textbook's move from here ---
  function nudge(button) {
    var box = button.closest('.mk-explore');
    var move = box && box.querySelector('[data-hint="1"]');
    if (move) { restart(move, 'mk-hint'); }
  }

  // --- Facts: Show reveals a card's back; Show all reveals every card ---
  function flipFact(card, open, quiet) {
    if (!card) { return; }
    var back = card.querySelector('.mk-fact-back');
    var button = card.querySelector('[data-mk="flip"]');
    if (open === undefined) { open = back.style.display === 'none'; }
    back.style.display = open ? '' : 'none';
    if (button) { button.textContent = open ? 'Hide' : 'Show'; }
    if (open && !quiet) { keepInView(card); }
  }

  function flipAllFacts(button) {
    var open = button.getAttribute('data-open') !== '1';
    button.setAttribute('data-open', open ? '1' : '0');
    button.textContent = open ? 'Hide all' : 'Show all';
    var cards = document.querySelectorAll('.mk-fact');
    for (var i = 0; i < cards.length; i++) { flipFact(cards[i], open, true); }
  }

  // --- Lessons search: hide lessons (and empty areas) as you type ---
  function filterLessons(query) {
    var words = query.toLowerCase().split(/\s+/).filter(function (word) { return word; });
    var areas = document.querySelectorAll('.mk-area');
    for (var i = 0; i < areas.length; i++) {
      var lessons = areas[i].querySelectorAll('.mk-lesson');
      var shown = 0;
      for (var j = 0; j < lessons.length; j++) {
        var text = lessons[j].getAttribute('data-search') || '';
        var match = words.every(function (word) { return text.indexOf(word) >= 0; });
        lessons[j].style.display = match ? '' : 'none';
        if (match) { shown += 1; }
      }
      areas[i].style.display = shown ? '' : 'none';
    }
  }

  document.addEventListener('input', function (event) {
    var box = event.target;
    if (box && box.classList && box.classList.contains('mk-search')) {
      filterLessons(box.value);
    }
  });

  function buttonFor(event) {
    var target = event.target;
    if (target && target.nodeType !== 1) { target = target.parentNode; }
    return target && target.closest ? target.closest('[data-mk]') : null;
  }

  var touchStart = null;
  var lastTouchPress = 0;
  document.addEventListener('touchstart', function (event) {
    var touch = event.touches[0];
    touchStart = touch ? {x: touch.clientX, y: touch.clientY} : null;
  }, true);
  document.addEventListener('touchend', function (event) {
    var button = buttonFor(event);
    var touch = event.changedTouches[0];
    if (!button || !touchStart || !touch) { return; }
    if (Math.abs(touch.clientX - touchStart.x) > 10 ||
        Math.abs(touch.clientY - touchStart.y) > 10) { return; }
    event.preventDefault();
    lastTouchPress = Date.now();
    press(button);
  }, true);
  document.addEventListener('click', function (event) {
    var button = buttonFor(event);
    if (!button || Date.now() - lastTouchPress < 700) { return; }
    press(button);
  }, true);

  new MutationObserver(typeset).observe(document.documentElement,
                                        {childList: true, subtree: true});
  document.addEventListener('DOMContentLoaded', typeset);
})();
"""
