"""Measured horizontal choices shared by worksheets and copied question cards."""
from reportlab.platypus import Flowable, Table, TableStyle

from .core import require


class ChoiceGrid(Flowable):
    """Use one row when options fit, otherwise two columns or a full-width list.

    Options retain their font size. Every mathematical item is measured at
    its actual cell width before choosing a layout; expressions never shrink
    or overflow just to preserve the number of columns.
    """

    def __init__(self, question, style, maximum_width):
        Flowable.__init__(self)
        self.question = question
        self.style = style
        self.maximum_width = maximum_width
        self.columns = 0
        self.table = None

    def option_blocks(self, choice):
        from .pdf import MathLine, paragraph
        from .content_rendering import content_flowables
        content = choice.content
        if content.blocks:
            return content_flowables(
                content, self.style["body"], self.question.generator_id + " choice")
        if content.math_tex:
            return [MathLine(content.math_tex, size=12)]
        return [paragraph(content.text, self.style["body"])]

    def build_table(self, width, columns):
        from .pdf import paragraph
        cell_width = width / columns
        label_width = 22
        gap = 10 if columns > 1 else 0
        content_width = cell_width - label_width - gap
        require(content_width > 20, "Choice column is too narrow")
        cells = []
        for index, choice in enumerate(self.question.choices):
            blocks = self.option_blocks(choice)
            for block in blocks:
                minimum = getattr(block, "minWidth", None)
                if minimum is not None:
                    require(minimum() <= content_width,
                            "Choice text is too wide for this column")
                measured_width, measured_height = block.wrapOn(
                    self.canv, content_width, 10000)
                require(measured_width <= content_width + 0.1,
                        "Choice content exceeds its column")
                # Long prose should use fewer columns, rather than form a
                # tall narrow strip beside short mathematical options.
                if columns > 1:
                    require(measured_height <= 48,
                            "Choice needs a wider column")
            cell = Table(
                [[paragraph(chr(65 + index) + ".", self.style["label"]), blocks]],
                colWidths=[label_width, content_width], hAlign="LEFT")
            cell.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            cells.append(cell)
        rows = []
        for start in range(0, len(cells), columns):
            row = cells[start:start + columns]
            rows.append(row + [""] * (columns - len(row)))
        table = Table(rows, colWidths=[cell_width] * columns, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        return table

    def wrap(self, available_width, available_height):
        width = min(available_width, self.maximum_width)
        attempts = list(dict.fromkeys((len(self.question.choices), 2, 1)))
        for columns in attempts:
            try:
                table = self.build_table(width, columns)
                measured = table.wrapOn(self.canv, width, 10000)
            except ValueError:
                if columns == 1:
                    raise
                continue
            self.columns = columns
            self.table = table
            self.width, self.height = measured
            return measured
        raise ValueError("Could not lay out choices")

    def draw(self):
        self.table.drawOn(self.canv, 0, 0)