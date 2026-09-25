"""Merge well-built generators into one multi-level generator without rewriting them.

A DispatchFamily owns one registered ID. Each of its levels routes to one of
several (source generator, source level) pairs. The source builds and
validates the question exactly as before; the family then relabels it with
its own identity. Use this for generators whose construction, contexts or
drawings are already checked (docs/CONSOLIDATION_PLAN.txt, decision 2);
weak generators should be rewritten instead.

Stored parameters: {"source": name, "source_level": n, "inner": the source's
own parameters}. Validation restores the source's labels and runs the
source's own checks, so the displayed question can never drift from the
source's mathematics, and nothing is checked twice by different code.
"""
from dataclasses import replace

from .core import make_context, require


class DispatchFamily:
    """Subclasses set info, sources ({name: generator}) and routes
    ({level: ((source name, source level), ...)})."""
    info = None
    sources = {}
    routes = {}

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        name, source_level = rng.choice(self.routes[difficulty])
        inner = self.sources[name].generate(rng.getrandbits(63), source_level)
        question = replace(
            inner,
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            tags=self.info.tags,
            parameters={"source": name, "source_level": source_level,
                        "inner": inner.parameters},
        )
        self.validate(question)
        return question

    def unwrap(self, question):
        """The source generator and the question as the source would label it."""
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        require(question.difficulty in self.routes, "Invalid difficulty")
        require(question.topic == self.info.topic and question.subtopic == self.info.subtopic,
                "Topic mismatch")
        require(question.tags == self.info.tags, "Tag mismatch")
        p = question.parameters
        require(isinstance(p, dict) and set(p) == {"source", "source_level", "inner"},
                "Unexpected parameters")
        require((p["source"], p["source_level"]) in self.routes[question.difficulty],
                "Route does not belong to this level")
        source = self.sources[p["source"]]
        inner = replace(
            question,
            generator_id=source.info.id,
            generator_version=source.info.version,
            topic=source.info.topic,
            subtopic=source.info.subtopic,
            difficulty=p["source_level"],
            tags=source.info.tags,
            parameters=p["inner"],
        )
        return source, inner

    def validate(self, question):
        source, inner = self.unwrap(question)
        return source.validate(inner)

    def validate_independently(self, question):
        source, inner = self.unwrap(question)
        return source.validate_independently(inner)


class SourceAwareRegistry:
    """A registry view for tests that exercise source classes directly.

    Source generators behind a DispatchFamily are no longer registered. This
    view serves them under their own IDs (even where a family reuses one of
    those IDs) and defers everything else to the real registry.
    """

    def __init__(self, registry, sources):
        self.registry = registry
        self.sources = dict(sources)

    def get(self, generator_id):
        if generator_id in self.sources:
            return self.sources[generator_id]
        return self.registry.get(generator_id)

    def __getattr__(self, name):
        return getattr(self.registry, name)