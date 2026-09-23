"""Command interface accepting argv for Forge, tests and future apps."""
import argparse
import json

from .catalogue import build_registry
from .validation import validate_many


def positive_integer(text):
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def parser():
    root = argparse.ArgumentParser(
        prog="mathsgen",
        description="Generate exact, reproducible GCSE maths questions.",
    )
    commands = root.add_subparsers(dest="command", required=True)

    topics = commands.add_parser("topics", help="List implemented topics")
    topics.add_argument("--json", action="store_true")

    generators = commands.add_parser("generators", help="List implemented generators")
    generators.add_argument("topic", nargs="?")
    generators.add_argument("--json", action="store_true")

    info = commands.add_parser("info", help="Inspect a generator and its difficulties")
    info.add_argument("generator_id")
    info.add_argument("--json", action="store_true")

    sample = commands.add_parser("sample", help="Generate reproducible examples")
    sample.add_argument("generator_id")
    sample.add_argument("--count", type=positive_integer, default=1)
    sample.add_argument("--difficulty", type=int, default=1)
    sample.add_argument("--seed", type=int, default=0)
    sample.add_argument("--worked", action="store_true")
    sample.add_argument("--json", action="store_true")

    validate = commands.add_parser("validate", help="Bulk-check a generator")
    validate.add_argument("generator_id")
    validate.add_argument("--runs", type=positive_integer, default=1000)
    validate.add_argument("--difficulty", type=int)
    validate.add_argument("--seed", type=int, default=0)
    validate.add_argument("--independent", action="store_true")
    validate.add_argument("--json", action="store_true")

    worksheet = commands.add_parser("worksheet", help="Assemble a mixed worksheet")
    source = worksheet.add_mutually_exclusive_group()
    source.add_argument("--topic")
    source.add_argument("--profile")
    source.add_argument("--spec")
    worksheet.add_argument("--count", type=positive_integer)
    worksheet.add_argument("--difficulty")
    worksheet.add_argument("--seed", type=int, default=0)
    worksheet.add_argument("--answers", action="store_true")
    worksheet.add_argument("--pdf", action="store_true")
    worksheet.add_argument("--worked", action="store_true")
    worksheet.add_argument("--output", help="PDF export directory; default: exports")
    worksheet.add_argument("--json", action="store_true")
    return root


def emit_json(value):
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def main(argv=None):
    arguments = parser().parse_args(argv)
    registry = build_registry()
    try:
        if arguments.command == "topics":
            topics = sorted({item.topic for item in registry.list()})
            if arguments.json:
                emit_json({"topics": topics})
            else:
                print("\n".join(topics))
            return 0

        if arguments.command == "generators":
            items = registry.list(arguments.topic)
            if arguments.topic and not items:
                raise ValueError("No implemented generators for topic: " + arguments.topic)
            if arguments.json:
                emit_json({"generators": [item.to_dict() for item in items]})
            else:
                for item in items:
                    print("{} — {}".format(item.id, item.title))
            return 0

        if arguments.command == "worksheet":
            from pathlib import Path
            from .worksheets import build_worksheet, quick_spec

            if (arguments.output or arguments.worked) and not arguments.pdf:
                raise ValueError("--output and --worked currently require --pdf")
            if arguments.spec:
                if arguments.count is not None or arguments.difficulty is not None:
                    raise ValueError("--spec owns count and difficulty; edit its sections")
                path = Path(arguments.spec)
                if not path.is_absolute():
                    path = Path(__file__).resolve().parent.parent / path
                with path.open("r", encoding="utf-8") as source_file:
                    specification = json.load(source_file)
            else:
                specification = quick_spec(
                    count=arguments.count if arguments.count is not None else 20,
                    difficulty=arguments.difficulty or "1:4",
                    topic=arguments.topic,
                    profile=arguments.profile,
                )
            worksheet = build_worksheet(specification, arguments.seed, registry)
            if arguments.pdf:
                from .export import export_worksheet

                output_root = Path(arguments.output or "exports")
                if not output_root.is_absolute():
                    output_root = Path(__file__).resolve().parent.parent / output_root
                result = export_worksheet(
                    worksheet, output_root,
                    answers=arguments.answers, worked=arguments.worked,
                )
                if arguments.json:
                    emit_json(result)
                else:
                    print("Exported {} questions.".format(result["question_count"]))
                    for report in result["pdfs"]:
                        print("{}: {} pages".format(report["mode"], report["pages"]))
                        print("  " + report["path"])
                    print("Visual review: pending")
                return 0
            if arguments.json:
                emit_json(worksheet.to_dict())
            else:
                print(worksheet.title)
                print("Seed: {} | questions: {}".format(
                    worksheet.seed, len(worksheet.questions)
                ))
                for number, question in enumerate(worksheet.questions, 1):
                    print("{}. {}".format(number, question.prompt.text))
                    for index, choice in enumerate(question.choices):
                        print("   {}. {}".format(chr(65 + index), choice.content.text))
                if arguments.answers:
                    print("\nANSWERS")
                    for number, question in enumerate(worksheet.questions, 1):
                        print("{}. {}".format(number, question.answer_display.text))
            return 0

        generator = registry.get(arguments.generator_id)
        if arguments.command == "info":
            if arguments.json:
                emit_json(generator.info.to_dict())
            else:
                print(generator.info.id + " — " + generator.info.title)
                print("Generator version: {}".format(generator.info.version))
                for level, description in sorted(
                    generator.info.difficulty_descriptions.items()
                ):
                    print("  {}: {}".format(level, description))
            return 0

        if arguments.command == "sample":
            questions = [
                generator.generate(arguments.seed + index, arguments.difficulty)
                for index in range(arguments.count)
            ]
            if arguments.json:
                emit_json({"questions": [question.to_dict() for question in questions]})
            else:
                for number, question in enumerate(questions, 1):
                    print("{}. {}".format(number, question.prompt.text))
                    for index, choice in enumerate(question.choices):
                        print("   {}. {}".format(chr(65 + index), choice.content.text))
                    print("   Answer: " + question.answer_display.text)
                    print("   Seed: {} | difficulty: {}".format(
                        question.seed, question.difficulty
                    ))
                    if arguments.worked:
                        for step in question.worked_solution:
                            print("   " + step.text)
                            if step.math_tex:
                                print("     TeX: " + step.math_tex)
            return 0

        result = validate_many(
            generator,
            runs=arguments.runs,
            seed=arguments.seed,
            difficulty=arguments.difficulty,
            independent=arguments.independent,
        )
        if arguments.json:
            emit_json(result)
        else:
            print("{generator_id}: {passed}/{runs} passed; {failed} failed.".format(**result))
            print("Independent checks: {}".format(result["independent"]))
            print("Elapsed: {} seconds".format(result["seconds"]))
            for failure in result["failure_examples"]:
                print("  seed={seed} difficulty={difficulty}: {error}".format(**failure))
        return 1 if result["failed"] else 0

    except (ValueError, ImportError, OSError) as error:
        if arguments.json:
            emit_json({"error": str(error), "command": arguments.command})
        else:
            print("Error: " + str(error))
        return 2