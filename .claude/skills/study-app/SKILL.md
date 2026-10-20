---
name: study-app
description: Use when the user wants a study guide, flashcards or a quiz from course material (PDF slides, notes, a course folder), wants to file a guide into a chapter (class), set an exam date, or open, run or change this STUDY app. Knows the app's data format and how to write exam-quality guides with Claude.
---

# STUDY app

This folder is a local study app. `StudyApp.cmd` starts `app.py` (Python server on 127.0.0.1:8765) and opens `ui.html` in a Chrome or Edge app window. Everything lives in this folder; paths below are relative to it.

## Two ways a guide gets made

1. **Quick (inside the app):** the student drops a PDF on the window. `app.py` runs the bundled Skill-Anything CLI (`.venv\Scripts\sa.exe pdf …`) with the model in `.env` (Groq by default) and files the result into a matching chapter. Short guide, about 15 flashcards and 12 questions per PDF. Good for a single lecture.
2. **Exam quality (you, Claude):** you read the whole course material and write the guide, flashcards and quiz yourself, then save them in the app's format (below). Much deeper: 25k to 80k characters of notes, 50 to 100 flashcards, 25 to 100 questions. Prefer this whenever the student asks for a real study guide.

## Recommended skill stack for exam-quality guides

Use whichever of these are available in the session; the workflow still works without them.
- `course-catchup-guide` (Anthropic skill): builds a from-zero guide for a whole course folder, ordered theory → setup → labs → exam. Use it for the notes.
- `pdf` (Anthropic skill): extract text and tables and run OCR on scanned slides before writing, so nothing is lost.
- this `study-app` skill: turns the result into the app's YAML, with flashcards and a quiz, and files it into a chapter.
- `impeccable` (github.com/pbakaus/impeccable): only for changing the app's design; read `DESIGN.md` first.
Use the strongest available Claude model for writing guides.

## Workflow (exam quality)

1. Ask for the course folder or files, the course name, and the exam date if there is one.
2. Read everything (slides, syllabus, past exams, notes). For scanned PDFs, OCR first.
3. Write `detailed_notes` as Markdown: `#` for the guide title, `##` for parts, `###` for topics. Explain from zero, with worked examples and "check yourself" questions. Put real equations in fenced ```latex blocks (rendered with KaTeX). Inline math may use `x^{2}`, `x_n`, `e^{jθ}`; the app turns those into superscripts and subscripts. Tables use pipe Markdown.
4. Write flashcards that each test one idea, with answers that can be checked against the notes (the "See in guide" button finds where each card is explained). Write a quiz with a mix of types.
5. Save the YAML to `output/<id>/<id>.yaml` (`<id>`: lowercase words joined by `-`, e.g. `networking-guide`). One folder per guide.
6. File it into a chapter by editing `classes.json` (create it if missing), or let the student pick the chapter in the app.
7. Tell the student to refresh the app (F5). Remind them that AI-written answers should be spot-checked before an exam.

## Guide YAML format (`output/<id>/<id>.yaml`)

```yaml
title: Networking — Catch-Up Guide          # shown everywhere
source_type: study_guide
source_ref: Claude (from the course folder)
summary: One paragraph overview shown first in the Guide tab.
detailed_notes: |                            # the main guide, Markdown
  # Networking — Catch-Up Guide
  ## Part 1 — Theory
  ### Delay, loss and throughput
  ...
key_concepts: [The Internet and protocols, Packet switching]   # plain strings
glossary:
  - {term: IXP, definition: Internet exchange point, where ISPs peer with each other.}
cheat_sheet: |                               # optional, Markdown
  ...
takeaways: [One line each.]
flashcards:
  - {front: What is an IXP?, back: A place where ISPs peer with each other., tags: [internet-structure]}
quiz_questions:
  - question: Which delay depends on packet length L and link rate R?
    type: multiple_choice                  # multiple_choice | true_false | fill_blank | comparison
    options: [A. Transmission delay L/R, B. Propagation delay, C. Processing delay, D. Queueing delay only]
    answer: A                              # letter for multiple_choice, True/False, short text for fill_blank, model answer for comparison
    explanation: Why the answer is right.
    difficulty: medium                     # easy | medium | hard
metadata: {generator: Claude, created: 2026-01-01}
```

Rules: valid YAML (quote strings containing `: ` or starting with special characters, or use `|` blocks); exactly four options for multiple choice, without leading letters being required (the app adds A to D); `fill_blank` answers short enough to type.

## Chapters (`classes.json`)

```json
{"classes": [{"id": "c-networking", "name": "Networking", "exam": "2026-12-15"}],
 "assign": {"networking-guide": "c-networking"}}
```
`exam` is optional (YYYY-MM-DD). The app adds a `shape` field itself (each chapter's 3D object, unique for up to 10 chapters); leave it alone unless asked. Keep existing entries when adding new ones.

## Running and changing the app

- First time: `setup.cmd` (creates `.venv`, installs packages, opens `.env` for the model key). Then `StudyApp.cmd`.
- Front end: `ui.html` (CSS, HTML, JS in one file; hash routes `#/`, `#/class/<id>`, `#/library`, `#/collection`, `#/progress`, `#/deck/<id>/guide|cards|quiz`). The server re-reads it per request, so a refresh shows edits.
- Server and API: `app.py`. Design: `DESIGN.md`. Product truth: `PRODUCT.md`.
- 3D objects: Blender renders in `tools/render_objects.py`, packed by `tools/pack_sprites.py` into `assets/<shape>.webp`.
- Tests: `node tools/test_find_in_guide.mjs` with the app running.
- Never edit `skill_anything/` (upstream CLI), never print the key in `.env`, never commit personal data (`output/`, `uploads/`, `*.json` data files are git-ignored).
- When testing in a browser, do not rate cards or finish quizzes on the student's real data: override `window.fetch` so POSTs return `{"ok":true}` first.
