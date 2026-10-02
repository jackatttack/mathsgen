# MathsGen

Generate GCSE maths practice worksheets and answer keys on an iPhone or iPad with Pythonista. Pick a ready-made mix for a year group or grade, build your own sheet block by block, make staged drill sheets, or generate a full Edexcel-style GCSE exam paper, then open, share, or save the resulting A4 PDFs. Questions use reproducible seeds and exact answers where appropriate.

[See a sample worksheet](examples/questions.pdf) · [See its answer key](examples/answers.pdf)

## Install in Pythonista

You need Pythonista 3 with `reportlab`, `matplotlib`, and `sympy` available. The installer checks for these before changing files. Save a new script named `bootstrap_mathsgen.py` **inside Pythonista's local Documents folder**, paste the following into it, and run it:

    from urllib.request import urlopen

    url = "https://raw.githubusercontent.com/jackatttack/mathsgen/main/install_mathsgen.py"
    with urlopen(url, timeout=60) as response:
        source = response.read()
    exec(compile(source, url, "exec"), {
        "__name__": "__main__",
        "__file__": __file__,
    })

The installer downloads the current `main` branch to local `Documents/mathsgen/`. Open **`mathsgen/launch_mathsgen.py`** in Pythonista and tap Run.

**To update, run `bootstrap_mathsgen.py` again.** That is all: it fetches the current version, keeps your saved worksheets, settings and feedback, and keeps the previous install as a dated backup (the two newest backups are kept). If you already have the latest version it changes nothing. If anything still looks old after an update, close Pythonista fully and reopen it. If you want to inspect it first, [read the installer source](install_mathsgen.py).

## Make a worksheet

The launcher opens the **Worksheet Maker**. Enter a title, then choose a mode at the top:

- **Quick start:** Choose a year group (Y7–Y11) or a grade band (1–3, 4–5, 6–7, 8–9), the subjects, and a total number of questions. MathsGen picks a mix suited to that class and orders it from easier to harder. Year groups and grades are a teacher's working estimates, not exam-board data.
- **Build:** Design a sheet block by block. The skill board lists every skill by topic and subheading, with Edexcel spec codes, year groups and grades; filter by topic or grade, or search. Tap a skill to put it on the sheet (it turns green); tap again to take it off. The sheet slides over the board: tap a card to choose questions or drill, the count, and difficulty levels 1–4 (progression within the skill, not GCSE grades); press and hold a card to move it. Generate, the answer key, the PDF style, and Open/Save sit at the top of the sheet.
- **Drill:** Tick skills for staged practice: each skill runs level by level, then optional applied problems.
- **Exam paper:** Choose Foundation or Higher and Paper 1, 2 or 3. MathsGen builds an Edexcel-style paper worth exactly 80 marks, balanced across Number, Algebra, Ratio, Geometry, and Probability & Statistics using the published tier weightings, ordered by approximate grade. Paper 1 is non-calculator; papers 2 and 3 favour calculator questions. Grades are indicative, not exam-board calibrated.

Tap **Generate preview** (in Build, **Generate** at the top of the sheet). Open the worksheet or answers from the buttons that appear. Use the PDF viewer's Share control to send a preview to another app. Tap **Save worksheet** to keep the *same* generated PDFs in `mathsgen/exports/`; it does not generate new questions. Your selections persist between sessions. Previews use temporary device storage, so save any you want to keep.

A given generator and seed reproduce the same question in this snapshot. Future generator updates may change its wording or structure, so save the PDF when you need that exact version.

## Links in the question toolbar

Question headings in generated PDFs include clickable actions. They use Pythonista's `pythonista3://` URL scheme and open **this local installation** at `mathsgen/tools/mathsgen_action.py`. They are for the teacher using Pythonista; a student can read the worksheet PDF without installing MathsGen.

- **+ New** opens a new question based on the selected one.
- **Answer** copies an answer image to the clipboard.
- **Flag** records the question locally for review.
- **Formula** or **Graph**, where available, copies the relevant teaching resource as an image.
- **Options** opens the available tools for that question.

The available actions vary by skill. Your PDF viewer must allow external links; if it does not, open the PDF in a viewer that does. The included example also targets `Documents/mathsgen/`, so its buttons work after installation. Toolbar links encode the generator version and original question: a future update to that generator may make an older PDF's actions report that the question needs regenerating. The PDF itself remains readable.

Pythonista's [URL scheme documentation](https://omz-software.com/pythonista/docs/ios/urlscheme.html) explains the local and iCloud script roots and how `argv` values are passed.

## Repository layout

- `launch_mathsgen.py` — everyday Pythonista entrypoint.
- `core/mathsgen/` — question engine, catalogue, PDF renderer, and native worksheet UI.
- `tools/mathsgen_action.py` — action target for PDF toolbar links.
- `tools/mathsgen_cli.py` — optional command interface.
- `tools/build_example.py` — reproducible example generator.
- `worksheet_specs/` — reusable worksheet specifications.
- `examples/` — sample question and answer PDFs.
- `tests/` and `docs/` — generator checks and extension guide.

This repo is a snapshot of the working MathsGen engine. Work on new generators continues separately. `requirements.txt` describes an off-device Python environment; it is not a command to replace Pythonista's bundled packages.