"""Study app: a local window around Skill-Anything. Drop a PDF, get flashcards + quiz, keep a library.

Run via StudyApp.cmd. Standard library + PyYAML only (already installed). Listens on 127.0.0.1 only,
unless started with --lan (StudyPhone.cmd): then phones on the same Wi-Fi can open it with a secret link.
"""
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from http.cookies import Morsel, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote

import yaml
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent
OUT, UP, PROG = ROOT / "output", ROOT / "uploads", ROOT / "progress.json"
LAN = "--lan" in sys.argv
PORT = 8766 if LAN else 8765  # phone mode gets its own port so it never collides with an open desktop window
LAN_IP, LAN_KEY = "", ""  # set in main() for --lan
MAX_UPLOAD = 200 * 1024 * 1024
IDLE_EXIT = 1800  # seconds without a browser ping before the server quits (study sessions can sit idle)

lock = threading.Lock()
job = {"state": "idle", "name": "", "msg": "", "started": 0}
last_ping = [0.0]


def read_progress():
    try:
        return json.loads(PROG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


stats_lock = threading.Lock()


def read_stats():
    try:
        s = json.loads((ROOT / "stats.json").read_text(encoding="utf-8"))
        return {"quiz": dict(s.get("quiz", {})), "reviews": dict(s.get("reviews", {})), "missed": dict(s.get("missed", {}))}
    except (OSError, ValueError, TypeError, AttributeError):
        return {"quiz": {}, "reviews": {}, "missed": {}}


def read_settings():
    try:
        g = int(json.loads((ROOT / "settings.json").read_text(encoding="utf-8")).get("goal", 20))
        return {"goal": min(max(g, 1), 500)}
    except (OSError, ValueError, TypeError, AttributeError):
        return {"goal": 20}


def add_stat(kind, did, body):
    """Append one quiz result {t,score,total} or one flashcard review timestamp for a deck."""
    now = int(time.time() * 1000)
    with stats_lock:
        s = read_stats()
        if kind == "quiz":
            score, total = int(body["score"]), int(body["total"])
            if not 0 <= score <= total <= 500 or total == 0:
                raise ValueError("bad score")
            s["quiz"].setdefault(did, []).append({"t": now, "score": score, "total": total})
            s["quiz"][did] = s["quiz"][did][-200:]
            # questions answered wrong stay "missed" until answered right in a later round
            missed = [str(q)[:400] for q in body.get("missed", [])][:300]
            right = {str(q)[:400] for q in body.get("right", [])}
            keep = [q for q in s["missed"].get(did, []) if q not in right and q not in missed]
            s["missed"][did] = (keep + missed)[-300:]
        else:
            s["reviews"].setdefault(did, []).append(now)
            s["reviews"][did] = s["reviews"][did][-5000:]
        (ROOT / "stats.json").write_text(json.dumps(s), encoding="utf-8")


def read_classes():
    try:
        c = json.loads((ROOT / "classes.json").read_text(encoding="utf-8"))
        return {"classes": list(c["classes"]), "assign": dict(c["assign"])}
    except (OSError, ValueError, KeyError, TypeError):
        return {"classes": [], "assign": {}}  # starts empty


def deck_files():
    """{deck id: yaml path} for every output/<id>/*.yaml."""
    found = {}
    if OUT.is_dir():
        for d in sorted(OUT.iterdir()):
            ys = sorted(d.glob("*.yaml")) if d.is_dir() else []
            if ys:
                found[d.name] = ys[0]
    return found


_deck_cache = {}


def load_deck(path):
    """Parsed deck, cached by file mtime (big guides take ~100 ms to parse; search and listings reuse them)."""
    mt = path.stat().st_mtime
    hit = _deck_cache.get(str(path))
    if hit and hit[0] == mt:
        return hit[1]
    d = _parse_deck(path)
    _deck_cache[str(path)] = (mt, d)
    return d


def search(q):
    """Substring search over titles, flashcards, quiz questions, glossary terms and guide notes; at most 40 hits."""
    def snip(text, at):
        s = re.sub(r"\s+", " ", text[max(0, at - 50):at + 110]).strip()
        return ("…" if at > 50 else "") + s

    hits = []
    for did, f in deck_files().items():
        try:
            d = load_deck(f)
        except Exception:
            continue
        per = 0
        if q in d["title"].lower():
            hits.append({"deck": did, "title": d["title"], "kind": "guide", "text": d["title"], "i": 0})
        for i, c in enumerate(d["cards"]):
            if per < 5 and (q in c["q"].lower() or q in c["a"].lower()):
                hits.append({"deck": did, "title": d["title"], "kind": "card", "text": c["q"], "i": i}); per += 1
        per = 0
        for i, x in enumerate(d["quiz"]):
            if per < 4 and q in x["q"].lower():
                hits.append({"deck": did, "title": d["title"], "kind": "quiz", "text": clean_md(x["q"]), "i": i}); per += 1
        for g in d["guide"]["glossary"]:
            if q in g["term"].lower() or q in g["definition"].lower():
                hits.append({"deck": did, "title": d["title"], "kind": "term", "text": g["term"] + ": " + g["definition"], "i": 0})
                break
        at = d["guide"]["notes"].lower().find(q)
        if at >= 0:
            hits.append({"deck": did, "title": d["title"], "kind": "note", "text": snip(d["guide"]["notes"], at), "i": 0})
    order = {"guide": 0, "term": 1, "card": 2, "quiz": 3, "note": 4}
    hits.sort(key=lambda h: order[h["kind"]])
    return hits[:40]


def clean_md(s):
    return re.sub(r"\s+", " ", s.replace("**", "")).strip()[:200]


def _parse_deck(path):
    p = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {
        "title": p.get("title", path.stem),
        "guide": {
            "summary": str(p.get("summary") or ""),
            "notes": str(p.get("detailed_notes") or ""),
            "concepts": [k if isinstance(k, str) else " ".join(str(v) for v in k.values()) if isinstance(k, dict) else str(k)
                         for k in p.get("key_concepts") or []],
            "glossary": [{"term": str(g.get("term", "")), "definition": str(g.get("definition", ""))}
                         for g in p.get("glossary") or [] if isinstance(g, dict)],
            "cheat": str(p.get("cheat_sheet") or ""),
            "takeaways": [str(t) for t in p.get("takeaways") or []],
        },
        "notes": str(p.get("detailed_notes") or ""),
        "cards": [{"q": c["front"], "a": c["back"]} for c in p.get("flashcards") or []],
        "quiz": [
            {"q": q["question"], "a": str(q["answer"]), "e": q.get("explanation", ""),
             "o": q.get("options") or [], "t": q.get("type", "")}
            for q in p.get("quiz_questions") or []
        ],
    }


QTYPES = ("multiple_choice", "true_false", "fill_blank", "comparison")
more_lock = threading.Lock()


def _norm_q(q):
    """Validate one generated question into the pack's schema, or None."""
    if not isinstance(q, dict) or q.get("type") not in QTYPES:
        return None
    question, ans = str(q.get("question", "")).strip(), str(q.get("answer", "")).strip()
    if not question or not ans:
        return None
    diff = q.get("difficulty") if q.get("difficulty") in ("easy", "medium", "hard") else "medium"
    item = {"question": question, "answer": ans, "explanation": str(q.get("explanation", "")),
            "difficulty": diff, "type": q["type"]}
    if q["type"] == "multiple_choice":
        opts = q.get("options")
        if not (isinstance(opts, list) and len(opts) == 4) or ans[:1].upper() not in "ABCD":
            return None
        item["options"] = ["ABCD"[i] + ". " + re.sub(r"^[A-Da-d][).:]\s*", "", str(o)) for i, o in enumerate(opts)]
        item["answer"] = ans[:1].upper()
    elif q["type"] == "true_false":
        item["answer"] = "True" if ans.lower().startswith("t") else "False"
    return item


def make_more(did, kind):
    """Ask the configured model for NEW cards/questions (avoiding existing ones) and append them to the pack yaml."""
    from openai import OpenAI

    path = deck_files()[did]
    cfg = dotenv_values(ROOT / ".env")
    p = yaml.safe_load(path.read_text(encoding="utf-8"))
    cards, quiz = p.setdefault("flashcards", []), p.setdefault("quiz_questions", [])
    source = "\n\n".join(filter(None, [
        str(p.get("summary") or ""), str(p.get("detailed_notes") or ""),
        "Key concepts:\n" + "\n".join(str(k) for k in p.get("key_concepts") or []),
        "Glossary: " + json.dumps(p.get("glossary") or [], ensure_ascii=False),
    ]))[:9000]
    want_c, want_q = (15 if kind in ("cards", "both") else 0), (12 if kind in ("quiz", "both") else 0)
    prompt = (
        f"Study notes:\n{source}\n\nAlready covered flashcards (do NOT repeat or paraphrase these):\n"
        + "\n".join("- " + c["front"] for c in cards[-40:])
        + "\n\nAlready covered quiz questions (do NOT repeat):\n"
        + "\n".join("- " + q["question"][:100] for q in quiz[-40:])
        + f"\n\nWrite {want_c} NEW flashcards and {want_q} NEW quiz questions on different facts from the notes. "
        'Return JSON only: {"flashcards":[{"front":"","back":"","tags":[""]}],"quiz_questions":[{"question":"","answer":"",'
        '"explanation":"","difficulty":"easy|medium|hard","type":"multiple_choice|true_false|fill_blank|comparison",'
        '"options":["","","",""]}]}. multiple_choice: exactly 4 options without letters, answer is one letter A-D. '
        "true_false: answer True or False. fill_blank: short answer. comparison: open question with a model answer. "
        "Mix the types. Use only facts supported by the notes."
    )
    client = OpenAI(api_key=cfg["SKILL_ANYTHING_API_KEY"], base_url=cfg["SKILL_ANYTHING_API_BASE"], timeout=120)
    r = client.chat.completions.create(
        model=cfg["SKILL_ANYTHING_MODEL"], temperature=0.7, response_format={"type": "json_object"},
        messages=[{"role": "system", "content": "You write accurate study material. Output valid JSON only."},
                  {"role": "user", "content": prompt}],
    )
    data = json.loads(r.choices[0].message.content)
    seen = {c["front"].strip().lower() for c in cards}
    new_c = []
    for c in data.get("flashcards") or []:
        if isinstance(c, dict) and str(c.get("front", "")).strip() and str(c.get("back", "")).strip() \
                and c["front"].strip().lower() not in seen:
            seen.add(c["front"].strip().lower())
            new_c.append({"front": c["front"].strip(), "back": str(c["back"]).strip(),
                          "tags": [str(t) for t in c.get("tags") or []][:3]})
    new_q = [x for x in map(_norm_q, data.get("quiz_questions") or []) if x]
    if not (new_c[:want_c] or new_q[:want_q]):
        raise ValueError("The model returned nothing usable. Try again.")
    bak = path.with_suffix(".yaml.bak")
    if not bak.exists():
        shutil.copy(path, bak)
    cards.extend(new_c[:want_c])
    quiz.extend(new_q[:want_q])
    path.write_text(yaml.safe_dump(p, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    return {"cards": len(new_c[:want_c]), "quiz": len(new_q[:want_q])}


def auto_assign(did):
    """Put a freshly generated deck into the existing class it belongs to, judged by topic. Returns the class name or ''."""
    try:
        from openai import OpenAI

        c = read_classes()
        if not c["classes"]:
            return ""
        files = deck_files()
        lines = []
        for cl in c["classes"]:
            titles = []
            for k, v in c["assign"].items():
                if v == cl["id"] and k in files and k != did:
                    titles.append(str(yaml.safe_load(files[k].read_text(encoding="utf-8")).get("title", k)))
            lines.append(f'- id: {cl["id"]} | name: {cl["name"]} | guides: {"; ".join(titles[:8]) or "none yet"}')
        p = yaml.safe_load(files[did].read_text(encoding="utf-8"))
        prompt = (
            "University classes:\n" + "\n".join(lines)
            + f'\n\nNew study guide: "{p.get("title", did)}"\nSummary: {str(p.get("summary") or "")[:600]}'
            + "\nKey concepts: " + "; ".join(str(k)[:60] for k in (p.get("key_concepts") or [])[:8])
            + '\n\nWhich class does this guide belong to? Reply JSON only: {"class_id": "<id>"} or {"class_id": null}. '
            "Pick a class only if the guide clearly belongs to that course's subject; otherwise null."
        )
        cfg = dotenv_values(ROOT / ".env")
        r = OpenAI(api_key=cfg["SKILL_ANYTHING_API_KEY"], base_url=cfg["SKILL_ANYTHING_API_BASE"], timeout=60).chat.completions.create(
            model=cfg["SKILL_ANYTHING_MODEL"], temperature=0, response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}])
        cid = json.loads(r.choices[0].message.content).get("class_id")
        c = read_classes()  # re-read: the user may have edited classes meanwhile
        match = next((x for x in c["classes"] if x["id"] == cid), None)
        if not match:
            return ""
        c["assign"][did] = match["id"]
        (ROOT / "classes.json").write_text(json.dumps(c), encoding="utf-8")
        return match["name"]
    except Exception:  # matching is a convenience; the deck is already saved
        return ""


locate_lock = threading.Lock()


def locate(q, a, passages):
    """Ask the model which numbered guide passages actually explain this flashcard. Returns indices, best first.
    Answers are cached in locate_cache.json, so asking again for the same card is instant and free."""
    import hashlib
    from openai import OpenAI

    key = hashlib.sha1(json.dumps([q, a, passages], ensure_ascii=False).encode("utf-8")).hexdigest()
    cache_f = ROOT / "locate_cache.json"
    with locate_lock:
        try:
            cache = json.loads(cache_f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            cache = {}
    if key in cache:
        return cache[key]
    listing = "\n".join(f"[{i}] ({p.get('heading', '')[:80]}) {p['text'][:420]}" for i, p in enumerate(passages))
    prompt = (
        f"Flashcard question: {q}\nFlashcard answer: {a}\n\n"
        f"Numbered passages from the student's study guide (section heading in brackets):\n{listing}\n\n"
        "Which passages actually explain or teach what this flashcard tests: the definition, the reasoning, "
        "the worked example or the rule behind the answer? Ignore passages that only share words. "
        'Reply JSON only: {"passages": [numbers, best first, at most 4]}; use [] if none explain it.'
    )
    cfg = dotenv_values(ROOT / ".env")
    r = OpenAI(api_key=cfg["SKILL_ANYTHING_API_KEY"], base_url=cfg["SKILL_ANYTHING_API_BASE"], timeout=60).chat.completions.create(
        model=cfg["SKILL_ANYTHING_MODEL"], temperature=0, response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
        # picking passages needs little deliberation; reasoning models answer several times faster on low
        **({"reasoning_effort": "low"} if "gpt-oss" in cfg["SKILL_ANYTHING_MODEL"] else {}))
    picked = json.loads(r.choices[0].message.content).get("passages") or []
    out = []
    for i in picked:
        if isinstance(i, int) and 0 <= i < len(passages) and i not in out:
            out.append(i)
    out = out[:4]
    with locate_lock:
        try:
            cache = json.loads(cache_f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            cache = {}
        cache[key] = out
        if len(cache) > 3000:  # keep the file small: drop the oldest half
            cache = dict(list(cache.items())[-1500:])
        cache_f.write_text(json.dumps(cache), encoding="utf-8")
    return out


def run_job(pdf, stem):
    sa = Path(sys.executable).parent / "sa.exe"
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "NO_COLOR": "1"}
    cls = ""
    try:
        r = subprocess.run(
            [str(sa), "pdf", str(pdf), "-o", str(OUT / stem), "-f", "study"],
            cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8",
            errors="replace", stdin=subprocess.DEVNULL, creationflags=0x08000000,
        )
        text = (r.stdout or "") + (r.stderr or "")
        if r.returncode == 0:
            state, msg = "done", stem
            cls = auto_assign(stem)
        else:
            lines = [ln for ln in text.splitlines() if ln.strip()]
            err = next((ln for ln in lines if "Error" in ln), lines[-1] if lines else "unknown error")
            state, msg = "error", err[:300]
    except OSError as e:
        state, msg = "error", str(e)
    with lock:
        job.update(state=state, msg=msg, cls=cls)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json", headers=None):
        data = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
        self.send_response(code)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def link_key(self):
        return parse_qs(self.path.partition("?")[2]).get("k", [""])[0]

    def host_ok(self):
        host, client = self.headers.get("Host", "").split(":")[0], self.client_address[0]
        if host in ("127.0.0.1", "localhost") and client == "127.0.0.1":
            return True
        if not LAN:
            return False
        # phone mode: the secret key is the guard (cookie from the link, or the link itself); any host name or address
        cookie = SimpleCookie(self.headers.get("Cookie", "")).get("k", Morsel()).value or ""
        ok = secrets.compare_digest(cookie, LAN_KEY) or secrets.compare_digest(self.link_key(), LAN_KEY)
        if not ok:
            print(f"refused {client} {self.command} {self.path.split('?')[0]} host={host} cookie={'wrong' if cookie else 'none'}", flush=True)
        return ok

    def do_GET(self):
        path = self.path.split("?")[0]
        if not self.host_ok():
            if LAN and path == "/":
                return self.send(403, b"<meta name=viewport content='width=device-width'><body style='font:17px system-ui;padding:24px'>"
                                 b"<h2>Open the full link</h2><p>Use the whole link shown in the StudyPhone window on the computer, "
                                 b"including the part after <b>?k=</b>.</p>", "text/html")
            return self.send(403, {"error": "bad host"})
        if path == "/":
            # phone mode: the link's key becomes a cookie, so the API calls and later visits work without it
            extra = {"Set-Cookie": f"k={LAN_KEY}; Path=/; Max-Age=31536000; HttpOnly; SameSite=Lax"} if LAN and self.link_key() else {}
            return self.send(200, UI.read_bytes(), "text/html", extra)
        if path.startswith("/assets/"):
            # rendered turntable sheets; only plain file names, only images
            name = unquote(path[len("/assets/"):])
            f = ROOT / "assets" / name
            if "/" in name or "\\" in name or f.suffix not in (".webp", ".png") or not f.is_file():
                return self.send(404, {"error": "not found"})
            data = f.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/webp" if f.suffix == ".webp" else "image/png")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "max-age=86400")
            self.end_headers()
            self.wfile.write(data)
            return
        if path.startswith("/vendor/"):
            # bundled third-party front-end files (KaTeX); only inside vendor/, only these types
            types = {".js": "text/javascript", ".css": "text/css", ".woff2": "font/woff2"}
            base = (ROOT / "vendor").resolve()
            f = (base / unquote(path[len("/vendor/"):])).resolve()
            if not f.is_relative_to(base) or f.suffix not in types or not f.is_file():
                return self.send(404, {"error": "not found"})
            data = f.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", types[f.suffix])
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "max-age=604800")
            self.end_headers()
            self.wfile.write(data)
            return
        if path == "/api/collection":
            out = []
            for did, f in deck_files().items():
                try:
                    out.append({"id": did, "cards": [c["q"] for c in load_deck(f)["cards"]]})
                except Exception:  # one broken deck must not hide the binder
                    continue
            return self.send(200, {"decks": out})
        if path == "/api/search":
            q = parse_qs(self.path.partition("?")[2]).get("q", [""])[0].strip().lower()
            return self.send(200, {"hits": search(q) if len(q) >= 2 else []})
        if path == "/api/ping":
            last_ping[0] = time.time()
            return self.send(200, {"ok": True})
        if path == "/api/decks":
            decks = []
            for did, f in deck_files().items():
                try:
                    d = load_deck(f)
                except Exception:  # a broken yaml must not hide the other decks
                    continue
                decks.append({"id": did, "title": d["title"], "cards": len(d["cards"]),
                              "quiz": len(d["quiz"]), "mtime": f.stat().st_mtime,
                              "guide": bool(d["guide"]["notes"] or d["guide"]["summary"])})
            return self.send(200, {"decks": decks, "progress": read_progress(), "classes": read_classes(),
                                  "stats": read_stats(), "settings": read_settings()})
        if path == "/api/job":
            with lock:
                return self.send(200, dict(job, elapsed=int(time.time() - job["started"])))
        if path.startswith("/api/deck/"):
            f = deck_files().get(unquote(path[len("/api/deck/"):]))
            if not f:
                return self.send(404, {"error": "no such deck"})
            return self.send(200, load_deck(f))
        self.send(404, {"error": "not found"})

    def do_POST(self):
        try:
            self._post()
        except (ValueError, TypeError, KeyError):  # malformed JSON body etc.
            self.send(400, {"error": "bad request"})

    def _post(self):
        if not self.host_ok() or self.headers.get("X-App") != "1":
            return self.send(403, {"error": "forbidden"})
        length = int(self.headers.get("Content-Length") or 0)
        path = self.path.split("?")[0]
        if path == "/api/upload":
            name = Path(unquote(self.headers.get("X-Filename", "upload.pdf"))).name
            if not name.lower().endswith(".pdf") or length <= 0 or length > MAX_UPLOAD:
                return self.send(400, {"error": "Send a .pdf under 200 MB"})
            with lock:
                if job["state"] == "running":
                    return self.send(409, {"error": "Another PDF is still being processed"})
                job.update(state="running", name=name, msg="", cls="", started=time.time())
            UP.mkdir(exist_ok=True)
            dest = UP / name
            with open(dest, "wb") as fh:
                left = length
                while left > 0:
                    chunk = self.rfile.read(min(1 << 20, left))
                    if not chunk:
                        break
                    fh.write(chunk)
                    left -= len(chunk)
            threading.Thread(target=run_job, args=(dest, dest.stem), daemon=True).start()
            return self.send(200, {"ok": True})
        if path.startswith("/api/progress/"):
            did = unquote(path[len("/api/progress/"):])
            if did not in deck_files() or length > 5_000_000:
                return self.send(400, {"error": "bad deck"})
            prog = read_progress()
            prog[did] = json.loads(self.rfile.read(length))
            PROG.write_text(json.dumps(prog), encoding="utf-8")
            return self.send(200, {"ok": True})
        if path.startswith("/api/stat/"):
            parts = path[len("/api/stat/"):].split("/", 1)
            kind, did = parts[0], unquote(parts[1]) if len(parts) > 1 else ""
            if kind not in ("quiz", "review") or did not in deck_files() or length > 10_000:
                return self.send(400, {"error": "bad request"})
            add_stat(kind, did, json.loads(self.rfile.read(length) or b"{}"))
            return self.send(200, {"ok": True})
        if path.startswith("/api/more/"):
            did = unquote(path[len("/api/more/"):])
            kind = (json.loads(self.rfile.read(length) or b"{}")).get("kind")
            if did not in deck_files() or kind not in ("cards", "quiz", "both"):
                return self.send(400, {"error": "bad request"})
            if not more_lock.acquire(blocking=False):
                return self.send(409, {"error": "Already generating, wait a moment"})
            try:
                return self.send(200, make_more(did, kind))
            except Exception as e:  # surface API/rate-limit/JSON problems to the user
                return self.send(502, {"error": f"{type(e).__name__}: {str(e)[:250]}"})
            finally:
                more_lock.release()
        if path == "/api/locate":
            if length > 200_000:
                return self.send(400, {"error": "too big"})
            body = json.loads(self.rfile.read(length))
            q, a, ps = str(body["q"])[:1000], str(body["a"])[:2000], body["passages"]
            if not isinstance(ps, list) or not 0 < len(ps) <= 60:
                return self.send(400, {"error": "send 1 to 60 passages"})
            ps = [{"text": str(p.get("text", ""))[:600], "heading": str(p.get("heading", ""))[:120]} for p in ps if isinstance(p, dict)]
            try:
                return self.send(200, {"passages": locate(q, a, ps)})
            except Exception as e:  # offline, rate limit or bad JSON: the page falls back to word matching
                return self.send(502, {"error": f"{type(e).__name__}: {str(e)[:200]}"})
        if path == "/api/settings":
            goal = int(json.loads(self.rfile.read(length))["goal"])
            if not 1 <= goal <= 500:
                return self.send(400, {"error": "goal must be 1 to 500"})
            (ROOT / "settings.json").write_text(json.dumps({"goal": goal}), encoding="utf-8")
            return self.send(200, {"ok": True})
        if path == "/api/classes":
            if length > 1_000_000:
                return self.send(400, {"error": "too big"})
            c = json.loads(self.rfile.read(length))
            ok = (isinstance(c.get("classes"), list) and isinstance(c.get("assign"), dict)
                  and all(isinstance(x, dict) and isinstance(x.get("id"), str) and isinstance(x.get("name"), str)
                          for x in c["classes"])
                  and all(isinstance(k, str) and isinstance(v, str) for k, v in c["assign"].items()))
            if not ok:
                return self.send(400, {"error": "bad classes"})
            (ROOT / "classes.json").write_text(json.dumps({"classes": c["classes"], "assign": c["assign"]}), encoding="utf-8")
            return self.send(200, {"ok": True})
        if path.startswith("/api/delete/"):
            did = unquote(path[len("/api/delete/"):])
            if did not in deck_files():
                return self.send(400, {"error": "bad deck"})
            shutil.rmtree(OUT / did)
            return self.send(200, {"ok": True})
        self.send(404, {"error": "not found"})


def open_window():
    url = f"http://127.0.0.1:{PORT}"
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
        for rel in ("Microsoft/Edge/Application/msedge.exe", "Google/Chrome/Application/chrome.exe"):
            exe = Path(base or "") / rel
            if base and exe.exists():
                subprocess.Popen([str(exe), f"--app={url}", "--window-size=1100,800"])
                return
    webbrowser.open(url)


def watchdog():
    while True:
        time.sleep(10)
        with lock:
            busy = job["state"] == "running"
        if last_ping[0] and not busy and time.time() - last_ping[0] > IDLE_EXIT:
            os._exit(0)


def lan_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))  # picks the Wi-Fi interface; UDP connect sends nothing
        return s.getsockname()[0]


def main():
    global LAN_IP, LAN_KEY
    if LAN:
        LAN_IP, LAN_KEY = lan_ip(), (ROOT / ".phone_key").read_text().strip() if (ROOT / ".phone_key").exists() else ""
        if not LAN_KEY:  # kept between runs so a phone that opened the link once stays signed in
            LAN_KEY = secrets.token_urlsafe(16)
            (ROOT / ".phone_key").write_text(LAN_KEY)
    try:
        server = ThreadingHTTPServer(("0.0.0.0" if LAN else "127.0.0.1", PORT), Handler)
    except OSError:  # already running: just open another window onto it
        open_window()
        return
    if not LAN:  # phone mode runs until its window is closed; a phone in a pocket stops pinging
        threading.Thread(target=watchdog, daemon=True).start()
    if LAN:
        print(f"\nPhone mode. On a phone on the same Wi-Fi, open:\n\n    http://{LAN_IP}:{PORT}/?k={LAN_KEY}\n\n"
              "Keep this link private. Close this window to stop.\n", flush=True)
    open_window()
    server.serve_forever()


UI = ROOT / "ui.html"  # the whole front end; re-read per request so edits show on refresh

if __name__ == "__main__":
    main()
