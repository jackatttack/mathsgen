"""Questions from mathsgen, one card at a time.

    from mathskit import questions

    deck = questions.Deck()                          # every GCSE skill, every grade
    deck.toggle(('group', 'algebra/Linear equations'))
    deck.toggle(('topic', 'geometry'))               # selections add up
    deck.toggle_band('Grades 1-3')                   # and grade bands narrow them
    deck.another()                                   # same skill and level, new numbers
    deck.harder(); deck.easier()                     # stays inside the bands
    deck.random()                                    # another skill from the pool
    deck.question                                    # a mathsgen core.Question

The pool is every (skill, level) pair whose skill is in any selected
topic, group or skill (none selected: all of them) and whose draft grade
falls in any selected band (none: all grades). Grades and bands come from
mathsgen's curriculum module (paper_blueprints/edexcel_1ma1.json).

mathsgen comes from the fork beside this package (projects/mathskit/mathsgen,
copied from iCloud on 2026-11-15); the iCloud working copy is never
touched. Its registry and topic_browser groups are used as they are, so
the menu matches mathsgen's own.
"""
import os
import random
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Where the MathsGen engine is: the fork beside mathskit while developing,
# or the MathsGen install mathskit ships inside (mathsgen/core).
MATHSGEN_CANDIDATES = (os.path.join(PROJECT_ROOT, 'mathsgen'),
                       os.path.join(os.path.dirname(PROJECT_ROOT), 'core'))


def find_mathsgen():
    for root in MATHSGEN_CANDIDATES:
        if os.path.isfile(os.path.join(root, 'mathsgen', 'catalogue.py')):
            return root
    return MATHSGEN_CANDIDATES[0]


MATHSGEN_ROOT = find_mathsgen()
RETRIES = 5          # fresh seeds to try if a generator refuses one
NO_MATCH = 'Nothing in that choice suits those grades: the question stays as it was.'

_loaded = {}


def mathsgen():
    """(registry, topic_browser, grades, bands), loaded once, always from the fork.
    grades maps (generator id, level) to its draft grade."""
    if not _loaded:
        if MATHSGEN_ROOT not in sys.path:
            sys.path.insert(0, MATHSGEN_ROOT)
        package = sys.modules.get('mathsgen')
        if package is not None and not os.path.abspath(package.__file__).startswith(MATHSGEN_ROOT):
            for name in list(sys.modules):          # another copy (iCloud) was loaded first
                if name == 'mathsgen' or name.startswith('mathsgen.'):
                    del sys.modules[name]
        from mathsgen import catalogue, topic_browser
        registry = catalogue.build_registry()
        try:
            from mathsgen import curriculum
            grades = {(tag.generator_id, tag.level): tag.grade
                      for tag in curriculum.load_level_tags(registry)}
            bands = dict(curriculum.GRADE_BANDS)
        except Exception:
            grades, bands = {}, {}
        _loaded.update(registry=registry, browser=topic_browser, grades=grades, bands=bands)
    return _loaded['registry'], _loaded['browser'], _loaded['grades'], _loaded['bands']


class Deck:
    """What to draw from (selections, bands) and the question showing."""

    def __init__(self, seed=None):
        self.registry, self.browser, self.grades, self.bands_available = mathsgen()
        self.rng = random.Random(seed)
        self.infos = {info.id: info for info in self.registry.list()}
        self.groups = self.browser.groups_for(list(self.infos.values()))
        self.selections = set()      # ('topic', t), ('group', key), ('generator', id)
        self.bands = set()           # labels from bands_available
        self.generator_id = None
        self.level = 1
        self.seed = None
        self.question = None
        self.error = None
        self.notice = ''
        self.pool_changed = False    # toggled since the last draw: Another draws from the pool
        self.random()

    # --- What is showing ---

    @property
    def info(self):
        return self.infos[self.generator_id]

    def levels(self, generator_id=None):
        return sorted(self.infos[generator_id or self.generator_id].difficulty_descriptions)

    def level_text(self):
        return self.info.difficulty_descriptions.get(self.level, '')

    def grade(self, generator_id=None, level=None):
        return self.grades.get((generator_id or self.generator_id, level or self.level))

    def group_of(self, info):
        name = self.browser.group_name(info)
        for group in self.groups:
            if group['topic'] == info.topic and group['title'] == name:
                return group
        return None

    def find_group(self, key):
        return next((group for group in self.groups if group['key'] == key), None)

    # --- The pool ---

    def selected_ids(self):
        if not self.selections:
            return sorted(self.infos)
        ids = set()
        for kind, value in self.selections:
            if kind == 'topic':
                ids.update(key for key, info in self.infos.items() if info.topic == value)
            elif kind == 'group' and self.find_group(value):
                ids.update(info.id for info in self.find_group(value)['infos'])
            elif kind == 'generator' and value in self.infos:
                ids.add(value)
        return sorted(ids)

    def allowed_levels(self, generator_id):
        levels = self.levels(generator_id)
        if not self.bands:
            return levels
        ranges = [self.bands_available[label] for label in self.bands]
        return [level for level in levels
                if any(low <= (self.grade(generator_id, level) or -1) <= high
                       for low, high in ranges)]

    def pool(self):
        """{generator id: [levels]} for everything that may be drawn."""
        pool = {}
        for generator_id in self.selected_ids():
            levels = self.allowed_levels(generator_id)
            if levels:
                pool[generator_id] = levels
        return pool

    def pool_name(self):
        if not self.selections:
            names = ['Every topic']
        else:
            names = []
            for kind, value in sorted(self.selections):
                if kind == 'topic':
                    names.append(self.browser.topic_style(value)[0])
                elif kind == 'group' and self.find_group(value):
                    names.append(self.find_group(value)['title'])
                elif kind == 'generator' and value in self.infos:
                    names.append(self.infos[value].title)
        shown = ' + '.join(names[:3]) + (' + %d more' % (len(names) - 3) if len(names) > 3 else '')
        if self.bands:
            shown += ' \u00b7 ' + ', '.join(sorted(self.bands))
        return shown

    # Changing the pool never changes the question showing: toggle freely,
    # then Random (or Another, Easier, Harder) draws from the new pool.

    def toggle(self, key):
        if key in self.selections:
            self.selections.discard(key)
        else:
            self.selections.add(key)
        self.pool_changed = True

    def toggle_band(self, label):
        if label in self.bands:
            self.bands.discard(label)
        elif label in self.bands_available:
            self.bands.add(label)
        self.pool_changed = True

    def clear(self):
        self.selections.clear()
        self.pool_changed = True

    def clear_bands(self):
        self.bands.clear()
        self.pool_changed = True

    def refit(self):
        """Keep the question if it still fits the pool; otherwise draw anew."""
        pool = self.pool()
        if not pool:
            self.notice = NO_MATCH
            return
        self.notice = ''
        if self.level not in pool.get(self.generator_id, ()):
            self.random()

    # --- Moving on ---

    def random(self):
        """Another skill from the pool (a different one when there is a choice)."""
        self.pool_changed = False
        pool = self.pool()
        if not pool:
            self.notice = NO_MATCH
            if self.question is not None:
                return
            pool = {key: self.levels(key) for key in self.infos}
        self.notice = ''
        choices = sorted(key for key in pool if key != self.generator_id) or sorted(pool)
        self.generator_id = self.rng.choice(choices)
        levels = pool[self.generator_id]
        if self.bands or self.level not in levels:
            self.level = self.rng.choice(levels)
        self.draw()

    def another(self):
        """New numbers for the same skill and level. If the pool has changed
        since the last draw, or no longer holds this skill and level, it
        draws from the pool instead: toggle the menu, then Another."""
        if self.pool_changed or self.level not in self.pool().get(self.generator_id, ()):
            self.random()
        else:
            self.draw()

    def draw(self):
        """Make the question for the current skill and level, with a fresh seed."""
        generator = self.registry.get(self.generator_id)
        for _ in range(RETRIES):
            self.seed = self.rng.randrange(1, 10 ** 9)
            try:
                self.question = generator.generate(self.seed, self.level)
                self.error = None
                return
            except Exception as error:
                self.question = None
                self.error = '%s: %s' % (type(error).__name__, error)

    def steps(self):
        return self.allowed_levels(self.generator_id) or self.levels()

    def harder(self):
        higher = [level for level in self.steps() if level > self.level]
        if higher:
            self.level = higher[0]
            self.draw()

    def easier(self):
        lower = [level for level in self.steps() if level < self.level]
        if lower:
            self.level = lower[-1]
            self.draw()
