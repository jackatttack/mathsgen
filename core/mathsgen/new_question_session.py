"""State and copy pipeline for the optional New Question interface.

The PDF's New action copies before presenting the interface. Subsequent
regenerations use the same question and image pipeline. This module does
not import Pythonista UI, and accepts an injectable clipboard writer so
its state transitions can be tested without modifying the user's clipboard.
"""

from dataclasses import replace
import hashlib
import json
from pathlib import Path

from .core import require
from .question_actions import (
    content_digest,
    new_question,
    render_question_card,
)


class NewQuestionSession:
    def __init__(self, source, registry, token, output_root,
                 clipboard_writer=None, image_converter=None):
        self.source = source
        self.registry = registry
        self.output_root = Path(output_root)
        key = hashlib.sha256(token.encode("ascii")).hexdigest()
        self.state_path = self.output_root / ("last_" + key + ".json")
        self.image_folder = self.output_root / "new_questions" / key
        self.levels = tuple(sorted(
            registry.get(source.generator_id).info.difficulty_descriptions
        ))
        require(bool(self.levels), "Generator has no advertised difficulty levels")
        require(source.difficulty in self.levels,
                "Original question difficulty is not supported")

        self.clipboard_writer = clipboard_writer
        self.image_converter = image_converter
        self.current_question = None
        self.current_png = None
        self.current_size = None
        self.level = source.difficulty

    def _copy_image(self, path):
        writer = self.clipboard_writer
        if writer is None:
            from .pythonista_card_image import copy_png
            writer = copy_png
        writer(path)

    def copy_new(self, level=None):
        """Generate, render and copy; commit the new state only after success."""
        level = self.level if level is None else level
        require(level in self.levels, "Unsupported question difficulty")

        previous = None
        if self.state_path.exists():
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
            previous = state["digest"]

        # Retain the actual worksheet question as the reference. A temporary
        # difficulty change does not alter its seed, prompt or settings.
        generation_source = replace(self.source, difficulty=level)
        question = new_question(
            generation_source,
            self.registry,
            previous=previous,
        )
        digest = content_digest(question, True)

        # Render to a distinct candidate so a failed copy cannot replace
        # the currently displayed question.
        self.image_folder.mkdir(parents=True, exist_ok=True)
        basename = "{}_{}_{}".format(
            level, question.seed, digest[:12]
        )
        pdf_path = self.image_folder / (basename + ".pdf")
        png_path = self.image_folder / (basename + ".png")

        try:
            size = render_question_card(question, pdf_path)
            converter = self.image_converter
            if converter is None:
                from .pythonista_card_image import pdf_to_image
                converter = pdf_to_image

            image = converter(pdf_path, size)
            image.save(str(png_path), "PNG")
            require(png_path.exists() and png_path.stat().st_size > 0,
                    "New question image was not created")

            # Only a successful clipboard copy may advance the session.
            self._copy_image(png_path)
        except Exception:
            pdf_path.unlink(missing_ok=True)
            png_path.unlink(missing_ok=True)
            raise
        finally:
            # The PDF is only an intermediate rasterisation file.
            pdf_path.unlink(missing_ok=True)

        state = {
            "digest": digest,
            "seed": question.seed,
            "generator": question.generator_id,
            "version": question.generator_version,
            "difficulty": question.difficulty,
            "settings": question.settings,
        }
        self.output_root.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(state), encoding="utf-8")
        temporary.replace(self.state_path)

        old_png = self.current_png
        self.current_question = question
        self.current_png = png_path
        self.current_size = image.size
        self.level = level

        # The new preview is committed; the previous image is no longer
        # needed. Never remove the image we have just committed.
        if old_png is not None and old_png != png_path:
            old_png.unlink(missing_ok=True)

        return question, png_path, image.size

    def copy_current(self):
        """Copy exactly the displayed question; do not generate or advance."""
        require(self.current_png is not None,
                "There is no generated question to copy")
        require(self.current_png.exists(),
                "The displayed question image is missing")
        self._copy_image(self.current_png)
        return self.current_question, self.current_png, self.current_size

    def adjacent_level(self, direction):
        """Return the next advertised level, or None at a boundary."""
        require(direction in (-1, 1), "Difficulty direction must be -1 or 1")
        position = self.levels.index(self.level) + direction
        if not 0 <= position < len(self.levels):
            return None
        return self.levels[position]