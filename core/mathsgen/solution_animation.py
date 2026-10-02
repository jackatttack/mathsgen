"""Animated worked solutions: a question's steps revealed one at a time.

Portable: imports Matplotlib and Pillow only, never ui, console, photos or
objc_util, so the same GIF can later serve the website.

Contract
- Input: a prompt Content and a sequence of step Contents, as found on
  Question.prompt and Question.worked_solution.
- A step with math_tex shows its explanation as a small caption above the
  equation. A step without math_tex (such as a final check) shows its text.
- Output: GIF bytes. Every frame has the same size. Frame k shows the prompt
  and the first k steps, with the newest caption highlighted.
- Text too wide for the image raises ValueError rather than being clipped.
"""
from io import BytesIO


# --- Editable settings ---------------------------------------------------

IMAGE_WIDTH_INCHES = 6.0
DPI = 150
LEFT_MARGIN = 0.07              # fraction of image width
TOP_MARGIN_INCHES = 0.35
BOTTOM_MARGIN_INCHES = 0.3
PROMPT_HEIGHT_INCHES = 1.0      # label + equation + divider
STEP_HEIGHT_INCHES = 0.85       # caption + equation
TEXT_STEP_HEIGHT_INCHES = 0.5   # a step with no equation
EQUATION_OFFSET_INCHES = 0.26   # gap between a caption and its equation

PROMPT_LABEL_SIZE = 12
CAPTION_SIZE = 10.5
EQUATION_SIZE = 19
TEXT_STEP_SIZE = 12

FIRST_FRAME_MS = 1500           # the question alone
STEP_FRAME_MS = 1700
FINAL_FRAME_MS = 3500           # the finished solution, before looping
PALETTE_COLOURS = 64

BACKGROUND = "#FFFFFF"
INK = "#17212B"
EARLIER_CAPTION = "#8A94A0"
NEWEST_CAPTION = "#2F6FDB"
DIVIDER = "#D5DAE0"
FONT_FAMILY = "DejaVu Sans"     # matches pdf.math_outline


# --- Public API ----------------------------------------------------------

def animate_question(question):
    """Return GIF bytes for a Question that has worked steps."""
    if not question.worked_solution:
        raise ValueError("Question {} has no worked solution to animate".format(
            question.generator_id))
    return animate_worked_solution(question.prompt, question.worked_solution)


def animate_worked_solution(prompt, steps):
    """Return GIF bytes revealing each step beneath the prompt."""
    steps = tuple(steps)
    if not steps:
        raise ValueError("A worked solution needs at least one step")

    height = image_height_inches(prompt, steps)
    frames = [
        render_frame(prompt, steps, shown, height)
        for shown in range(len(steps) + 1)
    ]
    durations = frame_durations(len(frames))
    return encode_gif(frames, durations)


# --- Layout --------------------------------------------------------------

def image_height_inches(prompt, steps):
    """Fixed height for every frame, sized for the complete solution."""
    height = TOP_MARGIN_INCHES + PROMPT_HEIGHT_INCHES + BOTTOM_MARGIN_INCHES
    for step in steps:
        height += STEP_HEIGHT_INCHES if step.math_tex else TEXT_STEP_HEIGHT_INCHES
    return height


def frame_durations(frame_count):
    durations = [STEP_FRAME_MS] * frame_count
    durations[0] = FIRST_FRAME_MS
    durations[-1] = FINAL_FRAME_MS
    return durations


def label_of(content):
    """Short visible label: display_text when the generator supplies one."""
    return getattr(content, "display_text", None) or content.text


def plain(text):
    """Stop Matplotlib reading a literal dollar sign as mathtext."""
    return text.replace("$", r"\$")


def math(tex):
    return "$" + tex + "$"


# --- Rendering -----------------------------------------------------------

def render_frame(prompt, steps, shown_count, height_inches):
    """Draw the prompt and the first shown_count steps as an RGB image."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    from matplotlib.lines import Line2D

    figure = Figure(figsize=(IMAGE_WIDTH_INCHES, height_inches), dpi=DPI,
                    facecolor=BACKGROUND)
    canvas = FigureCanvasAgg(figure)
    placed = []

    def y_fraction(y_inches):
        return 1 - y_inches / height_inches

    def place(y_inches, string, size, colour):
        placed.append(figure.text(
            LEFT_MARGIN, y_fraction(y_inches), string, fontsize=size,
            color=colour, va="top", ha="left", family=FONT_FAMILY,
        ))

    y = TOP_MARGIN_INCHES
    place(y, plain(label_of(prompt)), PROMPT_LABEL_SIZE, INK)
    if prompt.math_tex:
        place(y + EQUATION_OFFSET_INCHES, math(prompt.math_tex), EQUATION_SIZE, INK)
    y += PROMPT_HEIGHT_INCHES
    divider_y = y_fraction(y - 0.12)
    figure.add_artist(Line2D([LEFT_MARGIN, 1 - LEFT_MARGIN], [divider_y, divider_y],
                             color=DIVIDER, linewidth=1,
                             transform=figure.transFigure))

    for index, step in enumerate(steps[:shown_count]):
        newest = index == shown_count - 1
        caption_colour = NEWEST_CAPTION if newest else EARLIER_CAPTION
        if step.math_tex:
            place(y, plain(label_of(step)), CAPTION_SIZE, caption_colour)
            place(y + EQUATION_OFFSET_INCHES, math(step.math_tex), EQUATION_SIZE, INK)
            y += STEP_HEIGHT_INCHES
        else:
            place(y, plain(label_of(step)), TEXT_STEP_SIZE,
                  NEWEST_CAPTION if newest else INK)
            y += TEXT_STEP_HEIGHT_INCHES

    canvas.draw()
    refuse_overwide_text(placed, canvas)
    return canvas_to_image(canvas)


def refuse_overwide_text(texts, canvas):
    """Rendering bounds failures stay visible (QUESTION_SUPPORT_GUIDE)."""
    renderer = canvas.get_renderer()
    limit = IMAGE_WIDTH_INCHES * DPI * (1 - LEFT_MARGIN / 2)
    for text in texts:
        if text.get_window_extent(renderer=renderer).x1 > limit:
            raise ValueError("Too wide for the animation: " + text.get_text())


def canvas_to_image(canvas):
    from PIL import Image

    buffer = BytesIO()
    canvas.print_png(buffer)
    buffer.seek(0)
    image = Image.open(buffer)
    image.load()
    return image.convert("RGB")


def encode_gif(frames, durations):
    from PIL import Image

    paletted = [
        frame.convert("P", palette=Image.ADAPTIVE, colors=PALETTE_COLOURS)
        for frame in frames
    ]
    buffer = BytesIO()
    paletted[0].save(buffer, format="GIF", save_all=True,
                     append_images=paletted[1:], duration=durations, loop=0)
    return buffer.getvalue()