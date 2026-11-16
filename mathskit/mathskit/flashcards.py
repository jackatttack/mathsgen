"""Flashcards: one card at a time, with Leitner boxes for spaced practice.

    from mathskit import flashcards

    deck = flashcards.CardDeck()
    deck.card                       # {'id', 'q', 'a', 'tags', and maybe 'svg'}
    deck.got_it()                   # up a box, then the next card
    deck.again()                    # back to box 1, then the next card
    deck.toggle_tag('algebra')      # tags add up; tiers narrow them
    deck.toggle_tier('higher')
    deck.next()                     # draws from the new pool

The deck is library/flashcards/cards.json (built 2026-04-16), read as it
is: q and a are text with $...$ and $$...$$ maths, tags, and an optional
svg drawn for a dark background. Progress lives beside it in
progress.json and is never written into cards.json.

The next card is drawn at random, weighted towards low boxes
(BOX_WEIGHTS), and is never the card just shown when there is a choice.
Pure Python.
"""
import json
import os
import random

# --- Settings (editable) ------------------------------------------------------
LIBRARY = os.path.join(os.path.expanduser('~'), 'Documents', 'library', 'flashcards')
DECK_PATH = os.path.join(LIBRARY, 'cards.json')
PROGRESS_PATH = os.path.join(LIBRARY, 'progress.json')
TIERS = ('foundation', 'higher')       # tags shown as their own row
HIDDEN_TAGS = ('gcse',)                # on (nearly) every card: not worth a chip
TOP_BOX = 5
BOX_WEIGHTS = {1: 8, 2: 4, 3: 2, 4: 1, 5: 0.5}   # how often each box comes up
NO_MATCH = 'No cards match those tags: the card stays as it was.'


class CardDeck:
    def __init__(self, deck_path=DECK_PATH, progress_path=PROGRESS_PATH, seed=None):
        with open(deck_path, encoding='utf-8') as handle:
            self.cards = [card for card in json.load(handle) if card.get('q')]
        self.progress_path = progress_path
        self.boxes = load_boxes(progress_path)
        self.rng = random.Random(seed)
        self.tags = tag_counts(self.cards)            # [(tag, count)], most used first
        self.tiers = [tier for tier in TIERS if any(tier in card.get('tags', ()) for card in self.cards)]
        self.selected_tags = set()
        self.selected_tiers = set()
        self.card = None
        self.notice = ''
        self.pool_changed = False
        self.next()

    def box(self, card=None):
        return self.boxes.get((card or self.card)['id'], 1)

    # --- The pool ---

    def pool(self):
        out = []
        for card in self.cards:
            tags = set(card.get('tags', ()))
            if self.selected_tags and not tags & self.selected_tags:
                continue
            if self.selected_tiers and not tags & self.selected_tiers:
                continue
            out.append(card)
        return out

    def pool_name(self):
        name = ' + '.join(sorted(self.selected_tags)) if self.selected_tags else 'Every card'
        if self.selected_tiers:
            name += ' \u00b7 ' + ', '.join(sorted(self.selected_tiers))
        return name

    def toggle_tag(self, tag):
        self.selected_tags ^= {tag}
        self.pool_changed = True

    def toggle_tier(self, tier):
        self.selected_tiers ^= {tier}
        self.pool_changed = True

    def clear_tags(self):
        self.selected_tags.clear()
        self.pool_changed = True

    def clear_tiers(self):
        self.selected_tiers.clear()
        self.pool_changed = True

    # --- Moving on ---

    def next(self):
        """A card from the pool, weighted towards low boxes."""
        self.pool_changed = False
        pool = self.pool()
        if not pool:
            self.notice = NO_MATCH
            if self.card is not None:
                return
            pool = self.cards
        self.notice = ''
        choices = [card for card in pool if self.card is None or card['id'] != self.card['id']] or pool
        weights = [BOX_WEIGHTS.get(self.box(card), 1) for card in choices]
        self.card = self.rng.choices(choices, weights)[0]

    def got_it(self):
        self.boxes[self.card['id']] = min(TOP_BOX, self.box() + 1)
        self.save()
        self.next()

    def again(self):
        self.boxes[self.card['id']] = 1
        self.save()
        self.next()

    def save(self):
        """Write progress.json whole, through a temporary file."""
        temporary = self.progress_path + '.tmp'
        with open(temporary, 'w', encoding='utf-8') as handle:
            json.dump({'boxes': self.boxes}, handle, indent=1, sort_keys=True)
        os.replace(temporary, self.progress_path)


def load_boxes(path):
    try:
        with open(path, encoding='utf-8') as handle:
            return {key: int(value) for key, value in json.load(handle).get('boxes', {}).items()}
    except (OSError, ValueError):
        return {}


def tag_counts(cards):
    counts = {}
    for card in cards:
        for tag in card.get('tags', ()):
            if tag not in TIERS and tag not in HIDDEN_TAGS:
                counts[tag] = counts.get(tag, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))
