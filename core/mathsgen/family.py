"""Shared generate/validate flow for parameter-driven generator families.

A subclass supplies:
    info                    GeneratorInfo
    keys                    {level: set of parameter names}
    build(level, rng)       -> exact, JSON-compatible parameters
    check_rules(p, level)   raises ValueError when parameters break the rules
    parts(p, level)         -> dict(prompt, answer, answer_display, marks,
                                    working_lines)
    validate_independently(question)

validate() rebuilds every displayed field from the parameters and requires an
exact match, so a stored question can never drift from its mathematics.
"""
from .core import LayoutHint, Question, make_context, require


class GeneratorFamily:
    info = None
    keys = {}

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        parameters = self.build(difficulty, context.rng)
        parts = self.parts(parameters, difficulty)
        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=parts["prompt"],
            answer=parts["answer"],
            answer_display=parts["answer_display"],
            worked_solution=(),
            marks=parts["marks"],
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=parts["working_lines"]),
            parameters=parameters,
            question_visuals=tuple(parts.get("question_visuals", ())),
            answer_visuals=tuple(parts.get("answer_visuals", ())),
        )
        self.validate(question)
        return question

    def expected_keys(self, parameters, level):
        """Parameter names this question must have.

        The default is keys[level]. A family with several forms per level
        overrides this to return the keys for the question's own form.
        """
        return self.keys[level]

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in self.info.difficulty_descriptions, "Invalid difficulty")
        parameters = question.parameters
        require(isinstance(parameters, dict), "Unexpected parameters")
        require(set(parameters) == self.expected_keys(parameters, level),
                "Unexpected parameters")
        self.check_rules(parameters, level)
        parts = self.parts(parameters, level)
        require(question.prompt == parts["prompt"], "Prompt mismatch")
        require(question.answer == parts["answer"], "Answer mismatch")
        require(question.answer_display == parts["answer_display"], "Displayed answer mismatch")
        require(question.marks == parts["marks"], "Marks mismatch")
        # Optional visuals: parts may supply question_visuals/answer_visuals.
        require(list(question.question_visuals) == list(parts.get("question_visuals", ())),
                "Question visual mismatch")
        require(list(question.answer_visuals) == list(parts.get("answer_visuals", ())),
                "Answer visual mismatch")
        return True