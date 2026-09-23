"""Quick-copy New Question screen for Pythonista.

Opening New generates and copies first, then presents the result.
Refresh and difficulty changes also generate and copy immediately.
Copy repeats the currently displayed image without regenerating it.
"""

from pathlib import Path

import console
import ui

from .new_question_session import NewQuestionSession


BACKGROUND = "#F2F5FA"
WHITE = "#FFFFFF"
INK = "#1E293B"
MUTED = "#64748B"
ACCENT = "#24658A"
GREEN = "#208363"
BORDER = "#DDE5EF"


def make_label(text, size, colour=INK, bold=False):
    label = ui.Label()
    label.text = text
    label.text_color = colour
    label.font = ("Helvetica-Bold" if bold else "Helvetica", size)
    return label


def make_button(title, action, background=WHITE, tint=ACCENT):
    button = ui.Button(title=title)
    button.font = ("Helvetica-Bold", 15)
    button.background_color = background
    button.tint_color = tint
    button.corner_radius = 12
    button.action = action
    return button


class NewQuestionView(ui.View):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.busy = False
        self.name = "New question"
        self.background_color = BACKGROUND

        self.title_label = make_label("New question", 23, bold=True)
        self.add_subview(self.title_label)

        self.close_button = make_button(
            "Done", self.close_screen, BACKGROUND, ACCENT
        )
        self.add_subview(self.close_button)

        self.description = make_label(
            "Another question from the same generator", 12, MUTED
        )
        self.description.number_of_lines = 2
        self.add_subview(self.description)

        self.status = make_label(
            "Copied to clipboard · ready to paste", 12, GREEN
        )
        self.status.number_of_lines = 2
        self.add_subview(self.status)

        self.preview_card = ui.View()
        self.preview_card.background_color = WHITE
        self.preview_card.corner_radius = 15
        self.add_subview(self.preview_card)

        self.preview_image = ui.ImageView()
        self.preview_image.background_color = WHITE
        self.preview_image.content_mode = ui.CONTENT_SCALE_ASPECT_FIT
        self.preview_card.add_subview(self.preview_image)

        self.level_caption = make_label("DIFFICULTY", 10, MUTED, bold=True)
        self.add_subview(self.level_caption)

        self.down_button = make_button(
            "−", self.go_down, WHITE, ACCENT
        )
        self.add_subview(self.down_button)

        self.level_label = make_label("", 14, INK, bold=True)
        self.level_label.alignment = ui.ALIGN_CENTER
        self.add_subview(self.level_label)

        self.up_button = make_button(
            "+", self.go_up, WHITE, ACCENT
        )
        self.add_subview(self.up_button)

        self.refresh_button = make_button(
            "↻  Refresh", self.refresh, WHITE, ACCENT
        )
        self.add_subview(self.refresh_button)

        self.copy_button = make_button(
            "Copy this question", self.copy_current, GREEN, WHITE
        )
        self.add_subview(self.copy_button)

        self.show_current()

    def show_current(self):
        """The preview always reflects the last successfully copied PNG."""
        path = self.session.current_png
        if path is None:
            raise RuntimeError("No new question has been copied")
        image = ui.Image.from_data(Path(path).read_bytes())
        if image is None:
            raise RuntimeError("Unable to load the generated question preview")

        self.preview_image.image = image
        level = self.session.level
        self.level_label.text = "Level {}  {}".format(
            level, "★" * level
        )

        self.down_button.enabled = (
            self.session.adjacent_level(-1) is not None
        )
        self.up_button.enabled = (
            self.session.adjacent_level(1) is not None
        )
        self.down_button.alpha = 1.0 if self.down_button.enabled else 0.35
        self.up_button.alpha = 1.0 if self.up_button.enabled else 0.35

    def set_busy(self, busy):
        self.busy = busy
        for button in (
            self.down_button,
            self.up_button,
            self.refresh_button,
            self.copy_button,
        ):
            button.enabled = not busy
        if not busy:
            self.show_current()

    def generate(self, level):
        if self.busy:
            return

        self.set_busy(True)
        self.status.text = "Generating and copying..."
        self.status.text_color = MUTED

        try:
            question, path, size = self.session.copy_new(level)
        except Exception as error:
            self.status.text = "Could not copy. Previous question retained."
            self.status.text_color = MUTED
            console.alert(
                "New question failed",
                str(error),
                "OK",
                hide_cancel_button=True,
            )
        else:
            self.status.text = "Copied to clipboard · ready to paste"
            self.status.text_color = GREEN
            print("COPIED:", question.prompt.text)
            print("IMAGE:", size, str(path))
            console.hud_alert("New question copied", "success", 1.0)
        finally:
            self.set_busy(False)

    def refresh(self, sender):
        self.generate(self.session.level)

    def go_down(self, sender):
        level = self.session.adjacent_level(-1)
        if level is not None:
            self.generate(level)

    def go_up(self, sender):
        level = self.session.adjacent_level(1)
        if level is not None:
            self.generate(level)

    def copy_current(self, sender):
        if self.busy:
            return
        self.set_busy(True)
        try:
            question, path, size = self.session.copy_current()
        except Exception as error:
            self.status.text = "Could not copy the displayed question."
            self.status.text_color = MUTED
            console.alert(
                "Copy failed", str(error),
                "OK", hide_cancel_button=True,
            )
        else:
            self.status.text = "Displayed question copied again"
            self.status.text_color = GREEN
            console.hud_alert("Question copied", "success", 1.0)
        finally:
            self.set_busy(False)

    def close_screen(self, sender):
        self.close()

    def layout(self):
        width, height = self.width, self.height
        padding = 16
        content_width = width - 2 * padding

        self.title_label.frame = (
            padding, 13, content_width - 76, 30
        )
        self.close_button.frame = (
            width - padding - 70, 10, 70, 36
        )
        self.description.frame = (
            padding, 47, content_width, 24
        )
        self.status.frame = (
            padding, 78, content_width, 29
        )

        preview_top = 116
        preview_height = max(120, height - 305)
        self.preview_card.frame = (
            padding, preview_top, content_width, preview_height
        )
        self.preview_image.frame = (
            10, 10, content_width - 20, preview_height - 20
        )

        controls_top = height - 166
        self.level_caption.frame = (
            padding, controls_top - 22, 120, 19
        )

        self.down_button.frame = (
            padding, controls_top, 44, 47
        )
        self.level_label.frame = (
            padding + 49, controls_top, 95, 47
        )
        self.up_button.frame = (
            padding + 148, controls_top, 44, 47
        )
        self.refresh_button.frame = (
            width - padding - 113, controls_top, 113, 47
        )
        self.copy_button.frame = (
            padding, height - 75, content_width, 53
        )


def present_new_question(source, registry, token, output_root):
    """Copy first; only then show the optional regeneration interface."""
    session = NewQuestionSession(
        source, registry, token, output_root
    )
    question, png_path, size = session.copy_new()

    print("COPIED:", question.prompt.text)
    print("IMAGE:", size, str(png_path))
    console.hud_alert("New question copied", "success", 1.0)

    width, height = ui.get_screen_size()
    screen = NewQuestionView(session)
    screen.frame = (
        0, 0,
        min(560, width),
        min(780, height - 40),
    )
    screen.present("sheet")
    return screen