"""Turn a Skill-Anything pack .yaml into one self-contained, clickable HTML study page.

Usage: python make_html.py output/test/pack.yaml   (writes pack.html next to it)
"""
import json
import sys
from pathlib import Path

import yaml

src = Path(sys.argv[1])
p = yaml.safe_load(src.read_text(encoding="utf-8"))
data = {
    "title": p["title"],
    "cards": [{"q": c["front"], "a": c["back"]} for c in p.get("flashcards", [])],
    "quiz": [
        {"q": q["question"], "a": str(q["answer"]), "e": q.get("explanation", ""), "o": q.get("options") or []}
        for q in p.get("quiz_questions", [])
    ],
}

PAGE = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>__T__</title>
<style>
body{font:16px system-ui,sans-serif;max-width:760px;margin:0 auto;padding:16px;background:#f4f5f7;color:#1c1e21}
h1{font-size:1.4rem}nav button{padding:8px 16px;margin-right:6px;border:0;border-radius:8px;background:#dde1e7;cursor:pointer}
nav button.on{background:#2f6fed;color:#fff}.card{min-height:180px;display:flex;align-items:center;justify-content:center;
text-align:center;padding:24px;margin:16px 0;background:#fff;border-radius:14px;box-shadow:0 2px 8px #0002;cursor:pointer;font-size:1.15rem;white-space:pre-wrap}
.card.back{background:#e8f0ff}.row{display:flex;gap:8px;align-items:center}.row button{padding:8px 14px;border-radius:8px;border:0;background:#2f6fed;color:#fff;cursor:pointer}
.opt{display:block;width:100%;text-align:left;margin:6px 0;padding:10px;border:1px solid #ccd;border-radius:8px;background:#fff;cursor:pointer;font:inherit}
.opt.right{background:#c9f2d3}.opt.wrong{background:#f9c9c9}.exp{margin-top:12px;padding:12px;background:#fff;border-left:4px solid #2f6fed;border-radius:6px;white-space:pre-wrap}
input{width:100%;padding:10px;font:inherit;border:1px solid #ccd;border-radius:8px;box-sizing:border-box}
</style>
<h1>__T__</h1>
<nav><button id=bc class=on>Flashcards</button><button id=bq>Quiz</button></nav>
<div id=app></div>
<script>
const D=__D__;let mode="c",i=0,flip=false,score=0,answered=false;
const $=s=>document.querySelector(s),app=$("#app"),esc=s=>s.replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
function nav(m){mode=m;i=0;flip=false;score=0;answered=false;$("#bc").className=m=="c"?"on":"";$("#bq").className=m=="q"?"on":"";draw()}
$("#bc").onclick=()=>nav("c");$("#bq").onclick=()=>nav("q");
function go(d,n){i=(i+d+n)%n;flip=false;answered=false;draw()}
function draw(){
 if(mode=="c"){const c=D.cards[i];
  app.innerHTML=`<div class="card ${flip?"back":""}" id=cd>${esc(flip?c.a:c.q)}</div><div class=row><button id=pv>&larr;</button><span>${i+1} / ${D.cards.length} (click card to flip)</span><button id=nx>&rarr;</button></div>`;
  $("#cd").onclick=()=>{flip=!flip;draw()};$("#pv").onclick=()=>go(-1,D.cards.length);$("#nx").onclick=()=>go(1,D.cards.length);return}
 if(i>=D.quiz.length){app.innerHTML=`<div class=card>Done! Score: ${score} / ${D.quiz.length}</div><div class=row><button id=rs>Restart</button></div>`;$("#rs").onclick=()=>nav("q");return}
 const q=D.quiz[i];let h=`<p><b>Q${i+1}/${D.quiz.length}</b></p><div style="white-space:pre-wrap"><b>${esc(q.q)}</b></div>`;
 if(q.o.length)h+=q.o.map((o,k)=>`<button class=opt data-k="${o[0]}">${esc(o)}</button>`).join("");
 else h+=`<p><input id=fa placeholder="Type your answer, press Enter"></p>`;
 h+=`<div id=fb></div><div class=row><button id=nx>Next &rarr;</button></div>`;app.innerHTML=h;
 const show=ok=>{if(answered)return;answered=true;if(ok)score++;
  $("#fb").innerHTML=`<div class=exp><b>${ok?"Correct":"Answer: "+esc(q.a)}</b>\\n\\n${esc(q.e)}</div>`};
 document.querySelectorAll(".opt").forEach(b=>b.onclick=()=>{const ok=b.dataset.k==q.a[0];if(answered)return;
  b.classList.add(ok?"right":"wrong");document.querySelectorAll(".opt").forEach(x=>{if(x.dataset.k==q.a[0])x.classList.add("right")});show(ok)});
 const f=$("#fa");if(f)f.onkeydown=e=>{if(e.key=="Enter"){const norm=s=>s.toLowerCase().replace(/[^a-z0-9]/g,"");show(norm(f.value)==norm(q.a)||(norm(f.value).length>3&&norm(q.a).includes(norm(f.value))))}};
 $("#nx").onclick=()=>{i++;answered=false;draw()}}
draw();
</script>"""

out = src.with_suffix(".html")
out.write_text(PAGE.replace("__T__", data["title"]).replace("__D__", json.dumps(data)), encoding="utf-8")
print(out)
