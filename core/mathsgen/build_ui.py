"""Build editor: arrange a worksheet as an ordered list of blocks.

Shown over the Worksheet Maker when the teacher taps "Edit sheet":
- the sheet: one row per block in print order. Reorder shows drag handles,
  swipe left deletes, tap opens the block panel;
- the block panel: questions or drill, difficulties, count, applied problems;
- the library: every skill grouped by Edexcel strand in specification order;
  tap a skill to add it to the end of the sheet.

All data decisions live in build_model.py; this file only draws and reacts.
"""
import ui

from .build_model import (
    block_size, block_summary, default_block, drill_levels_by_skill,
    filter_sections, library_sections, maximum_count, supported_levels,
)
from .curriculum import load_level_tags


ACCENT = "#315BE8"
INK = "#182238"
MUTED = "#64748B"
DANGER = "#DC2626"
BACKGROUND = "#F3F5F9"


def make_label(text, size=15, bold=False, colour=INK, lines=1):
    item = ui.Label()
    item.text = text
    item.font = ("<System-Bold>" if bold else "<System>", size)
    item.text_color = colour
    item.number_of_lines = lines
    return item


def make_button(title, action, filled=False, colour=ACCENT):
    item = ui.Button(title=title)
    item.action = action
    item.font = ("<System-Bold>", 15)
    item.corner_radius = 8
    item.background_color = colour if filled else "white"
    item.tint_color = "white" if filled else colour
    return item


def content_frame(view):
    """(left, width) for content centred at a readable width."""
    width = min(max(view.width - 32, 240), 760)
    return (view.width - width) / 2, width


class BuildEditor(ui.View):
    """The sheet: blocks in print order. Done hands them back via on_done."""

    def __init__(self, registry, blocks, on_done):
        super().__init__()
        self.background_color = BACKGROUND
        self.registry = registry
        self.infos = {info.id: info for info in registry.list()}
        self.drill_levels = drill_levels_by_skill(registry)
        self.blocks = [dict(block) for block in blocks]
        self.on_done = on_done

        self.heading = make_label("Sheet", 24, bold=True)
        self.note = make_label("", 13, colour=MUTED)
        self.done_button = make_button("Done", self.finish, filled=True)
        self.add_button = make_button("+ Add skills", self.open_library, filled=True)
        self.order_button = make_button("Reorder", self.toggle_reorder)
        self.table = ui.TableView()
        self.table.data_source = self
        self.table.delegate = self
        self.table.row_height = 62
        self.table.background_color = BACKGROUND
        self.empty = make_label(
            "No blocks yet.\nTap + Add skills to start the sheet.", 15,
            colour=MUTED, lines=0)
        self.empty.alignment = ui.ALIGN_CENTER
        for view in (self.heading, self.note, self.done_button, self.add_button,
                     self.order_button, self.table, self.empty):
            self.add_subview(view)
        self.panel = BlockPanel(self)
        self.library = LibraryPanel(self)
        for overlay in (self.panel, self.library):
            overlay.hidden = True
            self.add_subview(overlay)
        self.refresh()

    def layout(self):
        left, width = content_frame(self)
        self.heading.frame = (left, 14, width - 100, 34)
        self.done_button.frame = (left + width - 90, 14, 90, 36)
        split = (width - 10) * 0.6
        self.add_button.frame = (left, 58, split, 40)
        self.order_button.frame = (left + split + 10, 58, width - split - 10, 40)
        self.note.frame = (left, 104, width, 22)
        self.table.frame = (0, 132, self.width, max(100, self.height - 132))
        self.empty.frame = (left, 190, width, 60)
        for overlay in (self.panel, self.library):
            overlay.frame = self.bounds

    def refresh(self):
        """Redraw the list, the count note and the empty message."""
        self.table.reload()
        self.empty.hidden = bool(self.blocks)
        total = sum(block_size(block) for block in self.blocks)
        self.note.text = "{} block{} · {} questions, printed in this order".format(
            len(self.blocks), "" if len(self.blocks) == 1 else "s", total)
        self.order_button.enabled = len(self.blocks) > 1
        self.order_button.alpha = 1 if self.order_button.enabled else 0.45

    # -------------------------------------------------- table data source

    def tableview_number_of_sections(self, tableview):
        return 1

    def tableview_number_of_rows(self, tableview, section):
        return len(self.blocks)

    def tableview_cell_for_row(self, tableview, section, row):
        block = self.blocks[row]
        cell = ui.TableViewCell("subtitle")
        cell.text_label.text = "{}. {}".format(row + 1, self.infos[block["generator_id"]].title)
        cell.detail_text_label.text = block_summary(block)
        cell.detail_text_label.text_color = MUTED
        cell.accessory_type = "disclosure_indicator"
        return cell

    def tableview_can_delete(self, tableview, section, row):
        return True

    def tableview_can_move(self, tableview, section, row):
        return True

    def tableview_delete(self, tableview, section, row):
        del self.blocks[row]
        self.refresh()

    def tableview_move_row(self, tableview, from_section, from_row, to_section, to_row):
        self.blocks.insert(to_row, self.blocks.pop(from_row))
        # Renumber once the drag animation has settled.
        ui.delay(self.refresh, 0.3)

    def tableview_did_select(self, tableview, section, row):
        if not tableview.editing:
            self.panel.open(row)

    # -------------------------------------------------- actions

    def toggle_reorder(self, sender):
        self.table.editing = not self.table.editing
        self.order_button.title = "Finish reorder" if self.table.editing else "Reorder"

    def open_library(self, sender):
        self.library.open()

    def add_block(self, generator_id):
        self.blocks.append(default_block(self.infos[generator_id]))
        self.refresh()

    def finish(self, sender):
        self.table.editing = False
        self.on_done(list(self.blocks))


class BlockPanel(ui.View):
    """Settings for one block: kind, difficulties, count, applied problems."""

    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.index = None
        self.background_color = BACKGROUND
        self.title = make_label("", 20, bold=True, lines=2)
        self.kind_control = ui.SegmentedControl()
        self.kind_control.tint_color = ACCENT
        self.kind_control.action = self.change_kind
        self.levels_label = make_label("Difficulty", 15, bold=True)
        self.level_buttons = []
        for level in (1, 2, 3, 4):
            pill = make_button(str(level), self.toggle_level)
            pill.name = str(level)
            self.level_buttons.append(pill)
        self.count_label = make_label("Questions", 15, bold=True)
        self.minus = make_button("−", self.change_count)
        self.minus.name = "-1"
        self.count_value = make_label("", 18, bold=True)
        self.count_value.alignment = ui.ALIGN_CENTER
        self.plus = make_button("+", self.change_count)
        self.plus.name = "1"
        self.apply_label = make_label("Applied problems after the drill", 15)
        self.apply_switch = ui.Switch()
        self.apply_switch.action = self.change_apply
        self.summary = make_label("", 14, colour=MUTED, lines=2)
        self.duplicate_button = make_button("Duplicate", self.duplicate)
        self.delete_button = make_button("Delete", self.delete, colour=DANGER)
        self.done_button = make_button("Done", self.close, filled=True)
        for view in (self.title, self.kind_control, self.levels_label,
                     *self.level_buttons, self.count_label, self.minus,
                     self.count_value, self.plus, self.apply_label,
                     self.apply_switch, self.summary, self.duplicate_button,
                     self.delete_button, self.done_button):
            self.add_subview(view)

    def layout(self):
        left, width = content_frame(self)
        self.title.frame = (left, 16, width, 56)
        self.kind_control.frame = (left, 84, width, 34)
        self.levels_label.frame = (left, 132, 110, 38)
        pill = min(52, (width - 120) / 4)
        for index, item in enumerate(self.level_buttons):
            item.frame = (left + width - 4 * pill + index * pill, 132, pill - 6, 38)
        self.count_label.frame = (left, 184, width - 150, 38)
        self.minus.frame = (left + width - 146, 184, 42, 38)
        self.count_value.frame = (left + width - 100, 184, 54, 38)
        self.plus.frame = (left + width - 42, 184, 42, 38)
        self.apply_label.frame = (left, 236, width - 60, 34)
        self.apply_switch.frame = (left + width - 51, 237, 51, 32)
        self.summary.frame = (left, 282, width, 40)
        third = (width - 20) / 3
        self.duplicate_button.frame = (left, 336, third, 42)
        self.delete_button.frame = (left + third + 10, 336, third, 42)
        self.done_button.frame = (left + 2 * third + 20, 336, third, 42)

    def block(self):
        return self.editor.blocks[self.index]

    def info(self):
        return self.editor.infos[self.block()["generator_id"]]

    def kinds(self):
        return ["questions", "drill"] if self.info().id in self.editor.drill_levels else ["questions"]

    def open(self, index):
        self.index = index
        self.sync()
        self.hidden = False
        self.bring_to_front()

    def sync(self):
        """Show the block's current settings."""
        block, kinds = self.block(), self.kinds()
        drill = block["kind"] == "drill"
        self.title.text = self.info().title
        self.kind_control.segments = [kind.title() for kind in kinds]
        self.kind_control.selected_index = kinds.index(block["kind"])
        supported = supported_levels(self.info(), self.editor.drill_levels, block["kind"])
        for pill in self.level_buttons:
            level = int(pill.name)
            chosen = level in block["levels"]
            pill.enabled = level in supported
            pill.background_color = ACCENT if chosen else "white"
            pill.tint_color = "white" if chosen else ACCENT
            pill.alpha = 1 if pill.enabled else 0.3
        self.count_label.text = "Items per level" if drill else "Questions"
        self.count_value.text = str(block["count"])
        self.apply_label.hidden = self.apply_switch.hidden = not drill
        self.apply_switch.value = bool(block.get("apply", True))
        self.summary.text = block_summary(block)

    def changed(self):
        self.sync()
        self.editor.refresh()

    def change_kind(self, sender):
        block = self.block()
        kind = self.kinds()[sender.selected_index]
        supported = supported_levels(self.info(), self.editor.drill_levels, kind)
        block["kind"] = kind
        block["levels"] = [level for level in block["levels"] if level in supported] or list(supported)
        block["count"] = min(block["count"], maximum_count(kind))
        self.changed()

    def toggle_level(self, sender):
        block = self.block()
        level = int(sender.name)
        levels = set(block["levels"])
        if level in levels:
            if len(levels) > 1:   # a block always keeps at least one level
                levels.remove(level)
        else:
            levels.add(level)
        block["levels"] = sorted(levels)
        self.changed()

    def change_count(self, sender):
        block = self.block()
        block["count"] = max(1, min(maximum_count(block["kind"]),
                                    block["count"] + int(sender.name)))
        self.changed()

    def change_apply(self, sender):
        self.block()["apply"] = bool(sender.value)
        self.changed()

    def duplicate(self, sender):
        block = self.block()
        self.editor.blocks.insert(self.index + 1, dict(block, levels=list(block["levels"])))
        self.close(sender)

    def delete(self, sender):
        del self.editor.blocks[self.index]
        self.close(sender)

    def close(self, sender=None):
        self.hidden = True
        self.index = None
        self.editor.refresh()


class LibraryPanel(ui.View):
    """Every skill by strand, in specification order. Tap adds a block."""

    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.background_color = BACKGROUND
        self.all_sections = None
        self.sections = []
        self.heading = make_label("Add skills", 22, bold=True)
        self.done_button = make_button("Done", self.close, filled=True)
        self.search = ui.TextField()
        self.search.placeholder = "Search skills, topics or spec codes"
        self.search.clear_button_mode = "while_editing"
        self.search.autocorrection_type = False
        self.search.spellchecking_type = False
        self.search.delegate = self
        self.status = make_label("Tap a skill to add it to the end of the sheet.", 13, colour=MUTED)
        self.table = ui.TableView()
        self.table.data_source = self
        self.table.delegate = self
        self.table.row_height = 58
        for view in (self.heading, self.done_button, self.search, self.status, self.table):
            self.add_subview(view)

    def layout(self):
        left, width = content_frame(self)
        self.heading.frame = (left, 14, width - 100, 34)
        self.done_button.frame = (left + width - 90, 14, 90, 36)
        self.search.frame = (left, 58, width, 40)
        self.status.frame = (left, 104, width, 22)
        self.table.frame = (0, 132, self.width, max(100, self.height - 132))

    def open(self):
        if self.all_sections is None:
            try:
                level_tags = load_level_tags(self.editor.registry)
                self.all_sections = library_sections(
                    self.editor.registry, level_tags, self.editor.drill_levels)
            except Exception as error:
                self.all_sections = []
                self.status.text = "Library unavailable: " + str(error)
        self.apply_filter()
        self.hidden = False
        self.bring_to_front()

    def apply_filter(self):
        self.sections = filter_sections(self.all_sections or [], self.search.text or "")
        self.table.reload()

    def textfield_did_change(self, textfield):
        self.apply_filter()

    def tableview_number_of_sections(self, tableview):
        return len(self.sections)

    def tableview_title_for_header(self, tableview, section):
        title, entries = self.sections[section]
        return "{} ({})".format(title, len(entries))

    def tableview_number_of_rows(self, tableview, section):
        return len(self.sections[section][1])

    def tableview_cell_for_row(self, tableview, section, row):
        entry = self.sections[section][1][row]
        cell = ui.TableViewCell("subtitle")
        cell.text_label.text = entry["title"]
        cell.detail_text_label.text = entry["detail"]
        cell.detail_text_label.text_color = MUTED
        return cell

    def tableview_did_select(self, tableview, section, row):
        entry = self.sections[section][1][row]
        self.editor.add_block(entry["generator_id"])
        self.status.text = "Added {} as block {}.".format(entry["title"], len(self.editor.blocks))

    def close(self, sender=None):
        self.search.end_editing()
        self.hidden = True
        self.editor.refresh()