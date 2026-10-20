# Design system: the study journal

Written from the built UI (`ui.html`). Chosen from three previewed directions (Studio, Atlas, Journal); earlier airfield-signage and card-table looks were replaced by this one.

The app reads like a well-made book: each class is a chapter, opened by its own rendered object. Professional, light, typographic; motion is precise rather than playful.

## Color
- Paper `#f5f5f2`, paper tones `#ecece7` / `#e1e1da`, white `#fff` only for things you act on (flashcards, quiz answers, search, job card).
- Ink `#141414`, secondary ink `#2c2c29`, muted `#6b6b66`, subtle `#9b9b94`.
- One accent: electric blue `#2f4dff` (progress, "Got it", active contents entry, chart marks, the blue in every rendered object).
- Right `#1b8a4c` on `#dff2e6`, wrong `#d4392a` on `#f9e2de`. Exam within 7 days uses the red pill; within 21 days the blue pill.
- Mastery tiers in the Collection are one blue ramp: Seen `#d9defd`, Learning `#aebafe`, Familiar `#7a8eff`, Known `#4b67ff`, Mastered `#1d33d1`.

## Type (installed Windows faces, nothing downloaded)
- Display: Sitka Banner. Chapter titles 64-124px, scaled down for long names (`hsz()`), never broken mid-word.
- Headings, lead sentences, questions: Sitka Heading.
- UI and reading body: Segoe UI Variable Text (guide body 17.5px / 1.75).
- Mono only for chart ticks, tables, keyboard hints and code.

## 3D
- `tools/render_objects.py` (Blender 4.5, Cycles, headless) renders one sculpture per subject family: `net` (wire lattice with nodes), `logic` (stacked slabs), `wave` (twisted ribbon), `shield` (nested glass cubes), `bars` (ring of bars). Chrome, glass and dark lacquer, one blue accent, transparent background.
- 36-frame turntables are packed by `tools/pack_sprites.py` into `assets/<shape>.webp` (6x6 sheets) and served at `/assets/`. In the app a `.tt` element shows one frame; drag scrubs it, and the chapter object turns slowly by itself when idle (paused while hidden, off with reduced motion).
- Ten designs: `net` (wire lattice), `logic` (stacked slabs), `wave` (twisted ribbon), `shield` (nested glass cubes), `bars` (ring of bars), `helix` (double helix), `gear` (meshing gears), `prism` (glass prism and beams), `orbit` (planet, ring, moons), `knot` (torus knot).
- Each class stores its design in `classes.json` (`shape`). `assignShapes()` keeps them unique while there are 10 or fewer classes (a keyword match when that design is free, otherwise a random free one); with more than 10, designs repeat. "Reroll object" under a chapter's object picks a different free design. Unfiled guides use the first design no class has.

## Layout
- Top bar: Study, Chapters, Library, Collection, Progress, search (Ctrl+K or /), New study guide. Bottom tab bar under 820px.
- Chapters (home): a spread of title + lead + three figures + actions, the turntable, and a right margin (today's goal dots, streak, next exam). Chapter tabs sit along the bottom like a book's edge; clicking one swaps the spread in place.
- Chapter page: opener (title, lead with the cards-per-day needed before the exam, exam controls, object), Contents (guide rows), Progress.
- Guide: reader with a sticky contents column that follows your position; article set like a book.
- Flashcards: one white card, 3D flip on Space or click, slides away on rating; progress line above. On the answer side, "See in guide" (G) opens the guide at `?card=<index>`: `rankPassages(…, wide)` shortlists up to 40 passages (paragraphs, list items, table rows, glossary entries) by shared word stems, each labelled with its section heading; `POST /api/locate` asks the model which ones actually explain the card (best first, cached in `locate_cache.json`, `reasoning_effort: low`). Offline or on error it falls back to the strict word ranking and says "offline match". The chosen passages get a highlighter-yellow `#fff0a1` band (current one `#ffe566`), shared words are bolded with a yellow underline stroke, and a dark bar at the bottom steps through them (Previous / Next / Back to the card / Clear). Test: `node tools/test_find_in_guide.mjs`.
- Search: an inline field in the top bar (Ctrl+K or / focuses it); it widens on focus and results drop down under it. No modal.
- Chapter tabs: a wrapping grid (never clipped) with the object thumbnail, two-line name, card count, due count, exam countdown and a progress line.
- Quiz: serif question, answer rows with letter keys (A-D, T/F, or 1-4), explanation panel, Enter for next.
- Progress: level and XP, four figures, two charts with tooltip and table view, per-chapter table.

## Math
- KaTeX 0.19.0 is bundled in `vendor/katex/` (MIT; js, css, woff2 fonts) and served from `/vendor/` (JS, CSS and woff2 only, path-checked). Offline.
- ` ```latex ` / `tex` / `math` fences in guide markdown become centered display equations; `$…$`, `\(…\)` and any word with a LaTeX command (`\theta`, `\frac{…}{…}`) render inline through KaTeX; anything KaTeX can't parse stays as plain text.
- Plain-text scripts render without KaTeX via `scripts()`: `x^{…}` (braces may hold spaces), `10^9`, `x_n`, `2^(n−1)` become `<sup>`/`<sub>`; snake_case like `actor_id` is left alone. `sqrt(` shows as `√(`.
- `renderMath(root)` runs on the guide, flashcard faces, quiz questions, options and explanations. Tests: `node tools/test_find_in_guide.mjs` (app running).

## Motion
- Screen changes: View Transitions crossfade on the root (never name `main`; it flattens the card flip).
- Focal: chapter switch (text rises in, object scales in, figures count up) and the turntable itself.
- Feedback: flip 0.6s, rating slide 0.26s, wrong answer nudge, bars grow once, tabs lift on hover.
- `prefers-reduced-motion`: no auto-rotate, flips become crossfades, no travel.

## Rules
- No gradients, glows, emoji, eyebrow labels or side-stripe accents. Shadows only under white objects lifted off the paper.
- Class names in the CSS: the page header is `.mast-h` (a generic `.top` collided with card internals once).
