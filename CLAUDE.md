# STUDY

A local study app: `StudyApp.cmd` starts `app.py` (Python server) and opens `ui.html` (the whole front end) in an app window. PDFs become a guide, flashcards and a quiz; chapters group guides by course; spaced repetition, quizzes and progress live in local JSON files.

- For anything about making guides, filing them into chapters, or running or changing the app, use the project skill `.claude/skills/study-app/SKILL.md`.
- UI work: read `DESIGN.md` (visual system) and `PRODUCT.md` (product truth) first. Edit `ui.html`; a browser refresh shows it.
- Do not edit upstream code in `skill_anything/` (the Skill-Anything CLI this app builds on).
- Never print or echo the key in `.env`, and never commit personal data: `output/`, `uploads/`, `.env` and the `*.json` data files are git-ignored on purpose.
- Tests: `node tools/test_find_in_guide.mjs` while the app is running.
