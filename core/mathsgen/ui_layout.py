"""Layout for the Ivory maker: persistent navigation, folded settings, footer.

Views are created elsewhere and only positioned or shown here.
Count actions update local labels without calling this layout.
"""
import ui

from .ui_design import GREEN, SURFACE


def layout_builder(host):
    width = min(max(host.width - 32, 240), 760)
    left = (host.width - width) / 2
    mini = host.mode == "mini"
    exam = host.mode == "exam"
    drill = host.mode == "drill"
    build = host.mode == "build"
    preview = host.report is not None
    show_status = bool(host.status.text) or host.busy
    footer_height = 164 if preview else (124 if show_status else 92)
    bottom = max(100, host.height - footer_height)
    host.heading.frame = (left, 6, width, 26)
    host.mode_control.frame = (left, 38, width, 34)
    top = 82
    host.scroll.frame = (0, top, host.width, max(40, bottom - top))
    host.scroll.scroll_enabled = not (build or drill)
    host.footer.frame = (0, bottom, host.width, footer_height)
    host.total_label.hidden = host.generate_button.hidden = False
    host.total_label.frame = (left, 4, width, 24)
    host.generate_button.frame = (left, 32, width, 44)
    host.status.hidden = not show_status
    host.status.frame = (left, 80, width, 34)
    for index, control in enumerate((
            host.open_questions, host.open_answers, host.save_button)):
        control.hidden = not preview
        control.frame = (left + index * (width + 6) / 3,
                         120, (width - 12) / 3, 36)
        control.font = ("<System-Bold>", 12)
    host.open_questions.title = "Open"
    host.open_answers.title = "Answers"
    host.save_button.title = "Saved" if host.saved_report else "Save"

    # Old controls stay alive for their saved-state and generation contracts.
    for control in host.scroll.subviews:
        control.hidden = True
    if host.workspace is not None:
        host.workspace.hidden = not build
    if host.drill_browser is not None:
        host.drill_browser.hidden = not drill
    if build:
        host.scroll.content_size = (host.width, 0)
        host.show_workspace()
        host.footer.bring_to_front()
        return

    y = 4
    host.subtitle.hidden = drill and not host.settings_open
    host.subtitle.number_of_lines = 2
    host.subtitle.frame = (left, y, width, 34)
    if not host.subtitle.hidden:
        y += 40
    host.settings_button.hidden = False
    title = "Exam paper" if exam else (host.title_field.text.strip() or "Untitled worksheet")
    answers = "Answers on" if host.answers.value else "Answers off"
    if drill:
        levels = ", ".join(str(level) for level in sorted(host.levels))
        host.settings_button.title = "{} Settings · {} per level · L{}".format(
            "▾" if host.settings_open else "▸", host.count_field.text, levels)
    else:
        host.settings_button.title = "{} {} · {}".format(
            "▾" if host.settings_open else "▸", title, answers)
    host.settings_button.frame = (left, y, width, 36)
    y += 44
    if host.settings_open:
        if not exam:
            host.title_field.hidden = False
            host.title_field.frame = (left, y, width, 38)
            y += 46
        host.answers_label.hidden = host.answers.hidden = False
        host.answers_label.frame = (left, y, width - 65, 32)
        host.answers.frame = (left + width - 51, y, 51, 31)
        y += 40
        if drill:
            host.apply_label.hidden = host.apply_switch.hidden = False
            host.apply_label.frame = (left, y, width - 64, 32)
            host.apply_switch.frame = (left + width - 51, y, 51, 31)
            y += 40

    if exam:
        for control in (host.exam_tier_control, host.exam_paper_control):
            control.hidden = False
            control.frame = (left, y, width, 34)
            y += 44
        host.exam_note.hidden = False
        host.exam_note.frame = (left, y, width, 48)
        y += 56
    elif not drill or host.settings_open:
        for control in (host.count_label, host.minus, host.count_field,
                        host.plus, host.count_slider):
            control.hidden = False
        host.count_label.frame = (left, y, width - 144, 36)
        host.minus.frame = (left + width - 140, y, 38, 36)
        host.count_field.frame = (left + width - 98, y, 56, 36)
        host.plus.frame = (left + width - 38, y, 38, 36)
        y += 40
        host.count_slider.frame = (left + 4, y, width - 8, 30)
        y += 38
        if drill:
            host.difficulty_label.hidden = False
            host.difficulty_label.frame = (left, y, 90, 34)
            pill_width = min(49, (width - 96) / 4)
            for index, control in enumerate(host.level_buttons):
                control.hidden = False
                control.frame = (left + width - 4 * pill_width + index * pill_width,
                                 y, pill_width - 5, 34)
            y += 42
        elif mini:
            for control in (host.quick_kind_control, host.quick_choice_control):
                control.hidden = False
                control.frame = (left, y, width, 34)
                y += 44

    if drill or mini:
        host.list_heading.hidden = host.select_all.hidden = host.clear.hidden = False
        host.list_heading.text = "Subjects" if mini else "Skills"
        host.list_heading.text_color = GREEN
        host.list_heading.frame = (left, y, width - 172, 34)
        host.select_all.frame = (left + width - 172, y, 96, 34)
        host.clear.frame = (left + width - 76, y, 76, 34)
        host.select_all.title = "Select shown" if drill else "Select all"
        host.clear.title = "Clear all"
        y += 40
    if drill:
        # Keep room for browsing when settings are expanded on small screens.
        controls_height = min(y, max(100, bottom - top - 160))
        host.scroll.frame = (0, top, host.width, controls_height)
        host.scroll.scroll_enabled = y > controls_height
        host.show_drill_browser(top + controls_height, bottom)
    elif mini:
        for topic in host.topics:
            row, name, detail, tick = host.subject_rows[topic]
            row.hidden = False
            row.frame = (left, y, width, 60)
            tick.frame = (6, 12, 32, 36)
            name.frame = (44, 6, width - 60, 27)
            detail.frame = (44, 33, width - 60, 20)
            y += 68
    host.scroll.content_size = (host.width, y + 12)
    offset = host.scroll.content_offset
    maximum = max(0, y + 12 - host.scroll.height)
    if offset[1] > maximum:
        host.scroll.content_offset = (offset[0], maximum)
    host.footer.bring_to_front()
    if not exam:
        host.update_count_summary()