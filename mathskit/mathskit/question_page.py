"""How a question card looks and behaves: HTML, CSS and the page script.

html(deck, go, menu_open) is what blocks.question() returns: the card
(topic stripe in mathsgen's topic colour, topic and group, level and
grade, the question and its diagrams, the answer hidden until Show
answer, the level's description), the buttons, and the pool line with its
menu: grade bands, then every topic and group from mathsgen's own menu.
Every chip toggles; the pool is everything that is on.

Show answer and opening the menu happen in the page (data-qc). Buttons
and chips carry go items for the tool's on_pick: 'another', 'easier',
'harder', 'random', 'all', 'all_grades', ('toggle', key), ('band', label).
menu_open keeps the menu open after a chip, so several can be toggled.

mathsgen Content becomes KaTeX like this (mathsgen never infers maths
from prose, and neither does this):
    blocks             paragraphs (runs with tex go inline) and equations
    math_tex           display_text as prose if there is any, then the
                       equation (text is only the plain fallback)
    text               as written, line breaks kept
Diagrams are inline SVG on a paper panel (figures.py). Pure Python.
"""
from .blocks import escape

SHOW_LABEL = 'Show answer'
HIDE_LABEL = 'Hide answer'
MENU_LABEL = 'Change \u25be'
CLOSE_LABEL = 'Close \u25b4'
FIGURE_FAILED = 'This question has a diagram that could not be drawn here yet.'
ASK_LABEL = 'New question from this pool \u25b6'


# --- mathsgen Content to HTML -------------------------------------------------

def text_html(words):
    return escape(words).replace('\n', '<br>')


def equation_html(tex):
    return '<div class="mk-eq" data-tex="%s">%s</div>' % (escape(tex), escape(tex))


def run_html(run):
    if 'tex' in run:
        return '<span class="mk-inline" data-tex="%s">%s</span>' % (escape(run['tex']),
                                                                    escape(run['text']))
    return text_html(run['text'])


def content_html(content):
    if content.blocks:
        out = []
        for block in content.blocks:
            if block['kind'] == 'equation':
                out.append(equation_html(block['tex']))
            else:
                runs = block.get('runs') or [{'text': block['text']}]
                out.append('<p>%s</p>' % ''.join(run_html(run) for run in runs))
        return ''.join(out)
    if content.math_tex:
        prose = '<p>%s</p>' % text_html(content.display_text) if content.display_text else ''
        return prose + equation_html(content.math_tex)
    return '<p>%s</p>' % text_html(content.text)


def figures_html(assets):
    from . import figures
    out = []
    for asset in assets:
        try:
            out.append('<div class="qc-figure">%s</div>' % figures.svg_for(asset))
        except Exception:
            out.append('<div class="qc-note">%s</div>' % escape(FIGURE_FAILED))
    return ''.join(out)


# --- The card -----------------------------------------------------------------

def html(deck, go, menu_open=False, extra_buttons=(), below=''):
    info = deck.info
    topic_title, colour, _wash = deck.browser.topic_style(info.topic)
    question = deck.question
    grade = deck.grade()
    level = 'Level %d' % deck.level + (' \u00b7 Grade %d' % grade if grade else '')
    out = ['<div class="qc-wrap%s">' % (' qc-menu-open' if menu_open else ''),
           '<div class="qc-card" style="--qc:%s">' % escape(colour)]
    out.append('<div class="qc-head"><span>%s \u00b7 %s</span><span class="qc-level">%s</span></div>'
               % (escape(topic_title), escape(deck.browser.group_name(info)), escape(level)))
    out.append('<div class="qc-title">%s</div>' % escape(info.title))
    if question is None:
        out.append('<div class="qc-note">Could not make a question: %s</div>' % escape(deck.error))
    else:
        out.append('<div class="qc-prompt">%s</div>' % content_html(question.prompt))
        out.append(figures_html(question.visual_assets('questions')))
        if question.choices:
            out.append('<div class="qc-choices">%s</div>' % ''.join(
                '<div class="qc-choice"><b>%s</b>%s</div>' % (escape(choice.id),
                                                              content_html(choice.content))
                for choice in question.choices))
        marks = '%d mark%s' % (question.marks, '' if question.marks == 1 else 's')
        out.append('<div class="qc-answer"><div class="qc-alabel"><span>Answer</span><span>%s'
                   '</span></div>%s%s</div>'
                   % (escape(marks), content_html(question.answer_display),
                      figures_html(question.visual_assets('answers'))))
    out.append('<div class="qc-leveltext">%s</div>' % escape(deck.level_text()))
    out.append('</div>')

    steps = deck.steps()
    buttons = ['<span class="mk-btn" data-qc="reveal" data-other="%s">%s</span>'
               % (escape(HIDE_LABEL), escape(SHOW_LABEL)),
               '<span class="mk-btn mk-go" %s>Another</span>' % go('another')]
    if any(step < deck.level for step in steps):
        buttons.append('<span class="mk-btn" %s>Easier</span>' % go('easier'))
    if any(step > deck.level for step in steps):
        buttons.append('<span class="mk-btn" %s>Harder</span>' % go('harder'))
    if len(deck.pool()) > 1:
        buttons.append('<span class="mk-btn" %s>Random</span>' % go('random'))
    for label, item in extra_buttons:
        buttons.append('<span class="mk-btn" %s>%s</span>' % (go(item), escape(label)))
    out.append('<div class="mk-controls">%s</div>' % ''.join(buttons))
    if below:
        out.append('<div class="qc-below">%s</div>' % below)

    if deck.notice:
        out.append('<div class="qc-note">%s</div>' % escape(deck.notice))
    labels = (CLOSE_LABEL, MENU_LABEL) if menu_open else (MENU_LABEL, CLOSE_LABEL)
    out.append('<div class="qc-pool">Pool: <b class="qc-pool-name">%s</b> (<span '
               'class="qc-pool-count">%d</span> skills) \u00b7 <span class="qc-link" '
               'data-qc="menu" data-other="%s">%s</span></div>'
               % (escape(deck.pool_name()), len(deck.pool()), escape(labels[1]), escape(labels[0])))
    out.append(menu_html(deck, go))
    out.append('</div>')
    return ''.join(out)


def chip(go, item, label, on, colour=None, role='topic'):
    """A menu chip. role tells the page script how it flips: 'topic' and
    'band' chips toggle; 'all' and 'all_grades' turn their row's others off."""
    style = ' style="--qc:%s"' % escape(colour) if colour else ''
    return '<span class="qc-chip%s"%s data-qc-chip="%s" %s>%s</span>' % (
        ' on' if on else '', style, role, go(item), escape(label))


def menu_html(deck, go):
    out = ['<div class="qc-menu">']
    if deck.bands_available:
        out.append('<div class="qc-topic">Grades</div><div class="qc-chips">')
        out.append(chip(go, 'all_grades', 'All grades', not deck.bands, role='all_grades'))
        for label in deck.bands_available:
            out.append(chip(go, ('band', label), label.replace('Grades ', ''), label in deck.bands,
                            role='band'))
        out.append('</div>')
    out.append('<div class="qc-topic">Topics</div><div class="qc-chips">%s</div>'
               % chip(go, 'all', 'Every topic (%d)' % len(deck.infos), not deck.selections,
                      role='all'))
    current = deck.group_of(deck.info)
    if current and len(current['infos']) > 1:
        out.append('<div class="qc-topic">Skills in %s</div><div class="qc-chips">'
                   % escape(current['title']))
        for info in current['infos']:
            key = ('generator', info.id)
            out.append(chip(go, ('toggle', key), info.title, key in deck.selections))
        out.append('</div>')
    topic = None
    for group in deck.groups:
        if group['topic'] != topic:
            if topic is not None:
                out.append('</div>')
            topic = group['topic']
            title, colour, _wash = deck.browser.topic_style(topic)
            out.append('<div class="qc-topic" style="--qc:%s">%s</div><div class="qc-chips">'
                       % (escape(colour), escape(title)))
            key = ('topic', topic)
            out.append(chip(go, ('toggle', key), 'All', key in deck.selections, colour))
        key = ('group', group['key'])
        out.append(chip(go, ('toggle', key), '%s (%d)' % (group['title'], len(group['infos'])),
                        key in deck.selections, colour))
    if topic is not None:
        out.append('</div>')
    out.append('<div class="mk-controls"><span class="mk-btn mk-go" %s>%s</span></div>'
               % (go('random'), escape(ASK_LABEL)))
    out.append('</div>')
    return ''.join(out)


CSS = """
.qc-wrap { margin: 0.2em 0 1em; }
.qc-card { background: var(--wash); border-radius: 14px; padding: 12px 14px 12px 18px;
    box-shadow: inset 4px 0 0 var(--qc, var(--accent)); }
.qc-head { display: flex; justify-content: space-between; gap: 10px;
    font: 12px/1.3 -apple-system, sans-serif; color: var(--muted); }
.qc-level { font-weight: 600; color: var(--accent); white-space: nowrap; }
.qc-title { font: 600 14px/1.3 -apple-system, sans-serif; margin: 3px 0 10px; opacity: 0.85; }
.qc-prompt { font-size: 17px; line-height: 1.5; }
.qc-prompt p, .qc-answer p, .qc-choice p { margin: 0 0 0.6em; }
.qc-figure { background: #FFFDF7; border-radius: 10px; padding: 8px; margin: 8px 0; }
.qc-figure svg { display: block; width: 100%; max-width: 460px; height: auto; margin: 0 auto; }
.qc-note { font: 13px/1.4 -apple-system, sans-serif; color: var(--muted); margin: 6px 0; }
.qc-choices { display: grid; gap: 4px; margin: 6px 0; }
.qc-choice { display: flex; gap: 10px; align-items: baseline; }
.qc-answer { display: none; margin-top: 10px; padding-top: 8px; border-top: 1px dashed var(--line); }
.qc-wrap.qc-shown .qc-answer { display: block; animation: mk-in 0.3s ease-out; }
.qc-alabel { display: flex; justify-content: space-between; font: 600 11px -apple-system, sans-serif;
    color: var(--accent); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.qc-leveltext { font: 12px/1.4 -apple-system, sans-serif; color: var(--muted); margin-top: 10px; }
.qc-below { margin-top: 6px; animation: mk-in 0.3s ease-out; }
.qc-pool { font: 13px -apple-system, sans-serif; color: var(--muted); margin-top: 8px; }
.qc-pool b { color: var(--text); font-weight: 600; }
.qc-link { color: var(--accent); cursor: pointer; -webkit-user-select: none; user-select: none; }
.qc-menu { display: none; margin-top: 6px; }
.qc-wrap.qc-menu-open .qc-menu { display: block; }
.qc-topic { font: 600 13px -apple-system, sans-serif; color: var(--qc, var(--text)); margin: 12px 0 5px; }
.qc-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
.qc-chip { padding: 4px 11px; border-radius: 999px; border: 1.5px solid var(--qc, var(--line));
    font: 13px/1.4 -apple-system, sans-serif; cursor: pointer; }
.qc-chip.on { background: var(--qc, var(--accent)); color: #111111; font-weight: 600; }
"""

# Show answer and the menu toggle in the page: [data-qc] taps are taken in
# touchend with preventDefault (the shell's fast tap stands aside); click is
# the fallback. data-other holds the label for the other state.
SCRIPT = r"""
(function () {
  function toggle(button) {
    var wrap = button.closest('.qc-wrap');
    if (!wrap) { return; }
    var name = button.getAttribute('data-qc') === 'reveal' ? 'qc-shown' : 'qc-menu-open';
    if (wrap.classList.contains(name)) { wrap.classList.remove(name); }
    else { wrap.classList.add(name); }
    var other = button.getAttribute('data-other');
    button.setAttribute('data-other', button.textContent);
    button.textContent = other;
  }

  function buttonFor(event) {
    var target = event.target;
    if (target && target.nodeType !== 1) { target = target.parentNode; }
    return target && target.closest ? target.closest('[data-qc]') : null;
  }

  var start = null, lastPress = 0;
  document.addEventListener('touchstart', function (event) {
    var touch = event.touches[0];
    start = touch ? {x: touch.clientX, y: touch.clientY} : null;
  }, true);
  document.addEventListener('touchend', function (event) {
    var button = buttonFor(event);
    var touch = event.changedTouches[0];
    if (!button || !start || !touch) { return; }
    if (Math.abs(touch.clientX - start.x) > 10 || Math.abs(touch.clientY - start.y) > 10) { return; }
    event.preventDefault();
    lastPress = Date.now();
    toggle(button);
  }, true);
  document.addEventListener('click', function (event) {
    var button = buttonFor(event);
    if (button && Date.now() - lastPress > 700) { toggle(button); }
  }, true);

  // --- Menu chips flip here at once. No preventDefault: the shell still sends
  // the chip's go item, and Python records the pool without redrawing, so the
  // page never jumps. Python then calls qcPool to update the pool line. ---
  function setAll(menu, selector, on) {
    var chips = menu.querySelectorAll(selector);
    for (var i = 0; i < chips.length; i++) {
      if (on) { chips[i].classList.add('on'); } else { chips[i].classList.remove('on'); }
    }
  }

  function flipChip(chip) {
    var menu = chip.closest('.qc-menu');
    if (!menu) { return; }
    var role = chip.getAttribute('data-qc-chip');
    if (role === 'all') { setAll(menu, '[data-qc-chip="topic"]', false); chip.classList.add('on'); return; }
    if (role === 'all_grades') { setAll(menu, '[data-qc-chip="band"]', false); chip.classList.add('on'); return; }
    if (chip.classList.contains('on')) { chip.classList.remove('on'); } else { chip.classList.add('on'); }
    var clear = role === 'band' ? 'all_grades' : 'all';
    var anyOn = menu.querySelector('[data-qc-chip="' + role + '"].on');
    setAll(menu, '[data-qc-chip="' + clear + '"]', !anyOn);
  }

  function chipFor(event) {
    var target = event.target;
    if (target && target.nodeType !== 1) { target = target.parentNode; }
    return target && target.closest ? target.closest('[data-qc-chip]') : null;
  }

  var chipStart = null, lastChip = 0;
  document.addEventListener('touchstart', function (event) {
    var touch = event.touches[0];
    chipStart = touch ? {x: touch.clientX, y: touch.clientY} : null;
  }, true);
  document.addEventListener('touchend', function (event) {
    var chip = chipFor(event);
    var touch = event.changedTouches[0];
    if (!chip || !chipStart || !touch) { return; }
    if (Math.abs(touch.clientX - chipStart.x) > 10 || Math.abs(touch.clientY - chipStart.y) > 10) { return; }
    lastChip = Date.now();
    flipChip(chip);
  }, true);
  document.addEventListener('click', function (event) {
    var chip = chipFor(event);
    if (chip && Date.now() - lastChip > 700) { flipChip(chip); }
  }, true);

  window.qcPool = function (name, count) {
    var label = document.querySelector('.qc-pool-name');
    var number = document.querySelector('.qc-pool-count');
    if (label) { label.textContent = name; }
    if (number) { number.textContent = String(count); }
  };
})();
"""
