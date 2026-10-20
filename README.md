# STUDY

A local study app that turns your course material into a **study guide, flashcards and a quiz**, and then helps you actually study it: spaced-repetition flashcards, quizzes that remember what you got wrong, chapters per course with exam countdowns, and progress you can see.

It runs on your own computer in an app window. Your guides, PDFs and progress stay on your machine. The only thing sent out is text to the AI model you choose (free Groq by default) when it writes or checks study material.

> Built on [Skill-Anything](https://github.com/thinhlpg/skill-anything) (MIT), which does the PDF-to-study-pack generation. This repo adds the app, the design, the Claude workflow and the 3D chapter objects.

---

## What you get

- **Chapters (home).** One chapter per course, each with its own spinning 3D object (rendered in Blender). The page opens on the chapter that needs you most: cards due, new cards, days to the exam.
- **Guide.** A clean reader with a contents column that follows you, tables, and properly typeset math (KaTeX).
- **Flashcards.** Spaced repetition: *Again* brings a card back soon, *Got it* pushes it further out each time. Space flips, 1 and 2 rate.
  **See in guide** (G): jumps to the exact passages in your guide that explain the card and highlights them.
- **Quiz.** Multiple choice, true/false, fill-in and open questions, answerable from the keyboard. *Replay missed* drills only the ones you got wrong, and the app remembers them for next time.
- **Write more.** One click writes 15 new flashcards or 12 new questions from the guide, without repeating old ones.
- **Search everything** (Ctrl+K): every guide, flashcard, question and glossary term.
- **Progress.** Daily goal, streak, level and XP, cards reviewed per day, quiz scores over time, mastery per chapter, and exam countdowns with "cards per day to be ready".
- **Collection.** Every card you have, darkening as you master it.
- Works offline for studying. Phone-width layout too.

---

## Requirements

- **Windows 10 or 11**
- **Python 3.10 or newer** from [python.org/downloads](https://www.python.org/downloads/). During install, tick **"Add python.exe to PATH"**.
- **Google Chrome or Microsoft Edge** (the app opens in an app window of either).
- **A free Groq API key** from [console.groq.com/keys](https://console.groq.com/keys) (sign in, *Create API key*, copy the key that starts with `gsk_`).
- Optional, for the best guides: a coding agent, either **[Claude Code](https://claude.com/claude-code)** or **[ChatGPT Codex](https://developers.openai.com/codex)** (see *Making great guides with an AI agent* below).
- Optional: **Git**, to clone and update. Without Git, use *Code → Download ZIP* on GitHub.

---

## Install (once, about 5 minutes)

1. **Get the code**
   - With Git: `git clone https://github.com/1HNF/STUDY.git`
   - Or on GitHub click **Code → Download ZIP** and unzip it (for example into `Documents\STUDY`).
2. **Run setup.** Open the folder and double-click **`setup.cmd`**. It
   - checks your Python version,
   - creates a private Python environment in `.venv`,
   - installs the packages the app needs (a minute or two),
   - creates your `.env` file and opens it in Notepad.
3. **Add your key.** In Notepad, replace `PASTE_YOUR_GROQ_API_KEY_HERE` with your Groq key, then save and close.
   Keep this key to yourself: never post it in chats or commit it. `.env` is git-ignored.
4. **Open the app.** Double-click **`StudyApp.cmd`**. A *Study* window opens.
   Tip: right-click `StudyApp.cmd` → *Send to* → *Desktop (create shortcut)*.

Prefer the terminal? The same steps by hand:

```bat
cd STUDY
py -m venv .venv
.venv\Scripts\python -m pip install -e ".[pdf,web]"
copy .env.example .env
notepad .env
StudyApp.cmd
```

---

## Using it

1. **Make a chapter** for each course: *Chapters → + New chapter*. Set the exam date on the chapter page.
2. **Add material.** Drag a PDF (slides or notes) anywhere onto the window, or click *New study guide*. After a minute or two a guide with flashcards and a quiz appears and is filed into the chapter it matches.
3. **Study.** *Continue studying* on the home page takes you to the cards that are due. Use the Guide, Flashcards and Quiz tabs on each guide.
4. **Track.** *Progress* shows your streak, level, reviews and quiz scores. Change your daily goal on the home page.

Closing the window is enough: the app stops by itself after a while. Opening `StudyApp.cmd` again picks up where you left off.

> AI writes the guides and questions. They are usually right, but spot-check answers against your slides before an exam.

---

## Making great guides with an AI agent (recommended)

Dropping a PDF into the app gives a quick, short guide for **one** PDF (about 15 flashcards and 12 questions), written by the small Groq model. For a real exam guide, let a coding agent read the whole course and write it. **Claude Code** and **ChatGPT Codex** both work: the project ships the same instructions and skills for each. The difference is large:

| Made by | Guide notes | Flashcards | Quiz |
|---|---|---|---|
| Drop a PDF in the app | ~5,000 characters | ~15 | ~12 |
| Claude Code or Codex, from the whole course folder | 25,000–80,000 characters | 50–100+ | 25–100 |

### Option A: Claude Code (Claude Pro or Max plan)

1. Install: the [Claude desktop app](https://claude.ai/download) (use its **Code** tab), or the terminal version from [claude.com/claude-code](https://claude.com/claude-code).
2. Sign in with your Claude account.
3. Open the **STUDY folder** (desktop: pick the folder; terminal: `cd STUDY` then `claude`).
4. Ask in plain words. Claude reads `CLAUDE.md` and loads the skills in `.claude/skills/` by itself.

### Option B: ChatGPT Codex (ChatGPT Plus, Pro, Business or Edu plan)

1. Install: the [Codex app](https://developers.openai.com/codex) (open a project folder there), or the terminal version: `npm install -g @openai/codex` (needs [Node.js](https://nodejs.org)).
2. Sign in: choose **Sign in with ChatGPT** and log in with your ChatGPT account. No API key needed.
3. Open the **STUDY folder** (app: pick the folder; terminal: `cd STUDY` then `codex`).
4. Ask in plain words. Codex reads `AGENTS.md` and finds the skills in `.agents/skills/` by itself. To call one directly, type `$course-guide` or `$study-app`, or pick it from `/skills`.

### What to ask (same for both)

> Make a study guide for my Networking course from the files in `C:\Uni\Networking`, put it in the Networking chapter, the exam is on 15 December.

The agent extracts every PDF (`tools/extract_pdf.py`: text, tables, and page images for scanned slides and diagrams), reads it all, writes the guide, flashcards and quiz, saves them in `output/`, files them into the chapter, and tells you to refresh the app (F5). Agents ask before running commands; allow the extractor and Python when asked.

Later: *"Add lectures 9 and 10 from the same folder to my Networking guide"* keeps your progress on the existing cards.

### Recommended skill stack

| Job | Claude Code | ChatGPT Codex |
|---|---|---|
| App format, chapters, exam dates, running the app | **study-app** (included) | **study-app** (included) |
| Whole course → from-zero guide (theory → setup → applied → labs and exam) | **course-guide** (included), or Anthropic's *course-catchup-guide* if your account has it | **course-guide** (included; *course-catchup-guide* is Claude-only, this is its open replacement) |
| PDF text, tables, scanned pages | `tools/extract_pdf.py` (included); optional Anthropic **pdf** skill | `tools/extract_pdf.py` (included); optional OpenAI **pdf** skill: type `$skill-installer pdf` in Codex |
| Lecture recordings → text | No Anthropic skill for this: give Claude a transcript or the slides | OpenAI **transcribe** skill: `$skill-installer transcribe` (needs an OpenAI API key, billed separately) |
| Changing the design (optional) | **impeccable**: [github.com/pbakaus/impeccable](https://github.com/pbakaus/impeccable) | **impeccable** supports Codex too (see its README) |

Pick the strongest model your plan offers for writing guides. Groq is still used inside the app for the quick upload, *Write more*, chapter matching and *See in guide*.

Skill sources: OpenAI's curated skills at [github.com/openai/skills](https://github.com/openai/skills), Anthropic's at [github.com/anthropics/skills](https://github.com/anthropics/skills).

---

## Settings

`.env` (created by `setup.cmd`, see `.env.example`):

| Setting | Default | Notes |
|---|---|---|
| `SKILL_ANYTHING_API_KEY` | your Groq key | Required for generating. Studying works without it. |
| `SKILL_ANYTHING_API_BASE` | `https://api.groq.com/openai/v1` | Any OpenAI-compatible endpoint (OpenAI, OpenRouter, …). |
| `SKILL_ANYTHING_MODEL` | `openai/gpt-oss-120b` | A model your endpoint offers. |

Groq's free tier has per-minute limits. If a very large PDF fails, split it into chapters.

---

## Your data and privacy

Everything personal stays in this folder on your computer and is **git-ignored**, so it never ends up on GitHub:

| File or folder | What it holds |
|---|---|
| `output/` | Your guides, flashcards and quizzes |
| `uploads/` | PDFs you dropped in |
| `progress.json` | Spaced-repetition state of every card |
| `stats.json` | Reviews and quiz results (charts, streak, missed questions) |
| `classes.json` | Your chapters, exam dates and their 3D objects |
| `settings.json` | Daily goal |
| `locate_cache.json` | Cached *See in guide* answers |
| `.env` | Your API key |

To back up your study data, copy those files and folders. To start fresh, delete them.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `StudyApp.cmd` says the app is not set up | Run `setup.cmd` first. |
| `setup.cmd` says Python is missing or too old | Install Python 3.10+ from python.org with *Add python.exe to PATH* ticked, then run it again. |
| A guide fails with an error mentioning 401 or *invalid API key* | Check the key in `.env` (no spaces, no quotes), save, and try again. |
| Error mentioning *rate limit* or 429 | Groq's free per-minute limit. Wait a minute, or split the PDF. |
| *Lost connection to the app* banner | The app stopped (it does this after a long idle time). Close the window and open `StudyApp.cmd` again. |
| Nothing opens | You need Chrome or Edge. If one is installed, open `http://127.0.0.1:8765` in it while the app runs. |
| Math shows as raw code | Refresh with F5. Make sure the `vendor/katex/` folder is present. |

---

## For developers

| Path | What it is |
|---|---|
| `app.py` | Local server (Python standard library) and JSON API on `127.0.0.1:8765` |
| `ui.html` | The entire front end (HTML, CSS, JS, no build step) |
| `DESIGN.md`, `PRODUCT.md` | The design system and product brief (read these before UI changes) |
| `AGENTS.md`, `CLAUDE.md` | Agent instructions: Codex reads `AGENTS.md`; `CLAUDE.md` imports it for Claude Code |
| `.agents/skills/`, `.claude/skills/` | The `study-app` and `course-guide` skills, one identical copy per agent (the tests check they match) |
| `tools/extract_pdf.py` | PDF → Markdown text, tables and page images for agents (`.venv\Scripts\python tools\extract_pdf.py <folder> --images`) |
| `tools/render_objects.py` | Blender script for the 10 chapter objects (`blender -b --factory-startup --python tools/render_objects.py -- assets/frames 36 360`) |
| `tools/pack_sprites.py` | Packs the 36 rendered frames into `assets/<shape>.webp` turntables |
| `tools/test_find_in_guide.mjs` | Tests for search ranking, math rendering, chapter objects and skill copies (`node tools/test_find_in_guide.mjs`) |
| `vendor/katex/` | KaTeX 0.19.0 for math (MIT) |
| `skill_anything/` | The upstream Skill-Anything CLI (`sa`), used to turn PDFs into study packs. Its own docs: [docs/SKILL_ANYTHING.md](docs/SKILL_ANYTHING.md) |
| `study.cmd`, `make_html.py` | Older command-line path: PDF to a standalone HTML flashcard page |

---

## Credits and license

- [Skill-Anything](https://github.com/thinhlpg/skill-anything) by its contributors: the PDF-to-study-pack engine (MIT, see `LICENSE`).
- [KaTeX](https://katex.org) for math rendering (MIT, `vendor/katex/LICENSE`).
- 3D chapter objects rendered with [Blender](https://www.blender.org).

Released under the MIT license (see `LICENSE`).
