#!/usr/bin/env python3
"""TheSDTrader reel renderer.

Usage:  python3 -I tools/render_reel.py <reel_dir> preview|cover|render

<reel_dir> holds spec.json and voice/s1.wav ... sN.wav (one Hindi clip per scene).
Output: video.mp4 and cover.jpg inside <reel_dir>.
Layout rules (Instagram safe area): brand tag from y=262, content y 400-1200,
subtitles centred near y=1360, nothing below y=1530, nothing right of x=930.
"""
import sys, os, json, math, subprocess, wave
import numpy as np
from multiprocessing import get_context
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H, FPS = 1080, 1920, 30
CX = 510  # content centre: the safe area is x 90-930 (Instagram buttons sit on the right)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOLD = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
REG = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"

BG = (10, 15, 31)
WHITE = (245, 247, 250); MUTED = (148, 163, 184); GOLD = (245, 190, 55)
GREEN = (34, 197, 94); RED = (239, 68, 68); CARD = (22, 31, 58); CARD2 = (32, 45, 84)
BLUE = (59, 130, 246); ORANGE = (251, 146, 60); DARK = (12, 16, 30)

_fc = {}
def F(size, bold=True):
    k = (size, bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(BOLD if bold else REG, size, layout_engine=ImageFont.Layout.RAQM)
    return _fc[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eb(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def prog(t, t0, dur): return clamp((t - t0) / dur)

def C(rgb, a=1.0):
    a = clamp(a)
    return tuple(int(BG[i] + (rgb[i] - BG[i]) * a) for i in range(3))

# ---------------------------------------------------------------- spec
REEL = None; SPEC = None; SEG = []; TOTAL = 0.0
REV = {"hook": [0.0, 0.07], "problem": [0.04], "analogy": [0.04, 0.30, 0.34, 0.62, 0.78],
       "facts": [0.03, 0.27, 0.50, 0.78], "headlines": [0.05, 0.38, 0.66], "baskets": [0.03, 0.21, 0.47, 0.73], "lesson": [0.05, 0.38, 0.62], "outro": [0.04, 0.5]}

def _dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", p]).decode().strip())

def load(reel_dir):
    global REEL, SPEC, SEG, TOTAL
    REEL = os.path.abspath(reel_dir)
    SPEC = json.load(open(os.path.join(REEL, "spec.json"), encoding="utf-8"))
    tempo = SPEC.get("voice_tempo", 1.0); lead = SPEC.get("lead", 0.12); pad = SPEC.get("pad", 0.15)
    t = 0.0; SEG = []
    for i, sc in enumerate(SPEC["scenes"]):
        vp = os.path.join(REEL, "voice", f"s{i+1}.wav")
        vd = _dur(vp) / tempo
        dur = lead + vd + pad + sc.get("tail", 0.0)
        SEG.append(dict(t0=t, dur=dur, lead=lead, vd=vd, vp=vp)); t += dur
    TOTAL = t

# ---------------------------------------------------------------- assets
_assets = {}
def face_img():
    if "face" not in _assets:
        p = os.path.join(ROOT, SPEC.get("face", "assets/face_original.png"))
        _assets["face"] = Image.open(p).convert("RGB")
    return _assets["face"]

def face_card(w, h):
    """Rounded face card with gold frame. The photo is only cropped and gently sharpened."""
    k = ("card", w, h)
    if k in _assets: return _assets[k]
    src = face_img().crop((80, 60, 420, 430)).resize((w, h), Image.LANCZOS)
    src = ImageEnhance.Sharpness(src).enhance(1.25)
    card = Image.new("RGBA", (w + 24, h + 24), (0, 0, 0, 0))
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], 34, fill=255)
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, w + 23, h + 23], 42, fill=GOLD + (255,))
    card.paste(src, (12, 12), m)
    strip = Image.new("RGBA", (w, 74), DARK + (215,))
    sm = Image.new("L", (w, 74), 255)
    card.alpha_composite(strip, (12, 12 + h - 74))
    cd.text((12 + w / 2, 12 + h - 37), SPEC["brand"], font=F(40), fill=GOLD, anchor="mm")
    _assets[k] = card
    return card

def avatar(r):
    k = ("av", r)
    if k in _assets: return _assets[k]
    src = face_img().crop((110, 85, 370, 345)).resize((2 * r, 2 * r), Image.LANCZOS)
    src = ImageEnhance.Sharpness(src).enhance(1.2)
    out = Image.new("RGBA", (2 * r + 12, 2 * r + 12), (0, 0, 0, 0))
    ImageDraw.Draw(out).ellipse([0, 0, 2 * r + 11, 2 * r + 11], fill=GOLD + (255,))
    m = Image.new("L", (2 * r, 2 * r), 0); ImageDraw.Draw(m).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
    out.paste(src, (6, 6), m)
    _assets[k] = out
    return out

def glow_mask(size):
    k = ("glow", size)
    if k in _assets: return _assets[k]
    y, x = np.mgrid[0:size, 0:size]
    r = np.sqrt((x - size / 2) ** 2 + (y - size / 2) ** 2) / (size / 2)
    a = np.clip(1 - r, 0, 1) ** 2 * 255
    _assets[k] = Image.fromarray(a.astype(np.uint8), "L")
    return _assets[k]

def base_bg():
    if "bg" not in _assets:
        arr = np.zeros((H, W, 3), np.uint8)
        t = (np.arange(H) / H)[:, None]
        arr[..., 0] = (10 + 8 * t); arr[..., 1] = (15 + 14 * t); arr[..., 2] = (31 + 30 * t)
        _assets["bg"] = Image.fromarray(arr, "RGB")
    return _assets["bg"]

def background(t):
    im = base_bg().copy(); g = glow_mask(900)
    gx = int(560 + 160 * math.sin(t * 0.45)); gy = int(260 + 120 * math.cos(t * 0.35))
    im.paste(Image.new("RGB", g.size, GOLD), (gx - 450, gy - 450), g.point(lambda v: int(v * 0.16)))
    bx = int(240 + 140 * math.cos(t * 0.3)); by = int(1450 + 100 * math.sin(t * 0.4))
    im.paste(Image.new("RGB", g.size, BLUE), (bx - 450, by - 450), g.point(lambda v: int(v * 0.14)))
    d = ImageDraw.Draw(im)
    for i in range(26):  # slow rising dust
        x = (i * 211) % W; y = (H - ((i * 337 + t * (14 + i % 5 * 6)) % H))
        d.ellipse([x, y, x + 4, y + 4], fill=C(GOLD, 0.22))
    return im

# ---------------------------------------------------------------- text helpers
def text(d, x, y, s, size, color, bold=True, anchor="mm", a=1.0):
    d.text((x, y), s, font=F(size, bold), fill=C(color, a), anchor=anchor, language="hi")

def parse_marked(s):
    """'a *b*c d' -> list of units; a unit is words glued together (no space between them)."""
    units, sep = [], True
    for i, part in enumerate(s.split("*")):
        hl = i % 2 == 1; pieces = part.split(" ")
        for j, w in enumerate(pieces):
            if w == "":
                sep = True; continue
            if sep or not units: units.append([])
            units[-1].append((w, hl)); sep = False
            if j < len(pieces) - 1: sep = True
    return units

def layout_marked(s, size, maxw, bold=True):
    f = F(size, bold); sp = f.getlength(" ", language="hi"); lines, cur, cw = [], [], 0
    for u in parse_marked(s):
        wl = [f.getlength(w, language="hi") for w, _ in u]; uw = sum(wl)
        if cur and cw + sp + uw > maxw:
            lines.append((cur, cw)); cur, cw = [], 0
        cw += (sp if cur else 0) + uw
        cur.append((u, wl, sp if cur else 0))
    if cur: lines.append((cur, cw))
    return lines

def marked(d, cx, cy, s, size, maxw, color=WHITE, hl=GOLD, lh=1.32, a=1.0, bold=True):
    f = F(size, bold); lines = layout_marked(s, size, maxw, bold)
    y = cy - (len(lines) - 1) * size * lh / 2
    for ln, wid in lines:
        x = cx - wid / 2
        for u, wl, gap in ln:
            x += gap
            for (w, h), l in zip(u, wl):
                d.text((x, y), w, font=f, fill=C(hl if h else color, a), anchor="lm", language="hi"); x += l
        y += size * lh
    return len(lines)

def rrect(d, box, r, fill=None, outline=None, width=0, a=1.0):
    d.rounded_rectangle(box, r, fill=C(fill, a) if fill else None,
                        outline=C(outline, a) if outline else None, width=width)

def persp_coeffs(dst, src):
    A, B = [], []
    for (x, y), (X, Y) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -X * x, -X * y]); B.append(X)
        A.append([0, 0, 0, x, y, 1, -Y * x, -Y * y]); B.append(Y)
    return np.linalg.solve(np.array(A, float), np.array(B, float))

def tilt(img, yaw):
    w, h = img.size; a = abs(yaw) * 0.1 * h
    dst = [(0, 0), (w, a), (w, h - a), (0, h)] if yaw >= 0 else [(0, a), (w, 0), (w, h), (0, h - a)]
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    return img.transform((w, h), Image.PERSPECTIVE, persp_coeffs(dst, src), Image.BICUBIC)

def paste_card(im, card, cx, cy, yaw=0.0, scale=1.0, shadow=True):
    c = tilt(card, yaw) if abs(yaw) > 1e-3 else card
    if scale != 1.0: c = c.resize((int(c.width * scale), int(c.height * scale)), Image.BICUBIC)
    x, y = int(cx - c.width / 2), int(cy - c.height / 2)
    if shadow:
        sh = Image.new("RGBA", (c.width + 80, c.height + 80), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([40, 56, c.width + 40, c.height + 56], 40, fill=(0, 0, 0, 150))
        sh = sh.filter(ImageFilter.GaussianBlur(18))
        im.paste(sh, (x - 40, y - 40), sh)
    im.paste(c, (x, y), c)

# ---------------------------------------------------------------- scenes
def reveals(sc, dur):
    return [r * dur for r in sc.get("rev", REV[sc["type"]])]

def slide(e, dy=40): return int((1 - e) * dy)

def sc_hook(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    e1 = eb(prog(lt, T[0], 0.4)); e2 = eb(prog(lt, T[1], 0.45))
    text(d, CX, 440 + slide(e1), sc["line1"], int(sc.get("size1", 62) * (0.85 + 0.15 * e1)), WHITE, a=clamp(e1 * 2))
    text(d, CX, 548 + slide(e2, 60), sc["line2"], int(sc.get("size2", 134) * (0.8 + 0.2 * e2)), GOLD, a=clamp(e2 * 2))
    g = glow_mask(760)
    im.paste(Image.new("RGB", g.size, GOLD), (CX - 380, 965 - 380), g.point(lambda v: int(v * (0.22 + 0.06 * math.sin(lt * 3)))))
    e = eb(prog(lt, 0.15, 0.6))
    yaw = 0.55 * math.sin(lt * 1.3)
    paste_card(im, face_card(480, 522), CX, 965 + slide(e, 80), yaw=yaw, scale=0.88 + 0.12 * e + 0.015 * lt)
    pulse = 1 + 0.06 * math.sin(lt * 4)
    d.text((865, 840), "?", font=F(int(230 * pulse)), fill=C(GOLD, 0.9), anchor="mm")

def sc_problem(im, d, lt, dur, sc):
    T = reveals(sc, dur); e = eb(prog(lt, T[0], 0.5)); p = 1 + 0.05 * math.sin(lt * 6)
    s = int(210 * e * p); cx, cy = CX, 740
    pts = [(cx, cy - s), (cx - int(s * 1.1), cy + int(s * .8)), (cx + int(s * 1.1), cy + int(s * .8))]
    d.polygon(pts, fill=C(GOLD, 0.95));
    inner = [(cx, cy - int(s * .72)), (cx - int(s * .8), cy + int(s * .68)), (cx + int(s * .8), cy + int(s * .68))]
    d.polygon(inner, fill=C(DARK))
    if s > 40: text(d, cx, cy + int(s * .22), "!", int(s * 1.05), GOLD)
    text(d, CX, 1040, sc["line1"], 56, WHITE, a=eo(prog(lt, T[0] + .25, .4)))
    text(d, CX, 1115, sc["line2"], 56, GOLD, a=eo(prog(lt, T[0] + .45, .4)))

def veg_icon(d, x, y, a):
    d.ellipse([x - 70, y - 20, x - 10, y + 40], fill=C(RED, a)); d.ellipse([x - 52, y - 32, x - 28, y - 14], fill=C(GREEN, a))
    d.ellipse([x - 5, y - 40, x + 45, y + 40], fill=C(GREEN, a))
    d.polygon([(x + 55, y - 30), (x + 95, y - 30), (x + 75, y + 50)], fill=C(ORANGE, a))

def pie_icon(d, x, y, r, pull, a):
    cols = [(BLUE), (30, 64, 175), (BLUE), (30, 64, 175), (BLUE)]
    for i, c in enumerate(cols):
        d.pieslice([x - r, y - r, x + r, y + r], i * 60, (i + 1) * 60, fill=C(c, a), outline=C(CARD, a), width=4)
    mid = math.radians(5 * 60 + 30); ox, oy = x + math.cos(mid) * pull, y + math.sin(mid) * pull
    d.pieslice([ox - r, oy - r, ox + r, oy + r], 300, 360, fill=C(GOLD, a), outline=C(CARD, a), width=4)

def sc_analogy(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    e = eo(prog(lt, T[0], .5)); a = clamp(e * 2.2)
    if e > .12:
        rrect(d, [90, 410 + slide(e), 930, 650 + slide(e)], 34, CARD, CARD2, 3, a)
        veg_icon(d, 230, 535 + slide(e), a)
        text(d, 360, 510 + slide(e), sc["a_hi"], 54, WHITE, anchor="lm", a=a)
        text(d, 360, 570 + slide(e), sc["a_en"], 30, MUTED, bold=False, anchor="lm", a=a)
        text(d, 360, 612 + slide(e), sc["a_sub"], 32, GOLD, bold=False, anchor="lm", a=a)
    ea = eo(prog(lt, T[1], .4))
    if ea > .05:
        pts = [(CX, 705 + int(8 * math.sin(lt * 5))), (CX - 30, 678), (CX + 30, 678)]
        d.polygon(pts, fill=C(GOLD, ea))
    e = eo(prog(lt, T[2], .5)); a = clamp(e * 2.2)
    if e > .12:
        rrect(d, [90, 720 + slide(e), 930, 960 + slide(e)], 34, CARD, GOLD, 3, a)
        pie_icon(d, 215, 840 + slide(e), 75, 36 * eb(prog(lt, T[2] + 0.5, 0.7)) + 4 * math.sin(lt * 4), a)
        text(d, 360, 790 + slide(e), sc["b_hi"], 54, WHITE, anchor="lm", a=a)
        text(d, 360, 848 + slide(e), sc["b_en"], 30, MUTED, bold=False, anchor="lm", a=a)
        text(d, 360, 898 + slide(e), sc["b_sub"], 32, GOLD, bold=False, anchor="lm", a=a)
    e = eb(prog(lt, T[3], .5))
    if e > 0.3:
        w = int(840 * clamp(e)); rrect(d, [CX - w // 2, 995, CX + w // 2, 1065], 35, GOLD)
        if e > .6: text(d, CX, 1030, sc["badge"], 34, DARK)
    for k, nm in enumerate(["BSE", "NSE"]):
        e = eb(prog(lt, T[4] + k * 0.18, .45))
        if e > 0.3:
            x0 = 90 + k * 440; w = int(400 * clamp(e))
            rrect(d, [x0, 1090, x0 + w, 1180], 22, CARD2, GOLD, 3)
            if e > .6:
                text(d, x0 + 200, 1122, nm, 36, WHITE)
                text(d, x0 + 200, 1158, sc["chips"][k], 22, MUTED, bold=False)

def clock_icon(d, x, y, r, a, t):
    d.ellipse([x - r, y - r, x + r, y + r], fill=C(CARD, a), outline=C(MUTED, a), width=4)
    end = 187.5 + 187.5 * eo(clamp(t))
    d.pieslice([x - r + 6, y - r + 6, x + r - 6, y + r - 6], 187.5, end, fill=C(GREEN, a * .85))
    d.line([x, y, x, y - r + 14], fill=C(WHITE, a), width=5); d.line([x, y, x + r // 2, y], fill=C(WHITE, a), width=5)

def sc_facts(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    for i, row in enumerate(sc["rows"]):
        e = eo(prog(lt, T[i], .5)); a = clamp(e * 2.2)
        if e <= .12: continue
        y0 = 410 + i * 197 + slide(e); y1 = y0 + 175
        rrect(d, [90, y0, 930, y1], 30, CARD, GOLD if row.get("hot") else CARD2, 3, a)
        cy = (y0 + y1) // 2
        if row["icon"] == "clock":
            clock_icon(d, 185, cy, 60, a, prog(lt, T[i] + .3, 1.2))
        else:
            rrect(d, [110, cy - 52, 262, cy + 52], 20, CARD2, None, 0, a)
            text(d, 186, cy, row["icon"], 46 if len(row["icon"]) > 4 else 50, GOLD, a=a)
        text(d, 300, cy - 30, row["t"], 44, WHITE, anchor="lm", a=a)
        text(d, 300, cy + 34, row["s"], 30, MUTED, bold=False, anchor="lm", a=a)
    if "source" in sc:
        text(d, CX, 1508, sc["source"], 25, MUTED, bold=False, a=eo(prog(lt, T[1], .6)))

def sc_lesson(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    cols = [GREEN, RED, GOLD]
    for i, row in enumerate(sc["rows"]):
        e = eb(prog(lt, T[i], .5)); a = clamp(e * 2.2)
        if e <= .12: continue
        y0 = 430 + i * 245 + slide(e, 60); y1 = y0 + 205
        rrect(d, [90, y0, 930, y1], 34, CARD, cols[i], 4, a)
        cy = (y0 + y1) // 2
        d.ellipse([125, cy - 38, 201, cy + 38], fill=C(cols[i], a))
        if i == 0:
            d.line([(141, cy + 2), (156, cy + 18), (186, cy - 18)], fill=C(DARK, a), width=9, joint="curve")
        else:
            text(d, 163, cy, ["", "!", "→"][i], 56, DARK, a=a)
        text(d, 235, cy - 26, row["t"], 46, WHITE, anchor="lm", a=a)
        text(d, 235, cy + 40, row["s"], 30, MUTED, bold=False, anchor="lm", a=a)

def sc_outro(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    e = eb(prog(lt, T[0], .6))
    ang = lt * 80
    for k in range(3):
        a0 = ang + k * 120; d.arc([CX - 188, 590 - 188, CX + 188, 590 + 188], a0, a0 + 50, fill=C(GOLD, .9), width=7)
    av = avatar(150)
    s = 0.85 + 0.15 * e; av = av.resize((int(av.width * s), int(av.height * s)), Image.BICUBIC)
    im.paste(av, (CX - av.width // 2, 590 - av.height // 2), av)
    text(d, CX, 835, SPEC["brand"], 96, GOLD, a=clamp(e * 1.5))
    text(d, CX, 912, sc["tag"], 34, MUTED, bold=False, a=clamp(e * 1.5))
    for k, nm in enumerate(sc["cta"]):
        ee = eb(prog(lt, T[0] + .5 + k * .2, .4))
        if ee > 0.3:
            x0 = 90 + k * 290; w = int(260 * clamp(ee))
            rrect(d, [x0, 970, x0 + w, 1040], 35, GOLD if k == 2 else CARD2, GOLD, 3)
            if ee > .6: text(d, x0 + 130, 1005, nm, 34, DARK if k == 2 else WHITE)
    e = eo(prog(lt, T[1], .5))
    if e > .12:
        rrect(d, [90, 1075, 930, 1195], 28, CARD, GOLD, 3, clamp(e * 2.2))
        text(d, CX, 1118, sc["notice_hi"], 40, WHITE, a=e)
        text(d, CX, 1166, sc["notice_en"], 28, MUTED, bold=False, a=e)

def sc_headlines(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    for i, (txt, up) in enumerate([(sc["h1"], False), (sc["h2"], True)]):
        e = eo(prog(lt, T[i], .5)); a = clamp(e * 2.2)
        if e <= .12: continue
        y0 = 430 + i * 215 + slide(e); y1 = y0 + 175; cy = (y0 + y1) // 2
        col = GREEN if up else RED
        rrect(d, [90, y0, 930, y1], 34, CARD, col, 3, a)
        pts = [(190, cy - 42), (148, cy + 38), (232, cy + 38)] if up else [(190, cy + 42), (148, cy - 38), (232, cy - 38)]
        d.polygon(pts, fill=C(col, a))
        text(d, 285, cy, txt, 56, WHITE, anchor="lm", a=a)
    e = eb(prog(lt, T[2], .5))
    if e > .15:
        d.text((CX, 970), "?", font=F(int(230 * clamp(e) * (1 + 0.05 * math.sin(lt * 5)))), fill=C(GOLD), anchor="mm")
        text(d, CX, 1130, sc["note"], 34, MUTED, bold=False, a=clamp(e))

def sc_baskets(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    e = eo(prog(lt, T[0], .5))
    if e > .12:
        rrect(d, [90, 400 + slide(e), 930, 470 + slide(e)], 35, GOLD, None, 0, clamp(e * 2.2))
        text(d, CX, 435 + slide(e), sc["head"], 36, DARK, a=clamp(e * 2.2))
    for i, card in enumerate(sc["cards"]):
        e = eo(prog(lt, T[1 + i], .5)); a = clamp(e * 2.2)
        if e <= .12: continue
        y0 = 495 + i * 225 + slide(e); y1 = y0 + 200; cy = (y0 + y1) // 2
        rrect(d, [90, y0, 930, y1], 30, CARD, GOLD, 3, a)
        rrect(d, [110, cy - 60, 282, cy + 60], 22, CARD2, None, 0, a)
        text(d, 196, cy, card["n"], 72 if len(card["n"]) <= 3 else 38, GOLD, a=a)
        text(d, 320, cy - 30, card["t"], 52, WHITE, anchor="lm", a=a)
        text(d, 320, cy + 36, card["s"], 30, MUTED, bold=False, anchor="lm", a=a)
    e = eo(prog(lt, T[3], .5)); a = clamp(e * 2.2)
    if e > .12 and "bars_t" in sc:
        text(d, CX, 965 + slide(e), sc["bars_t"], 38, WHITE, a=a)
        for k, (lab, wid) in enumerate([("बड़ी", 700), ("मध्यम", 430), ("छोटी", 240)]):
            ee = eo(prog(lt, T[3] + 0.15 * k, .5)); y = 1015 + k * 52
            if ee > .2:
                rrect(d, [90, y, 90 + int(wid * ee), y + 40], 12, GOLD)
                if ee > .7: text(d, 110, y + 20, lab, 26, DARK, anchor="lm")
        text(d, CX, 1195, sc["bars_n"], 26, MUTED, bold=False, a=a)

SCENES = dict(hook=sc_hook, headlines=sc_headlines, baskets=sc_baskets, problem=sc_problem, analogy=sc_analogy, facts=sc_facts, lesson=sc_lesson, outro=sc_outro)

# ---------------------------------------------------------------- chrome + subtitles
def chrome(im, d, t):
    av = avatar(46); im.paste(av, (90, 262), av)
    text(d, 206, 292, SPEC["brand"], 46, GOLD, anchor="lm")
    text(d, 206, 338, SPEC.get("tagline", ""), 25, MUTED, bold=False, anchor="lm")
    rrect(d, [690, 276, 930, 326], 25, CARD, GOLD, 2)
    text(d, 810, 301, SPEC.get("day_tag", ""), 24, GOLD)

def subtitle(im, d, i, lt):
    sc = SPEC["scenes"][i]; seg = SEG[i]
    subs = sc.get("subs") or []
    if not subs: return
    start = seg["lead"]; spoken = seg["vd"]
    if lt < start: return
    wts = [len(s.replace("*", "")) for s in subs]; tot = float(sum(wts))
    pos = (lt - start) / spoken if spoken > 0 else 1
    cum = 0; idx = len(subs) - 1
    for k, w in enumerate(wts):
        cum += w / tot
        if pos <= cum: idx = k; break
    size = 50
    n = len(layout_marked(subs[idx], size, 800))
    ph = int(n * size * 1.32 + 44); cy = 1350
    rrect(d, [90, cy - ph // 2, 930, cy + ph // 2], 30, DARK, CARD2, 2)
    marked(d, CX, cy, subs[idx], size, 800)

# ---------------------------------------------------------------- frame
TR = 0.32
def scene_at(t):
    for i, s in enumerate(SEG):
        if t < s["t0"] + s["dur"]: return i
    return len(SEG) - 1

def draw_scene(i, t_abs, lt):
    im = background(t_abs); d = ImageDraw.Draw(im)
    sc = SPEC["scenes"][i]
    SCENES[sc["type"]](im, d, lt, SEG[i]["dur"], sc)
    return im

def zoom(im, s):
    if s <= 1.0001: return im
    w, h = int(W / s), int(H / s); x, y = (W - w) // 2, (H - h) // 2
    return im.crop((x, y, x + w, y + h)).resize((W, H), Image.BICUBIC)

def frame(t):
    i = scene_at(t); seg = SEG[i]; lt = t - seg["t0"]
    im = draw_scene(i, t, lt)
    if i > 0 and lt < TR:
        prev = draw_scene(i - 1, t, SEG[i - 1]["dur"])
        im = Image.blend(prev, im, eo(lt / TR))
    im = zoom(im, 1.0 + 0.03 * lt / seg["dur"])
    d = ImageDraw.Draw(im)
    chrome(im, d, t)
    subtitle(im, d, i, lt)
    if i > 0 and lt < TR:  # gold sweep on cut
        x = int(eo(lt / TR) * (W + 200)) - 100
        d.rectangle([x, 400, x + 6, 1200], fill=C(GOLD, 1 - lt / TR))
    return im

def render_frame(n):
    return frame(n / FPS).tobytes()

# ---------------------------------------------------------------- audio
def music(path, total):
    sr = 44100; n = int(sr * total); t = np.arange(n) / sr
    out = np.zeros(n); rs = np.random.RandomState(7); step = 60.0 / 104 / 2
    def add(sig, s):
        e = min(n, s + len(sig))
        if e > s: out[s:e] += sig[:e - s]
    for k in range(int(total / step)):
        s = int(k * step * sr); pos = k % 8
        if pos in (0, 4, 6):
            L = int(0.28 * sr); tt = np.arange(L) / sr
            add(np.sin(2 * np.pi * (95 * np.exp(-tt * 20) + 52) * tt) * np.exp(-tt * 11) * 0.8, s)
        if pos in (2, 3, 5, 7):
            L = int(0.12 * sr); tt = np.arange(L) / sr
            add((np.sin(2 * np.pi * 420 * tt) * 0.5 + rs.randn(L) * 0.5) * np.exp(-tt * 38) * 0.28, s)
        L = int(0.04 * sr); add(rs.randn(L) * np.exp(-np.arange(L) / sr * 120) * (0.10 if pos % 2 else 0.06), s)
    def midi(m): return 440.0 * 2 ** ((m - 69) / 12)
    def pluck(freq, dur=0.6):
        N = int(sr * dur); dl = int(sr / freq); buf = rs.uniform(-1, 1, dl); y = np.zeros(N)
        for i in range(N):
            y[i] = buf[i % dl]; buf[i % dl] = 0.5 * (buf[i % dl] + buf[(i + 1) % dl]) * 0.997
        return y * np.exp(-np.arange(N) / sr * 3.0)
    phrase = [74, 75, 78, 75, 74, 73, 74, None, 78, 79, 81, 79, 78, 75, 74, None]; cache = {}
    for k in range(int(total / step)):
        m = phrase[k % 16]
        if m is None or k < 8: continue
        if m not in cache: cache[m] = pluck(midi(m))
        add(cache[m] * 0.35, int(k * step * sr))
    for fq, g in [(73.42, .10), (110.0, .08), (146.83, .05)]:
        out += (np.sin(2 * np.pi * fq * t) + 0.4 * np.sin(2 * np.pi * 2 * fq * t)) * g * (0.8 + 0.2 * np.sin(2 * np.pi * 0.3 * t))
    out *= np.minimum(1, t / 0.4) * np.minimum(1, (total - t) / 2.0)
    out = out / (np.abs(out).max() + 1e-9) * 0.6
    write_wav(path, out, sr)

def write_wav(path, x, sr):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())

def sfx(path, total):
    sr = 44100; n = int(sr * total); out = np.zeros(n); rs = np.random.RandomState(3)
    def add(sig, t0):
        s = int(t0 * sr); e = min(n, s + len(sig))
        if e > s: out[s:e] += sig[:e - s]
    def whoosh(L=0.45):
        m = int(L * sr); x = rs.randn(m); y = np.zeros(m); env = np.sin(np.pi * np.arange(m) / m) ** 2
        a = 0.02 + 0.5 * (np.arange(m) / m) ** 2; v = 0.0
        for i in range(m):
            v += a[i] * (x[i] - v); y[i] = v
        return y * env * 1.6
    def pop(f=900, L=0.09):
        tt = np.arange(int(L * sr)) / sr
        return np.sin(2 * np.pi * (f + 700 * tt * 8) * tt) * np.exp(-tt * 45) * 0.7
    def chime(L=1.1):
        tt = np.arange(int(L * sr)) / sr
        return (np.sin(2 * np.pi * 1318 * tt) + 0.5 * np.sin(2 * np.pi * 1975 * tt)) * np.exp(-tt * 3.5) * 0.4
    for i, sc in enumerate(SPEC["scenes"]):
        seg = SEG[i]
        if i > 0: add(whoosh(), seg["t0"] - 0.08)
        for r in reveals(sc, seg["dur"]):
            if i == 0 and r < 0.01: continue
            add(pop(), seg["t0"] + r)
    add(chime(), SEG[-1]["t0"] + reveals(SPEC["scenes"][-1], SEG[-1]["dur"])[1])
    write_wav(path, out / (np.abs(out).max() + 1e-9) * 0.7, sr)

def build_audio(out_path):
    tmp = os.path.join(REEL, "_tmp"); os.makedirs(tmp, exist_ok=True)
    mp, sp = os.path.join(tmp, "music.wav"), os.path.join(tmp, "sfx.wav")
    music(mp, TOTAL); sfx(sp, TOTAL)
    tempo = SPEC.get("voice_tempo", 1.0)
    ins = ["-i", mp, "-i", sp]; fc = "[0:a]volume=%s[m];[1:a]volume=%s[x];" % (SPEC.get("music_vol", 0.2), SPEC.get("sfx_vol", 0.4))
    for i, seg in enumerate(SEG):
        ins += ["-i", seg["vp"]]; ms = int((seg["t0"] + seg["lead"]) * 1000)
        fc += f"[{i+2}:a]aresample=44100,atempo={tempo},adelay={ms}|{ms},volume={SPEC.get('voice_vol', 1.5)}[c{i}];"
    labels = "[m][x]" + "".join(f"[c{i}]" for i in range(len(SEG)))
    fc += f"{labels}amix=inputs={len(SEG)+2}:normalize=0:duration=first,alimiter=limit=0.95[out]"
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error"] + ins + ["-filter_complex", fc, "-map", "[out]", "-ac", "1", out_path])

# ---------------------------------------------------------------- cover
def cover(path):
    cv = SPEC["cover"]
    im = base_bg().copy(); g = glow_mask(1100)
    im.paste(Image.new("RGB", g.size, GOLD), (540 - 550, 1240 - 550), g.point(lambda v: int(v * 0.30)))
    im.paste(Image.new("RGB", g.size, BLUE), (200 - 550, 420 - 550), g.point(lambda v: int(v * 0.16)))
    d = ImageDraw.Draw(im)
    rrect(d, [200, 290, 880, 360], 35, CARD, GOLD, 3)
    text(d, 540, 325, cv["pill"], 34, GOLD)
    text(d, 540, 520, cv["l1"], 178, WHITE)
    text(d, 540, 735, cv["l2"], 210, GOLD)
    text(d, 540, 905, cv["sub"], 54, WHITE)
    paste_card(im, face_card(500, 544), 540, 1245, yaw=0.35, scale=1.0)
    d = ImageDraw.Draw(im)
    text(d, 540, 1585, SPEC["brand"], 74, GOLD)
    d.rectangle([340, 1630, 740, 1636], fill=GOLD)
    im.save(path, quality=93)

# ---------------------------------------------------------------- main
if __name__ == "__main__":
    reel, mode = sys.argv[1], sys.argv[2]
    load(reel)
    print("scenes:", [(round(s["t0"], 2), round(s["dur"], 2)) for s in SEG], "total", round(TOTAL, 2))
    if mode == "cover":
        cover(os.path.join(REEL, "cover.jpg"))
    elif mode == "preview":
        times = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else \
            [SEG[i]["t0"] + SEG[i]["dur"] * f for i in range(len(SEG)) for f in ((.5, .95) if i < len(SEG) - 1 else (.4, .9))]
        tiles = [frame(t).resize((360, 640)) for t in times]
        sheet = Image.new("RGB", (360 * 5, 640 * ((len(tiles) + 4) // 5)))
        for k, tl in enumerate(tiles): sheet.paste(tl, ((k % 5) * 360, (k // 5) * 640))
        sheet.save(os.path.join(REEL, "_preview.png"))
    else:
        build_audio(os.path.join(REEL, "_tmp", "mix.wav"))
        n = int(TOTAL * FPS)
        out = os.path.join(REEL, "video.mp4")
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                               "-r", str(FPS), "-i", "-", "-i", os.path.join(REEL, "_tmp", "mix.wav"),
                               "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                               "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        with get_context("fork").Pool(os.cpu_count() or 2) as pool:
            for k, b in enumerate(pool.imap(render_frame, range(n), chunksize=6)):
                ff.stdin.write(b)
                if k % 300 == 0: print("frame", k, "/", n, flush=True)
        ff.stdin.close(); ff.wait()
        print("wrote", out)
