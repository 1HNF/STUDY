---
name: course-guide
description: Use when the student wants a full, exam-quality study guide for a whole course or a folder of material (slides, notes, syllabus, past exams), or wants to catch up on a course from zero. Reads every file, then writes the guide, flashcards and quiz for the STUDY app. Works in Claude Code and in ChatGPT Codex.
---

# Course guide (from zero to exam)

Turns a course folder into one deep guide for this app. Open replacement for Anthropic's `course-catchup-guide`, so it works the same in Claude Code and Codex. The app's file format, chapters and exam dates are in the `study-app` skill; read it too.

## 1. Ask (once, briefly)

- Where the material is (a folder or files), the course name, the exam date if any.
- What the exam looks like if the student knows (written, multiple choice, lab, oral). Otherwise infer it from past exams or the syllabus.

## 2. Extract everything first

Run from the STUDY folder (the venv already has the packages):

```bat
.venv\Scripts\python tools\extract_pdf.py "<course folder>" --images
```

It writes `work/extract/<pdf name>.md` (text and tables per page) and `work/extract/<pdf name>/page-NN.png`. `work/` is git-ignored.
- Read every `.md` file fully. Do not skim and do not stop after the first few lectures.
- Open the page images for pages the script flags as having little or no text (scanned slides, diagrams, handwritten notes) and for any page whose text looks garbled or refers to a figure. Read the image instead.
- Word, PowerPoint, text and Markdown files: read them directly (`pdf`/`docx`/`pptx` skills help if installed). Lecture recordings: use a transcription skill if one is available (Codex: `transcribe`), otherwise ask for the slides or a transcript.

## 3. Plan the order

Order the guide the way a student who missed everything should learn it:
1. **Theory foundations**: the concepts everything else builds on.
2. **Setup**: tools, software, environments the course uses (only if it uses any).
3. **Applied theory**: methods, algorithms, techniques, with worked examples.
4. **Labs, exercises and the exam**: how each lab or exercise type is solved, past exam questions, common traps.

Map every lecture to a part. Note what past exams ask most and give it the most space.

## 4. Write

- `detailed_notes` in Markdown: `#` guide title, `##` parts, `###` topics. Explain from zero, define every term on first use, add a worked example per method, and end each `###` topic with 2–4 "Check yourself" questions.
- Equations in fenced ```latex blocks; inline `x^{2}`, `x_n`. Tables in pipe Markdown.
- Use only what the material says; when you add general knowledge to explain something, keep it consistent with the slides. Mark anything the material leaves unclear.
- Target size: 25,000–80,000 characters of notes, 50–100+ flashcards (one idea each), 25–100 quiz questions mixing all four types, with explanations.
- Fill `summary`, `key_concepts`, `glossary`, `cheat_sheet` (formulas and facts to memorise) and `takeaways`.

## 5. Save and file

Follow the `study-app` skill: YAML at `output/<id>/<id>.yaml`, validate it parses (`.venv\Scripts\python -c "import yaml,sys; yaml.safe_load(open(sys.argv[1],encoding='utf-8'))" output\<id>\<id>.yaml`), file it into a chapter in `classes.json` with the exam date, and tell the student to press F5 in the app.

## 6. Keep it updated

When new lectures arrive, extract only the new files, add their topics in the right part (not appended at the end), add flashcards and questions for them, and keep the existing ones so the student's progress is kept (progress is keyed by each card's front, so do not reword old fronts).
