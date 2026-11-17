#!/usr/bin/env python3
"""Build the BINA course player pages from content/*.json files.
Usage: python3 build_course.py [--no-audio]
Reads whichever content/pX_he.json / pX_en.json exist, renders lesson pages
under site_he/course/ and site_en/course/, and (unless --no-audio) generates
lecturer intro audio via edge-tts into site_*/assets/audio/.
"""
import json, os, re, sys, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))

TRACKS = {
    "p1": {"he": {"name": "AI ביום-יום", "lecturer": "נועה", "price": "197₪", "en_price": "$49"},
           "en": {"name": "Everyday AI", "lecturer": "Alex", "price": "$49"}},
    "p2": {"he": {"name": "קריירה ב-AI", "lecturer": "נועה", "price": "997₪", "en_price": "$249"},
           "en": {"name": "AI Career", "lecturer": "Alex", "price": "$249"}},
    "p3": {"he": {"name": "AI מתקדם", "lecturer": "רוני", "price": "1,997₪", "en_price": "$499"},
           "en": {"name": "Advanced AI", "lecturer": "Roni", "price": "$499"}},
}
VOICES = {("he","p1"): "he-IL-HilaNeural", ("he","p2"): "he-IL-HilaNeural",
         ("he","p3"): "he-IL-HilaNeural",  # Roni HE (pitch-shifted)
         ("en","p1"): "en-US-ChristopherNeural", ("en","p2"): "en-US-ChristopherNeural",
         ("en","p3"): "en-US-JennyNeural"}

T = {  # UI strings
 "he": {"course":"הקורס", "lessons":"שיעורים", "goal":"מה תדעו לעשות", "listen":"השמע את המרצה",
        "try":"פרומפט מוכן להעתקה", "copy":"העתק", "copied":"הועתק!", "exercise":"תרגיל",
        "prev":"שיעור קודם", "next":"שיעור הבא", "done":"סמן כהושלם ✓", "completed":"הושלם ✓",
        "all":"כל המסלולים", "back":"חזרה לאתר", "home":"בינה", "progress":"ההתקדמות שלך",
        "backToCourse":"כל השיעורים", "toSite":"לעמוד הבית"},
 "en": {"course":"Course", "lessons":"lessons", "goal":"What you'll be able to do", "listen":"Play the lecturer",
        "try":"Copy-ready prompt", "copy":"Copy", "copied":"Copied!", "exercise":"Exercise",
        "prev":"Previous", "next":"Next", "done":"Mark complete ✓", "completed":"Done ✓",
        "all":"All tracks", "back":"Back", "home":"BINA", "progress":"Your progress",
        "backToCourse":"All lessons", "toSite":"Home"},
}

def md(text):
    """markdown-lite -> HTML: paragraphs, **bold**, `code`, - lists."""
    def inline(s):
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
        return s
    out, in_list = [], False
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            if in_list: out.append("</ul>"); in_list = False
            continue
        if line.startswith("- "):
            if not in_list: out.append("<ul>"); in_list = True
            out.append(f"<li>{inline(line[2:])}</li>")
        else:
            if in_list: out.append("</ul>"); in_list = False
            out.append(f"<p>{inline(line)}</p>")
    if in_list: out.append("</ul>")
    return "\n".join(out)

CSS = """
:root{--bg:#0a0a10;--bg2:#101018;--card:#15151f;--ink:#f4f4fa;--mut:#a0a0af;
--pur:#8b5cf6;--teal:#2dd4bf;--gold:#fbbf24;--border:#232330}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:'Rubik','Inter',sans-serif;line-height:1.75}
a{color:var(--teal);text-decoration:none}
.wrap{max-width:860px;margin:0 auto;padding:0 22px}
.topbar{position:sticky;top:0;z-index:10;background:rgba(10,10,16,.9);backdrop-filter:blur(8px);border-bottom:1px solid var(--border)}
.topbar .in{max-width:860px;margin:0 auto;padding:14px 22px;display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.logo{font-weight:900;font-size:1.2rem;color:var(--ink)}
.logo b{color:var(--pur)}
.crumb{color:var(--mut);font-size:.9rem}
main{padding:44px 0 90px}
.goal{display:inline-block;background:rgba(45,212,191,.12);border:1px solid rgba(45,212,191,.35);color:var(--teal);padding:8px 18px;border-radius:100px;font-size:.92rem;margin:6px 0 26px}
h1{font-size:clamp(1.7rem,4vw,2.5rem);font-weight:900;line-height:1.25;margin-bottom:8px}
h2{font-size:1.35rem;font-weight:700;margin:38px 0 12px;color:var(--ink)}
h2::before{content:'';display:inline-block;width:26px;height:3px;background:var(--pur);border-radius:2px;margin-inline-end:12px;vertical-align:middle}
p{margin:0 0 14px;color:#d8d8e4}
ul{margin:0 0 14px;padding-inline-start:24px}
li{margin-bottom:8px;color:#d8d8e4}
code{background:#1d1d2a;border:1px solid var(--border);padding:1px 7px;border-radius:6px;font-size:.9em;direction:ltr;display:inline-block}
.audiobox{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:18px 20px;margin:4px 0 10px;display:flex;align-items:center;gap:14px}
.audiobox img{width:52px;height:52px;border-radius:50%;object-fit:cover}
.audiobox span{color:var(--mut);font-size:.9rem}
audio{width:100%;height:40px}
.prompt{background:var(--card);border:1px solid var(--border);border-inline-start:3px solid var(--teal);border-radius:12px;padding:16px 18px;margin:12px 0;position:relative}
.prompt p{margin:0 0 0;white-space:pre-wrap;font-size:.95rem;color:#e8e8f2}
.copy{position:absolute;top:10px;inset-inline-end:10px;background:rgba(45,212,191,.12);border:1px solid rgba(45,212,191,.35);color:var(--teal);padding:4px 14px;border-radius:100px;cursor:pointer;font-size:.8rem;font-family:inherit}
.exbox{background:linear-gradient(180deg,rgba(251,191,36,.08),transparent);border:1px dashed rgba(251,191,36,.4);border-radius:14px;padding:20px 22px;margin:34px 0}
.exbox h3{color:var(--gold);font-size:1.05rem;margin-bottom:8px}
.nav{display:flex;justify-content:space-between;gap:14px;margin-top:50px;flex-wrap:wrap}
.btn{display:inline-block;padding:13px 26px;border-radius:12px;font-weight:700;font-size:.95rem;cursor:pointer;border:none;font-family:inherit}
.b1{background:var(--pur);color:#fff}.b2{background:transparent;color:var(--ink);border:1px solid var(--border)}
.b1:hover{filter:brightness(1.15)}.b2:hover{border-color:var(--pur)}
.donebtn{width:100%;margin-top:26px;background:rgba(45,212,191,.12);border:1px solid rgba(45,212,191,.4);color:var(--teal);padding:14px;border-radius:12px;font-size:1rem;cursor:pointer;font-family:inherit;font-weight:700}
.donebtn.on{background:rgba(45,212,191,.25)}
/* course index */
.tracks{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px;margin-top:34px}
.tcard{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:26px}
.tcard h2{margin:0 0 4px;font-size:1.3rem}
.tcard .lec{color:var(--teal);font-size:.9rem;margin-bottom:14px}
.tcard .pr{color:var(--gold);font-weight:700;margin-bottom:14px}
.pbar{height:6px;background:#1d1d2a;border-radius:3px;overflow:hidden;margin:10px 0 4px}
.pbar i{display:block;height:100%;background:var(--teal);width:0%}
.plist{list-style:none;margin-top:10px}
.plist li a{display:flex;gap:10px;align-items:center;padding:10px 6px;border-bottom:1px dashed var(--border);color:var(--ink);font-size:.95rem}
.plist li a:hover{color:var(--teal)}
.plist .n{color:var(--mut);font-family:monospace;font-size:.85rem;flex-shrink:0}
.chip{background:rgba(139,92,246,.15);color:#c4b0f5;border:1px solid rgba(139,92,246,.35);border-radius:100px;padding:1px 10px;font-size:.75rem;flex-shrink:0}
"""

def page_head(lang, title, rel_root=".."):
    fonts = "Rubik:wght@400;500;700;900" if lang == "he" else "Rubik:wght@400;500;700;900&family=Inter:wght@400;500;700"
    fam = "'Rubik',sans-serif" if lang == "he" else "'Inter',sans-serif"
    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{'rtl' if lang=='he' else 'ltr'}">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · בינה BINA</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family={fonts}&display=swap" rel="stylesheet">
<style>body{{font-family:{fam}}}{CSS}</style></head><body>"""

def lesson_page(lang, track, lesson, idx, total, rel_root=".."):
    t = T[lang]; meta = TRACKS[track][lang]
    lecturer = "נועה" if lang == "he" else ("Alex" if track != "p3" else "Roni")
    avatar = ("noa" if lang == "he" else ("alex" if track != "p3" else "roni")) + ".png"
    sections = "\n".join(f"<h2>{s['h']}</h2>\n{md(s['body'])}" for s in lesson["sections"])
    prompts = ""
    for p in lesson.get("prompts", []):
        prompts += f"""<div class="prompt"><p>{p.replace('<','&lt;').replace('>','&gt;')}</p>
<button class="copy" onclick="cp(this)">{t['copy']}</button></div>\n"""
    prev_id = f"{track}-{idx-1:02d}" if idx > 1 else None
    next_id = f"{track}-{idx+1:02d}" if idx < total else None
    prev_lnk = f"<a class='btn b2' href='{prev_id}.html'>← {t['prev']}</a>" if prev_id else "<span></span>"
    next_lnk = f"<a class='btn b1' href='{next_id}.html'>{t['next']} →</a>" if next_id else f"<a class='btn b1' href='index.html'>{t['all']} →</a>"
    return f"""{page_head(lang, lesson['title'])}
<div class="topbar"><div class="in">
<a class="logo" href="{rel_root}/index.html">בינ<b>ה</b> · BINA</a>
<span class="crumb">{meta['name']} · {t['course']} {idx}/{total}</span>
</div></div>
<main><div class="wrap">
<h1>{lesson['title']}</h1>
<div class="goal">🎯 {t['goal']}: {lesson['goal']}</div>
<div class="audiobox"><img src="{rel_root}/assets/{avatar}" alt="{lecturer}">
<div style="flex:1"><span>{lecturer} · {t['listen']}</span>
<audio controls preload="none" src="{rel_root}/assets/audio/{lesson['id']}.mp3"></audio></div></div>
{sections}
{f"<h2>{t['try']}</h2>" + prompts if prompts else ""}
<div class="exbox"><h3>💪 {t['exercise']}</h3><p>{md(lesson['exercise'])}</p></div>
<div class="nav">{prev_lnk}{next_lnk}</div>
<button class="donebtn" id="done" onclick="markDone()">{t['done']}</button>
</div></main>
<script>
const ID='{lesson['id']}';
const done=localStorage.getItem('bina-'+ID)==='1';
const b=document.getElementById('done');
if(done){{b.classList.add('on');b.textContent='{t['completed']}';}}
function markDone(){{const d=localStorage.getItem('bina-'+ID)==='1';
localStorage.setItem('bina-'+ID,d?'0':'1');
if(!d){{b.classList.add('on');b.textContent='{t['completed']}';}}else{{b.classList.remove('on');b.textContent='{t['done']}';}}}}
function cp(btn){{const txt=btn.parentElement.querySelector('p').innerText;
navigator.clipboard.writeText(txt);btn.textContent='{t['copied']}';
setTimeout(()=>btn.textContent='{t['copy']}',1500);}}
</script></body></html>"""

def index_page(lang, tracks_data):
    t = T[lang]
    cards = ""
    for track, lessons, meta in tracks_data:
        total = len(lessons)
        items = "".join(
            f"<li><a href='{track}/{l['id']}.html'><span class='n'>{l['id']}</span>{l['title']}"
            f"<span class='chip' data-done='{l['id']}'></span></a></li>" for l in lessons)
        cards += f"""<div class="tcard"><h2>{meta['name']}</h2>
<div class="lec">🎓 {meta['lecturer']} · {total} {t['lessons']}</div>
<div class="pr">{meta['price']}</div>
<div class="pbar" data-track="{track}"><i></i></div>
<span style="font-size:.8rem;color:var(--mut)" data-plabel="{track}"></span>
<ul class="plist">{items}</ul></div>\n"""
    return f"""{page_head(lang, T[lang]['course'], ".")}
<div class="topbar"><div class="in">
<a class="logo" href="../index.html">בינ<b>ה</b> · BINA</a>
<span class="crumb">{t['course']}</span>
</div></div>
<main><div class="wrap">
<h1>{t['progress']}</h1>
<div class="tracks">{cards}</div>
</div></main>
<script>
const TRACKS={json.dumps([t0 for t0,_,_ in tracks_data])};
const COUNTS={json.dumps({t0: len(ls) for t0,ls,_ in tracks_data})};
let tot=0,dn=0;
TRACKS.forEach(tr=>{{let d=0;
for(let i=1;i<=COUNTS[tr];i++){{const id=tr+'-'+String(i).padStart(2,'0');
if(localStorage.getItem('bina-'+id)==='1'){{d++;const c=document.querySelector(`[data-done="${{id}}"]`);if(c)c.textContent='✓';}}}}
tot+=COUNTS[tr];dn+=d;
const bar=document.querySelector(`[data-track="${{tr}}"] i`);
if(bar)bar.style.width=(d/COUNTS[tr]*100)+'%';
const lab=document.querySelector(`[data-plabel="${{tr}}"]`);
if(lab)lab.textContent=d+'/'+COUNTS[tr];}});
document.title+=dn>0?` (${{dn}}✓)`:'';
</script></body></html>"""

def main():
    make_audio = "--no-audio" not in sys.argv
    audios = []  # (text, voice, outpath, pitch)
    for lang, site in [("he", "site_he"), ("en", "site_en")]:
        tracks_data = []
        for track in ["p1", "p2", "p3"]:
            cpath = f"{ROOT}/content/{track}_{lang}.json"
            if not os.path.exists(cpath):
                continue
            data = json.load(open(cpath))
            lessons = data["lessons"]
            os.makedirs(f"{ROOT}/{site}/course/{track}", exist_ok=True)
            total = len(lessons)
            for idx, lesson in enumerate(lessons, 1):
                html = lesson_page(lang, track, lesson, idx, total)
                with open(f"{ROOT}/{site}/course/{track}/{lesson['id']}.html", "w") as f:
                    f.write(html)
                if make_audio:
                    out = f"{ROOT}/{site}/assets/audio/{lesson['id']}.mp3"
                    os.makedirs(os.path.dirname(out), exist_ok=True)
                    if not os.path.exists(out):
                        pitch = "-20Hz" if (lang == "he" and track == "p3") else "+0Hz"
                        audios.append((lesson["audio_intro"], VOICES[(lang, track)], out, pitch))
            tracks_data.append((track, lessons, TRACKS[track][lang]))
            print(f"{site}/{track}: {total} lessons")
        if tracks_data:
            with open(f"{ROOT}/{site}/course/index.html", "w") as f:
                f.write(index_page(lang, tracks_data))
    if make_audio and audios:
        async def gen_all():
            import edge_tts
            sem = asyncio.Semaphore(4)
            async def one(text, voice, out, pitch):
                async with sem:
                    for attempt in range(3):
                        try:
                            c = edge_tts.Communicate(text, voice, rate="+8%", pitch=pitch)
                            await c.save(out)
                            if os.path.getsize(out) > 20000:
                                return True
                        except Exception:
                            await asyncio.sleep(2)
                    print("FAILED:", out)
                    return False
            results = await asyncio.gather(*[one(*a) for a in audios])
            print(f"audio: {sum(results)}/{len(results)} ok")
        asyncio.run(gen_all())
    print("BUILD DONE")

if __name__ == "__main__":
    main()
