# STUDY

A local study app: `StudyApp.cmd` starts `app.py` (Python server) and opens `ui.html` (the whole front end) in an app window. PDFs become a guide, flashcards and a quiz; chapters group guides by course; spaced repetition, quizzes and progress live in local JSON files.

These instructions are shared by every coding agent: Codex reads `AGENTS.md`, Claude Code reads `CLAUDE.md`, which imports this file.

- Project skills live in two identical copies: `.agents/skills/` (Codex) and `.claude/skills/` (Claude Code). Edit both, or `node tools/test_find_in_guide.mjs` fails.
  - `study-app`: the app's guide format, chapters, exam dates, and how to run or change the app.
  - `course-guide`: a full exam-quality guide from a whole course folder (uses `tools/extract_pdf.py`).
- UI work: read `DESIGN.md` (visual system) and `PRODUCT.md` (product truth) first. Edit `ui.html`; a browser refresh shows it.
- Do not edit upstream code in `skill_anything/` (the Skill-Anything CLI this app builds on).
- Never print or echo the key in `.env`, and never commit personal data: `output/`, `uploads/`, `work/`, `.env` and the `*.json` data files are git-ignored on purpose.
- Python: use the project venv, `.venv\Scripts\python`.
- Tests: `node tools/test_find_in_guide.mjs` (the real-guide part runs only while the app is running).
