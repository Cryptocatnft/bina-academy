#!/usr/bin/env python3
"""BINA social/promo video factory: AR/RU landscape promos + 40 vertical clips (10 x 4 langs)."""
import json, os, asyncio, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = "/root/bina-academy"
A = f"{ROOT}/assets"
DATA = json.load(open(f"{ROOT}/social_clips.json"))
PUR, TEAL, GOLD = (139,92,246), (45,212,191), (251,191,36)
INK, MUT, BG = (244,244,250), (160,160,175), (10,10,16)
ACCENTS = [TEAL, PUR, GOLD, (244,114,182), (96,165,250), (251,146,60), (52,211,153), (167,139,250), (251,146,60), TEAL]

def font(path, size, wght=None):
    f = ImageFont.truetype(f"{A}/{path}", size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f

def base(w, h):
    img = Image.new("RGB", (w, h), BG)
    g = Image.new("RGB", (w, h), BG); gd = ImageDraw.Draw(g)
    gd.ellipse([-w//3, -h//3, w//2, h//2], fill=(30,20,60))
    gd.ellipse([w//2, h//2, w+w//3, h+h//3], fill=(8,55,55))
    return Image.blend(img, g.filter(ImageFilter.GaussianBlur(w//5)), 0.8)

def cover(img, box):
    x0,y0,x1,y1 = box; bw,bh = x1-x0, y1-y0; iw,ih = img.size
    s = max(bw/iw, bh/ih)
    img = img.resize((int(iw*s)+1, int(ih*s)+1))
    return img.crop(((img.width-bw)//2, (img.height-bh)//2, (img.width-bw)//2+bw, (img.height-bh)//2+bh))

def dim(img, amt): return Image.blend(img, Image.new("RGB", img.size, BG), amt)

def T(d, xy, s, fnt, fill, anchor="mm", rtl=True, lang="he"):
    d.text(xy, s, font=fnt, fill=fill, anchor=anchor,
          direction="rtl" if rtl else "ltr", language=lang)

# ---------- LANDSCAPE PROMOS (ar, ru) ----------
PROMOS = {
 "ar": {
   "voice": "ar-EG-SalmaNeural", "avatar": "layla.png", "font": "Tajawal-Bold.ttf", "wght": None, "lang": "ar",
   "s1": [("بينا", 300), ("BINA ACADEMY", "en"), ("الدورة التي بناها الذكاء الاصطناعي", 92), ("ونحن فخورون بذلك", 70)],
   "s2": [("ليلى", 190), ("مدرّسة ذكاء اصطناعي.", 85), ("نعم، هي أيضاً من إنتاج الذكاء الاصطناعي", 58)],
   "s3": [("المسار 1 · الذكاء الاصطناعي اليومي", 92), ("حيل ذكية لا يعرفها أحد", 70)],
   "s4": [("المسار 2 · مسار مهني", 92), ("من الصفر حتى الوظيفة، مع شهادة", 70)],
   "s5": [("المسار 3 · الذكاء الاصطناعي المتقدم", 92), ("سيُذيب دماغ المطورين", 70)],
   "s6": [("BINA.academy", "en"), ("بُني بالذكاء الاصطناعي. ويعلّمك الذكاء الاصطناعي.", 76)],
   "tts": "مرحبا! أنا ليلى، مدرّسة الذكاء الاصطناعي. نعم، أنا أيضاً ذكاء اصطناعي، ونحن فخورون بذلك. كل درس في بينا كُتب وأُنتج بالذكاء الاصطناعي، لأن أفضل ما نجيده هو أن نعلّمك استخدامنا. ثلاثة مسارات: مهارات يومية ذكية، مسار مهني مع شهادة، ومسار متقدم سيُذيب عقلك. هيّا نبدأ!",
 },
 "ru": {
   "voice": "ru-RU-SvetlanaNeural", "avatar": "daria.png", "font": "Rubik.ttf", "wght": 700, "lang": "ru",
   "s1": [("BINA", 300), ("AI ACADEMY", "en"), ("Курс, построенный ИИ", 92), ("и мы этим гордимся", 70)],
   "s2": [("Дарья", 190), ("Преподаватель ИИ.", 85), ("Да, её тоже создал ИИ", 58)],
   "s3": [("Трек 1 · ИИ на каждый день", 92), ("приёмы, которых никто не знает", 70)],
   "s4": [("Трек 2 · Карьера в ИИ", 92), ("от нуля до оффера, с сертификатом", 70)],
   "s5": [("Трек 3 · Продвинутый ИИ", 92), ("взорвёт мозг даже разработчику", 70)],
   "s6": [("BINA.academy", "en"), ("Построен ИИ. Научит вас ИИ.", 76)],
   "tts": "Привет! Я Дарья, ваш преподаватель искусственного интеллекта. И да — меня тоже создал ИИ, и мы этим гордимся. Каждый урок BINA написан и спродюсирован искусственным интеллектом, ведь лучше всего мы умеем учить вас пользоваться нами. Три трека: умные навыки на каждый день, карьерный путь с сертификатом и продвинутый курс, который взорвёт вам мозг. Начнём!",
 },
}
def en_font(sz, w=600):
    f = ImageFont.truetype(f"{A}/SpaceGrotesk.ttf", sz)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f

def build_promo(lang):
    P = PROMOS[lang]
    F = lambda sz: font(P["font"], sz, P["wght"])
    W,H = 1920,1080
    slides = []
    def s_logo():
        img = base(W,H); img.paste(dim(cover(Image.open(f"{A}/hero.png"),(0,0,W,H)),0.6),(0,0)); d=ImageDraw.Draw(img)
        big, small, l3, l4 = P["s1"]
        T(d,(W/2,330),big,F(300),INK,lang=P["lang"])
        d.line([(W/2-360,560),(W/2+360,560)],fill=PUR,width=6)
        d.text((W/2,640),small,font=en_font(64),fill=TEAL,anchor="mm")
        T(d,(W/2,790),l3,F(92),INK,lang=P["lang"]); T(d,(W/2,910),l4,F(70),GOLD,lang=P["lang"])
    def s_lec():
        img = base(W,H)
        # avatar left half for RTL-feel (mirrors HE layout), gradient over its inner edge
        av = cover(Image.open(f"{A}/{P['avatar']}"),(0,0,1100,H)); img.paste(av,(0,0))
        grad = Image.new("L",(700,H),0); gd=ImageDraw.Draw(grad)
        for i in range(700): gd.line([(i,0),(i,H)],fill=int(255*(i/700)))
        img.paste(Image.new("RGB",(700,H),BG),(400,0),grad)
        d=ImageDraw.Draw(img)
        n1,n2,n3 = P["s2"]
        T(d,(1160,390),n1,F(190),INK,lang=P["lang"])
        T(d,(1160,550),n2,F(85),TEAL,lang=P["lang"])
        T(d,(1160,665),n3,F(56),MUT,lang=P["lang"])
    def s_pkg(num):
        img = base(W,H); d=ImageDraw.Draw(img)
        t1,t2 = P[f"s{num}"]
        acc = [TEAL,PUR,GOLD][num-3]
        d.ellipse([(W-420,-180),(W+220,460)],fill=tuple(int(acc[i]*0.18) for i in range(3)))
        T(d,(140,180),t1,F(84),acc,lang=P["lang"])
        T(d,(140,360),t2,F(66),INK,lang=P["lang"])
        d.line([(140,560),(560,560)],fill=acc,width=6)
    def s_cta():
        img = base(W,H)
        img.paste(dim(cover(Image.open(f"{A}/roni.png"),(0,0,W,H)),0.72),(0,0)); d=ImageDraw.Draw(img)
        u,s = P["s6"]
        d.text((W/2,420),u,font=en_font(130),fill=INK,anchor="mm")
        T(d,(W/2,580),s,F(72),GOLD,lang=P["lang"])
    for fn in [s_logo,s_lec,s_pkg,s_pkg,s_pkg,s_cta]: fn()
    # instead: build slide list properly
    # (re-generate in order and save)
    order = [s_logo, s_lec, lambda: s_pkg(3), lambda: s_pkg(4), lambda: s_pkg(5), s_cta]
    for i, fn in enumerate(order, 1):
        # reset: functions above painted on shared canvases; call fresh
        pass
    # simpler: re-run each builder and capture image by rebuilding
    def capture(builder):
        W_,H_ = 1920,1080
        globals()['_cap'] = None
        # builders create and paste internally; make them return via closure list
    return None

# The functional-painting above got tangled; use a clean generic painter instead:
def landscape_slide(kind, lang):
    P = PROMOS[lang]
    F = lambda sz: font(P["font"], sz, P["wght"])
    W,H = 1920,1080
    if kind == "s1":
        img = base(W,H); img.paste(dim(cover(Image.open(f"{A}/hero.png"),(0,0,W,H)),0.6),(0,0)); d=ImageDraw.Draw(img)
        big,small,l3,l4 = P["s1"]
        T(d,(W/2,330),big,F(300),INK,lang=P["lang"])
        d.line([(W/2-360,560),(W/2+360,560)],fill=PUR,width=6)
        d.text((W/2,640),small,font=en_font(64),fill=TEAL,anchor="mm")
        T(d,(W/2,790),l3,F(92),INK,lang=P["lang"]); T(d,(W/2,910),l4,F(70),GOLD,lang=P["lang"])
    elif kind == "s2":
        img = base(W,H)
        av = cover(Image.open(f"{A}/{P['avatar']}"),(0,0,1100,H)); img.paste(av,(0,0))
        grad = Image.new("L",(700,H),0); gd=ImageDraw.Draw(grad)
        for i in range(700): gd.line([(i,0),(i,H)],fill=int(255*(i/700)))
        img.paste(Image.new("RGB",(700,H),BG),(400,0),grad)
        d=ImageDraw.Draw(img)
        n1,n2,n3 = P["s2"]
        T(d,(1160,390),n1,F(190),INK,lang=P["lang"])
        T(d,(1160,550),n2,F(85),TEAL,lang=P["lang"])
        T(d,(1160,665),n3,F(56),MUT,lang=P["lang"])
    elif kind in ("s3","s4","s5"):
        num = int(kind[1]); img = base(W,H); d=ImageDraw.Draw(img)
        t1,t2 = P[kind]; acc = [TEAL,PUR,GOLD][num-3]
        d.ellipse([(W-420,-180),(W+220,460)],fill=tuple(int(acc[i]*0.18) for i in range(3)))
        T(d,(140,180),t1,F(84),acc,lang=P["lang"])
        T(d,(140,360),t2,F(66),INK,lang=P["lang"])
        d.line([(140,560),(560,560)],fill=acc,width=6)
    else:  # s6
        img = base(W,H)
        img.paste(dim(cover(Image.open(f"{A}/roni.png"),(0,0,W,H)),0.72),(0,0)); d=ImageDraw.Draw(img)
        u,s = P["s6"]
        d.text((W/2,420),u,font=en_font(130),fill=INK,anchor="mm")
        T(d,(W/2,580),s,F(72),GOLD,lang=P["lang"])
    return img

def ffprobe_dur(p):
    r = subprocess.run(f"ffprobe -v error -show_entries format=duration -of csv=p=0 {p}",shell=True,capture_output=True,text=True)
    try: return float(r.stdout.strip())
    except: return 0

def assemble(prefix, slide_files, audio_path, out, W, H, port=False):
    dur = ffprobe_dur(audio_path)
    if dur < 5: print("AUDIO FAIL", audio_path); return False
    N, FADE, FPS = len(slide_files), 0.8, 30
    d = round((dur + (N-1)*FADE)/N, 2); frames = int(d*FPS)
    inputs = []
    for s in slide_files:
        inputs += ["-loop","1","-t",str(d+FADE),"-i",s]
    inputs += ["-i", audio_path]
    filters = []
    big = max(W,H)*1.25
    for i in range(N):
        z = "min(1+0.0006*on,1.14)" if i%2==0 else "max(1.14-0.0006*on,1.0)"
        filters.append(f"[{i}:v]scale={big}:{big if port else int(big*9/16)}," if False else
                      f"[{i}:v]scale={W*11//10}:{H*11//10},zoompan=z='{z}':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},format=yuv420p[v{i}]")
    off, prev = 0, "v0"
    for i in range(1,N):
        off = round(off+d,2)
        lab = f"x{i}" if i < N-1 else "xl"
        filters.append(f"[{prev}][v{i}]xfade=transition=fade:duration={FADE}:offset={off}[{lab}]")
        prev = lab
    filters.append(f"[xl]fade=t=out:st={dur-0.8}:d=0.8[vout]")
    cmd = ["ffmpeg","-y"] + inputs + ["-filter_complex",";".join(filters),
        "-map","[vout]","-map",f"{N}:a","-c:v","libx264","-preset","veryfast","-crf","23",
        "-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out]
    r = subprocess.run(cmd,capture_output=True,text=True)
    ok = r.returncode==0 and os.path.exists(out)
    print(("OK " if ok else "FAIL ") + out, f"{ffprobe_dur(out):.1f}s" if ok else r.stderr[-300:])
    return ok

async def tts_all(jobs):
    import edge_tts
    sem = asyncio.Semaphore(3)
    async def one(text, voice, out, pitch="+0Hz"):
        async with sem:
            for _ in range(3):
                try:
                    await edge_tts.Communicate(text, voice, rate="+8%", pitch=pitch).save(out)
                    if os.path.getsize(out) > 15000: return True
                except Exception: await asyncio.sleep(2)
            print("TTS FAIL", out); return False
    res = await asyncio.gather(*[one(*j) for j in jobs])
    print(f"TTS: {sum(res)}/{len(res)}")

def main():
    mode = sys.argv[1] if len(sys.argv)>1 else "all"
    # 1) AR/RU landscape promos
    if mode in ("all","promos"):
        for lang in ["ar","ru"]:
            P = PROMOS[lang]
            files = []
            for kind in ["s1","s2","s3","s4","s5","s6"]:
                p = f"{A}/{lang}_{kind}.png"
                landscape_slide(kind, lang).save(p, quality=95)
                files.append(p)
            aud = f"{A}/promo_{lang}.mp3"
            if not os.path.exists(aud):
                asyncio.run(tts_all([(P["tts"], P["voice"], aud)]))
            assemble(f"{lang}", files, aud, f"{A}/promo_{lang}.mp4", 1920, 1080)
    # 2) 40 vertical clips
    if mode in ("all","social"):
        L = DATA["langs"]; topics = DATA["topics"]
        W,H = 1080,1920
        jobs, metas = [], []
        for lang, cfg in L.items():
            for t in topics:
                d = t[lang]
                out_aud = f"{A}/svid_{lang}_{t['n']:02d}.mp3"
                script = f"{L[lang]['series']}! {d['hook']}. {L[lang]['steps_word'][0]} {d['steps'][0]}. {L[lang]['steps_word'][1]} {d['steps'][1]}. {L[lang]['steps_word'][2]} {d['steps'][2]}. {L[lang]['cta']}"
                jobs.append((script, cfg["voice"], out_aud))
                metas.append((lang, t, d, out_aud))
        asyncio.run(tts_all(jobs))
        for lang, t, d, aud in metas:
            cfg = L[lang]
            Fb = lambda sz: font(cfg["font"], sz, cfg["font_weight"])
            Fe = lambda sz,w=600: en_font(sz,w)
            acc = ACCENTS[(t["n"]-1) % len(ACCENTS)]
            # slide 1: avatar + hook
            img = base(W,H)
            av = cover(Image.open(f"{A}/{cfg['avatar']}"),(0,240,W,1240)); img.paste(av,(0,240))
            grad = Image.new("L",(W,260),0); gd=ImageDraw.Draw(grad)
            for i in range(260): gd.line([(0,i),(W,i)],fill=int(255*(i/260)))
            img.paste(Image.new("RGB",(W,260),BG),(0,240),grad)
            g2 = Image.new("L",(W,420),0); gd2=ImageDraw.Draw(g2)
            for i in range(420): gd2.line([(0,i),(W,i)],fill=int(255*(1-i/420)))
            img.paste(Image.new("RGB",(W,420),BG),(0,820),g2)
            dr = ImageDraw.Draw(img)
            T(dr,(W/2,150),cfg["series"],Fb(62),acc,rtl=cfg["rtl"],lang=lang[:2])
            f_hook = Fb(96)
            T(dr,(W/2,1080),d["hook"],f_hook,INK,rtl=cfg["rtl"],lang=lang[:2])
            p1 = f"{A}/sv_{lang}_{t['n']:02d}_a.png"; img.save(p1,quality=95)
            # slide 2: steps + CTA
            img = base(W,H); dr = ImageDraw.Draw(img)
            dr.rounded_rectangle([60,180,W-60,420],radius=24,fill=(21,21,31),outline=tuple(int(acc[i]*0.55) for i in range(3)),width=2)
            T(dr,(W/2,300),d["hook"],Fb(66),INK,rtl=cfg["rtl"],lang=lang[:2])
            y = 560
            for si, step in enumerate(d["steps"]):
                dr.rounded_rectangle([70,y,W-70,y+280],radius=22,fill=(21,21,31),outline=(35,35,48),width=2)
                dr.ellipse([100 if not cfg["rtl"] else W-190, y+90, 190 if not cfg["rtl"] else W-100, y+180], fill=tuple(int(acc[i]*0.8) for i in range(3)))
                T(dr,(300 if not cfg["rtl"] else W-300, y+140),str(si+1),Fe(80,700) if not cfg["rtl"] else Fb(80),BG,rtl=False,lang="en")
                T(dr,(W/2,y+140),step,Fb(58),INK,rtl=cfg["rtl"],lang=lang[:2])
                y += 340
            T(dr,(W/2,1770),cfg["cta"],Fb(70),acc,rtl=cfg["rtl"],lang=lang[:2])
            p2 = f"{A}/sv_{lang}_{t['n']:02d}_b.png"; img.save(p2,quality=95)
            out = f"{ROOT}/social/{lang}/clip_{t['n']:02d}.mp4"
            os.makedirs(os.path.dirname(out), exist_ok=True)
            assemble(f"{lang}{t['n']}", [p1,p2], aud, out, W, H, port=True)
    print("ALL DONE")

if __name__ == "__main__":
    main()
