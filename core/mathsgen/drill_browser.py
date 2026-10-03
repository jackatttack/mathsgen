"""Adapt Drill selection to the same skill browser used by Build."""
from collections import Counter

from .build_model import drill_levels_by_skill, library_sections
from .curriculum import load_level_tags
from .topic_browser import ORDER, groups_for


class DrillBrowserModel:
    """Browser-facing data; the worksheet maker owns selection and saving."""

    def __init__(self, host):
        self.host = host
        self.drill_levels = drill_levels_by_skill(host.registry)
        infos = [info for info in host.infos if info.id in self.drill_levels]
        self.infos = {info.id: info for info in infos}
        self.groups = groups_for(infos)
        present = {info.topic for info in infos}
        self.topics = [topic for topic in ORDER if topic in present]
        self.topics += sorted(present - set(self.topics))
        self.load_error = ""
        sections = library_sections(
            host.registry, load_level_tags(host.registry), self.drill_levels)
        self.entries = {
            entry["generator_id"]: entry
            for _, entries in sections for entry in entries
            if entry["generator_id"] in self.infos
        }

    def counts(self):
        return Counter({key: 1 for key in self.host.drill_selected})

    def toggle_skill(self, generator_id):
        selected = self.host.drill_selected
        if generator_id in selected:
            selected.remove(generator_id)
            added = False
        else:
            selected.add(generator_id)
            added = True
        self.host.update_count_summary()
        self.host.drill_browser.mark_tiles()
        self.host.save()
        return added