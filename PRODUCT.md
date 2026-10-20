# Product

<!-- impeccable:product-schema 1 -->

## Platform

web (a local app: Python server + one HTML file, shown in a Chrome or Edge app window on Windows 10/11; also usable at phone width)

## Stack

Plain HTML/CSS/JS in `ui.html`, Python standard-library server in `app.py`. No frameworks, no npm, no network fonts (the app works offline). Fonts are installed Windows system faces; KaTeX is bundled in `vendor/katex/`.

## Users

University students, and anyone studying from slides and notes (certificates, licences, self-study), who study in short sessions at a laptop. Each person runs their own copy with their own courses. They want to see steady progress and keep going.

## Product Purpose

Turn course material (PDF slides, notes) into a study guide, flashcards and a quiz, then make the student actually study: spaced-repetition flashcards, quizzes, chapters that group guides by course, exam countdowns and visible progress. Success is a student who opens it daily and can see what they know and what is still weak.

## Positioning

Everything for one student's courses lives locally in one place: guide, flashcards, quiz, chapter progress, exam countdown. Nothing is sent anywhere except the model calls that write or check study material from the student's own notes.

## Operating Context

Quick generation uses an OpenAI-compatible API (Groq by default) with the key in `.env`; studying works offline. Deep, exam-quality guides are written by a coding agent (Claude Code or ChatGPT Codex) and filed into the app through the bundled `course-guide` and `study-app` skills. Data lives in `output/`, `progress.json`, `stats.json`, `classes.json`, `settings.json`, `locate_cache.json`, all git-ignored. Decks are AI-written, so answers should be spot-checked before an exam.

## Capabilities and Constraints

Drop-a-PDF generation with automatic chapter matching; chapters with exam countdowns; guide reader with contents column and rendered math; flashcards with spaced repetition and "See in guide"; quiz (multiple choice, true/false, fill-in, open answer with self-grading, replay missed); write more cards or questions; library; collection; progress dashboard (level/XP, streak, daily goal, charts with table view); inline search; phone layout.

## Brand Commitments

Professional and calm but rewarding: a study journal, not a game. Green means correct, red means wrong, one electric-blue accent.
