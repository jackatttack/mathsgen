"""Build workspace: a skill board and a worksheet sheet, one at a time.

This is the whole Build tab. A switch at the top shows either:
- Skills: topic headers, topic_browser subheadings and one row per skill
  (dark, compact, after the snippet keyboard). Headers fold; search or a
  grade chip unfolds what matches. Tap a row to put the skill on the sheet
  (green tick); tap again to take it off.
- Sheet: title, Generate, answers, style and the preview actions, then one
  card per block led by its full skill title. Tap a card to open its
  controls: drill, applied, count, difficulty, Up / Down / To top,
  Duplicate, Remove, Hide.

Stability rules (this replaced a slide-over version that could crash):
- no animations, timers, custom drag tracking or Objective-C tricks;
- a control changes only what it owns (+ updates one card and the total);
- the sheet's cards are rebuilt only when the sheet is shown after a change.
Recent actions are written to log_path so a crash names its last tap.

The host hears about changes through on_change(blocks, title), settings
through on_settings(answers, theme_index), Generate through on_generate()
and preview actions through on_action(name). Data decisions live in
build_model.py and topic_browser.py; this module draws and reacts.
"""
import time
from collections import Counter, deque
from pathlib import Path

import ui

from .build_model import (
    block_size, block_summary, default_block, drill_levels_by_skill,
    library_sections, maximum_count, supported_levels,
)
from .curriculum import GRADE_BANDS, load_level_tags
from .topic_browser import ORDER, groups_for, topic_style


# ------------------------------------------------------------ editable look

from .ui_design import (
    PAPER, SURFACE, GROUP, BORDER, INK, MUTED, GREEN, SELECTED, PRESSED,
    DANGER, HEADING_FONT,
)

BOARD = PAPER
TILE = SURFACE
GROUP_TILE = GROUP
TILE_PRESSED = PRESSED
SEARCH_FIELD = SURFACE
ACTIVE = GREEN
TEXT = INK
ADDED_TILE = SELECTED
ADDED_EDGE = GREEN
PAPER_EDGE = BORDER
CARD = SURFACE
INK_MUTED = MUTED
# Topic headers stay neutral: green is kept for skills that are on the sheet.
from .ui_design import HEADER as HEADER_TILE  # noqa: E402

TOPIC_COLOURS = dict.fromkeys(
    ("number", "algebra", "ratio", "geometry", "probability", "data",
     "problem_solving"), GREEN,
)

RADIUS = 7
GAP = 6
SWITCH_HEIGHT = 44     # the Skills | Sheet switch strip
ROW_TITLE_SIZE = 15
CARD_TITLE_SIZE = 16
CARD_TOP = 12          # space above a card's title
CARD_ROW = 44          # each row of controls on an open card
MAX_LOG_LINES = 50


# ------------------------------------------------------------ small helpers

def text_label(text, size=14, colour=INK, bold=False, lines=1):
    item = ui.Label()
    item.text = text
    item.font = ("<System-Bold>" if bold else "<System>", size)
    item.text_color = colour
    item.number_of_lines = lines
    item.touch_enabled = False   # taps fall through to the row or card
    return item


def flat_button(title, action, background, tint, size=14):
    item = ui.Button(title=title)
    item.action = action
    item.background_color = background
    item.tint_color = tint
    item.font = ("<System-Bold>", size)
    item.corner_radius = RADIUS
    return item


def text_height(text, width, size, bold=False):
    """Height that text needs when wrapped to width (so nothing is cut off)."""
    font = ("<System-Bold>" if bold else "<System>", size)
    try:
        return ui.measure_string(text, max_width=max(20, width), font=font)[1] + 2
    except Exception:
        per_line = max(1, int(width / (size * 0.55)))
        lines = max(1, -(-len(text) // per_line))
        return lines * size * 1.3


def inside(view, touch):
    x, y = touch.location
    return 0 <= x <= view.width and 0 <= y <= view.height


def row_detail(entry):
    """'N2, N8 · Y7–Y9 · G2–4 · Drill' from a library entry."""
    parts = entry["detail"].split(" · ")
    shown = [parts[0]]
    for part in parts[1:]:
        if part.startswith("Drill"):
            shown.append("Drill")
        else:
            shown.append(part.replace("Grades ", "G").replace("Grade ", "G"))
    return " · ".join(shown)


def chip_width(title):
    return len(title) * 8 + 26


class ActionLog:
    """The last MAX_LOG_LINES actions, rewritten to a small file after each,
    so that if Pythonista ever crashes the file shows what was tapped last."""

    def __init__(self, path):
        self.path = Path(path) if path else None
        self.lines = deque(maxlen=MAX_LOG_LINES)

    def add(self, text):
        if self.path is None:
            return
        now = time.time()
        stamp = time.strftime("%H:%M:%S", time.localtime(now))
        self.lines.append("{}.{:03d} {}".format(stamp, int(now % 1 * 1000), text))
        try:
            self.path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        except Exception:
            pass


# ------------------------------------------------------------ workspace

class Workspace(ui.View):
    """The Skills | Sheet switch over the board or the sheet."""

    def __init__(self, registry, blocks, title, on_change, answers=True,
                 theme_index=0, theme_names=("Ivory",),
                 on_settings=None, on_generate=None, on_action=None, log_path=None):
        super().__init__()
        self.background_color = BOARD
        self.registry = registry
        self.infos = {info.id: info for info in registry.list()}
        self.drill_levels = drill_levels_by_skill(registry)
        self.blocks = [dict(block) for block in blocks]
        self.on_change = on_change
        self.on_settings = on_settings
        self.on_generate = on_generate
        self.on_action = on_action
        self.log = ActionLog(log_path)
        self.load_error = ""
        try:
            sections = library_sections(registry, load_level_tags(registry), self.drill_levels)
        except Exception as error:
            sections = []
            self.load_error = "Skill details unavailable: " + str(error)
        self.entries = {entry["generator_id"]: entry
                        for _, entries in sections for entry in entries}
        self.groups = groups_for(list(self.infos.values()))
        present = {group["topic"] for group in self.groups}
        self.topics = [topic for topic in ORDER if topic in present] + sorted(present - set(ORDER))
        self.showing_sheet = bool(self.blocks)
        self.sheet_dirty = True
        self.switch = ui.SegmentedControl()
        self.switch.tint_color = ACTIVE
        self.switch.action = self.switch_view
        self.board = SkillBoard(self)
        self.sheet = SheetView(self, title, answers, theme_index, theme_names)
        for view in (self.switch, self.board, self.sheet):
            self.add_subview(view)
        self.update_switch()
        self.log.add("open Build with {} blocks".format(len(self.blocks)))

    def layout(self):
        # Narrower and shorter than the main mode tabs, so it reads as part of Build.
        switch_width = min(self.width - 24, 300)
        self.switch.frame = ((self.width - switch_width) / 2, 8, switch_width, 28)
        body = (0, SWITCH_HEIGHT, self.width, max(100, self.height - SWITCH_HEIGHT))
        self.board.frame = body
        self.sheet.frame = body
        self.show_sheet(self.showing_sheet, logged=False)

    # -------------------------------------------------- which view

    def switch_view(self, sender):
        self.show_sheet(sender.selected_index == 1)

    def show_sheet(self, showing, logged=True):
        self.showing_sheet = showing
        if showing and self.sheet_dirty:
            self.sheet.rebuild()
        self.board.hidden = showing
        self.sheet.hidden = not showing
        self.update_switch()
        if logged:
            self.log.add("show " + ("sheet" if showing else "skills"))

    def update_switch(self):
        """Relabel the switch only when its text or choice actually changes."""
        labels = ["Skills", "Sheet ({})".format(len(self.blocks))]
        if list(self.switch.segments) != labels:
            self.switch.segments = labels
        index = 1 if self.showing_sheet else 0
        if self.switch.selected_index != index:
            self.switch.selected_index = index

    # -------------------------------------------------- data

    def colour_for(self, generator_id):
        info = self.infos.get(generator_id)
        return TOPIC_COLOURS.get(info.topic if info else None, ACTIVE)

    def counts(self):
        """How many blocks each skill has on the sheet."""
        return Counter(block["generator_id"] for block in self.blocks)

    def toggle_skill(self, generator_id):
        """Put a skill on the sheet, or take every block of it off. True if added."""
        if generator_id in self.counts():
            self.blocks[:] = [b for b in self.blocks if b["generator_id"] != generator_id]
            added = False
        else:
            self.blocks.append(default_block(self.infos[generator_id]))
            added = True
        self.log.add(("add " if added else "remove ") + generator_id)
        self.structure_changed()
        return added

    def structure_changed(self):
        """Blocks were added, removed or moved: marks, switch label, host."""
        self.sheet_dirty = True
        if self.showing_sheet:
            self.sheet.rebuild()
        self.board.mark_tiles()
        self.update_switch()
        self.notify()

    def notify(self):
        self.on_change(list(self.blocks), self.sheet.title_field.text)

    def sync_results(self, state):
        """Show the host's generate state: busy, status, ready, answers, saved."""
        self.sheet.sync_results(state)


# ------------------------------------------------------------ the board

class SkillBoard(ui.View):
    """Topic headers, subheadings and skill rows on a dark board."""

    def __init__(self, workspace):
        super().__init__()
        self.workspace = workspace
        self.background_color = BOARD
        self.topic = None
        self.grades = None
        self.filters_open = False
        self.filters_button = flat_button(
            "▸ Filters · All subjects · Any grade",
            self.toggle_filters, PAPER, ACTIVE, 12)
        self.add_subview(self.filters_button)
        self.open_topics = set()
        self.open_groups = set()
        self.rows = []
        self.headers = []
        self.fold_button = flat_button("Expand all", self.toggle_fold, TILE, TEXT, 13)
        self.search = ui.TextField()
        self.search.background_color = SEARCH_FIELD
        self.search.text_color = TEXT
        self.search.bordered = False
        self.search.corner_radius = RADIUS
        self.search.font = ("<System>", 15)
        self.search.clear_button_mode = "while_editing"
        self.search.autocorrection_type = False
        self.search.spellchecking_type = False
        self.search.delegate = self
        # Our own placeholder, because the system one is unreadable on dark.
        self.placeholder = text_label("Search skills, topics or spec codes", 15, MUTED)
        self.topic_strip, self.topic_chips = self.chip_row(
            [("all", "All")] + [(topic, topic_style(topic)[0]) for topic in workspace.topics],
            self.pick_topic)
        self.grade_strip, self.grade_chips = self.chip_row(
            [("any", "Any grade")] + [(key, key.replace("Grades ", "G").replace("-", "–"))
                                      for key in GRADE_BANDS],
            self.pick_grades)
        self.status = text_label(
            workspace.load_error or "Tap a skill to add it. Tap again to remove it.",
            13, MUTED)
        self.grid = ui.ScrollView()
        self.grid.background_color = BOARD
        for view in (self.fold_button, self.search, self.placeholder,
                     self.topic_strip, self.grade_strip, self.status, self.grid):
            self.add_subview(view)

    def chip_row(self, choices, action):
        strip = ui.ScrollView()
        strip.shows_horizontal_scroll_indicator = False
        chips = []
        for key, title in choices:
            chip = flat_button(title, action, TILE, TEXT, 13)
            chip.name = key
            chips.append(chip)
            strip.add_subview(chip)
        return strip, chips

    def layout(self):
        left, width = 12, max(220, self.width - 24)
        self.search.frame = (left, 4, width - 104, 40)
        self.placeholder.frame = (left + 10, 4, width - 124, 40)
        self.fold_button.frame = (left + width - 98, 4, 98, 40)
        self.filters_button.frame = (left, 48, width, 32)
        for strip, chips, y in ((self.topic_strip, self.topic_chips, 86),
                                (self.grade_strip, self.grade_chips, 124)):
            strip.hidden = not self.filters_open
            x = left
            for chip in chips:
                chip.frame = (x, 0, chip_width(chip.title), 32)
                x += chip_width(chip.title) + GAP
            strip.frame = (0, y, self.width, 32)
            strip.content_size = (x + left, 32)
        bottom = 162 if self.filters_open else 84
        self.status.frame = (left, bottom, width, 20)
        self.grid.frame = (0, bottom + 24, self.width,
                           max(60, self.height - bottom - 24))
        self.update_filter_summary()
        self.fill_grid()

    def toggle_filters(self, sender):
        self.filters_open = not self.filters_open
        self.layout()

    def update_filter_summary(self):
        subject = topic_style(self.topic)[0] if self.topic else "All subjects"
        grade = "Grades {}–{}".format(*self.grades) if self.grades else "Any grade"
        self.filters_button.title = "{} Filters · {} · {}".format(
            "▾" if self.filters_open else "▸", subject, grade)

    # -------------------------------------------------- filters

    def pick_topic(self, sender):
        self.topic = None if sender.name == "all" else sender.name
        if self.topic:
            self.open_topics.add(self.topic)
        self.fill_grid()
        self.grid.content_offset = (0, 0)

    def pick_grades(self, sender):
        self.grades = None if sender.name == "any" else GRADE_BANDS[sender.name]
        self.fill_grid()

    def textfield_did_change(self, textfield):
        self.placeholder.hidden = bool(textfield.text)
        self.fill_grid()

    def filtering(self):
        """Search or a grade band unfolds everything that matches."""
        return bool((self.search.text or "").strip()) or self.grades is not None

    def visible(self, group):
        """The group's skills that pass the grade band and search."""
        words = (self.search.text or "").lower().split()
        shown = []
        for info in group["infos"]:
            entry = self.workspace.entries.get(info.id)
            if entry is None:
                continue
            if self.grades:
                low, high = self.grades
                if not any(low <= grade <= high for grade in entry["grades"]):
                    continue
            text = " ".join([entry["search"], group["title"].lower(),
                             topic_style(info.topic)[0].lower()])
            if all(word in text for word in words):
                shown.append(info)
        return shown

    def style_chips(self):
        self.update_filter_summary()
        for chip in self.topic_chips:
            chosen = (chip.name == "all" and self.topic is None) or chip.name == self.topic
            colour = ACTIVE if chip.name == "all" else TOPIC_COLOURS.get(chip.name, ACTIVE)
            chip.background_color = colour if chosen else TILE
            chip.tint_color = "white" if chosen else TEXT
        for chip in self.grade_chips:
            chosen = ((chip.name == "any" and self.grades is None)
                      or GRADE_BANDS.get(chip.name) == self.grades)
            chip.background_color = ACTIVE if chosen else TILE
            chip.tint_color = "white" if chosen else TEXT

    # -------------------------------------------------- the list

    def fill_grid(self):
        """Topic headers, then (when open) subheadings and skill rows."""
        self.style_chips()
        if not hasattr(self, "_row_cache"):
            self._row_cache = {}
            self._header_cache = {}
            self._empty = text_label("No skills match.", 14, MUTED)
            self.grid.add_subview(self._empty)
        for view in self.grid.subviews:
            view.hidden = True
        self.rows, self.headers = [], []
        left, width = 12, self.width - 24
        filtering = self.filtering()
        y = 4
        for topic in self.workspace.topics:
            if self.topic and topic != self.topic:
                continue
            groups = [(group, self.visible(group)) for group in self.workspace.groups
                      if group["topic"] == topic]
            groups = [(group, shown) for group, shown in groups if shown]
            if not groups:
                continue
            colour = TOPIC_COLOURS.get(topic, ACTIVE)
            ids = [info.id for _, shown in groups for info in shown]
            opened = filtering or topic in self.open_topics
            y = self.add_header("topic", topic, topic_style(topic)[0], colour, ids,
                                opened, left, y, width)
            if not opened:
                continue
            for group, shown in groups:
                if len(group["infos"]) == 1:
                    y = self.add_row(shown[0], colour, left + 12, y, width - 12)
                    continue
                group_open = filtering or group["key"] in self.open_groups
                y = self.add_header("group", group["key"], group["title"], colour,
                                    [info.id for info in shown], group_open,
                                    left + 12, y, width - 12)
                if group_open:
                    for info in shown:
                        y = self.add_row(info, colour, left + 24, y, width - 24)
            y += 8
        if not self.headers:
            self._empty.hidden = False
            self._empty.frame = (left, 10, width, 24)
        self.grid.content_size = (self.width, y + 40)
        self.fold_button.title = "Fold all" if (self.open_topics or self.open_groups) else "Expand all"
        self.mark_tiles()

    def add_header(self, kind, key, title, colour, ids, opened, x, y, width):
        cache_key = (kind, key)
        header = self._header_cache.get(cache_key)
        if header is None:
            header = HeaderRow(self, kind, key, title, colour, ids, opened)
            self._header_cache[cache_key] = header
            self.grid.add_subview(header)
        header.ids = ids
        header.title_text = ("▾ " if opened else "▸ ") + title
        header.title.text = header.title_text
        header.hidden = False
        height = header.needed_height(width)
        header.frame = (x, y, width, height)
        self.headers.append(header)
        return y + height + GAP

    def add_row(self, info, colour, x, y, width):
        row = self._row_cache.get(info.id)
        if row is None:
            row = SkillRow(self, self.workspace.entries[info.id], colour)
            self._row_cache[info.id] = row
            self.grid.add_subview(row)
        row.hidden = False
        height = row.needed_height(width)
        row.frame = (x, y, width, height)
        self.rows.append(row)
        return y + height + GAP

    def header_tapped(self, header):
        opened = self.open_topics if header.kind == "topic" else self.open_groups
        if header.key in opened:
            opened.remove(header.key)
        else:
            opened.add(header.key)
        self.fill_grid()

    def toggle_fold(self, sender):
        if self.open_topics or self.open_groups:
            self.open_topics, self.open_groups = set(), set()
        else:
            self.open_topics = set(self.workspace.topics)
            self.open_groups = {group["key"] for group in self.workspace.groups}
        self.fill_grid()

    def mark_tiles(self):
        """Green ticks on rows, on-sheet counts on headers."""
        counts = self.workspace.counts()
        for row in self.rows:
            row.set_added(counts.get(row.entry["generator_id"], 0))
        for header in self.headers:
            header.set_count(sum(1 for skill in header.ids if counts.get(skill)))

    def row_tapped(self, row):
        added = self.workspace.toggle_skill(row.entry["generator_id"])
        self.status.text = ("Added {}." if added else "Removed {}.").format(row.entry["title"])


class HeaderRow(ui.View):
    """A foldable topic header or subheading with its on-sheet count."""

    def __init__(self, board, kind, key, title, colour, ids, opened):
        super().__init__()
        self.board = board
        self.kind = kind
        self.key = key
        self.ids = ids
        topic = kind == "topic"
        self.size = 17 if topic else 15
        self.minimum = 46 if topic else 40
        self.background_color = HEADER_TILE if topic else GROUP_TILE
        self.border_color = BORDER
        self.border_width = 1 if topic else 0
        self.corner_radius = RADIUS
        self.bar = ui.View()
        self.bar.background_color = colour if topic else GROUP_TILE
        self.bar.touch_enabled = False
        self.title_text = ("▾ " if opened else "▸ ") + title
        self.title = text_label(self.title_text, self.size, TEXT, bold=True, lines=0)
        self.detail = text_label("", 13, MUTED)
        self.detail.alignment = ui.ALIGN_RIGHT
        for view in (self.bar, self.title, self.detail):
            self.add_subview(view)
        self.set_count(0)

    def needed_height(self, width):
        return max(self.minimum, text_height(self.title_text, width - 168, self.size, True) + 16)

    def layout(self):
        self.bar.hidden = True
        self.title.frame = (14, 0, self.width - 168, self.height)
        self.detail.frame = (self.width - 152, 0, 142, self.height)

    def set_count(self, on_sheet):
        total = len(self.ids)
        text = "{} skill{}".format(total, "" if total == 1 else "s")
        if on_sheet:
            text += " · {} on sheet".format(on_sheet)
        self.detail.text = text
        self.detail.text_color = ADDED_EDGE if on_sheet else MUTED

    def touch_ended(self, touch):
        if inside(self, touch):
            self.board.header_tapped(self)


class SkillRow(ui.View):
    """One skill: topic stripe, full title, codes/years/grades line, tick."""

    def __init__(self, board, entry, colour):
        super().__init__()
        self.board = board
        self.entry = entry
        self.added = 0
        self.corner_radius = RADIUS
        self.stripe = ui.View()
        self.stripe.background_color = colour
        self.stripe.touch_enabled = False
        self.title = text_label(entry["title"], ROW_TITLE_SIZE, TEXT, bold=True, lines=0)
        self.detail = text_label(row_detail(entry), 12, MUTED)
        self.mark = text_label("", 22, ADDED_EDGE, bold=True)
        self.mark.alignment = ui.ALIGN_CENTER
        for view in (self.stripe, self.title, self.detail, self.mark):
            self.add_subview(view)
        self.set_added(0)

    def title_width(self, width):
        return width - 60

    def needed_height(self, width):
        title = text_height(self.entry["title"], self.title_width(width), ROW_TITLE_SIZE, True)
        return 8 + title + 2 + 17 + 8

    def layout(self):
        title = text_height(self.entry["title"], self.title_width(self.width), ROW_TITLE_SIZE, True)
        self.stripe.hidden = True
        self.title.frame = (44, 8, self.title_width(self.width), title)
        self.mark.frame = (6, max(8, (self.height - 32) / 2), 32, 32)
        self.detail.frame = (44, self.height - 25, self.width - 54, 17)

    def resting_colour(self):
        return ADDED_TILE if self.added else TILE

    def set_added(self, count):
        self.added = count
        self.background_color = self.resting_colour()
        self.border_color = ADDED_EDGE if count else BORDER
        self.border_width = 1
        # A plus says "add"; a circle read like a pick-one radio button.
        self.mark.text = "✓" if count else "+"
        self.mark.text_color = ADDED_EDGE if count else MUTED

    def touch_began(self, touch):
        self.background_color = TILE_PRESSED

    def touch_ended(self, touch):
        self.background_color = self.resting_colour()
        if inside(self, touch):
            self.board.row_tapped(self)


# ------------------------------------------------------------ the sheet

class SheetView(ui.View):
    """The worksheet: header tools, then one card per block."""

    def __init__(self, workspace, title, answers, theme_index, theme_names):
        super().__init__()
        self.workspace = workspace
        self.background_color = PAPER
        self.settings_open = False
        self.settings_button = flat_button(
            "▸ Worksheet settings", self.toggle_settings, SURFACE, ACTIVE, 13)
        self.add_subview(self.settings_button)
        self.title_field = ui.TextField()
        self.title_field.text = title
        self.title_field.placeholder = "Worksheet title"
        self.title_field.font = ("<System-Bold>", 19)
        self.title_field.text_color = INK
        self.title_field.background_color = PAPER
        self.title_field.bordered = False
        self.title_field.delegate = self
        self.generate_button = flat_button("Generate", self.generate, ACTIVE, "white", 15)
        self.summary = text_label("", 13, INK_MUTED)
        self.answers_label = text_label("Answers", 14, INK, bold=True)
        self.answers_switch = ui.Switch()
        self.answers_switch.value = bool(answers)
        self.answers_switch.tint_color = ACTIVE
        self.answers_switch.action = self.change_settings
        self.style_control = ui.SegmentedControl()
        self.style_control.segments = list(theme_names)
        self.style_control.selected_index = theme_index
        self.style_control.tint_color = ACTIVE
        self.style_control.action = self.change_settings
        self.result_status = text_label("", 12, INK_MUTED)
        self.open_button = self.result_button("Open", "open_questions")
        self.answers_button = self.result_button("Answers", "open_answers")
        self.save_button = self.result_button("Save", "save")
        self.scroll = ui.ScrollView()
        self.scroll.background_color = PAPER
        self.empty = text_label(
            "No blocks yet. Switch to Skills and tap skills to add them.\n"
            "Tap a card to edit it or move it.", 14, INK_MUTED, lines=0)
        self.empty.alignment = ui.ALIGN_CENTER
        self.cards = []
        self.results_shown = False
        for view in (self.title_field, self.generate_button, self.summary,
                     self.answers_label, self.answers_switch, self.style_control,
                     self.result_status, self.open_button, self.answers_button,
                     self.save_button, self.scroll, self.empty):
            self.add_subview(view)
        self.sync_results({})

    def result_button(self, title, name):
        button = flat_button(title, self.run_action, CARD, ACTIVE, 13)
        button.name = name
        button.border_width = 1
        button.border_color = PAPER_EDGE
        return button

    def layout(self):
        left, width = 12, max(220, self.width - 24)
        external = getattr(self.workspace, "external_actions", False)
        self.settings_button.frame = (left, 8, width, 38)
        self.update_settings_summary()
        self.title_field.hidden = not self.settings_open
        self.answers_label.hidden = self.answers_switch.hidden = not self.settings_open
        self.style_control.hidden = True
        self.title_field.frame = (left, 54, width, 38)
        self.answers_label.frame = (left, 102, width - 65, 32)
        self.answers_switch.frame = (left + width - 51, 102, 51, 31)
        top = 144 if self.settings_open else 54
        self.generate_button.hidden = self.summary.hidden = external
        for control in (self.result_status, self.open_button,
                        self.answers_button, self.save_button):
            control.hidden = external or not self.results_shown
        bottom_height = 0 if external else (156 if self.results_shown else 88)
        bottom = max(top + 40, self.height - bottom_height)
        if not external:
            self.summary.frame = (left, bottom, width, 22)
            self.generate_button.frame = (left, bottom + 28, width, 44)
            if self.results_shown:
                self.result_status.frame = (left, bottom + 76, width, 24)
                button_width = (width - 12) / 3
                for index, control in enumerate((
                        self.open_button, self.answers_button, self.save_button)):
                    control.frame = (left + index * (button_width + 6),
                                     bottom + 108, button_width, 36)
        self.scroll.frame = (0, top, self.width, max(40, bottom - top))
        self.empty.frame = (left, top + 24, width, 64)
        self.place_cards()

    def update_settings_summary(self):
        title = self.title_field.text.strip() or "Untitled worksheet"
        answers = "Answers on" if self.answers_switch.value else "Answers off"
        self.settings_button.title = "{} {} · {}".format(
            "▾" if self.settings_open else "▸", title, answers)

    def toggle_settings(self, sender):
        if self.settings_open:
            self.title_field.end_editing()
        self.settings_open = not self.settings_open
        self.layout()

    # -------------------------------------------------- header

    def textfield_did_end_editing(self, textfield):
        self.workspace.log.add("title")
        self.update_settings_summary()
        self.workspace.notify()

    def change_settings(self, sender):
        self.workspace.log.add("settings")
        self.update_settings_summary()
        if self.workspace.on_settings:
            self.workspace.on_settings(bool(self.answers_switch.value),
                                       self.style_control.selected_index)

    def generate(self, sender):
        self.title_field.end_editing()
        self.workspace.log.add("generate")
        if self.workspace.on_generate:
            self.workspace.on_generate()

    def run_action(self, sender):
        self.workspace.log.add("action " + sender.name)
        if self.workspace.on_action:
            self.workspace.on_action(sender.name)

    def sync_results(self, state):
        """Generate button and preview row from the host's state."""
        busy = bool(state.get("busy"))
        ready = bool(state.get("ready"))
        status = state.get("status") or ""
        self.generate_button.title = "Working…" if busy else "Generate"
        self.generate_button.enabled = not busy and bool(self.workspace.blocks)
        self.generate_button.alpha = 1 if self.generate_button.enabled else 0.45
        shown = ready or busy or bool(status)
        for view in (self.result_status, self.open_button, self.answers_button, self.save_button):
            view.hidden = getattr(self.workspace, "external_actions", False) or not shown
        self.result_status.text = status
        self.open_button.enabled = ready
        self.answers_button.enabled = ready and bool(state.get("answers"))
        saved = bool(state.get("saved"))
        self.save_button.title = "Saved" if saved else "Save"
        self.save_button.enabled = ready and not saved
        for button in (self.open_button, self.answers_button, self.save_button):
            button.alpha = 1 if button.enabled else 0.4
        if shown != self.results_shown:
            self.results_shown = shown
            self.layout()

    # -------------------------------------------------- cards

    def card_width(self):
        return max(100, self.scroll.width - 24)

    def rebuild(self):
        """Reuse cards; retain hidden removed cards until this sheet closes.

        An action can originate inside a card. Never destroy that card or its
        touched control while UIKit is still delivering the action.
        """
        if not hasattr(self, "_card_cache"):
            self._card_cache = {}
        for card in self._card_cache.values():
            card.hidden = True
        cards = []
        for block in self.workspace.blocks:
            key = id(block)
            card = self._card_cache.get(key)
            if card is None:
                card = BlockCard(self, block)
                self._card_cache[key] = card
                self.scroll.add_subview(card)
            card.hidden = False
            cards.append(card)
        self.cards = cards
        self.workspace.sheet_dirty = False
        self.place_cards()
        self.update_summary()

    def place_cards(self):
        """Stack the cards in order and tell each where it sits."""
        width = self.card_width()
        y = 8
        last = len(self.cards)
        for number, card in enumerate(self.cards, 1):
            card.number = number
            card.is_first = number == 1
            card.is_last = number == last
            card.measure_width = width
            card.refresh()
            card.frame = (12, y, width, card.height_needed())
            y += card.height_needed() + GAP
        self.scroll.content_size = (self.scroll.width, y + 80)
        self.empty.hidden = bool(self.cards)

    def update_summary(self):
        blocks = self.workspace.blocks
        total = sum(block_size(block) for block in blocks)
        self.summary.text = "{} block{} · {} questions".format(
            len(blocks), "" if len(blocks) == 1 else "s", total)
        if not self.generate_button.title.startswith("Working"):
            self.generate_button.enabled = bool(blocks)
            self.generate_button.alpha = 1 if blocks else 0.45

    def toggle_card(self, card):
        card.opened = not card.opened
        self.workspace.log.add(("open " if card.opened else "close ") + card.info.id)
        self.place_cards()

    def move_card(self, card, where):
        """where: 'up', 'down' or 'top'. Keeps the card open after moving."""
        index = self.cards.index(card)
        target = {"up": index - 1, "down": index + 1, "top": 0}[where]
        if target < 0 or target >= len(self.cards) or target == index:
            return
        self.cards.insert(target, self.cards.pop(index))
        blocks = self.workspace.blocks
        blocks.insert(target, blocks.pop(index))
        self.workspace.log.add("move {} {}".format(where, card.info.id))
        self.place_cards()
        self.workspace.board.mark_tiles()
        self.workspace.notify()

    def duplicate_card(self, card):
        index = self.cards.index(card)
        copy = dict(card.block, levels=list(card.block["levels"]))
        self.workspace.blocks.insert(index + 1, copy)
        self.workspace.log.add("duplicate " + card.info.id)
        self.workspace.structure_changed()

    def remove_card(self, card):
        del self.workspace.blocks[self.cards.index(card)]
        self.workspace.log.add("remove card " + card.info.id)
        self.workspace.structure_changed()

    def card_changed(self, card, what):
        """A setting inside one card changed: that card, the total, the host."""
        self.workspace.log.add("{} {}".format(what, card.info.id))
        self.update_summary()
        self.workspace.notify()


class BlockCard(ui.View):
    """One block, led by its full skill title. Tap to show or hide controls."""

    def __init__(self, sheet, block, opened=False):
        super().__init__()
        self.sheet = sheet
        self.block = block
        self.opened = opened
        self.actions_open = False
        self.number = 0
        self.is_first = self.is_last = False
        self.measure_width = 300
        workspace = sheet.workspace
        self.info = workspace.infos[block["generator_id"]]
        self.colour = workspace.colour_for(block["generator_id"])
        self.has_drill = self.info.id in workspace.drill_levels
        self.background_color = CARD
        self.corner_radius = RADIUS
        self.stripe = ui.View()
        self.stripe.background_color = self.colour
        self.stripe.touch_enabled = False
        self.badge = text_label("", 13, "white", bold=True)
        self.badge.alignment = ui.ALIGN_CENTER
        self.badge.background_color = self.colour
        self.badge.corner_radius = 6
        self.heading = text_label(self.info.title, CARD_TITLE_SIZE, INK, bold=True, lines=0)
        self.summary = text_label("", 14, INK_MUTED)
        self.hint = text_label("Edit", 13, self.colour, bold=True)
        self.hint.alignment = ui.ALIGN_RIGHT

        self.drill_label = text_label("Drill", 14, INK, bold=True)
        self.drill_switch = ui.Switch()
        self.drill_switch.action = self.change_drill
        self.drill_switch.tint_color = ACTIVE
        self.apply_label = text_label("Applied", 14, INK)
        self.apply_label.alignment = ui.ALIGN_RIGHT
        self.apply_switch = ui.Switch()
        self.apply_switch.action = self.change_apply
        self.apply_switch.tint_color = ACTIVE
        self.count_label = text_label("Questions", 14, INK, bold=True)
        self.minus = flat_button("−", self.change_count, PAPER, INK, 18)
        self.minus.name = "-1"
        self.count_value = ui.TextField()
        self.count_value.font = ("<System-Bold>", 16)
        self.count_value.text_color = INK
        self.count_value.background_color = PAPER
        self.count_value.corner_radius = RADIUS
        self.count_value.alignment = ui.ALIGN_CENTER
        self.count_value.keyboard_type = ui.KEYBOARD_NUMBERS
        self.count_value.delegate = self
        self.count_slider = ui.Slider()
        self.count_slider.tint_color = ACTIVE
        self.count_slider.action = self.slide_count
        self.actions_button = flat_button(
            "▸ Actions", self.toggle_actions, PAPER, ACTIVE, 13)
        self.close_button = flat_button(
            "Close", self.hide, PAPER, ACTIVE, 13)
        self.plus = flat_button("+", self.change_count, PAPER, INK, 18)
        self.plus.name = "1"
        self.level_label = text_label("Difficulty", 14, INK, bold=True)
        self.level_pills = []
        for level in (1, 2, 3, 4):
            pill = flat_button(str(level), self.toggle_level, PAPER, INK, 15)
            pill.name = str(level)
            pill.border_width = 1
            self.level_pills.append(pill)
        self.up_button = flat_button("▲ Up", self.move, PAPER, INK, 13)
        self.up_button.name = "up"
        self.down_button = flat_button("▼ Down", self.move, PAPER, INK, 13)
        self.down_button.name = "down"
        self.top_button = flat_button("To top", self.move, PAPER, INK, 13)
        self.top_button.name = "top"
        self.duplicate_button = flat_button("Duplicate", self.duplicate, PAPER, INK, 13)
        self.remove_button = flat_button("Remove", self.remove, PAPER, DANGER, 13)
        self.hide_button = flat_button("Hide", self.hide, self.colour, "white", 13)
        self.row_views = {
            "drill": [self.drill_label, self.drill_switch, self.apply_label, self.apply_switch],
            "count": [self.count_label, self.minus, self.count_value, self.plus],
            "slider": [self.count_slider],
            "actions": [self.actions_button, self.close_button],
            "levels": [self.level_label, *self.level_pills],
            "move": [self.up_button, self.down_button, self.top_button],
            "buttons": [self.duplicate_button, self.remove_button, self.hide_button],
        }
        for view in (self.stripe, self.badge, self.heading, self.summary, self.hint):
            self.add_subview(view)
        for views in self.row_views.values():
            for view in views:
                self.add_subview(view)

    # -------------------------------------------------- size

    def rows(self):
        """Control rows shown when open; skills without drill skip that row."""
        rows = (["drill"] if self.has_drill else []) + [
            "count", "slider", "levels", "actions",
        ]
        if self.actions_open:
            rows.extend(["move", "buttons"])
        return rows

    def title_height(self, width):
        return text_height(self.info.title, width - 112, CARD_TITLE_SIZE, True)

    def closed_height(self, width):
        return CARD_TOP + self.title_height(width) + 4 + 20 + 12

    def height_needed(self):
        height = self.closed_height(self.measure_width)
        if self.opened:
            height += len(self.rows()) * CARD_ROW + 8
        return height

    def layout(self):
        width = self.width
        title = self.title_height(width)
        self.stripe.frame = (0, 0, 5, self.height)
        self.badge.frame = (16, CARD_TOP + 1, 26, 24)
        self.heading.frame = (50, CARD_TOP, width - 112, title)
        self.hint.frame = (width - 60, CARD_TOP + 2, 48, 22)
        self.summary.frame = (50, CARD_TOP + title + 4, width - 62, 20)
        third = (width - 32 - 16) / 3
        y = self.closed_height(width)
        for row in self.rows():
            if row == "drill":
                self.drill_label.frame = (16, y, 50, 32)
                self.drill_switch.frame = (68, y + 1, 51, 31)
                self.apply_label.frame = (width - 150, y, 82, 32)
                self.apply_switch.frame = (width - 63, y + 1, 51, 31)
            elif row == "count":
                self.count_label.frame = (16, y, width - 170, 34)
                self.minus.frame = (width - 152, y, 40, 34)
                self.count_value.frame = (width - 108, y, 52, 34)
                self.plus.frame = (width - 52, y, 40, 34)
            elif row == "slider":
                self.count_slider.frame = (20, y, width - 40, 32)
            elif row == "actions":
                self.actions_button.frame = (16, y, width - 120, 34)
                self.close_button.frame = (width - 96, y, 80, 34)
            elif row == "levels":
                self.level_label.frame = (16, y, 100, 34)
                for index, pill in enumerate(self.level_pills):
                    pill.frame = (width - 12 - 4 * 46 + index * 46, y, 40, 34)
            else:
                trio = self.row_views[row]
                for index, button in enumerate(trio):
                    button.frame = (16 + index * (third + 8), y, third, 34)
            y += CARD_ROW

    # -------------------------------------------------- show

    def refresh(self):
        """Show the block's settings and whether the card is open."""
        block = self.block
        self.badge.text = str(self.number or "")
        self.summary.text = block_summary(block)
        self.hint.text = "Hide" if self.opened else "Edit"
        self.border_color = self.colour if self.opened else PAPER_EDGE
        self.border_width = 2 if self.opened else 1
        shown = set(self.rows()) if self.opened else set()
        for row, views in self.row_views.items():
            for view in views:
                view.hidden = row not in shown
        if self.opened:
            self.show_controls()

    def show_controls(self):
        block = self.block
        drill = block["kind"] == "drill"
        self.apply_label.hidden = self.apply_switch.hidden = not drill
        self.drill_switch.value = drill
        self.apply_switch.value = bool(block.get("apply", True))
        self.count_label.text = "Items per level" if drill else "Questions"
        self.count_value.text = str(block["count"])
        limit = maximum_count(block["kind"])
        self.count_slider.value = (block["count"] - 1) / max(1, limit - 1)
        self.actions_button.title = "▾ Actions" if self.actions_open else "▸ Actions"
        supported = supported_levels(self.info, self.sheet.workspace.drill_levels, block["kind"])
        for pill in self.level_pills:
            level = int(pill.name)
            chosen = level in block["levels"]
            pill.enabled = level in supported
            pill.alpha = 1 if pill.enabled else 0.3
            pill.background_color = self.colour if chosen else PAPER
            pill.tint_color = "white" if chosen else INK
            pill.border_color = self.colour if chosen else PAPER_EDGE
        for button, allowed in ((self.up_button, not self.is_first),
                                (self.top_button, not self.is_first),
                                (self.down_button, not self.is_last)):
            button.enabled = allowed
            button.alpha = 1 if allowed else 0.35

    def settings_changed(self, what):
        """Only this card's labels change; the sheet updates its total."""
        self.summary.text = block_summary(self.block)
        self.show_controls()
        self.sheet.card_changed(self, what)

    def touch_began(self, touch):
        # Nothing happens on press; defined so taps are always delivered.
        pass

    def touch_ended(self, touch):
        # Taps on the card body (not its buttons) open or close it.
        if inside(self, touch):
            self.sheet.toggle_card(self)

    # -------------------------------------------------- controls

    def change_drill(self, sender):
        block = self.block
        kind = "drill" if sender.value else "questions"
        supported = supported_levels(self.info, self.sheet.workspace.drill_levels, kind)
        block["kind"] = kind
        block["levels"] = [level for level in block["levels"] if level in supported] or list(supported)
        block["count"] = min(block["count"], maximum_count(kind))
        self.settings_changed("drill on" if sender.value else "drill off")

    def change_apply(self, sender):
        self.block["apply"] = bool(sender.value)
        self.settings_changed("applied")

    def set_count(self, value):
        """Commit one integer count without rebuilding or relaying out cards."""
        limit = maximum_count(self.block["kind"])
        value = max(1, min(limit, int(value)))
        if value == self.block["count"]:
            self.show_controls()
            return
        self.block["count"] = value
        self.settings_changed("count {}".format(value))

    def change_count(self, sender):
        self.set_count(self.block["count"] + int(sender.name))

    def slide_count(self, sender):
        limit = maximum_count(self.block["kind"])
        self.set_count(1 + int(sender.value * (limit - 1) + 0.5))

    def textfield_did_end_editing(self, textfield):
        try:
            value = int(textfield.text.strip())
        except (ValueError, TypeError):
            self.show_controls()
            return
        self.set_count(value)

    def textfield_should_return(self, textfield):
        textfield.end_editing()
        return True

    def toggle_actions(self, sender):
        self.actions_open = not self.actions_open
        self.sheet.workspace.log.add("actions " + self.info.id)
        self.sheet.place_cards()

    def toggle_level(self, sender):
        level = int(sender.name)
        levels = set(self.block["levels"])
        if level in levels:
            if len(levels) > 1:   # a block always keeps at least one level
                levels.remove(level)
        else:
            levels.add(level)
        self.block["levels"] = sorted(levels)
        self.settings_changed("levels " + ",".join(map(str, self.block["levels"])))

    def move(self, sender):
        self.sheet.move_card(self, sender.name)

    def duplicate(self, sender):
        self.sheet.duplicate_card(self)

    def remove(self, sender):
        self.sheet.remove_card(self)

    def hide(self, sender):
        self.sheet.toggle_card(self)