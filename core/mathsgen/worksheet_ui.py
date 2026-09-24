"""Single-screen Pythonista worksheet builder driven by the live registry."""
import json
from pathlib import Path
import secrets
import threading

import ui

from .topic_browser import groups_for, matches, topic_style


ACCENT = "#315BE8"
INK = "#182238"
MUTED = "#64748B"
# PDF themes offered in the builder, in segment order (see theme.py).
THEME_CHOICES = ("calm", "classic", "contrast")


def make_spec(registry, selected, count, levels, title, shuffle):
    if type(count) is not int or count < 1:
        raise ValueError("Enter a positive number of questions per type.")
    if not selected:
        raise ValueError("Tick at least one question type.")
    if not levels:
        raise ValueError("Choose at least one difficulty.")
    if not title.strip():
        raise ValueError("Enter a worksheet title.")
    known = {info.id for info in registry.list()}
    if set(selected) - known:
        raise ValueError("Some selected generators are no longer available.")
    sections = []
    for info in registry.list():
        if info.id in selected:
            supported = sorted(set(levels) & set(info.difficulty_descriptions))
            if not supported:
                raise ValueError("No selected difficulty is supported by " + info.title)
            sections.append({
                "generator_ids": [info.id],
                "count": count,
                "difficulties": supported,
            })
    return {"title": title.strip(), "shuffle": bool(shuffle), "sections": sections}


def label(text, size=14, bold=False):
    view = ui.Label()
    view.text = text
    view.font = ("<System-Bold>" if bold else "<System>", size)
    view.text_color = INK
    return view


def button(title, action):
    view = ui.Button()
    view.title = title
    view.action = action
    view.font = ("<System-Bold>", 14)
    view.tint_color = ACCENT
    view.corner_radius = 9
    return view


def field(text, placeholder):
    view = ui.TextField()
    view.text = text
    view.placeholder = placeholder
    view.font = ("<System>", 16)
    view.background_color = "white"
    view.text_color = INK
    view.corner_radius = 8
    view.border_width = 1
    view.border_color = "#DFE5EF"
    return view


class WorksheetBuilder(ui.View):
    def __init__(self, registry, root):
        super().__init__()
        self.name = "Worksheet Maker"
        self.background_color = "#F3F5F9"
        self.registry = registry
        self.root = Path(root)
        self.state_path = self.root / "worksheet_ui_settings.json"
        self.infos = registry.list()
        self.groups = groups_for(self.infos)
        self.expanded_groups = set()
        self.expanded_topics = set()
        self.selected = set()
        self.levels = {1, 2, 3, 4}
        self.busy = False
        self.closed = False
        self.report = None
        self.saved_report = None
        # Each mode keeps its own count; skill selections and subject
        # filters are both preserved while the other mode is shown.
        self.mode = "skills"
        self.per_type_count = 5
        self.mini_total = 12
        self.topics = list(dict.fromkeys(group["topic"] for group in self.groups))
        self.mini_subjects = set(self.topics)
        self.exam_tier = "higher"
        self.exam_paper = 1

        self.scroll = ui.ScrollView()
        self.scroll.always_bounce_vertical = True
        self.add_subview(self.scroll)

        self.heading = label("Build your worksheet", 24, True)
        self.subtitle = label("Tick skills below. Each gets the same question count.", 12)
        self.subtitle.text_color = MUTED
        self.title_field = field("Maths Practice", "Worksheet title")
        self.title_field.delegate = self
        self.count_label = label("Questions per type", 14, True)
        self.minus = button("−", self.change_count)
        self.plus = button("+", self.change_count)
        self.count_field = field("5", "5")
        self.count_field.alignment = ui.ALIGN_CENTER
        # Numbers-and-punctuation keyboard: digits first, with a return key
        # that dismisses it (the number pad has no way to close).
        self.count_field.keyboard_type = ui.KEYBOARD_NUMBERS
        self.count_field.delegate = self
        self.difficulty_label = label("Difficulty", 14, True)
        self.level_buttons = []
        for level in (1, 2, 3, 4):
            item = button(str(level), self.toggle_level)
            item.name = str(level)
            self.level_buttons.append(item)

        self.order = ui.SegmentedControl()
        self.order.segments = ["Set order", "Random"]
        self.order.selected_index = 1
        self.order.tint_color = ACCENT
        self.order.action = self.settings_changed
        self.answers_label = label("Answer key", 13)
        self.answers = ui.Switch()
        self.answers.value = True
        self.answers.tint_color = ACCENT
        self.answers.action = self.settings_changed
        self.theme_label = label("PDF style", 13)
        self.theme_control = ui.SegmentedControl()
        self.theme_control.segments = [name.title() for name in THEME_CHOICES]
        self.theme_control.selected_index = 0
        self.theme_control.tint_color = ACCENT
        self.theme_control.action = self.settings_changed
        self.list_heading = label("QUESTION TYPES", 12, True)
        self.select_all = button("All", self.select_everything)
        self.clear = button("Clear", self.clear_selection)

        self.mode_control = ui.SegmentedControl()
        self.mode_control.segments = ["Skills", "Mini paper", "Exam paper"]
        self.mode_control.selected_index = 0
        self.mode_control.tint_color = ACCENT
        self.mode_control.action = self.change_mode
        self.order_note = label("Order: easier → harder (automatic)", 13)
        self.order_note.text_color = MUTED
        # Exam papers: the builder sets marks, grades, title and order; only
        # the tier and paper number are chosen here.
        self.exam_tier_control = ui.SegmentedControl()
        self.exam_tier_control.segments = ["Foundation", "Higher"]
        self.exam_tier_control.tint_color = ACCENT
        self.exam_tier_control.action = self.change_exam
        self.exam_paper_control = ui.SegmentedControl()
        self.exam_paper_control.segments = ["Paper 1", "Paper 2", "Paper 3"]
        self.exam_paper_control.tint_color = ACCENT
        self.exam_paper_control.action = self.change_exam
        self.exam_note = label("", 12)
        self.exam_note.text_color = MUTED
        self.exam_note.number_of_lines = 2

        for view in [
            self.mode_control, self.order_note,
            self.exam_tier_control, self.exam_paper_control, self.exam_note,
            self.heading, self.subtitle, self.title_field, self.count_label,
            self.minus, self.plus, self.count_field, self.difficulty_label,
            *self.level_buttons, self.order, self.answers_label, self.answers,
            self.theme_label, self.theme_control,
            self.list_heading, self.select_all, self.clear,
        ]:
            self.scroll.add_subview(view)

        self.search_field = field("", "Search skills or topics")
        self.search_field.delegate = self
        self.search_clear = button("Clear", self.clear_search)
        self.scroll.add_subview(self.search_field)
        self.scroll.add_subview(self.search_clear)
        self.empty_label = label("No matching skills. Try a different search.", 13)
        self.empty_label.text_color = MUTED
        self.empty_label.number_of_lines = 2
        self.scroll.add_subview(self.empty_label)

        self.rows = []
        self.topic_labels = {}
        self.topic_header_details = {}
        self.group_headers = {}
        self.group_selection_buttons = {}
        self.row_lookup = {}
        for group in self.groups:
            topic = group["topic"]
            topic_title, colour, tint = topic_style(topic)
            if topic not in self.topic_labels:
                heading = button("", self.toggle_topic)
                heading.name = topic
                heading.background_color = tint
                heading.border_color = colour
                heading.border_width = 1
                title = label("", 16, True)
                title.text_color = colour
                title.number_of_lines = 2
                summary = label("", 11)
                summary.text_color = colour
                for child in (title, summary):
                    child.touch_enabled = False
                    heading.add_subview(child)
                self.topic_labels[topic] = heading
                self.topic_header_details[topic] = (title, summary)
                self.scroll.add_subview(heading)
            header = button("", self.toggle_group)
            header.name = group["key"]
            header.background_color = tint
            name = label("", 14, True)
            name.text_color = colour
            name.number_of_lines = 2
            count = label("", 11)
            count.text_color = colour
            count.alignment = ui.ALIGN_RIGHT
            for child in (name, count):
                child.touch_enabled = False
                header.add_subview(child)
            self.group_headers[group["key"]] = (header, name, count)
            self.scroll.add_subview(header)
            select_group = button("Select all", self.toggle_group_selection)
            select_group.name = group["key"]
            select_group.background_color = tint
            select_group.tint_color = colour
            select_group.font = ("<System-Bold>", 12)
            self.group_selection_buttons[group["key"]] = select_group
            self.scroll.add_subview(select_group)
            for info in group["infos"]:
                row = button("", self.toggle_generator)
                row.name = info.id
                row.border_width = 1
                row.border_color = tint
                title = label(info.title, 14, True)
                title.number_of_lines = 2
                detail = label("", 11)
                detail.number_of_lines = 2
                detail.text_color = MUTED
                tick = label("", 22, True)
                tick.text_color = colour
                tick.alignment = ui.ALIGN_CENTER
                for child in (title, detail, tick):
                    child.touch_enabled = False
                    row.add_subview(child)
                self.scroll.add_subview(row)
                record = (info, row, title, detail, tick)
                self.rows.append(record)
                self.row_lookup[info.id] = record

        self.subject_rows = {}
        for topic in self.topics:
            topic_title, colour, tint = topic_style(topic)
            row = button("", self.toggle_subject)
            row.name = topic
            row.border_width = 1
            name = label(topic_title, 15, True)
            name.text_color = colour
            detail = label("", 11)
            detail.text_color = MUTED
            tick = label("", 22, True)
            tick.text_color = colour
            tick.alignment = ui.ALIGN_CENTER
            for child in (name, detail, tick):
                child.touch_enabled = False
                row.add_subview(child)
            self.scroll.add_subview(row)
            self.subject_rows[topic] = (row, name, detail, tick)

        self.footer = ui.View()
        self.footer.background_color = "#F3F5F9"
        self.add_subview(self.footer)
        self.total_label = label("", 15, True)
        self.generate_button = button("Generate preview", self.generate)
        self.generate_button.background_color = ACCENT
        self.generate_button.tint_color = "white"
        self.generate_button.font = ("<System-Bold>", 17)
        self.status = label("", 12)
        self.status.number_of_lines = 2
        self.status.text_color = MUTED
        self.open_questions = button("Open worksheet", self.open_pdf)
        self.open_questions.name = "questions"
        self.open_answers = button("Open answers", self.open_pdf)
        self.open_answers.name = "answers"
        self.open_questions.enabled = False
        self.open_answers.enabled = False
        self.save_button = button("Save worksheet", self.save_worksheet)
        self.save_button.background_color = "white"
        self.save_button.enabled = False
        for view in (
            self.total_label, self.generate_button, self.status,
            self.open_questions, self.open_answers, self.save_button,
        ):
            self.footer.add_subview(view)
        self.restore()
        self.refresh()

    def layout(self):
        width = min(max(self.width - 32, 240), 760)
        left = (self.width - width) / 2
        has_preview = self.report is not None
        show_status = bool(self.status.text) or self.busy
        footer_height = 214 if has_preview else (132 if show_status else 96)
        self.status.hidden = not show_status
        for control in (self.open_questions, self.open_answers, self.save_button):
            control.hidden = not has_preview
        self.scroll.frame = (0, 0, self.width, max(100, self.height - footer_height))
        mini = self.mode == "mini"
        exam = self.mode == "exam"
        # Exam mode replaces the title, count and difficulty rows with the
        # tier and paper choices; the builder sets everything else.
        for view in (self.title_field, self.count_label, self.minus, self.plus,
                     self.count_field, self.difficulty_label, *self.level_buttons):
            view.hidden = exam
        for view in (self.exam_tier_control, self.exam_paper_control, self.exam_note):
            view.hidden = not exam
        self.exam_tier_control.frame = (left, 114, width, 34)
        self.exam_paper_control.frame = (left, 158, width, 34)
        self.exam_note.frame = (left, 198, width, 44)
        self.heading.frame = (left, 12, width, 30)
        self.mode_control.frame = (left, 48, width, 32)
        self.subtitle.frame = (left, 84, width, 24)
        self.title_field.frame = (left, 114, width, 40)
        self.count_label.frame = (left, 168, width - 144, 34)
        self.minus.frame = (left + width - 140, 166, 38, 38)
        self.count_field.frame = (left + width - 98, 166, 56, 38)
        self.plus.frame = (left + width - 38, 166, 38, 38)
        self.difficulty_label.frame = (left, 216, 100, 34)
        pill_width = min(49, (width - 104) / 4)
        for index, item in enumerate(self.level_buttons):
            item.frame = (left + width - 4 * pill_width + index * pill_width,
                          216, pill_width - 5, 34)
        # Mini papers always run easier to harder, so the order control is
        # replaced by a note rather than silently ignored.
        self.order.hidden = mini or exam
        self.order_note.hidden = not mini
        self.order.frame = (left, 264, width, 34)
        self.order_note.frame = (left, 264, width, 34)
        settings_y = 250 if exam else 310
        self.answers_label.frame = (left, settings_y, 130, 32)
        self.answers.frame = (left + width - 51, settings_y, 51, 32)
        self.theme_label.frame = (left, settings_y + 46, 110, 34)
        self.theme_control.frame = (left + width - 230, settings_y + 46, 230, 34)
        self.list_heading.text = "SUBJECTS" if mini else "SKILLS"
        self.list_heading.frame = (left, 404, width - 165, 32)
        self.select_all.frame = (left + width - 165, 402, 90, 36)
        self.clear.frame = (left + width - 75, 402, 75, 36)
        self.clear.title = "Clear all"
        self.search_field.hidden = mini or exam
        self.search_clear.hidden = mini or exam
        for view in (self.list_heading, self.select_all, self.clear):
            view.hidden = exam
        self.search_field.frame = (left, 444, width - 64, 40)
        self.search_clear.frame = (left + width - 60, 444, 60, 40)
        query = self.search_field.text or ""
        searching = bool(query.strip()) and not mini
        self.search_clear.enabled = searching
        self.select_all.title = "All shown" if searching else "Select all"
        for row, name, detail, tick in self.subject_rows.values():
            row.hidden = True

        for heading in self.topic_labels.values():
            heading.hidden = True
        for header, name, count in self.group_headers.values():
            header.hidden = True
        for control in self.group_selection_buttons.values():
            control.hidden = True
        for info, row, title, detail, tick in self.rows:
            row.hidden = True
        if exam:
            self.empty_label.hidden = True
            self.finish_layout(settings_y + 92, left, width, footer_height)
            return
        if mini:
            # Individual skill selections stay hidden but preserved.
            y = 444
            for topic in self.topics:
                row, name, detail, tick = self.subject_rows[topic]
                row.hidden = False
                row.frame = (left, y, width, 58)
                tick.frame = (6, 11, 32, 36)
                name.frame = (44, 6, width - 64, 26)
                detail.frame = (44, 32, width - 64, 20)
                y += 64
            self.empty_label.hidden = True
            self.finish_layout(y, left, width, footer_height)
            return
        y = 500
        shown_topics = set()
        match_count = 0
        for group in self.groups:
            visible = [info for info in group["infos"] if matches(info, query)]
            if not visible:
                continue
            match_count += len(visible)
            topic = group["topic"]
            topic_opened = searching or topic in self.expanded_topics
            if topic not in shown_topics:
                heading = self.topic_labels[topic]
                heading.hidden = False
                # Compact card: the count sits on the title line, right-aligned.
                heading.frame = (left, y, width, 52)
                title, summary = self.topic_header_details[topic]
                title.frame = (12, 4, width - 150, 44)
                summary.frame = (width - 142, 4, 130, 44)
                summary.alignment = ui.ALIGN_RIGHT
                title.text = ("▾ " if topic_opened else "▸ ") + topic_style(topic)[0]
                topic_infos = [info for info in self.infos if info.topic == topic]
                selected_count = sum(info.id in self.selected for info in topic_infos)
                summary.text = "{}/{} selected".format(selected_count, len(topic_infos))
                if searching:
                    summary.text += " · {} matching".format(
                        sum(matches(info, query) for info in topic_infos)
                    )
                y += 58
                shown_topics.add(topic)
            if not topic_opened:
                continue
            key = group["key"]
            opened = searching or key in self.expanded_groups
            header, name, count = self.group_headers[key]
            header.hidden = False
            # Indented under its topic, with the count on the title line.
            header.frame = (left + 10, y, width - 112, 48)
            name.frame = (12, 4, width - 208, 40)
            count.frame = (width - 192, 4, 70, 40)
            count.alignment = ui.ALIGN_RIGHT
            name.text = ("▾ " if opened else "▸ ") + group["title"]
            selected = sum(info.id in self.selected for info in group["infos"])
            count.text = "{}/{} selected".format(selected, len(group["infos"]))
            control = self.group_selection_buttons[key]
            control.hidden = False
            control.frame = (left + width - 96, y + 4, 96, 40)
            all_selected = all(info.id in self.selected for info in visible)
            if searching:
                control.title = "Clear shown" if all_selected else "All shown"
            else:
                control.title = "Clear" if all_selected else "Select all"
            y += 54
            if opened:
                for info in visible:
                    _, row, title, detail, tick = self.row_lookup[info.id]
                    row.hidden = False
                    row.frame = (left + 20, y, width - 20, 64)
                    tick.frame = (6, 14, 32, 36)
                    title.frame = (44, 6, width - 76, 30)
                    detail.frame = (44, 36, width - 76, 22)
                    y += 70
            y += 8
        self.empty_label.hidden = match_count != 0
        self.empty_label.frame = (left, y, width, 48)
        if not match_count:
            y += 56
        self.finish_layout(y, left, width, footer_height)

    def finish_layout(self, y, left, width, footer_height):
        """Size the scroll content and place the fixed footer."""
        self.scroll.content_size = (self.width, y + 12)
        old_x, old_y = self.scroll.content_offset
        maximum_y = max(0, y + 12 - self.scroll.height)
        if old_y > maximum_y:
            self.scroll.content_offset = (old_x, maximum_y)
        self.footer.frame = (0, self.height - footer_height, self.width, footer_height)
        self.total_label.frame = (left, 5, width, 26)
        self.generate_button.frame = (left, 36, width, 46)
        self.status.frame = (left, 85, width, 36)
        self.open_questions.frame = (left, 124, width / 2 - 4, 36)
        self.open_answers.frame = (left + width / 2 + 4, 124, width / 2 - 4, 36)
        self.save_button.frame = (left, 165, width, 36)

    def restore(self):
        if not self.state_path.exists():
            return
        try:
            with self.state_path.open("r", encoding="utf-8") as source:
                state = json.load(source)
            selected = state["selected"]
            levels = state["levels"]
            count = state["count"]
            if not isinstance(selected, list) or not all(isinstance(x, str) for x in selected):
                raise ValueError("Invalid selections")
            if not isinstance(levels, list) or not levels or any(type(x) is not int or x not in (1, 2, 3, 4) for x in levels):
                raise ValueError("Invalid levels")
            if type(count) is not int or count < 1 or not isinstance(state["title"], str):
                raise ValueError("Invalid settings")
            self.selected = set(selected) & {info.id for info in self.infos}
            self.levels = set(levels)
            self.count_field.text = str(count)
            self.title_field.text = state["title"]
            self.order.selected_index = 1 if state.get("shuffle", True) else 0
            self.answers.value = bool(state.get("answers", True))
            theme = state.get("theme", "calm")
            self.theme_control.selected_index = (
                THEME_CHOICES.index(theme) if theme in THEME_CHOICES else 0
            )
            self.per_type_count = count
            mini_total = state.get("mini_total", 12)
            if type(mini_total) is int and mini_total >= 1:
                self.mini_total = mini_total
            subjects = state.get("mini_subjects")
            if isinstance(subjects, list) and all(isinstance(x, str) for x in subjects):
                self.mini_subjects = set(subjects) & set(self.topics)
            tier = state.get("exam_tier")
            if tier in ("foundation", "higher"):
                self.exam_tier = tier
            paper = state.get("exam_paper")
            if type(paper) is int and paper in (1, 2, 3):
                self.exam_paper = paper
            if state.get("mode") == "mini":
                self.mode = "mini"
                self.mode_control.selected_index = 1
                self.count_field.text = str(self.mini_total)
            elif state.get("mode") == "exam":
                self.mode = "exam"
                self.mode_control.selected_index = 2
            expanded = state.get("expanded_groups", [])
            if isinstance(expanded, list) and all(isinstance(key, str) for key in expanded):
                self.expanded_groups = set(expanded) & set(self.group_headers)
            topics = state.get("expanded_topics", [])
            if isinstance(topics, list) and all(isinstance(key, str) for key in topics):
                self.expanded_topics = set(topics) & set(self.topic_labels)
        except Exception as error:
            self.status.text = "Could not restore settings: " + str(error)

    def save(self):
        try:
            self.store_count()
            from launch_mathsgen import write_json
            write_json(self.state_path, {
                "selected": sorted(self.selected),
                "levels": sorted(self.levels),
                "count": self.per_type_count,
                "mode": self.mode,
                "mini_total": self.mini_total,
                "mini_subjects": sorted(self.mini_subjects),
                "exam_tier": self.exam_tier,
                "exam_paper": self.exam_paper,
                "title": self.title_field.text,
                "shuffle": self.order.selected_index == 1,
                "answers": self.answers.value,
                "theme": THEME_CHOICES[self.theme_control.selected_index],
                "expanded_groups": sorted(self.expanded_groups),
                "expanded_topics": sorted(self.expanded_topics),
            })
        except Exception as error:
            self.status.text = "Could not save selections: " + str(error)

    def refresh(self):
        try:
            count = int(self.count_field.text)
            valid = count > 0
        except ValueError:
            count, valid = 0, False
        mini = self.mode == "mini"
        exam = self.mode == "exam"
        self.count_label.text = "Total questions" if mini else "Questions per type"
        if exam:
            self.subtitle.text = "Edexcel-style: 80 marks, weighted by strand, easiest first."
        else:
            self.subtitle.text = (
                "A balanced paper that gets harder as it goes." if mini
                else "Tick skills below. Each gets the same question count."
            )
        if not self.busy:
            self.generate_button.title = (
                "Generate exam paper" if exam
                else "Generate mini paper" if mini else "Generate preview"
            )
        self.exam_tier_control.selected_index = 0 if self.exam_tier == "foundation" else 1
        self.exam_paper_control.selected_index = self.exam_paper - 1
        calculator = "non-calculator" if self.exam_paper == 1 else "calculator allowed"
        self.exam_note.text = (
            "Paper {} is {}. Title, questions, marks and order are set automatically."
        ).format(self.exam_paper, calculator)
        if exam:
            self.total_label.text = "{} · Paper {} · 80 marks".format(
                self.exam_tier.title(), self.exam_paper)
            can_generate = True
        elif mini:
            self.total_label.text = "{} questions · {} of {} subjects".format(
                count, len(self.mini_subjects), len(self.topics)
            )
            can_generate = bool(valid and self.mini_subjects and self.levels)
        else:
            self.total_label.text = "{} types × {} each = {} questions".format(
                len(self.selected), count, count * len(self.selected)
            )
            can_generate = bool(valid and self.selected and self.levels)
        self.generate_button.enabled = can_generate and not self.busy
        self.generate_button.alpha = 1 if self.generate_button.enabled else 0.45
        ready = self.report is not None and not self.busy
        self.open_questions.enabled = ready
        self.open_answers.enabled = ready and any(
            item["mode"] == "answers" for item in self.report["pdfs"]
        )
        self.save_button.enabled = ready and self.saved_report is None
        self.save_button.title = "Saved to exports" if self.saved_report else "Save worksheet"
        self.save_button.alpha = 1 if self.save_button.enabled else 0.45
        for item in self.level_buttons:
            active = int(item.name) in self.levels
            item.background_color = ACCENT if active else "white"
            item.tint_color = "white" if active else ACCENT
        for topic, (row, name, detail, tick) in self.subject_rows.items():
            active = topic in self.mini_subjects
            colour, tint = topic_style(topic)[1:]
            row.background_color = tint if active else "white"
            row.border_color = colour if active else tint
            tick.text = "✓" if active else "○"
            detail.text = "{} skills".format(sum(info.topic == topic for info in self.infos))
        for info, row, title, detail, tick in self.rows:
            active = info.id in self.selected
            colour, tint = topic_style(info.topic)[1:]
            row.background_color = tint if active else "white"
            row.border_color = colour if active else tint
            tick.text = "✓" if active else "○"
            supported = sorted(self.levels & set(info.difficulty_descriptions))
            if len(supported) == 1:
                detail.text = info.difficulty_descriptions[supported[0]]
            elif supported:
                detail.text = "Difficulty " + ", ".join(map(str, supported))
            else:
                detail.text = "Choose a supported difficulty."
        self.layout()

    def toggle_topic(self, sender):
        """Fold a subject without changing its selections or nested groups."""
        if (self.search_field.text or "").strip():
            self.status.text = "Clear search to collapse subjects."
            self.layout()
            return
        topic = sender.name
        if topic not in self.topic_labels:
            return
        if topic in self.expanded_topics:
            self.expanded_topics.remove(topic)
        else:
            self.expanded_topics.add(topic)
        self.layout()
        self.save()

    def toggle_group(self, sender):
        if (self.search_field.text or "").strip():
            self.status.text = "Clear search to collapse groups."
            return
        key = sender.name
        if key in self.expanded_groups:
            self.expanded_groups.remove(key)
        else:
            self.expanded_groups.add(key)
        self.layout()
        self.save()

    def toggle_group_selection(self, sender):
        group = next((item for item in self.groups
                      if item["key"] == sender.name), None)
        if group is None:
            return
        query = self.search_field.text or ""
        targets = {info.id for info in group["infos"] if matches(info, query)}
        if not targets:
            return
        if targets <= self.selected:
            self.selected.difference_update(targets)
        else:
            self.selected.update(targets)
        self.settings_changed(sender)

    def clear_search(self, sender):
        self.search_field.text = ""
        self.search_field.end_editing()
        self.refresh()

    def settings_changed(self, sender):
        self.refresh()
        self.save()

    def textfield_did_change(self, textfield):
        self.refresh()

    def textfield_did_end_editing(self, textfield):
        self.settings_changed(textfield)

    def textfield_should_return(self, textfield):
        textfield.end_editing()
        return True

    def change_count(self, sender):
        try:
            count = int(self.count_field.text)
        except ValueError:
            count = 5
        self.count_field.text = str(max(1, count + (1 if sender is self.plus else -1)))
        self.settings_changed(sender)

    def toggle_level(self, sender):
        level = int(sender.name)
        if level in self.levels:
            if len(self.levels) == 1:
                self.status.text = "Keep at least one difficulty selected."
                return
            self.levels.remove(level)
        else:
            self.levels.add(level)
        self.settings_changed(sender)

    def toggle_generator(self, sender):
        if sender.name in self.selected:
            self.selected.remove(sender.name)
        else:
            self.selected.add(sender.name)
        self.settings_changed(sender)

    def select_everything(self, sender):
        if self.mode == "mini":
            self.mini_subjects = set(self.topics)
        else:
            query = self.search_field.text or ""
            self.selected.update(info.id for info in self.infos if matches(info, query))
        self.settings_changed(sender)

    def clear_selection(self, sender):
        if self.mode == "mini":
            self.mini_subjects.clear()
        else:
            self.selected.clear()
        self.settings_changed(sender)

    def store_count(self):
        """Keep the visible count in the current mode's own setting."""
        try:
            count = int(self.count_field.text)
        except ValueError:
            return
        if count < 1 or self.mode == "exam":
            return
        if self.mode == "mini":
            self.mini_total = count
        else:
            self.per_type_count = count

    def change_mode(self, sender):
        """Switch modes, preserving each mode's count and selections."""
        self.store_count()
        self.mode = ("skills", "mini", "exam")[self.mode_control.selected_index]
        self.count_field.text = str(self.mini_total if self.mode == "mini" else self.per_type_count)
        self.status.text = ""
        self.settings_changed(sender)

    def change_exam(self, sender):
        """Tier and paper choices for exam mode."""
        self.exam_tier = ("foundation", "higher")[self.exam_tier_control.selected_index]
        self.exam_paper = self.exam_paper_control.selected_index + 1
        self.settings_changed(sender)

    def toggle_subject(self, sender):
        if sender.name in self.mini_subjects:
            self.mini_subjects.remove(sender.name)
        else:
            self.mini_subjects.add(sender.name)
        self.settings_changed(sender)

    def generate(self, sender):
        if self.busy:
            return
        self.title_field.end_editing()
        self.count_field.end_editing()
        self.search_field.end_editing()
        mini = self.mode == "mini"
        exam = self.mode == "exam"
        tier, paper = self.exam_tier, self.exam_paper
        try:
            title = self.title_field.text.strip()
            if exam:
                spec = None
            elif mini:
                total = int(self.count_field.text)
                if total < 1:
                    raise ValueError("Enter a positive total number of questions.")
                if not self.mini_subjects:
                    raise ValueError("Include at least one subject.")
                if not title:
                    raise ValueError("Enter a worksheet title.")
                levels, subjects, spec = sorted(self.levels), sorted(self.mini_subjects), None
            else:
                spec = make_spec(
                    self.registry, self.selected, int(self.count_field.text),
                    self.levels, self.title_field.text, self.order.selected_index == 1,
                )
        except Exception as error:
            self.status.text = str(error)
            return
        self.save()
        include_answers = self.answers.value
        theme = THEME_CHOICES[self.theme_control.selected_index]
        self.busy = True
        self.generate_button.title = "Generating…"
        self.status.text = "Building questions and PDFs…"
        self.refresh()
        seed = secrets.randbits(53)

        def work():
            try:
                from .preview import create_preview
                if exam:
                    from .exam_paper import build_exam_paper
                    worksheet = build_exam_paper(self.registry, tier, paper, seed)
                elif mini:
                    from .mini_paper import build_mini_paper
                    worksheet = build_mini_paper(
                        self.registry, total, levels, subjects, title, seed,
                    )
                else:
                    from .worksheets import build_worksheet
                    worksheet = build_worksheet(spec, seed, self.registry)
                # One place sets the PDF theme, for skill sets and mini papers alike.
                from dataclasses import replace as with_changes
                worksheet = with_changes(worksheet, specification=dict(
                    worksheet.specification, theme=theme))
                report = create_preview(worksheet, answers=include_answers)
            except Exception as error:
                message = str(error)
                ui.delay(lambda message=message: self.finished(None, message), 0)
            else:
                ui.delay(lambda report=report: self.finished(report, None), 0)

        threading.Thread(target=work, daemon=True).start()

    def finished(self, report, error):
        if self.closed:
            return
        self.busy = False

        if error:
            self.status.text = "Could not generate: " + error
        else:
            self.report = report
            self.saved_report = None
            self.status.text = "Preview: {} questions. Open to share, or Save to keep.".format(
                report["question_count"]
            )
            self.open_questions.enabled = True
            self.open_answers.enabled = any(item["mode"] == "answers" for item in report["pdfs"])
        self.refresh()

    def save_worksheet(self, sender):
        if self.busy or self.report is None or self.saved_report is not None:
            return
        report = self.report
        self.busy = True
        self.status.text = "Saving the previewed PDFs..."
        self.refresh()

        def work():
            try:
                from .preview import save_preview
                saved = save_preview(report, self.root / "exports")
            except Exception as error:
                message = str(error)
                ui.delay(
                    lambda message=message: self.save_finished(None, message), 0
                )
            else:
                ui.delay(lambda saved=saved: self.save_finished(saved, None), 0)

        threading.Thread(target=work, daemon=True).start()

    def save_finished(self, report, error):
        if self.closed:
            return
        self.busy = False
        if error:
            self.status.text = "Could not save; preview retained: " + error
        else:
            self.saved_report = report
            self.report = report
            self.status.text = "Saved in exports/" + Path(report["directory"]).name
        self.refresh()

    @ui.in_background
    def open_pdf(self, sender):
        import console
        if not self.report:
            return
        for item in self.report["pdfs"]:
            if item["mode"] == sender.name:
                try:
                    console.quicklook(item["path"])
                except Exception as error:
                    message = str(error)
                    ui.delay(lambda message=message: setattr(self.status, "text", message), 0)
                return

    def will_close(self):
        self.closed = True
        self.save()


def present(registry, root):
    view = WorksheetBuilder(registry, root)
    view.present("fullscreen")
    return view