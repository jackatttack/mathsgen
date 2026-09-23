# <tool: Maths Worksheet Maker>
"""Run directly in Pythonista to choose questions and generate worksheet PDFs."""
import copy
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
STATE_PATH = ROOT / "launcher_settings.json"
SAVED_SETUPS = ROOT / "saved_setups"


def load_engine():
    """Refresh the live generator catalogue in Pythonista's shared process."""
    core_path = str(ROOT / "core")
    if core_path not in sys.path:
        sys.path.insert(0, core_path)
    for name in list(sys.modules):
        if name == "mathsgen" or name.startswith("mathsgen."):
            del sys.modules[name]
    from mathsgen.catalogue import build_registry
    return build_registry()


def default_setup():
    return {
        "title": "Maths Practice",
        "shuffle": True,
        "answers": True,
        "seed": "",
        "sections": [],
    }


def parse_levels(text, supported):
    """Accept forms such as 2, 1:3 or 1,3."""
    levels = set()
    for part in text.split(","):
        part = part.strip()
        if ":" in part:
            bounds = part.split(":")
            if len(bounds) != 2:
                raise ValueError("Use levels such as 2, 1:3 or 1,3.")
            first, last = map(int, bounds)
            if first > last or first not in supported or last not in supported:
                raise ValueError("Invalid difficulty range.")
            values = range(first, last + 1)
        else:
            values = [int(part)]
        for value in values:
            if value not in supported:
                raise ValueError("Unsupported difficulty: {}".format(value))
            levels.add(value)
    if not levels:
        raise ValueError("Choose at least one difficulty.")
    return sorted(levels)


def validate_setup(setup, registry, allow_empty=False):
    if not isinstance(setup, dict):
        raise ValueError("The setup must be an object.")
    if not isinstance(setup.get("title"), str) or not setup["title"].strip():
        raise ValueError("Enter a worksheet title.")
    for key in ("shuffle", "answers"):
        if type(setup.get(key)) is not bool:
            raise ValueError("Invalid setting: " + key)
    seed = setup.get("seed")
    if not isinstance(seed, str):
        raise ValueError("Seed must be text or blank.")
    if seed.strip():
        int(seed)
    sections = setup.get("sections")
    if not isinstance(sections, list) or (not sections and not allow_empty):
        raise ValueError("Add at least one question section.")
    for section in sections:
        if not isinstance(section, dict):
            raise ValueError("Invalid section.")
        ids = section.get("generator_ids")
        if not isinstance(ids, list) or len(ids) != 1 or not isinstance(ids[0], str):
            raise ValueError("Each section must select one generator.")
        info = registry.get(ids[0]).info
        count = section.get("count")
        if type(count) is not int or count < 1:
            raise ValueError("Question counts must be positive whole numbers.")
        levels = section.get("difficulties")
        if not isinstance(levels, list) or not levels:
            raise ValueError("Choose difficulty levels.")
        if any(type(level) is not int or level not in info.difficulty_descriptions for level in levels):
            raise ValueError("Unsupported difficulty for " + info.title)
        if len(set(levels)) != len(levels):
            raise ValueError("Repeated difficulty level.")
    return setup


def worksheet_spec(setup):
    return {
        "title": setup["title"].strip(),
        "shuffle": setup["shuffle"],
        "sections": copy.deepcopy(setup["sections"]),
    }


def write_json(path, value):
    """Atomically save settings, preserving the old file if writing fails."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=str(path.parent),
            prefix=".mathsgen_", suffix=".tmp", delete=False,
        ) as output:
            temporary = output.name
            json.dump(value, output, indent=2, ensure_ascii=False)
        os.replace(temporary, str(path))
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def read_json(path):
    with Path(path).open("r", encoding="utf-8") as source:
        return json.load(source)


def choose(dialogs, title, labels):
    selected = dialogs.list_dialog(title, labels)
    return None if selected is None else labels.index(selected)


def show_message(console, title, message):
    console.alert(title, message, "OK", hide_cancel_button=True)


def difficulty_guide(console, info):
    show_message(
        console, info.title,
        "\n\n".join(
            "{}: {}".format(level, description)
            for level, description in sorted(info.difficulty_descriptions.items())
        ),
    )


def edit_section(dialogs, console, info, existing=None):
    existing = existing or {
        "count": 5,
        "difficulties": [min(info.difficulty_descriptions)],
    }
    count_text = str(existing["count"])
    levels_text = ",".join(map(str, existing["difficulties"]))
    while True:
        result = dialogs.form_dialog(
            title=info.title,
            fields=[
                {"type": "text", "key": "count", "title": "Questions", "value": count_text},
                {"type": "text", "key": "levels", "title": "Levels: 1,3 or 2:4", "value": levels_text},
            ],
        )
        if result is None:
            return None
        count_text, levels_text = result["count"], result["levels"]
        try:
            count = int(count_text)
            if count < 1:
                raise ValueError("Enter a positive question count.")
            levels = parse_levels(levels_text, info.difficulty_descriptions)
            return {"generator_ids": [info.id], "count": count, "difficulties": levels}
        except ValueError as error:
            show_message(console, "Check these settings", str(error))


def open_export(dialogs, console, report):
    if not report:
        raise ValueError("Generate a worksheet first.")
    paths = [Path(item["path"]) for item in report["pdfs"]]
    while True:
        index = choose(
            dialogs, "PDFs - seed {}".format(report["seed"]),
            ["Open " + path.stem for path in paths],
        )
        if index is None:
            return
        if not paths[index].is_file():
            raise ValueError("This PDF has been moved or removed.")
        console.quicklook(str(paths[index]))


def main():
    import console
    import dialogs

    registry = load_engine()
    latest_report = None
    try:
        setup = read_json(STATE_PATH) if STATE_PATH.exists() else default_setup()
        validate_setup(setup, registry, allow_empty=True)
    except Exception as error:
        show_message(
            console, "Could not load saved selections",
            str(error) + "\n\nThe saved file has been left unchanged.",
        )
        return

    while True:
        try:
            total = sum(section["count"] for section in setup["sections"])
            action = choose(
                dialogs, "{} - {} questions".format(setup["title"], total),
                [
                    "Generate worksheet PDFs",
                    "Add questions",
                    "Edit or remove a section",
                    "Worksheet settings",
                    "Save this setup",
                    "Load a saved setup",
                    "Open latest PDFs",
                ],
            )
            if action is None:
                return
            candidate = copy.deepcopy(setup)

            if action == 0:
                validate_setup(setup, registry)
                from mathsgen.worksheets import build_worksheet
                from mathsgen.export import export_worksheet

                seed = int(setup["seed"]) if setup["seed"].strip() else secrets.randbits(53)
                console.show_activity("Building worksheet...")
                try:
                    worksheet = build_worksheet(worksheet_spec(setup), seed, registry)
                    report = export_worksheet(
                        worksheet, ROOT / "exports", answers=setup["answers"],
                    )
                finally:
                    console.hide_activity()
                latest_report = report
                show_message(
                    console, "Worksheet ready",
                    "{} questions\nSeed: {}\nSaved in exports/{}".format(
                        len(worksheet.questions), seed, Path(report["directory"]).name
                    ),
                )
                open_export(dialogs, console, report)

            elif action == 1:
                topics = sorted({info.topic for info in registry.list()})
                index = choose(
                    dialogs, "Choose topic",
                    [topic.replace("_", " ").title() for topic in topics],
                )
                if index is None:
                    continue
                infos = registry.list(topics[index])
                index = choose(
                    dialogs, "Choose question type",
                    ["{}. {}".format(i + 1, info.title) for i, info in enumerate(infos)],
                )
                if index is None:
                    continue
                info = infos[index]
                difficulty_guide(console, info)
                section = edit_section(dialogs, console, info)
                if section is None:
                    continue
                candidate["sections"].append(section)

            elif action == 2:
                if not setup["sections"]:
                    raise ValueError("Add some questions first.")
                labels = [
                    "{}. {} questions | {} | levels {}".format(
                        i + 1, section["count"],
                        registry.get(section["generator_ids"][0]).info.title,
                        ",".join(map(str, section["difficulties"])),
                    )
                    for i, section in enumerate(setup["sections"])
                ]
                index = choose(dialogs, "Worksheet sections", labels)
                if index is None:
                    continue
                section = setup["sections"][index]
                info = registry.get(section["generator_ids"][0]).info
                option = choose(dialogs, info.title, [
                    "Change count or levels", "Difficulty guide", "Remove this section",
                ])
                if option is None:
                    continue
                if option == 1:
                    difficulty_guide(console, info)
                    continue
                if option == 2:
                    del candidate["sections"][index]
                else:
                    changed = edit_section(dialogs, console, info, section)
                    if changed is None:
                        continue
                    candidate["sections"][index] = changed

            elif action == 3:
                result = dialogs.form_dialog(
                    title="Worksheet settings",
                    fields=[
                        {"type": "text", "key": "title", "title": "Title", "value": setup["title"]},
                        {"type": "text", "key": "seed", "title": "Seed (blank = new)", "value": setup["seed"]},
                        {"type": "switch", "key": "shuffle", "title": "Mix question order", "value": setup["shuffle"]},
                        {"type": "switch", "key": "answers", "title": "Create answer key", "value": setup["answers"]},
                    ],
                )
                if result is None:
                    continue
                candidate.update(result)

            elif action == 4:
                validate_setup(setup, registry)
                name = dialogs.input_alert("Save setup", "Choose a name.", setup["title"])
                if name is None or not name.strip():
                    continue
                filename = "setup_" + secrets.token_hex(8) + ".json"
                write_json(SAVED_SETUPS / filename, {"name": name.strip(), "setup": setup})
                console.hud_alert("Setup saved", "success")

            elif action == 5:
                records, problems = [], []
                for path in sorted(SAVED_SETUPS.glob("*.json")):
                    try:
                        record = read_json(path)
                        validate_setup(record["setup"], registry)
                        if not isinstance(record["name"], str):
                            raise ValueError("Invalid setup name")
                        records.append(record)
                    except Exception as error:
                        problems.append(path.name + ": " + str(error))
                if problems:
                    show_message(console, "Some setups could not be loaded", "\n".join(problems[:5]))
                if not records:
                    raise ValueError("No usable saved setups. Save a setup first.")
                labels = [
                    "{}. {} ({} questions)".format(
                        i + 1, record["name"],
                        sum(section["count"] for section in record["setup"]["sections"]),
                    )
                    for i, record in enumerate(records)
                ]
                index = choose(dialogs, "Load setup", labels)
                if index is None:
                    continue
                candidate = copy.deepcopy(records[index]["setup"])

            elif action == 6:
                open_export(dialogs, console, latest_report)

            validate_setup(candidate, registry, allow_empty=True)
            if candidate != setup:
                write_json(STATE_PATH, candidate)
                setup = candidate

        except KeyboardInterrupt:
            # Some Pythonista dialogs signal cancellation this way.
            continue
        except Exception as error:
            console.hide_activity()
            show_message(console, "Could not complete that", str(error))


if __name__ == "__main__":
    registry = load_engine()
    from mathsgen.worksheet_ui import present
    worksheet_view = present(registry, ROOT)
