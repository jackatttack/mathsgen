"""How a flashcard looks and behaves: HTML, CSS and the page script.

html(deck, go) is what blocks.flashcard() returns: the card (tags and
box, the question), tap the card to show the answer under it with the
card's SVG on a dark panel (the deck's drawings use a dark palette), Got
it and Again (only once flipped, so recall comes first), Skip, and the
pool line with a menu of tiers and tags.

Flipping happens in the page (data-fc). The menu reuses the question
card's chips and their page script (question_page: data-qc-chip, qcPool),
so both menus look and behave the same. Go items for the tool's on_pick:
'next', 'got', 'again', 'all_tags', 'all_tiers', ('tag', t), ('tier', t).

q and a are the deck's own text: line breaks kept, $...$ and $$...$$
typeset by KaTeX (they sit in .mk-text). Pure Python.
"""
from .blocks import escape
from .flashcards import HIDDEN_TAGS, TOP_BOX
from .question_page import CLOSE_LABEL, MENU_LABEL, chip

FLIP_HINT = 'Tap the card to see the answer'
ASK_LABEL = 'New card from this pool \u25b6'


def text_html(words):
    return escape(words).replace('\n', '<br>')


def html(deck, go):
    card = deck.card
    tags = ' \u00b7 '.join(tag for tag in card.get('tags', ()) if tag not in HIDDEN_TAGS)
    svg = '<div class="fc-svg">%s</div>' % card['svg'] if card.get('svg') else ''
    out = ['<div class="qc-wrap fc-wrap">',
           '<div class="fc-card" data-fc="flip">',
           '<div class="fc-head"><span>%s</span><span class="qc-level">Box %d of %d</span></div>'
           % (escape(tags), deck.box(), TOP_BOX),
           '<div class="fc-q mk-text">%s</div>' % text_html(card['q']),
           '<div class="fc-a"><div class="qc-alabel"><span>Answer</span></div>'
           '<div class="mk-text">%s</div>%s</div>' % (text_html(card.get('a', '')), svg),
           '<div class="fc-hint">%s</div>' % escape(FLIP_HINT),
           '</div>']
    out.append('<div class="mk-controls"><span class="mk-btn fc-grade" %s>Again</span>'
               '<span class="mk-btn mk-go fc-grade" %s>Got it</span>'
               '<span class="mk-btn" %s>Skip</span></div>' % (go('again'), go('got'), go('next')))
    if deck.notice:
        out.append('<div class="qc-note">%s</div>' % escape(deck.notice))
    out.append('<div class="qc-pool">Pool: <b class="qc-pool-name">%s</b> (<span '
               'class="qc-pool-count">%d</span> cards) \u00b7 <span class="qc-link" '
               'data-qc="menu" data-other="%s">%s</span></div>'
               % (escape(deck.pool_name()), len(deck.pool()), escape(CLOSE_LABEL), escape(MENU_LABEL)))
    out.append(menu_html(deck, go))
    out.append('</div>')
    return ''.join(out)


def menu_html(deck, go):
    out = ['<div class="qc-menu">']
    if deck.tiers:
        out.append('<div class="qc-topic">Tiers</div><div class="qc-chips">')
        out.append(chip(go, 'all_tiers', 'All tiers', not deck.selected_tiers, role='all_grades'))
        for tier in deck.tiers:
            out.append(chip(go, ('tier', tier), tier.title(), tier in deck.selected_tiers,
                            role='band'))
        out.append('</div>')
    out.append('<div class="qc-topic">Tags</div><div class="qc-chips">')
    out.append(chip(go, 'all_tags', 'Every card (%d)' % len(deck.cards), not deck.selected_tags,
                    role='all'))
    for tag, count in deck.tags:
        out.append(chip(go, ('tag', tag), '%s (%d)' % (tag, count), tag in deck.selected_tags))
    out.append('</div>')
    out.append('<div class="mk-controls"><span class="mk-btn mk-go" %s>%s</span></div>'
               % (go('next'), escape(ASK_LABEL)))
    out.append('</div>')
    return ''.join(out)


CSS = """
.fc-card { background: var(--wash); border-radius: 16px; padding: 14px 16px 12px 20px;
    min-height: 170px; cursor: pointer; box-shadow: inset 4px 0 0 var(--accent);
    -webkit-user-select: none; user-select: none; }
.fc-head { display: flex; justify-content: space-between; gap: 10px;
    font: 12px/1.3 -apple-system, sans-serif; color: var(--muted); }
.fc-q { font-size: 19px; line-height: 1.45; margin: 12px 0 6px; }
.fc-a { display: none; margin-top: 12px; padding-top: 10px; border-top: 1px dashed var(--line);
    font-size: 16px; line-height: 1.5; }
.fc-wrap.fc-flipped .fc-a { display: block; animation: mk-in 0.3s ease-out; }
.fc-hint { font: 12px -apple-system, sans-serif; color: var(--muted); text-align: center; margin-top: 10px; }
.fc-wrap.fc-flipped .fc-hint { display: none; }
.fc-svg { background: #1C1E2B; border-radius: 10px; padding: 10px; margin-top: 10px; }
.fc-svg svg { display: block; width: 100%; max-width: 320px; height: auto; max-height: 260px; margin: 0 auto; }
.fc-grade { display: none; }
.fc-wrap.fc-flipped .fc-grade { display: inline-block; }
"""

# Tap the card to flip it: [data-fc] taps are taken in touchend with
# preventDefault (the card carries no go item); click is the fallback.
SCRIPT = r"""
(function () {
  function flip(card) {
    var wrap = card.closest('.fc-wrap');
    if (!wrap) { return; }
    if (wrap.classList.contains('fc-flipped')) { wrap.classList.remove('fc-flipped'); }
    else { wrap.classList.add('fc-flipped'); }
  }

  function cardFor(event) {
    var target = event.target;
    if (target && target.nodeType !== 1) { target = target.parentNode; }
    return target && target.closest ? target.closest('[data-fc]') : null;
  }

  var start = null, lastFlip = 0;
  document.addEventListener('touchstart', function (event) {
    var touch = event.touches[0];
    start = touch ? {x: touch.clientX, y: touch.clientY} : null;
  }, true);
  document.addEventListener('touchend', function (event) {
    var card = cardFor(event);
    var touch = event.changedTouches[0];
    if (!card || !start || !touch) { return; }
    if (Math.abs(touch.clientX - start.x) > 10 || Math.abs(touch.clientY - start.y) > 10) { return; }
    event.preventDefault();
    lastFlip = Date.now();
    flip(card);
  }, true);
  document.addEventListener('click', function (event) {
    var card = cardFor(event);
    if (card && Date.now() - lastFlip > 700) { flip(card); }
  }, true);
})();
"""
