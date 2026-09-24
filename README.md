# MathsGen

Generate GCSE maths practice worksheets and answer keys on an iPhone or iPad with Pythonista. Pick individual skills, build a mixed mini paper, or generate a full Edexcel-style GCSE exam paper, then open, share, or save the resulting A4 PDFs. Questions use reproducible seeds and exact answers where appropriate.

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

The installer downloads the current `main` branch to local `Documents/mathsgen/`. An update asks before replacing an existing installation, carries saved worksheets, settings and feedback into the new install, and keeps the previous folder as a dated backup. Open **`mathsgen/launch_mathsgen.py`** in Pythonista and tap Run. If you want to inspect it first, [read the installer source](install_mathsgen.py).

## Make a worksheet

The launcher opens the **Worksheet Maker**. Enter a title, then choose a mode at the top:

- **Skills:** Expand a subject and its topic groups, or search for a skill. Tick the skills you want. Set the number of questions *per selected skill* and select difficulty levels 1–4. The levels describe progression within each skill; they are not GCSE grades. Use Set order or Random, choose whether to include an answer key, and select a PDF style.
- **Mini paper:** Set the total number of questions, levels, and included subjects. MathsGen chooses a mix across those subjects and orders questions from easier to harder.
- **Exam paper:** Choose Foundation or Higher and Paper 1, 2 or 3. MathsGen builds an Edexcel-style paper worth exactly 80 marks, balanced across Number, Algebra, Ratio, Geometry, and Probability & Statistics using the published tier weightings, ordered by approximate grade. Paper 1 is non-calculator; papers 2 and 3 favour calculator questions. Grades are indicative, not exam-board calibrated.

Tap **Generate preview**. Open worksheet or answers from the bottom bar. Use the PDF viewer's Share control to send a preview to another app. Tap **Save worksheet** to keep the *same* generated PDFs in `mathsgen/exports/`; it does not generate new questions. Your selections persist between sessions. Previews use temporary device storage, so save any you want to keep.

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