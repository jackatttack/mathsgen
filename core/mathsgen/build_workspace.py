"""Build workspace: a skill board with the worksheet lying on top of it.

This is the whole Build tab:
- The board (dark, compact, after the snippet keyboard) lists skills the way
  the app always has: topic headers, then subheadings (topic_browser groups),
  then one row per skill. Headers fold; search or a grade chip unfolds what
  matches. Tap a skill row to put it on the sheet (green tick); tap again to
  take it off.
- The sheet (light paper) slides over the board from the right. Drag its
  edge bar, or tap it, to bring it in or tuck it away. Its header holds the
  title, Generate, the answer-key switch, the PDF style, and the preview
  actions (Open, Answers, Save) once a preview exists.
- Each block is a card led by its skill. Tap a card to show or hide its
  controls. Press and hold a card (or drag its grip bar) to move it.

Readability rule: titles are measured and never truncated.

The host hears about changes through on_change(blocks, title), settings
through on_settings(answers, theme_index), Generate through on_generate()
and preview actions through on_action(name). Data decisions live in
build_model.py and topic_browser.py; this module draws and reacts.
"""
from collections import Counter

import ui

from .build_model import (
    block_size, block_summary, default_block, drill_levels_by_skill,
    library_sections, maximum_count, supported_levels,
)
from .curriculum import GRADE_BANDS, load_level_tags
from .topic_browser import ORDER, groups_for, topic_style


# ------------------------------------------------------------ editable look

# The board borrows the snippet keyboard's palette.
BOARD = "#161616"
TILE = "#2C2C2E"
GROUP_TILE = "#232325"
TILE_PRESSED = "#48484A"
SEARCH_FIELD = "#3A3A3C"
ACTIVE = "#5E5CE6"
TEXT = "#F2F2F2"
MUTED = "#B4B4B8"
# Skills already on the sheet.
ADDED_TILE = "#17382A"
ADDED_EDGE = "#34C759"
# The sheet is paper on top of it.
PAPER = "#FBFAF6"
PAPER_EDGE = "#E2DED3"
GRIP = "#BDB7A7"
CARD = "#FFFFFF"
INK = "#1F2430"
INK_MUTED = "#5B6472"
DANGER = "#C0392B"

# One colour per app topic, used on the board and on the cards.
TOPIC_COLOURS = {
    "number": "#2F80ED", "algebra": "#8E6CEF", "ratio": "#56CCF2",
    "geometry": "#F2994A", "probability": "#EB5757", "data": "#27AE60",
    "problem_solving": "#2DD4BF",
}

RADIUS = 7
GAP = 6
HANDLE_WIDTH = 30     # the sheet's edge bar
OPEN_GAP = 22         # board left visible beside an open sheet
ROW_TITLE_SIZE = 15
CARD_TITLE_SIZE = 16
GRIP_HEIGHT = 26      # the grab strip on top of each card
CARD_ROW = 44         # each row of controls on an open card
TAP_SLOP = 6          # movement under this still counts as a tap
HOLD_DELAY = 0.3      # press this long on a card to pick it up


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


def lift(view):
    """Give a view a soft shadow so it reads as an object. Optional nicety."""
    try:
        from objc_util import CGSize, ObjCInstance
        layer = ObjCInstance(view).layer()
        layer.setShadowOpacity_(0.45)
        layer.setShadowRadius_(16)
        layer.setShadowOffset_(CGSize(-6, 0))
        layer.setMasksToBounds_(False)
    except Exception:
        pass


def point_in(touch, view, target):
    """A touch location in another view's coordinates (stable while dragging)."""
    return ui.convert_point(touch.location, view, target)


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


# ------------------------------------------------------------ workspace

class Workspace(ui.View):
    """The board with the sheet on top. See the module docstring for hooks."""

    def __init__(self, registry, blocks, title, on_change, answers=True,
                 theme_index=0, theme_names=("Calm", "Classic", "Contrast"),
                 on_settings=None, on_generate=None, on_action=None):
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
        self.load_error = ""
        try:
            sections = library_sections(registry, load_level_tags(registry), self.drill_levels)
        except Exception as error:
            sections = []
            self.load_error = "Skill details unavailable: " + str(error)
        # Spec codes, years, grades and search text for each skill.
        self.entries = {entry["generator_id"]: entry
                        for _, entries in sections for entry in entries}
        # The app's own topic -> subheading grouping.
        self.groups = groups_for(list(self.infos.values()))
        present = {group["topic"] for group in self.groups}
        self.topics = [topic for topic in ORDER if topic in present] + sorted(present - set(ORDER))
        self.sheet_open = bool(self.blocks)
        self.board = SkillBoard(self)
        self.sheet = SheetDrawer(self, title, answers, theme_index, theme_names)
        self.add_subview(self.board)
        self.add_subview(self.sheet)

    def layout(self):
        self.board.frame = (0, 0, self.width - HANDLE_WIDTH, self.height)
        self.sheet.frame = self.sheet_frame(self.sheet_open)

    def sheet_frame(self, opened):
        x = OPEN_GAP if opened else self.width - HANDLE_WIDTH
        return (x, 0, self.width - OPEN_GAP, self.height)

    def set_sheet_open(self, opened):
        self.sheet_open = opened

        def slide():
            self.sheet.frame = self.sheet_frame(opened)
        ui.animate(slide, 0.25)

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
        self.sheet.rebuild()
        self.sheet.handle.pulse()
        self.changed()
        return added

    def changed(self):
        """Refresh the board's green marks and report the sheet to the host."""
        self.board.mark_tiles()
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
        self.topic = None         # None shows every topic
        self.grades = None        # None shows every grade
        self.open_topics = set()
        self.open_groups = set()
        self.rows = []
        self.headers = []
        self.heading = text_label("Skills", 24, TEXT, bold=True)
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
        for view in (self.heading, self.fold_button, self.search, self.placeholder,
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
        left, width = 12, self.width - 24
        self.heading.frame = (left, 8, width - 120, 32)
        self.fold_button.frame = (left + width - 110, 8, 110, 32)
        self.search.frame = (left, 46, width, 38)
        self.placeholder.frame = (left + 12, 46, width - 24, 38)
        for strip, chips, y in ((self.topic_strip, self.topic_chips, 92),
                                (self.grade_strip, self.grade_chips, 130)):
            x = left
            for chip in chips:
                chip.frame = (x, 0, chip_width(chip.title), 32)
                x += chip_width(chip.title) + GAP
            strip.frame = (0, y, self.width, 32)
            strip.content_size = (x + left, 32)
        self.status.frame = (left, 168, width, 18)
        self.grid.frame = (0, 190, self.width, max(100, self.height - 190))
        self.fill_grid()

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
        for view in list(self.grid.subviews):
            self.grid.remove_subview(view)
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
                    # A one-skill group needs no subheading.
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
            empty = text_label("No skills match.", 14, MUTED)
            empty.frame = (left, 10, width, 24)
            self.grid.add_subview(empty)
        self.grid.content_size = (self.width, y + 40)
        self.fold_button.title = "Fold all" if (self.open_topics or self.open_groups) else "Expand all"
        self.mark_tiles()

    def add_header(self, kind, key, title, colour, ids, opened, x, y, width):
        header = HeaderRow(self, kind, key, title, colour, ids, opened)
        height = header.needed_height(width)
        header.frame = (x, y, width, height)
        self.grid.add_subview(header)
        self.headers.append(header)
        return y + height + GAP

    def add_row(self, info, colour, x, y, width):
        row = SkillRow(self, self.workspace.entries[info.id], colour)
        height = row.needed_height(width)
        row.frame = (x, y, width, height)
        self.grid.add_subview(row)
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
        if added:
            row.flash()
            self.status.text = "Added {}.".format(row.entry["title"])
        else:
            self.status.text = "Removed {}.".format(row.entry["title"])


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
        self.background_color = TILE if topic else GROUP_TILE
        self.corner_radius = RADIUS
        self.bar = ui.View()
        self.bar.background_color = colour if topic else GROUP_TILE
        self.bar.touch_enabled = False
        self.title_text = ("▾ " if opened else "▸ ") + title
        self.title = text_label(self.title_text, self.size, colour if topic else TEXT,
                                bold=True, lines=0)
        self.detail = text_label("", 13, MUTED)
        self.detail.alignment = ui.ALIGN_RIGHT
        for view in (self.bar, self.title, self.detail):
            self.add_subview(view)
        self.set_count(0)

    def needed_height(self, width):
        return max(self.minimum, text_height(self.title_text, width - 168, self.size, True) + 16)

    def layout(self):
        self.bar.frame = (0, 0, 4, self.height)
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
        self.colour = colour
        self.added = 0
        self.corner_radius = RADIUS
        self.stripe = ui.View()
        self.stripe.background_color = colour
        self.stripe.touch_enabled = False
        self.title = text_label(entry["title"], ROW_TITLE_SIZE, TEXT, bold=True, lines=0)
        self.detail = text_label(row_detail(entry), 12, MUTED)
        self.mark = text_label("", 14, ADDED_EDGE, bold=True)
        self.mark.alignment = ui.ALIGN_RIGHT
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
        self.stripe.frame = (0, 0, 4, self.height)
        self.title.frame = (14, 8, self.title_width(self.width), title)
        self.mark.frame = (self.width - 44, 8, 36, 20)
        self.detail.frame = (14, self.height - 25, self.width - 22, 17)

    def resting_colour(self):
        return ADDED_TILE if self.added else TILE

    def set_added(self, count):
        self.added = count
        self.background_color = self.resting_colour()
        self.border_color = ADDED_EDGE
        self.border_width = 2 if count else 0
        self.mark.text = "" if not count else ("✓" if count == 1 else "✓×{}".format(count))

    def touch_began(self, touch):
        self.background_color = TILE_PRESSED

    def touch_ended(self, touch):
        self.background_color = self.resting_colour()
        if inside(self, touch):
            self.board.row_tapped(self)

    def flash(self):
        self.background_color = self.colour

        def settle():
            self.background_color = self.resting_colour()
        ui.animate(settle, 0.45)


# ------------------------------------------------------------ the sheet

class SheetDrawer(ui.View):
    """The worksheet as paper: edge bar, header tools and block cards."""

    def __init__(self, workspace, title, answers, theme_index, theme_names):
        super().__init__()
        self.workspace = workspace
        self.background_color = PAPER
        lift(self)
        self.handle = EdgeHandle(self)
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
        self.answers_switch.action = self.change_settings
        self.style_control = ui.SegmentedControl()
        self.style_control.segments = list(theme_names)
        self.style_control.selected_index = theme_index
        self.style_control.tint_color = ACTIVE
        self.style_control.action = self.change_settings
        # Preview results: a status line and three small actions.
        self.result_status = text_label("", 12, INK_MUTED)
        self.open_button = self.result_button("Open", "open_questions")
        self.answers_button = self.result_button("Answers", "open_answers")
        self.save_button = self.result_button("Save", "save")
        self.scroll = ui.ScrollView()
        self.scroll.background_color = PAPER
        # Cards get touches at once, so a drag can start before scrolling does.
        self.scroll.delays_content_touches = False
        self.empty = text_label(
            "Tap skills on the board to add them here.\n"
            "Tap a card to edit it. Press and hold a card to move it.",
            14, INK_MUTED, lines=0)
        self.empty.alignment = ui.ALIGN_CENTER
        self.cards = []
        self.dragging = None
        self.last_drag_y = 0
        self.results_shown = False
        for view in (self.handle, self.title_field, self.generate_button, self.summary,
                     self.answers_label, self.answers_switch, self.style_control,
                     self.result_status, self.open_button, self.answers_button,
                     self.save_button, self.scroll, self.empty):
            self.add_subview(view)
        self.sync_results({})
        self.rebuild()

    def result_button(self, title, name):
        button = flat_button(title, self.run_action, CARD, ACTIVE, 13)
        button.name = name
        button.border_width = 1
        button.border_color = PAPER_EDGE
        return button

    def layout(self):
        self.handle.frame = (0, 0, HANDLE_WIDTH, self.height)
        left = HANDLE_WIDTH + 12
        width = self.width - left - 12
        self.title_field.frame = (left, 8, width - 112, 36)
        self.generate_button.frame = (left + width - 104, 8, 104, 36)
        self.summary.frame = (left, 46, width, 18)
        self.answers_label.frame = (left, 70, 70, 31)
        self.answers_switch.frame = (left + 72, 70, 51, 31)
        style_width = min(210, width - 132)
        self.style_control.frame = (left + width - style_width, 70, style_width, 30)
        top = 110
        if self.results_shown:
            button_width = 72
            right = left + width
            self.save_button.frame = (right - button_width, 108, button_width, 28)
            self.answers_button.frame = (right - 2 * button_width - 6, 108, button_width, 28)
            self.open_button.frame = (right - 3 * button_width - 12, 108, button_width, 28)
            self.result_status.frame = (left, 108, width - 3 * button_width - 18, 28)
            top = 144
        self.scroll.frame = (HANDLE_WIDTH, top, self.width - HANDLE_WIDTH,
                             max(100, self.height - top))
        self.empty.frame = (left, top + 50, width, 60)
        self.place_cards()

    # -------------------------------------------------- header

    def textfield_did_end_editing(self, textfield):
        self.workspace.changed()

    def change_settings(self, sender):
        if self.workspace.on_settings:
            self.workspace.on_settings(bool(self.answers_switch.value),
                                       self.style_control.selected_index)

    def generate(self, sender):
        self.title_field.end_editing()
        if self.workspace.on_generate:
            self.workspace.on_generate()

    def run_action(self, sender):
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
            view.hidden = not shown
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
        return max(100, self.scroll.width - 22)

    def rebuild(self):
        """Recreate one card per block, keeping which cards were open."""
        opened = {id(card.block) for card in self.cards if card.opened}
        for card in self.cards:
            self.scroll.remove_subview(card)
        self.cards = [BlockCard(self, block, id(block) in opened)
                      for block in self.workspace.blocks]
        for card in self.cards:
            self.scroll.add_subview(card)
        self.place_cards()
        self.update_summary()

    def place_cards(self, skip=None):
        """Stack the cards in order; skip leaves a dragged card where it is."""
        width = self.card_width()
        y = 8
        for number, card in enumerate(self.cards, 1):
            card.number = number
            card.measure_width = width
            card.refresh()
            if card is not skip:
                card.frame = (11, y, width, card.height_needed())
            y += card.height_needed() + GAP
        self.scroll.content_size = (self.scroll.width, y + 80)
        self.empty.hidden = bool(self.cards)

    def animate_layout(self, skip=None):
        ui.animate(lambda: self.place_cards(skip), 0.2)

    def update_summary(self):
        blocks = self.workspace.blocks
        total = sum(block_size(block) for block in blocks)
        self.summary.text = "{} block{} · {} questions".format(
            len(blocks), "" if len(blocks) == 1 else "s", total)
        self.handle.set_count(len(blocks))
        if not self.generate_button.title.startswith("Working"):
            self.generate_button.enabled = bool(blocks)
            self.generate_button.alpha = 1 if blocks else 0.45

    def toggle_card(self, card):
        card.opened = not card.opened
        self.animate_layout()

    def duplicate_card(self, card):
        index = self.cards.index(card)
        copy = dict(card.block, levels=list(card.block["levels"]))
        self.workspace.blocks.insert(index + 1, copy)
        self.rebuild()
        self.workspace.changed()

    def remove_card(self, card):
        del self.workspace.blocks[self.cards.index(card)]
        self.rebuild()
        self.workspace.changed()

    def card_changed(self):
        self.update_summary()
        self.workspace.changed()

    # -------------------------------------------------- moving a card

    def begin_drag(self, card, point):
        self.dragging = card
        self.last_drag_y = point[1]
        card.bring_to_front()
        card.alpha = 0.9
        card.border_color = ACTIVE
        card.border_width = 2
        self.scroll.scroll_enabled = False

    def drag_to(self, card, point):
        """Follow the finger; when the card passes a neighbour, swap slots."""
        card.y += point[1] - self.last_drag_y
        self.last_drag_y = point[1]
        centre = card.y + card.height / 2
        target, y = 0, 8
        for other in self.cards:
            if other is card:
                continue
            if centre > y + other.height_needed() / 2:
                target += 1
            y += other.height_needed() + GAP
        if target != self.cards.index(card):
            self.cards.remove(card)
            self.cards.insert(target, card)
            self.animate_layout(skip=card)

    def end_drag(self, card):
        self.dragging = None
        card.alpha = 1
        self.scroll.scroll_enabled = True
        self.workspace.blocks[:] = [each.block for each in self.cards]
        self.animate_layout()
        self.workspace.changed()


class EdgeHandle(ui.View):
    """The sheet's left edge bar: drag to slide the sheet, tap to toggle it."""

    def __init__(self, drawer):
        super().__init__()
        self.drawer = drawer
        self.background_color = PAPER_EDGE
        self.pill = ui.View()
        self.pill.background_color = GRIP
        self.pill.corner_radius = 2.5
        self.pill.touch_enabled = False
        self.count = text_label("0", 14, INK, bold=True)
        self.count.alignment = ui.ALIGN_CENTER
        self.add_subview(self.pill)
        self.add_subview(self.count)
        self.start_x = self.last_x = 0

    def layout(self):
        self.pill.frame = (self.width / 2 - 2.5, self.height / 2 - 24, 5, 48)
        self.count.frame = (0, self.height / 2 + 32, self.width, 20)

    def set_count(self, number):
        self.count.text = str(number)

    def pulse(self):
        self.count.text_color = ACTIVE

        def settle():
            self.count.text_color = INK
        ui.delay(settle, 0.6)

    def touch_began(self, touch):
        x = point_in(touch, self, self.drawer.workspace)[0]
        self.start_x = self.last_x = x

    def touch_moved(self, touch):
        workspace = self.drawer.workspace
        x = point_in(touch, self, workspace)[0]
        dx, self.last_x = x - self.last_x, x
        lowest, highest = OPEN_GAP, workspace.width - HANDLE_WIDTH
        self.drawer.x = max(lowest, min(highest, self.drawer.x + dx))

    def touch_ended(self, touch):
        workspace = self.drawer.workspace
        x = point_in(touch, self, workspace)[0]
        if abs(x - self.start_x) < TAP_SLOP:
            workspace.set_sheet_open(not workspace.sheet_open)
        else:
            middle = (OPEN_GAP + workspace.width - HANDLE_WIDTH) / 2
            workspace.set_sheet_open(self.drawer.x < middle)


class GripBar(ui.View):
    """The strip on top of a card: press and drag it to move the card at once."""

    def __init__(self, card):
        super().__init__()
        self.card = card
        self.pill = ui.View()
        self.pill.background_color = GRIP
        self.pill.corner_radius = 3
        self.pill.touch_enabled = False
        self.add_subview(self.pill)

    def layout(self):
        self.pill.frame = (self.width / 2 - 24, 10, 48, 6)

    def touch_began(self, touch):
        drawer = self.card.drawer
        drawer.begin_drag(self.card, point_in(touch, self, drawer.scroll))

    def touch_moved(self, touch):
        drawer = self.card.drawer
        drawer.drag_to(self.card, point_in(touch, self, drawer.scroll))

    def touch_ended(self, touch):
        self.card.drawer.end_drag(self.card)


class BlockCard(ui.View):
    """One block, led by its full skill title. Closed: a summary. Open: controls.

    Tap toggles the controls. Press and hold for HOLD_DELAY picks the card up
    to move it; moving before then lets the sheet scroll instead.
    """

    def __init__(self, drawer, block, opened=False):
        super().__init__()
        self.drawer = drawer
        self.block = block
        self.opened = opened
        self.number = 0
        self.measure_width = 300
        self.press_token = None
        self.press_point = (0, 0)
        self.press_moved = False
        self.lifted = False
        workspace = drawer.workspace
        self.info = workspace.infos[block["generator_id"]]
        self.colour = workspace.colour_for(block["generator_id"])
        self.has_drill = self.info.id in workspace.drill_levels
        self.background_color = CARD
        self.corner_radius = RADIUS
        self.stripe = ui.View()
        self.stripe.background_color = self.colour
        self.stripe.touch_enabled = False
        self.grip = GripBar(self)
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
        self.apply_label = text_label("Applied", 14, INK)
        self.apply_label.alignment = ui.ALIGN_RIGHT
        self.apply_switch = ui.Switch()
        self.apply_switch.action = self.change_apply
        self.count_label = text_label("Questions", 14, INK, bold=True)
        self.minus = flat_button("−", self.change_count, PAPER, INK, 18)
        self.minus.name = "-1"
        self.count_value = text_label("", 16, INK, bold=True)
        self.count_value.alignment = ui.ALIGN_CENTER
        self.plus = flat_button("+", self.change_count, PAPER, INK, 18)
        self.plus.name = "1"
        self.level_label = text_label("Difficulty", 14, INK, bold=True)
        self.level_pills = []
        for level in (1, 2, 3, 4):
            pill = flat_button(str(level), self.toggle_level, PAPER, INK, 15)
            pill.name = str(level)
            pill.border_width = 1
            self.level_pills.append(pill)
        self.duplicate_button = flat_button("Duplicate", self.duplicate, PAPER, INK, 13)
        self.remove_button = flat_button("Remove", self.remove, PAPER, DANGER, 13)
        self.hide_button = flat_button("Hide", self.hide, self.colour, "white", 13)
        self.row_views = {
            "drill": [self.drill_label, self.drill_switch, self.apply_label, self.apply_switch],
            "count": [self.count_label, self.minus, self.count_value, self.plus],
            "levels": [self.level_label, *self.level_pills],
            "buttons": [self.duplicate_button, self.remove_button, self.hide_button],
        }
        for view in (self.stripe, self.grip, self.badge, self.heading, self.summary, self.hint):
            self.add_subview(view)
        for views in self.row_views.values():
            for view in views:
                self.add_subview(view)
        self.refresh()

    # -------------------------------------------------- size

    def rows(self):
        """Control rows shown when open; skills without drill skip that row."""
        return (["drill"] if self.has_drill else []) + ["count", "levels", "buttons"]

    def title_height(self, width):
        return text_height(self.info.title, width - 112, CARD_TITLE_SIZE, True)

    def closed_height(self, width):
        return GRIP_HEIGHT + 4 + self.title_height(width) + 4 + 20 + 12

    def height_needed(self):
        height = self.closed_height(self.measure_width)
        if self.opened:
            height += len(self.rows()) * CARD_ROW + 8
        return height

    def layout(self):
        width = self.width
        title = self.title_height(width)
        top = GRIP_HEIGHT + 4
        self.stripe.frame = (0, 0, 5, self.height)
        self.grip.frame = (5, 0, width - 5, GRIP_HEIGHT)
        self.badge.frame = (16, top + 1, 26, 24)
        self.heading.frame = (50, top, width - 112, title)
        self.hint.frame = (width - 60, top + 2, 48, 22)
        self.summary.frame = (50, top + title + 4, width - 62, 20)
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
            elif row == "levels":
                self.level_label.frame = (16, y, 100, 34)
                for index, pill in enumerate(self.level_pills):
                    pill.frame = (width - 12 - 4 * 46 + index * 46, y, 40, 34)
            else:
                third = (width - 32 - 16) / 3
                self.duplicate_button.frame = (16, y, third, 34)
                self.remove_button.frame = (16 + third + 8, y, third, 34)
                self.hide_button.frame = (16 + 2 * (third + 8), y, third, 34)
            y += CARD_ROW

    # -------------------------------------------------- show

    def refresh(self):
        """Show the block's settings and whether the card is open."""
        workspace = self.drawer.workspace
        block = self.block
        drill = block["kind"] == "drill"
        self.badge.text = str(self.number or "")
        self.summary.text = block_summary(block)
        self.hint.text = "Hide" if self.opened else "Edit"
        if self.drawer.dragging is not self:
            self.border_color = self.colour if self.opened else PAPER_EDGE
            self.border_width = 2 if self.opened else 1
        shown = set(self.rows()) if self.opened else set()
        for row, views in self.row_views.items():
            for view in views:
                view.hidden = row not in shown
        if not self.opened:
            return
        self.apply_label.hidden = self.apply_switch.hidden = not drill
        self.drill_switch.value = drill
        self.apply_switch.value = bool(block.get("apply", True))
        self.count_label.text = "Items per level" if drill else "Questions"
        self.count_value.text = str(block["count"])
        supported = supported_levels(self.info, workspace.drill_levels, block["kind"])
        for pill in self.level_pills:
            level = int(pill.name)
            chosen = level in block["levels"]
            pill.enabled = level in supported
            pill.alpha = 1 if pill.enabled else 0.3
            pill.background_color = self.colour if chosen else PAPER
            pill.tint_color = "white" if chosen else INK
            pill.border_color = self.colour if chosen else PAPER_EDGE

    def changed(self):
        self.refresh()
        self.drawer.card_changed()

    # -------------------------------------------------- touch: tap or hold

    def touch_began(self, touch):
        token = object()
        self.press_token = token
        self.press_point = point_in(touch, self, self.drawer.scroll)
        self.press_moved = False
        self.lifted = False
        ui.delay(lambda: self.lift_if_held(token), HOLD_DELAY)

    def lift_if_held(self, token):
        """Pick the card up if the same press is still down and still."""
        if token is self.press_token and not self.press_moved and not self.lifted:
            self.lifted = True
            self.drawer.begin_drag(self, self.press_point)

    def touch_moved(self, touch):
        point = point_in(touch, self, self.drawer.scroll)
        if self.lifted:
            self.drawer.drag_to(self, point)
        elif (abs(point[0] - self.press_point[0]) > TAP_SLOP
              or abs(point[1] - self.press_point[1]) > TAP_SLOP):
            self.press_moved = True

    def touch_ended(self, touch):
        lifted, moved = self.lifted, self.press_moved
        self.press_token = None
        self.lifted = False
        if lifted:
            self.drawer.end_drag(self)
        elif not moved and self.drawer.dragging is None:
            self.drawer.toggle_card(self)

    # -------------------------------------------------- controls

    def change_drill(self, sender):
        block = self.block
        kind = "drill" if sender.value else "questions"
        supported = supported_levels(self.info, self.drawer.workspace.drill_levels, kind)
        block["kind"] = kind
        block["levels"] = [level for level in block["levels"] if level in supported] or list(supported)
        block["count"] = min(block["count"], maximum_count(kind))
        self.changed()

    def change_apply(self, sender):
        self.block["apply"] = bool(sender.value)
        self.changed()

    def change_count(self, sender):
        block = self.block
        block["count"] = max(1, min(maximum_count(block["kind"]),
                                    block["count"] + int(sender.name)))
        self.changed()

    def toggle_level(self, sender):
        level = int(sender.name)
        levels = set(self.block["levels"])
        if level in levels:
            if len(levels) > 1:   # a block always keeps at least one level
                levels.remove(level)
        else:
            levels.add(level)
        self.block["levels"] = sorted(levels)
        self.changed()

    def duplicate(self, sender):
        self.drawer.duplicate_card(self)

    def remove(self, sender):
        self.drawer.remove_card(self)

    def hide(self, sender):
        self.drawer.toggle_card(self)