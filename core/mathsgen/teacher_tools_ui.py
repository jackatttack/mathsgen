"""Touch-friendly Pythonista interface for question-specific teacher tools.

The main action on each resource copies it immediately. Preview renders
the same resource without modifying the clipboard.

This module is intentionally Pythonista-specific. It is imported only by
the device action handler, not by the portable MathsGen engine.
"""

from pathlib import Path

import console
import ui

from .teacher_tools import available_tools
from .teacher_tool_output import render_tool_image, copy_tool_image


# ---------------------------------------------------------------------------
# Editable presentation settings
# ---------------------------------------------------------------------------

BACKGROUND = "#F5F6FA"
CARD_BACKGROUND = "#FFFFFF"
INK = "#202936"
MUTED = "#64748B"
ACCENT = "#24658A"

ROW_HEIGHT = 76
SIDE_PADDING = 14


class TeacherToolbox(ui.View):
    """Present available tools for one fixed source question.

    Generating or previewing a resource never changes the source question.
    The tool registry determines which resources appear in the interface.
    """

    def __init__(self, question, output_root):
        super().__init__()

        self.question = question
        self.output_root = Path(output_root)
        self.tools = available_tools(question)

        self.name = "MathsGen Teacher Tools"
        self.background_color = BACKGROUND

        self.selected_tool_id = None
        self.tool_rows = []

        self.heading = ui.Label()
        self.heading.text = "Teacher tools"
        self.heading.font = ("Helvetica-Bold", 22)
        self.heading.text_color = INK
        self.add_subview(self.heading)

        self.subtitle = ui.Label()
        self.subtitle.text = (
            "{}  ·  Difficulty {}".format(
                question.generator_id.replace(".", " / "),
                question.difficulty,
            )
        )
        self.subtitle.font = ("Helvetica", 11)
        self.subtitle.text_color = MUTED
        self.subtitle.number_of_lines = 2
        self.add_subview(self.subtitle)

        self.status = ui.Label()
        self.status.text = "Copy a resource or open its preview."
        self.status.font = ("Helvetica", 12)
        self.status.text_color = MUTED
        self.add_subview(self.status)

        self.tool_list = ui.ScrollView()
        self.tool_list.background_color = BACKGROUND
        self.add_subview(self.tool_list)

        for tool in self.tools:
            self.add_tool_row(tool)

        self.preview_title = ui.Label()
        self.preview_title.text = "Preview"
        self.preview_title.font = ("Helvetica-Bold", 15)
        self.preview_title.text_color = INK
        self.add_subview(self.preview_title)

        self.preview_image = ui.ImageView()
        self.preview_image.background_color = CARD_BACKGROUND
        self.preview_image.content_mode = ui.CONTENT_SCALE_ASPECT_FIT
        self.add_subview(self.preview_image)

        self.copy_preview_button = ui.Button(title="Copy preview")
        self.copy_preview_button.font = ("Helvetica-Bold", 14)
        self.copy_preview_button.tint_color = ACCENT
        self.copy_preview_button.enabled = False
        self.copy_preview_button.action = self.copy_selected
        self.add_subview(self.copy_preview_button)

        self.close_button = ui.Button(title="Close")
        self.close_button.tint_color = MUTED
        self.close_button.action = self.close_toolbox
        self.add_subview(self.close_button)

    def add_tool_row(self, tool):
        """Create one resource row without tool-specific UI branching."""

        row = ui.View()
        row.background_color = CARD_BACKGROUND

        name = ui.Label()
        name.text = tool.label
        name.font = ("Helvetica-Bold", 14)
        name.text_color = INK
        name.number_of_lines = 2
        row.add_subview(name)

        category = ui.Label()
        category.text = tool.kind.title()
        category.font = ("Helvetica", 11)
        category.text_color = MUTED
        row.add_subview(category)

        copy_button = ui.Button(title="Copy")
        copy_button.font = ("Helvetica-Bold", 13)
        copy_button.tint_color = ACCENT
        copy_button.action = self.make_copy_action(tool.id)
        row.add_subview(copy_button)

        preview_button = ui.Button(title="Preview")
        preview_button.font = ("Helvetica", 12)
        preview_button.tint_color = ACCENT
        preview_button.action = self.make_preview_action(tool.id)
        row.add_subview(preview_button)

        self.tool_list.add_subview(row)

        self.tool_rows.append((
            row,
            name,
            category,
            copy_button,
            preview_button,
        ))

    def make_copy_action(self, tool_id):
        """Bind a button to one stable tool ID."""

        def action(sender):
            self.copy_tool(tool_id)

        return action

    def make_preview_action(self, tool_id):
        """Bind a preview button without copying anything."""

        def action(sender):
            self.preview_tool(tool_id)

        return action

    def copy_tool(self, tool_id):
        """Run the tool's default action directly into the clipboard."""

        self.status.text = "Preparing resource..."

        try:
            resource, path, size = copy_tool_image(
                self.question,
                tool_id,
                self.output_root,
            )
        except Exception as error:
            self.status.text = "Copy failed."
            console.alert(
                "MathsGen tool failed",
                str(error),
                "OK",
                hide_cancel_button=True,
            )
            return

        self.status.text = "{} copied to clipboard.".format(
            resource.title
        )

        console.hud_alert(
            "{} copied".format(resource.title),
            "success",
            1.0,
        )

    def preview_tool(self, tool_id):
        """Render a preview without modifying the current clipboard."""

        self.status.text = "Preparing preview..."

        try:
            resource, path, size = render_tool_image(
                self.question,
                tool_id,
                self.output_root,
            )

            image = ui.Image.from_data(
                Path(path).read_bytes()
            )

            if image is None:
                raise RuntimeError("Pythonista could not load the preview.")

        except Exception as error:
            self.status.text = "Preview failed."
            console.alert(
                "MathsGen preview failed",
                str(error),
                "OK",
                hide_cancel_button=True,
            )
            return

        self.preview_image.image = image
        self.preview_title.text = resource.title
        self.selected_tool_id = tool_id
        self.copy_preview_button.enabled = True

        self.status.text = "Preview ready. Clipboard unchanged."

    def copy_selected(self, sender):
        """Copy the currently selected preview using its tool defaults."""

        if self.selected_tool_id is None:
            return

        self.copy_tool(self.selected_tool_id)

    def close_toolbox(self, sender):
        self.close()

    def layout(self):
        """Fit the list and preview to the available iPhone/iPad space."""

        width = self.width
        height = self.height

        padding = SIDE_PADDING
        content_width = width - 2 * padding

        self.heading.frame = (
            padding,
            12,
            content_width - 65,
            30,
        )

        self.close_button.frame = (
            width - 75,
            12,
            65,
            30,
        )

        self.subtitle.frame = (
            padding,
            45,
            content_width,
            32,
        )

        self.status.frame = (
            padding,
            78,
            content_width,
            24,
        )

        # Keep the resource list compact when only a few tools exist.
        # As the registry grows, the list becomes independently scrollable.
        desired_list_height = len(self.tools) * ROW_HEIGHT + 8

        available_list_height = max(
            80,
            height * 0.43,
        )

        list_height = min(
            desired_list_height,
            available_list_height,
        )

        self.tool_list.frame = (
            padding,
            108,
            content_width,
            list_height,
        )

        for index, (
            row,
            name,
            category,
            copy_button,
            preview_button,
        ) in enumerate(self.tool_rows):

            row.frame = (
                0,
                index * ROW_HEIGHT,
                content_width,
                ROW_HEIGHT - 5,
            )

            name.frame = (
                10,
                7,
                max(80, content_width - 165),
                25,
            )

            category.frame = (
                10,
                34,
                max(80, content_width - 165),
                22,
            )

            copy_button.frame = (
                content_width - 150,
                7,
                65,
                48,
            )

            preview_button.frame = (
                content_width - 83,
                7,
                78,
                48,
            )

        self.tool_list.content_size = (
            content_width,
            desired_list_height,
        )

        preview_top = 108 + list_height + 9

        self.preview_title.frame = (
            padding,
            preview_top,
            content_width,
            24,
        )

        image_top = preview_top + 27

        self.preview_image.frame = (
            padding,
            image_top,
            content_width,
            max(60, height - image_top - 58),
        )

        self.copy_preview_button.frame = (
            padding,
            height - 46,
            content_width,
            36,
        )


def present_toolbox(question, output_root):
    """Open the Pythonista toolbox for an already validated question."""

    screen_width, screen_height = ui.get_screen_size()

    toolbox = TeacherToolbox(question, output_root)

    toolbox.frame = (
        0,
        0,
        min(560, screen_width),
        min(780, screen_height - 50),
    )

    toolbox.present("sheet")

    return toolbox