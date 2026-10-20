// Checks the "See in guide" ranking from ui.html against a real deck.
// Usage: node tools/test_find_in_guide.mjs   (app must be running on 127.0.0.1:8765)
import { readFileSync } from "node:fs";
import assert from "node:assert/strict";

const html = readFileSync(new URL("../ui.html", import.meta.url), "utf8");
const src = html.slice(html.indexOf("const STOP="), html.indexOf("function markWords"));
const { rankPassages, toks } = new Function(src + "; return { rankPassages, toks };")();

// 1. synthetic: the passage that explains the card must win, unrelated text must not match
const texts = [
  "HTTP is a request/response protocol on top of TCP.",
  "A 304 Not Modified response tells the browser its cached copy is still valid (conditional GET).",
  "Throughput is the rate at which bits are delivered end to end.",
  "The weather was nice today.",
];
const r = rankPassages("What does a 304 status code mean? Not Modified: the cached copy is still valid", texts);
assert.equal(r[0].i, 1, "the 304 passage should rank first");
assert.ok(!r.some(x => x.i === 3), "unrelated text must not match");
assert.deepEqual(toks("The TCP and the IP"), ["tcp"], "stopwords and short words are dropped");

// 1b. the plain-text math converter (^ and _ to superscript / subscript)
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const scripts = new Function(html.slice(html.indexOf("function scripts("), html.indexOf("const MATH_SKIP=")) + "; return scripts;")();
assert.equal(scripts("e^{jπ}"), "e<sup>jπ</sup>");
assert.equal(scripts("e^{−(t − 2)}"), "e<sup>−(t − 2)</sup>", "braces may hold spaces");
assert.equal(scripts("2^10 and x_n"), "2<sup>10</sup> and x<sub>n</sub>");
assert.equal(scripts("2^(n-1)"), "2<sup>n-1</sup>");
assert.equal(scripts("actor_id and file_name"), "actor_id and file_name", "snake_case is not math");
assert.equal(scripts("e^{−t}1(t)"), "e<sup>−t</sup>1(t)");
assert.equal(scripts(esc("a < b^2")), "a &lt; b<sup>2</sup>", "works on escaped html");
// guard against lost lines from scripted edits: the quiz must still wire its Next button
assert.ok(/\$\("#nx"\)\.onclick=\(\)=>\{i\+\+;draw\(\)\}/.test(html), "quiz Next button handler present");

// 1c. every class gets its own 3D object while there are 10 or fewer classes
const { assignShapes, SHAPES } = new Function(html.slice(html.indexOf("const SHAPES="), html.indexOf("function rerollShape(")) + "; return { assignShapes, SHAPES };")();
assert.equal(SHAPES.length, 10);
for (let n = 1; n <= 10; n++) {
  const C = Array.from({ length: n }, (_, i) => ({ id: "c" + i, name: i % 2 ? "Networking " + i : "Course " + i }));
  assignShapes(C);
  assert.equal(new Set(C.map(c => c.shape)).size, n, `${n} classes must all differ`);
}
const many = Array.from({ length: 13 }, (_, i) => ({ id: "c" + i, name: "Course " + i }));
assignShapes(many);
assert.ok(many.every(c => SHAPES.includes(c.shape)) && new Set(many.map(c => c.shape)).size === 10, "13 classes reuse, but use all 10");
const kept = [{ id: "a", name: "X", shape: "gear" }, { id: "b", name: "Y", shape: "gear" }];
assert.equal(assignShapes(kept), true); assert.notEqual(kept[0].shape, kept[1].shape, "duplicates are repaired");
assert.equal(kept[0].shape, "gear", "the first keeps its object");
const again = JSON.stringify(kept); assignShapes(kept); assert.equal(JSON.stringify(kept), again, "stable once assigned");

// 2. real deck (if the app is running and has a guide): most cards should find at least one passage
let list = null;
try { list = await (await fetch("http://127.0.0.1:8765/api/decks")).json(); } catch { /* app not running */ }
const first = list && list.decks.find(d => d.guide && d.cards);
if (!first) { console.log("ok (no running app or no guides yet: real-deck check skipped)"); process.exit(0); }
const deck = await (await fetch("http://127.0.0.1:8765/api/deck/" + encodeURIComponent(first.id))).json();
const g = deck.guide;
const blocks = [g.summary, ...g.notes.split(/\n+/), ...g.concepts, ...g.glossary.map(x => x.term + ": " + x.definition), ...g.takeaways].filter(Boolean);
const found = deck.cards.filter(c => rankPassages(c.q + " " + c.a, blocks).length > 0).length;
console.log(`real deck: ${found} of ${deck.cards.length} cards found a passage`);
assert.ok(found / deck.cards.length > 0.8, "expected most cards to find a passage");
console.log("ok");
