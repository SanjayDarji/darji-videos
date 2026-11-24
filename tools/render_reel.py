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

BG_DELTA = (8, 14, 30)
PW = (255, 255, 255); SUB_HL = (245, 190, 55); BRANDC = GOLD; SLAB = (40, 40, 62)
def apply_theme(th):
    if not th: return
    g = globals()
    for k in ("BG", "GOLD", "CARD", "CARD2", "DARK", "BLUE", "ORANGE", "GREEN", "RED", "MUTED", "WHITE", "PW", "SUB_HL", "BRANDC", "SLAB"):
        if k in th: g[k] = tuple(th[k])
    if "SER3" in th: g["SER3"] = [tuple(c) for c in th["SER3"]]
    if "bg_delta" in th: g["BG_DELTA"] = tuple(th["bg_delta"])

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
       "facts": [0.03, 0.27, 0.50, 0.78], "headlines": [0.05, 0.38, 0.66], "baskets": [0.03, 0.21, 0.47, 0.73], "lesson": [0.05, 0.38, 0.62], "outro": [0.04, 0.5],
       "chook": [0.0, 0.14], "anatomy": [0.02, 0.26, 0.42, 0.58, 0.75], "gvr": [0.03, 0.5], "patterns": [0.08, 0.33, 0.7], "quiz": [0.0, 0.2, 0.5, 0.72],
       "isohook": [0.0, 0.2], "isocmp": [0.03, 0.2, 0.4, 0.6], "isobars": [0.03, 0.15], "poll": [0.0, 0.18, 0.5, 0.75],
       "lvhook": [0.0, 0.2], "lvdef": [0.03, 0.5], "lvflip": [0.03], "quiz2": [0.0, 0.2, 0.5, 0.72]}

def _dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", p]).decode().strip())

def load(reel_dir):
    global REEL, SPEC, SEG, TOTAL
    REEL = os.path.abspath(reel_dir)
    SPEC = json.load(open(os.path.join(REEL, "spec.json"), encoding="utf-8"))
    apply_theme(SPEC.get("theme"))
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
        arr[..., 0] = (BG[0] + BG_DELTA[0] * t); arr[..., 1] = (BG[1] + BG_DELTA[1] * t); arr[..., 2] = (BG[2] + BG_DELTA[2] * t)
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

def marked(d, cx, cy, s, size, maxw, color=None, hl=None, lh=1.32, a=1.0, bold=True):
    color = color or WHITE; hl = hl or GOLD
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
    text(d, CX, 835, SPEC["brand"], 96, BRANDC, a=clamp(e * 1.5))
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
    for i, (txt, up) in enumerate([(sc["h1"], bool(sc.get("up_first"))), (sc["h2"], not sc.get("up_first"))]):
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
        d.text((CX, 970), sc.get("mark", "?"), font=F(int(230 * clamp(e) * (1 + 0.05 * math.sin(lt * 5)))), fill=C(GOLD), anchor="mm")
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


# ---------------------------------------------------------------- candlestick scenes
def candle(d, x, hi, lo, b0, b1, w, col, a=1.0, ghost=False):
    top, bot = min(b0, b1), max(b0, b1)
    if bot - top < 7:
        m = (top + bot) // 2; top, bot = m - 3, m + 4
    d.line([(x, hi), (x, lo)], fill=C(MUTED if ghost else col, a), width=max(4, w // 9))
    if ghost:
        d.rounded_rectangle([x - w // 2, top, x + w // 2, bot], radius=max(3, w // 12), fill=C(CARD2, a), outline=C(MUTED, a), width=4)
    else:
        d.rounded_rectangle([x - w // 2, top, x + w // 2, bot], radius=max(3, w // 12), fill=C(col, a))

def dashed(d, x0, y, x1, col, a, dash=14, gap=10, width=3):
    x = x0
    while x < x1:
        d.line([(x, y), (min(x + dash, x1), y)], fill=C(col, a), width=width); x += dash + gap

SERIES = [(50, 56, 47, 54), (54, 58, 51, 52), (52, 53, 44, 46), (46, 50, 42, 49), (49, 57, 48, 55),
          (55, 60, 53, 58), (58, 61, 54, 55), (55, 56, 45, 47), (47, 62, 46, 60)]  # illustrative only

def py(p, y0, y1, lo=40, hi=64): return int(y1 - (p - lo) / (hi - lo) * (y1 - y0))

def draw_series(d, x0, step, w, y0, y1, k, a=1.0):
    for i, (o, h, l, c) in enumerate(SERIES):
        e = k(i)
        if e <= 0.02: continue
        col = GREEN if c >= o else RED
        cc = o + (c - o) * e; hh = o + (h - o) * e; ll = o + (l - o) * e
        candle(d, x0 + i * step, py(hh, y0, y1), py(ll, y0, y1), py(o, y0, y1), py(cc, y0, y1), w, col, min(1.0, e * 3) * a)

def sc_chook(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    e1 = eb(prog(lt, T[0], .4)); e2 = eb(prog(lt, T[1], .45))
    text(d, CX, 440 + slide(e1), sc["line1"], int(sc.get("size1", 62) * (0.85 + 0.15 * e1)), WHITE, a=clamp(e1 * 2))
    text(d, CX, 556 + slide(e2, 60), sc["line2"], int(sc.get("size2", 110) * (0.8 + 0.2 * e2)), GOLD, a=clamp(e2 * 2))
    ce = eo(prog(lt, 0.1, .5))
    rrect(d, [90, 650, 930, 1185], 34, CARD, CARD2, 2, clamp(ce * 2))
    for gy in (770, 890, 1010, 1120): d.line([(120, gy), (900, gy)], fill=C(CARD2, .55 * clamp(ce)), width=2)
    draw_series(d, 165, 88, 44, 700, 1150, lambda i: eo(prog(lt, 0.3 + i * 0.2, 0.35)))
    e = eb(prog(lt, 0.3 + 8 * 0.2 + 0.35, 0.5))
    if e > .1:
        x = 165 + 8 * 88; pul = 0.65 + 0.35 * math.sin(lt * 7)
        rrect(d, [x - 42, py(62, 700, 1150) - 22, x + 42, py(46, 700, 1150) + 22], 20, None, GOLD, 4, clamp(e) * pul)
    text(d, CX, 1218, sc.get("note", ""), 24, MUTED, bold=False, a=clamp(ce))

def sc_anatomy(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    ce = eb(prog(lt, T[0], .7)); cx = 300; mid = 810
    Y = dict(high=480, close=620, open=980, low=1140)
    if ce > .05:
        s = clamp(ce)
        g = glow_mask(520)
        im.paste(Image.new("RGB", g.size, GREEN), (cx - 260, mid - 260), g.point(lambda v: int(v * 0.16 * s)))
        yy = lambda y: int(mid + (y - mid) * s)
        candle(d, cx, yy(Y["high"]), yy(Y["low"]), yy(Y["close"]), yy(Y["open"]), 150, GREEN, a=clamp(ce * 2))
        if s > .9:
            text(d, cx, 800, "बॉडी", 42, DARK)
            text(d, cx - 92, 550, "पूँछ", 28, MUTED, bold=False, anchor="rm")
            text(d, cx - 92, 1060, "पूँछ", 28, MUTED, bold=False, anchor="rm")
    for name, hi_txt, key, k in [("OPEN", "खुलने की कीमत", "open", 1), ("HIGH", "सबसे ऊँची कीमत", "high", 2),
                                 ("LOW", "सबसे नीची कीमत", "low", 3), ("CLOSE", "बंद होने की कीमत", "close", 4)]:
        e = eo(prog(lt, T[k], .45)); a = clamp(e * 2.2)
        if e <= .12: continue
        y = Y[key]; ox = int((1 - e) * 40); sx = cx + 75 if key in ("open", "close") else cx
        dashed(d, sx, y, 505, GOLD, a)
        d.ellipse([sx - 9, y - 9, sx + 9, y + 9], fill=C(GOLD, a))
        rrect(d, [510 + ox, y - 46, 930, y + 46], 26, CARD, GOLD, 3, a)
        text(d, 538 + ox, y - 16, name, 38, WHITE, anchor="lm", a=a)
        text(d, 538 + ox, y + 24, hi_txt, 28, MUTED, bold=False, anchor="lm", a=a)

def sc_gvr(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    for i, (col, ttl, l1, l2) in enumerate([(GREEN, "हरी कैंडल", sc["g1"], sc["g2"]), (RED, "लाल कैंडल", sc["r1"], sc["r2"])]):
        e = eo(prog(lt, T[i], .5)); a = clamp(e * 2.2)
        if e <= .12: continue
        x0 = 90 + i * 430; cx = x0 + 205; oy = slide(e)
        rrect(d, [x0, 420 + oy, x0 + 410, 1165 + oy], 34, CARD, col, 3, a)
        text(d, cx, 480 + oy, ttl, 46, col, a=a)
        gr = eb(prog(lt, T[i] + .1, .6)); s = clamp(gr); m = 770 + oy
        yy = lambda y: int(m + (y + oy - m) * s)
        top, bot = 660, 880
        candle(d, cx, yy(580), yy(980), yy(top), yy(bot), 96, col, a=a)
        if s > .9:
            up = i == 0
            text(d, cx - 66, top + oy, "CLOSE" if up else "OPEN", 26, MUTED, bold=False, anchor="rm", a=a)
            text(d, cx - 66, bot + oy, "OPEN" if up else "CLOSE", 26, MUTED, bold=False, anchor="rm", a=a)
            pts = [(cx + 118, 690 + oy), (cx + 88, 750 + oy), (cx + 148, 750 + oy)] if up else [(cx + 118, 850 + oy), (cx + 88, 790 + oy), (cx + 148, 790 + oy)]
            d.polygon(pts, fill=C(col, a))
        text(d, cx, 1060 + oy, l1, 38, WHITE, a=a)
        text(d, cx, 1112 + oy, l2, 30, MUTED, bold=False, a=a)
    text(d, CX, 1208, sc.get("note", ""), 24, MUTED, bold=False, a=eo(prog(lt, T[1] + .3, .5)))

def mini_pattern(d, kind, cx, cy, a):
    if kind == "doji":
        candle(d, cx, cy - 78, cy + 78, cy, cy, 86, WHITE, a)
    elif kind == "hammer":
        candle(d, cx, cy - 70, cy + 84, cy - 66, cy - 24, 70, GREEN, a)
    else:
        candle(d, cx - 36, cy - 28, cy + 44, cy - 12, cy + 30, 44, RED, a)
        candle(d, cx + 34, cy - 74, cy + 80, cy + 66, cy - 58, 56, GREEN, a)

def sc_patterns(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    for i, row in enumerate(sc["rows"]):
        e = eo(prog(lt, T[i], .5)); a = clamp(e * 2.2)
        if e <= .12: continue
        y0 = 405 + i * 262 + slide(e); y1 = y0 + 240; cy = (y0 + y1) // 2
        rrect(d, [90, y0, 930, y1], 32, CARD, GOLD if row.get("hot") else CARD2, 3, a)
        rrect(d, [108, y0 + 18, 292, y1 - 18], 24, CARD2, None, 0, a)
        gr = eb(prog(lt, T[i] + .1, .5))
        if gr > .2: mini_pattern(d, row["kind"], 200, cy, a)
        text(d, 318, cy - 56, row["t"], 42, WHITE, anchor="lm", a=a)
        text(d, 318, cy - 2, row["s1"], 30, GOLD, bold=False, anchor="lm", a=a)
        text(d, 318, cy + 46, row["s2"], 30, MUTED, bold=False, anchor="lm", a=a)
    if "source" in sc:
        text(d, CX, 1215, sc["source"], 24, MUTED, bold=False, a=eo(prog(lt, T[1], .6)))

def sc_quiz(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    e = eo(prog(lt, T[0], .5))
    if e > .12:
        rrect(d, [90, 400 + slide(e), 930, 470 + slide(e)], 35, GOLD, None, 0, clamp(e * 2.2))
        text(d, CX, 435 + slide(e), sc["head"], 36, DARK, a=clamp(e * 2.2))
        pul = 1 + 0.06 * math.sin(lt * 5)
        candle(d, 280, 520, 860, 590, 780, 150, MUTED, a=clamp(e * 2), ghost=True)
        d.text((280, 685), "?", font=F(int(130 * pul)), fill=C(GOLD, 0.95 * clamp(e * 2)), anchor="mm")
    e = eb(prog(lt, T[1], .5)); a = clamp(e * 2.2)
    if e > .12:
        for k, (nm, val) in enumerate([("OPEN", sc["open"]), ("CLOSE", sc["close"])]):
            y0 = 545 + k * 150 + slide(e); y1 = y0 + 125
            rrect(d, [490, y0, 930, y1], 28, CARD, GOLD, 3, a)
            text(d, 520, (y0 + y1) // 2, nm, 34, MUTED, anchor="lm", a=a)
            text(d, 905, (y0 + y1) // 2, val, 60, GOLD, anchor="rm", a=a)
    e = eb(prog(lt, T[2], .5)); a = clamp(e * 2.2)
    if e > .12:
        for k, (lab, col) in enumerate([("A · हरी", GREEN), ("B · लाल", RED)]):
            x0 = 90 + k * 430; y0 = 905 + slide(e)
            rrect(d, [x0, y0, x0 + 410, y0 + 120], 34, CARD, col, 4, a)
            d.ellipse([x0 + 28, y0 + 38, x0 + 72, y0 + 82], fill=C(col, a))
            text(d, x0 + 100, y0 + 60, lab, 46, WHITE, anchor="lm", a=a)
    e = eb(prog(lt, T[3], .5))
    if e > .12:
        s = 1 + 0.04 * math.sin(lt * 6)
        text(d, CX, 1105, sc["ask"], int(46 * s), GOLD, a=clamp(e * 2))
        text(d, CX, 1180, sc.get("note", ""), 24, MUTED, bold=False, a=clamp(e))

SCENES = dict(hook=sc_hook, headlines=sc_headlines, baskets=sc_baskets, problem=sc_problem, analogy=sc_analogy, facts=sc_facts, lesson=sc_lesson, outro=sc_outro,
              chook=sc_chook, anatomy=sc_anatomy, gvr=sc_gvr, patterns=sc_patterns, quiz=sc_quiz)


# ---------------------------------------------------------------- support / resistance scenes
def poly_anim(d, pts, p, col, a=1.0, width=6):
    n = len(pts) - 1; pos = clamp(p) * n
    for i in range(n):
        if pos <= i: break
        f = min(1.0, pos - i)
        x0, y0 = pts[i]; x1, y1 = pts[i + 1]
        d.line([(x0, y0), (x0 + (x1 - x0) * f, y0 + (y1 - y0) * f)], fill=C(col, a), width=width)
        r = width // 2
        d.ellipse([x0 - r, y0 - r, x0 + r, y0 + r], fill=C(col, a))
    i = min(int(pos), n - 1); f = min(1.0, pos - i)
    hx = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f; hy = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
    if 0 < p < 1: d.ellipse([hx - 10, hy - 10, hx + 10, hy + 10], fill=C(GOLD, a))
    return pos

def touch_rings(d, pts, pos, idxs, seg_t, col):
    for k in idxs:
        if pos >= k:
            age = (pos - k) * seg_t
            if age < 0.6:
                r = int(12 + age * 80); al = 1 - age / 0.6; x, y = pts[k]
                d.ellipse([x - r, y - r, x + r, y + r], outline=C(col, al), width=4)

def sc_lvhook(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    e1 = eb(prog(lt, T[0], .4)); e2 = eb(prog(lt, T[1], .45))
    text(d, CX, 440 + slide(e1), sc["line1"], int(sc.get("size1", 58) * (0.85 + 0.15 * e1)), WHITE, a=clamp(e1 * 2))
    text(d, CX, 556 + slide(e2, 60), sc["line2"], int(sc.get("size2", 100) * (0.8 + 0.2 * e2)), GOLD, a=clamp(e2 * 2))
    ce = eo(prog(lt, 0.1, .5))
    rrect(d, [90, 650, 930, 1185], 34, CARD, CARD2, 2, clamp(ce * 2))
    yr, ys = 745, 1085
    for y, col, lab, t0, up in [(yr, RED, "RESISTANCE · छत", .35, True), (ys, GREEN, "SUPPORT · फ़र्श", .6, False)]:
        e = eo(prog(lt, t0, .4))
        if e > .05:
            dashed(d, 120, y, 120 + int(780 * e), col, clamp(e * 2), width=4)
            text(d, 135, y - 26 if up else y + 28, lab, 26, col, anchor="lm", a=clamp(e * 2))
    prices = [64, 69.6, 60.4, 69.8, 60.3, 69.5, 60.6, 66]
    xy = [(160 + int(i * 105), int(ys - (p - 60) / 10 * (ys - yr))) for i, p in enumerate(prices)]
    PD = sc.get("pathdur", 3.6)
    pos = poly_anim(d, xy, prog(lt, .9, PD), WHITE, 1.0, 7)
    touch_rings(d, xy, pos, [1, 2, 3, 4, 5, 6], PD / (len(xy) - 1), GOLD)
    text(d, CX, 1218, sc.get("note", ""), 24, MUTED, bold=False, a=clamp(ce))

def sc_lvdef(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    specs = [(GREEN, "SUPPORT", "फ़र्श", sc["s1"], sc["s2"], [(0, .05), (.30, .95), (.5, .45), (.72, .95), (1, .35)], .95),
             (RED, "RESISTANCE", "छत", sc["r1"], sc["r2"], [(0, .95), (.3, .05), (.5, .55), (.72, .05), (1, .65)], .05)]
    for i, (col, ttl, hi, l1, l2, pts, lv) in enumerate(specs):
        e = eo(prog(lt, T[i], .5)); a = clamp(e * 2.2)
        if e <= .12: continue
        x0 = 90 + i * 430; cx = x0 + 205; oy = slide(e)
        rrect(d, [x0, 420 + oy, x0 + 410, 1165 + oy], 34, CARD, col, 3, a)
        text(d, cx, 478 + oy, ttl, 42, col, a=a)
        text(d, cx, 538 + oy, hi, 42, GOLD, a=a)
        ly = int(610 + lv * 340) + oy
        dashed(d, x0 + 30, ly, x0 + 380, col, a, width=4)
        xy = [(x0 + 45 + int(u * 320), 610 + int(v * 340) + oy) for u, v in pts]
        pos = poly_anim(d, xy, prog(lt, T[i] + .2, 2.2), WHITE, a, 6)
        touch_rings(d, xy, pos, [1, 3], 2.2 / (len(xy) - 1), col)
        text(d, cx, 1050 + oy, l1, 36, WHITE, a=a)
        text(d, cx, 1105 + oy, l2, 28, MUTED, bold=False, a=a)
    text(d, CX, 1208, sc.get("note", ""), 24, MUTED, bold=False, a=eo(prog(lt, T[1] + .3, .5)))

def sc_lvflip(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    ce = eo(prog(lt, T[0], .5)); a = clamp(ce * 2.2)
    if ce <= .1: return
    rrect(d, [90, 430, 930, 1170], 34, CARD, GOLD, 3, a)
    text(d, CX, 484, sc["title"], 44, GOLD, a=a)
    X = lambda u: 140 + int(u * 750); Y = lambda v: 540 + int(v * 580)
    uv = [(0, .88), (.12, .5), (.22, .8), (.34, .5), (.44, .76), (.56, .16), (.68, .5), (.8, .2), (.93, .08)]
    xy = [(X(u), Y(v)) for u, v in uv]
    PD = sc.get("pathdur", 6.5); n = len(xy) - 1
    p = prog(lt, .6, PD); pos = p * n; flipped = pos >= 5.0
    ly = Y(.5); col = GREEN if flipped else RED
    dashed(d, 120, ly, 900, col, a, width=4)
    if not flipped: text(d, 135, ly - 28, "छत · RESISTANCE", 28, RED, anchor="lm", a=a)
    else: text(d, 895, ly + 52, "अब फ़र्श · SUPPORT", 28, GREEN, anchor="rm", a=a)
    poly_anim(d, xy, p, WHITE, a, 7)
    touch_rings(d, xy, pos, [1, 3, 6], PD / n, GOLD)
    if flipped:
        e = clamp((pos - 5.0) * (PD / n) / 0.4)
        text(d, xy[5][0] - 10, xy[5][1] - 36, "BREAKOUT", 28, GOLD, a=e)
    text(d, CX, 1138, sc.get("note", ""), 24, MUTED, bold=False, a=a)

def sc_quiz2(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    e = eo(prog(lt, T[0], .5))
    if e > .12:
        a = clamp(e * 2.2)
        rrect(d, [90, 400 + slide(e), 930, 470 + slide(e)], 35, GOLD, None, 0, a)
        text(d, CX, 435 + slide(e), sc["head"], 36, DARK, a=a)
        rrect(d, [90, 500, 470, 890], 30, CARD, CARD2, 3, a)
        ly = 590
        dashed(d, 110, ly, 450, GOLD, a, width=4)
        text(d, 112, ly - 26, "₹100 = ?", 30, GOLD, anchor="lm", a=a)
        pv = [(0, .95), (.22, .2), (.38, .72), (.55, .2), (.70, .74), (.88, .2), (1.0, .62)]
        xy = [(120 + int(u * 320), 520 + int(v * 350)) for u, v in pv]
        PD = sc.get("pathdur", 4.0)
        pos = poly_anim(d, xy, prog(lt, T[1], PD), WHITE, a, 6)
        touch_rings(d, xy, pos, [1, 3, 5], PD / (len(xy) - 1), GOLD)
    e = eb(prog(lt, T[1], .5)); a = clamp(e * 2.2)
    if e > .12:
        rrect(d, [490, 500 + slide(e), 930, 890 + slide(e)], 30, CARD, GOLD, 3, a)
        text(d, 710, 600 + slide(e), sc["l1"], 40, WHITE, a=a)
        text(d, 710, 690 + slide(e), sc["l2"], 36, MUTED, bold=False, a=a)
        text(d, 710, 790 + slide(e), sc["l3"], 40, GOLD, a=a)
    e = eb(prog(lt, T[2], .5)); a = clamp(e * 2.2)
    if e > .12:
        for k, (lab, col) in enumerate([("A · सपोर्ट", GREEN), ("B · रेजिस्टेंस", RED)]):
            x0 = 90 + k * 430; y0 = 935 + slide(e)
            rrect(d, [x0, y0, x0 + 410, y0 + 115], 34, CARD, col, 4, a)
            d.ellipse([x0 + 26, y0 + 36, x0 + 68, y0 + 78], fill=C(col, a))
            text(d, x0 + 86, y0 + 58, lab, 38, WHITE, anchor="lm", a=a)
    e = eb(prog(lt, T[3], .5))
    if e > .12:
        s = 1 + 0.04 * math.sin(lt * 6)
        text(d, CX, 1105, sc["ask"], int(46 * s), GOLD, a=clamp(e * 2))
        text(d, CX, 1170, sc.get("note", ""), 24, MUTED, bold=False, a=clamp(e))

SCENES.update(lvhook=sc_lvhook, lvdef=sc_lvdef, lvflip=sc_lvflip, quiz2=sc_quiz2)


# ---------------------------------------------------------------- 3D-style scenes (real perspective projection of boxes)
SER3 = [(57, 135, 229), (217, 89, 38), (25, 158, 112)]   # validated dark categorical slots 1-3 (dataviz palette)
PILE = [(57, 135, 229), (217, 89, 38), (25, 158, 112), (144, 133, 233), (213, 81, 129), (201, 133, 0), (110, 120, 140)]

def shade(col, f): return tuple(max(0, min(255, int(c * f))) for c in col)

def box3d(d, xc, y0, zc, w, h, dp, col, th, ox, oy, sc, el, a=1.0):
    ct, st = math.cos(th), math.sin(th); cf, sf = math.sqrt(1 - el * el), el
    def P(X, Y, Z):
        xr = X * ct + Z * st; zr = -X * st + Z * ct
        return (ox + xr * sc, oy - (Y * cf + zr * sf) * sc)
    x0, x1 = xc - w / 2, xc + w / 2; z0, z1 = zc - dp / 2, zc + dp / 2; y1 = y0 + h
    faces = [((0, 0, -1), [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)]),
             ((0, 0, 1), [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]),
             ((-1, 0, 0), [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)]),
             ((1, 0, 0), [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)])]
    for (nx, ny, nz), cs in faces:
        if -nx * st + nz * ct < 0:
            light = 0.80 + 0.20 * (-(nx * ct + nz * st))
            pts = [P(*c) for c in cs]
            d.polygon(pts, fill=C(shade(col, light), a)); d.line(pts + [pts[0]], fill=C(BG, a), width=2)
    top = [P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)]
    d.polygon(top, fill=C(shade(col, 1.18), a)); d.line(top + [top[0]], fill=C(BG, a), width=2)
    return P

def cube_pile(d, th, ox, oy, sc, k=lambda i: 1.0, a=1.0, size=70, gap=4):
    pos = []
    for j in range(3):
        for i in range(3): pos.append(((i - 1) * (size + gap), 0, (j - 1) * (size + gap)))
    for j in range(2):
        for i in range(2): pos.append(((i - .5) * (size + gap), size + gap, (j - .5) * (size + gap)))
    pos.append((0, 2 * (size + gap), 0))
    ct, st = math.cos(th), math.sin(th); items = []
    for idx, (X, Y, Z) in enumerate(pos):
        e = k(idx)
        if e <= .02: continue
        items.append((-X * st + Z * ct, Y, idx, X, Y, Z, e))
    for zr, _, idx, X, Y, Z, e in sorted(items, key=lambda t: (-t[0], t[1])):
        s2 = clamp(e * 1.15, 0, 1.06)
        box3d(d, X, Y + (1 - clamp(e)) * 160, Z, size * s2, size * s2, size * s2, PILE[idx % len(PILE)], th, ox, oy, sc, 0.5, clamp(e * 3) * a)

def sc_isohook(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    e1 = eb(prog(lt, T[0], .4)); e2 = eb(prog(lt, T[1], .45))
    text(d, CX, 440 + slide(e1), sc["line1"], int(sc.get("size1", 60) * (0.85 + 0.15 * e1)), WHITE, a=clamp(e1 * 2))
    text(d, CX, 556 + slide(e2, 60), sc["line2"], int(sc.get("size2", 96) * (0.8 + 0.2 * e2)), GOLD, a=clamp(e2 * 2))
    ce = eo(prog(lt, 0.1, .5))
    rrect(d, [90, 650, 930, 1185], 34, CARD, CARD2, 2, clamp(ce * 2))
    cube_pile(d, 0.6 + lt * 0.55, CX, 1110, 1.45, lambda i: eb(prog(lt, .5 + i * .14, .42)))
    for k, ch in enumerate(sc.get("chips", [])):
        ct0 = sc.get('chip_t', [1.6, 2.1])[k] if k < len(sc.get('chip_t', [1.6, 2.1])) else 1.6 + k * .5
        e = eb(prog(lt, ct0, .45)); a = clamp(e * 2.2)
        if e <= .1: continue
        x0 = 105 if k == 0 else 635
        rrect(d, [x0, 800 + k * 40 + slide(e), x0 + 280, 872 + k * 40 + slide(e)], 36, CARD2, GOLD, 3, a)
        text(d, x0 + 140, 836 + k * 40 + slide(e), ch, 34, WHITE, a=a)
    text(d, CX, 1218, sc.get("note", ""), 24, MUTED, bold=False, a=clamp(ce))

def sc_isocmp(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    be = eo(prog(lt, T[0], .5)); a0 = clamp(be * 2)
    rrect(d, [90, 420, 930, 1215], 34, CARD, CARD2, 2, a0)
    bb = eo(prog(lt, T[1], .5))
    if be > .05:
        text(d, CX, 640, sc["col_name"], 26, WHITE, a=a0)
        va = clamp(1 - bb * 2.5) * a0
        if va > .02 and sc.get("vs"):
            for k, nm in enumerate(sc["vs"]):
                x0 = 120 if k == 0 else 540
                rrect(d, [x0, 470, x0 + 360, 570], 40, CARD2, SER3[0] if k == 0 else SER3[1], 4, va)
                text(d, x0 + 180, 520, nm, 34, WHITE, a=va)
            text(d, CX, 520, "vs", 30, MUTED, bold=False, a=va)
    if bb > .05:
        val = sc["badge"] * eo(prog(lt, T[1] + .05, 1.0))
        text(d, CX, 500, f"{val:.0f}%", 132, GOLD, a=clamp(bb * 2))
        text(d, CX, 592, sc["badge_cap"], 27, MUTED, bold=False, a=clamp(bb * 2))
    th = 0.5 + 0.34 * math.sin(lt * 0.8); ox, oy, scl, el = 510, 1010, 1.0, 0.5; PXP = 3.0
    box3d(d, 0, -14, 0, 440, 14, 250, SLAB, th, ox, oy, scl, el, a=a0)
    g1 = eo(prog(lt, T[1], .9)); g2 = eo(prog(lt, T[1] + .45, .9))
    v1, v2 = sc["badge"], 100 - sc["badge"]
    h1 = v1 * PXP * g1; h2 = v2 * PXP * g2
    if h1 > 1: box3d(d, 0, 0, 0, 170, h1, 170, SER3[0], th, ox, oy, scl, el)
    if h2 > 1: box3d(d, 0, v1 * PXP * g1, 0, 170, h2, 170, (72, 78, 108), th, ox, oy, scl, el)
    ct, st = math.cos(th), math.sin(th); cf, sf = math.sqrt(1 - el * el), el
    def P(X, Y, Z):
        xr = X * ct + Z * st; zr = -X * st + Z * ct
        return (ox + xr * scl, oy - (Y * cf + zr * sf) * scl)
    le = eo(prog(lt, T[2], .5)); a = clamp(le * 2)
    if le > .05:
        for (nm, val, ymid, col, lx, anc) in ((sc["seg1"], v1, v1 / 2, SER3[0], 124, "lm"), (sc["seg2"], v2, v1 + v2 / 2, (72, 78, 108), 896, "rm")):
            px, py2 = P(0, ymid * PXP, 0)
            d.rectangle([lx - 12 if anc == "lm" else lx + 4, py2 - 9, lx - 4 if anc == "lm" else lx + 12, py2 + 9], fill=C(col, a))
            text(d, lx + (4 if anc == "lm" else -4), py2 - 18, f"{val:.0f}%", 40, WHITE, anchor=anc, a=a)
            text(d, lx + (4 if anc == "lm" else -4), py2 + 22, nm, 24, MUTED, anchor=anc, bold=False, a=a)
            ex = 124 + 230 if anc == "lm" else 896 - 230
            d.line([(ex, py2), (px, py2)], fill=C(col, a * .9), width=3)
            d.ellipse([px - 7, py2 - 7, px + 7, py2 + 7], fill=C(WHITE, a))
    ce = eb(prog(lt, T[3], .5))
    if ce > .08:
        ac = clamp(ce * 2.2)
        text(d, CX, 1110, sc.get("chips_head", ""), 24, MUTED, bold=False, a=ac)
        for k, ch in enumerate(sc.get("chips", [])):
            e = eb(prog(lt, T[3] + k * .55, .4)); aa = clamp(e * 2.2)
            if e <= .08: continue
            x0 = 100 + k * 275
            rrect(d, [x0, 1132 + slide(e), x0 + 255, 1204 + slide(e)], 26, CARD2, SER3[k], 3, aa)
            nm, sb = (ch if isinstance(ch, (list, tuple)) else (ch, ""))
            text(d, x0 + 127, 1156 + slide(e), nm, 27, WHITE, a=aa)
            if sb: text(d, x0 + 127, 1185 + slide(e), sb, 22, MUTED, bold=False, a=aa)
    text(d, CX, 1236, sc.get("note", ""), 22, MUTED, bold=False, a=clamp(be))

def obl_box(d, x, y, w, h, dx, dy, col, a=1.0):
    d.polygon([(x + w, y), (x + w + dx, y - dy), (x + w + dx, y + h - dy), (x + w, y + h)], fill=C(shade(col, .62), a))
    d.polygon([(x, y), (x + dx, y - dy), (x + w + dx, y - dy), (x + w, y)], fill=C(shade(col, 1.2), a))
    d.rectangle([x, y, x + w, y + h], fill=C(col, a))

def sc_isobars(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    be = eo(prog(lt, T[0], .5)); a = clamp(be * 2.2)
    rrect(d, [90, 420, 930, 1215], 34, CARD, CARD2, 2, clamp(be * 2))
    text(d, CX, 478, sc["title"], 32, GOLD, a=a)
    if sc.get("sub"): text(d, CX, 520, sc["sub"], 24, MUTED, bold=False, a=a)
    mx = max(v for _, v in sc["rows"]); L = 290; step = sc.get("step", 100); hl = sc.get("hl")
    for i, (nm, v) in enumerate(sc["rows"]):
        g = eo(prog(lt, T[1] + i * .2, .7)); y = 575 + i * step
        if g <= .02: continue
        col = SER3[0] if (hl is None or i in hl) else (72, 78, 108)
        text(d, 110, y + 30, nm, 27, WHITE if col == SER3[0] else MUTED, anchor="lm", a=clamp(g * 3))
        w = max(10, int(v / mx * L * g))
        obl_box(d, 440, y, w, 60, 24, 14, col, clamp(g * 3))
        text(d, 440 + w + 42, y + 30, sc.get("fmt", "{:.0f}%").format(v * g), 29, WHITE, anchor="lm", a=clamp(g * 3))
    text(d, CX, 1236, sc.get("note", ""), 22, MUTED, bold=False, a=clamp(be))

def sc_poll(im, d, lt, dur, sc):
    T = reveals(sc, dur)
    e = eo(prog(lt, T[0], .5))
    if e > .12:
        a = clamp(e * 2.2)
        rrect(d, [90, 400 + slide(e), 930, 470 + slide(e)], 35, GOLD, None, 0, a)
        text(d, CX, 435 + slide(e), sc["head"], 36, DARK, a=a)
        marked(d, CX, 585, sc["q"], 54, 820, a=a)
    for k, (lab, txt) in enumerate(sc["opts"]):
        ot = (sc.get('opt_rev') or [T[1] / dur + k * .35 / dur for k in range(3)])[k] * dur if sc.get('opt_rev') else T[1] + k * .35
        e = eb(prog(lt, ot, .45)); a = clamp(e * 2.2)
        if e <= .1: continue
        y0 = 700 + k * 135 + slide(e)
        rrect(d, [90, y0, 930, y0 + 108], 30, CARD, SER3[k], 4, a)
        obl_box(d, 118, y0 + 24, 60, 60, 16, 10, SER3[k], a)
        text(d, 148, y0 + 56, lab, 40, PW, a=a)
        text(d, 250, y0 + 54, txt, 44, WHITE, anchor="lm", a=a)
    e = eb(prog(lt, T[3], .5))
    if e > .12:
        s = 1 + 0.04 * math.sin(lt * 6)
        text(d, CX, 1160, sc["ask"], int(46 * s), GOLD, a=clamp(e * 2))
        text(d, CX, 1225, sc.get("note", ""), 24, MUTED, bold=False, a=clamp(e))

SCENES.update(isohook=sc_isohook, isocmp=sc_isocmp, isobars=sc_isobars, poll=sc_poll)

def cover_s2(path):
    cv = SPEC["cover"]
    im = base_bg().copy(); g = glow_mask(1100)
    im.paste(Image.new("RGB", g.size, GOLD), (800 - 550, 1180 - 550), g.point(lambda v: int(v * 0.30)))
    im.paste(Image.new("RGB", g.size, BLUE), (150 - 550, 380 - 550), g.point(lambda v: int(v * 0.20)))
    d = ImageDraw.Draw(im)
    cube_pile(d, 0.65, 215, 1530, 1.25); cube_pile(d, -0.45, 880, 1480, 0.95)
    rrect(d, [100, 290, 690, 360], 35, CARD, GOLD, 3)
    text(d, 395, 325, cv["pill"], 34, GOLD)
    text(d, 100, 540, cv["l1"], cv.get("s1", 190), WHITE, anchor="lm")
    text(d, 100, 720, cv["l2"], cv.get("s2", 130), GOLD, anchor="lm")
    text(d, 100, 860, cv["sub"], 46, MUTED, anchor="lm")
    paste_card(im, face_card(520, 566), 600, 1220, yaw=-0.32, scale=1.0)
    d = ImageDraw.Draw(im)
    text(d, 100, 1755, SPEC["brand"], 70, GOLD, anchor="lm")
    d.rectangle([100, 1800, 460, 1806], fill=GOLD)
    im.save(path, quality=93)

# ---------------------------------------------------------------- chrome + subtitles
def chrome(im, d, t):
    av = avatar(46); im.paste(av, (90, 262), av)
    text(d, 206, 292, SPEC["brand"], 46, BRANDC, anchor="lm")
    text(d, 206, 338, SPEC.get("tagline", ""), 25, MUTED, bold=False, anchor="lm")
    tag = SPEC.get("day_tag", "")
    pw = max(240, int(d.textlength(tag, font=F(24))) + 54)
    rrect(d, [930 - pw, 276, 930, 326], 25, CARD, GOLD, 2)
    text(d, 930 - pw // 2, 301, tag, 24, GOLD)

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
    marked(d, CX, cy, subs[idx], size, 800, color=PW, hl=SUB_HL)

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

def extruded(im, cx, cy, s, size, depth, top, bot, side, glow=None):
    from PIL import ImageFilter
    mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).text((cx, cy), s, font=F(size, True), fill=255, anchor="mm", language="hi")
    if glow:
        gl = mask.filter(ImageFilter.GaussianBlur(46)).point(lambda v: int(v * 0.55))
        im.paste(Image.new("RGB", (W, H), glow), (0, 0), gl)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    for i in range(depth, 0, -1):
        col = shade(side, 0.38 + 0.62 * (1 - i / depth))
        ld.text((cx + i * 1.15, cy + i * 1.15), s, font=F(size, True), fill=col + (255,), anchor="mm", language="hi")
    grad = np.zeros((H, W, 3), np.uint8); y0, y1 = cy - size * .5, cy + size * .5
    t = np.clip((np.arange(H) - y0) / (y1 - y0), 0, 1)[:, None]
    for k in range(3): grad[..., k] = (top[k] + (bot[k] - top[k]) * t).astype(np.uint8)
    layer.paste(Image.fromarray(grad, "RGB"), (0, 0), mask)
    im.paste(layer.convert("RGB"), (0, 0), layer.split()[3])

def cover_s3(path):
    cv = SPEC["cover"]; CORAL = (255, 82, 102)
    im = base_bg().copy()
    for (gx, gy, gs, col, al) in ((540, 760, 1500, (110, 70, 255), .42), (880, 1520, 900, (255, 82, 102), .16), (150, 1450, 800, (80, 90, 235), .22)):
        g = glow_mask(gs); im.paste(Image.new("RGB", g.size, col), (gx - gs // 2, gy - gs // 2), g.point(lambda v, al=al: int(v * al)))
    d = ImageDraw.Draw(im)
    # perspective floor grid
    vx, vy = 540, 1180
    for k in range(-14, 15):
        d.line([(vx + k * 18, vy), (vx + k * 190, 1920)], fill=C((120, 90, 255), .20), width=2)
    for j in range(1, 11):
        y = vy + 740 * (j / 10) ** 2.1
        d.line([(0, y), (W, y)], fill=C((120, 90, 255), .10 + .16 * j / 10), width=2)
    # floating cubes
    for (X, Y, sz, col, th) in ((120, 700, 96, PILE[1], .6), (965, 640, 84, PILE[2], -.5), (95, 1085, 70, PILE[3], .8), (985, 1010, 100, PILE[0], -.7)):
        box3d(d, 0, 0, 0, sz, sz, sz, col, th, X, Y, 1.0, .5)
    # hero number
    extruded(im, 540, 728, cv["hero"], cv.get("hs", 430), 44, (255, 255, 255), (186, 160, 255), (92, 60, 230), glow=(120, 80, 255))
    d = ImageDraw.Draw(im)
    text(d, CX, 1000, cv["cap"], 56, WHITE)
    text(d, CX, 1062, cv["src"], 28, MUTED, bold=False)
    # stamp
    st = Image.new("RGBA", (980, 230), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
    sd.rounded_rectangle([10, 10, 970, 220], 36, outline=CORAL + (255,), width=9)
    sd.rounded_rectangle([30, 30, 950, 200], 26, outline=CORAL + (190,), width=3)
    sd.text((490, 108), cv["stamp"], font=F(104, True), fill=CORAL + (255,), anchor="mm")
    st = st.rotate(7, expand=True, resample=Image.BICUBIC)
    im.paste(st.convert("RGB"), (540 - st.width // 2, 335 - st.height // 2), st.split()[3])
    d = ImageDraw.Draw(im)
    # question
    text(d, CX, 1160, cv["q1"], 92, WHITE)
    text(d, CX, 1268, cv["q2"], 108, GOLD)
    # 3D column (43 / 57)
    th = 0.62; ox, oy = 805, 1668; P = 2.2
    box3d(d, 0, -12, 0, 300, 12, 190, (40, 40, 62), th, ox, oy, 1.0, .5)
    box3d(d, 0, 0, 0, 130, 43 * P, 130, SER3[0], th, ox, oy, 1.0, .5)
    box3d(d, 0, 43 * P, 0, 130, 57 * P, 130, (84, 90, 124), th, ox, oy, 1.0, .5)
    # face disc with neon ring
    r = 172; fx, fy = 290, 1548
    g = glow_mask(2 * r + 330); im.paste(Image.new("RGB", g.size, (130, 90, 255)), (fx - g.size[0] // 2, fy - g.size[1] // 2), g.point(lambda v: int(v * .55)))
    d = ImageDraw.Draw(im)
    d.ellipse([fx - r - 18, fy - r - 18, fx + r + 18, fy + r + 18], fill=GOLD)
    d.ellipse([fx - r - 7, fy - r - 7, fx + r + 7, fy + r + 7], fill=DARK)
    src = face_img().crop((95, 60, 385, 350)).resize((2 * r, 2 * r), Image.LANCZOS)
    m = Image.new("L", (2 * r, 2 * r), 0); ImageDraw.Draw(m).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
    im.paste(src, (fx - r, fy - r), m)
    d = ImageDraw.Draw(im)
    rrect(d, [fx - 175, fy + r - 30, fx + 175, fy + r + 38], 34, GOLD, None, 0)
    text(d, fx, fy + r + 4, SPEC["brand"], 40, DARK)
    text(d, CX, 1842, cv.get("foot", "शैक्षणिक जानकारी · निवेश सलाह नहीं"), 28, MUTED, bold=False)
    im.save(path, quality=94)


ANTON = "/usr/share/fonts/truetype/google-fonts/ofl/anton/Anton-Regular.ttf"
POPB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"

def person_cutout():
    """GrabCut person cutout of the face photo -> RGBA (face pixels untouched)."""
    import cv2
    rgb = np.array(face_img().convert("RGB")); im = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR); h, w = im.shape[:2]
    m = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    cv2.rectangle(m, (60, 300), (w - 40, h), cv2.GC_PR_FGD, -1)
    cv2.ellipse(m, (250, 210), (115, 150), 0, 0, 360, cv2.GC_PR_FGD, -1)
    cv2.ellipse(m, (250, 230), (70, 100), 0, 0, 360, cv2.GC_FGD, -1)
    cv2.rectangle(m, (170, 380), (340, h), cv2.GC_FGD, -1)
    cv2.rectangle(m, (0, 0), (w, 40), cv2.GC_BGD, -1); cv2.rectangle(m, (0, 0), (55, 260), cv2.GC_BGD, -1)
    cv2.rectangle(m, (w - 45, 0), (w, 300), cv2.GC_BGD, -1)
    cv2.rectangle(m, (95, 150), (166, 300), cv2.GC_BGD, -1); cv2.fillPoly(m, [np.array([(314, 150), (w, 150), (w, 336), (380, 332), (332, 318), (304, 290), (293, 262), (293, 241), (314, 241)], np.int32)], cv2.GC_BGD)
    cv2.rectangle(m, (150, 241), (190, 282), cv2.GC_BGD, -1)
    cv2.grabCut(im, m, None, np.zeros((1, 65)), np.zeros((1, 65)), 8, cv2.GC_INIT_WITH_MASK)
    a = ((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD)).astype(np.uint8) * 255
    r_, g_, b_ = [rgb[..., i].astype(int) for i in range(3)]
    teal = ((g_ - r_) > 26) & ((b_ - r_) > 36); teal[300:] = False
    teal = cv2.dilate(teal.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool); teal[300:] = False
    a[teal] = 0
    a = cv2.morphologyEx(a, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)); a = cv2.morphologyEx(a, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(a)
    if n > 1: a = ((lab == 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])) * 255).astype(np.uint8)
    a = cv2.erode(a, np.ones((3, 3), np.uint8))
    out = Image.fromarray(rgb).convert("RGBA"); out.putalpha(Image.fromarray(a))
    return out

def dilate_L(mask, px):
    import cv2
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * px + 1, 2 * px + 1))
    return Image.fromarray(cv2.dilate(np.array(mask), k))

def sticker(im, layer_rgba, pos, outline=16, shadow=(14, 16), ol=(255, 255, 255), sh=(12, 12, 12)):
    """paste an RGBA layer (full-canvas coords via pos) with white sticker outline + hard black shadow"""
    lw, lh = layer_rgba.size; cv = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cv.paste(layer_rgba, pos, layer_rgba)
    a = cv.split()[3]; big = dilate_L(a, outline).filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(1.2))
    shm = Image.new("L", (W, H), 0); shm.paste(big, shadow, big)
    im.paste(Image.new("RGB", (W, H), sh), (0, 0), shm)
    im.paste(Image.new("RGB", (W, H), ol), (0, 0), big)
    im.paste(cv.convert("RGB"), (0, 0), a)

def cover_s4(path):
    cv = SPEC["cover"]; YEL = (255, 221, 0); BLK = (14, 14, 14); RED = (255, 52, 52)
    yy, xx = np.mgrid[0:H, 0:W]; dist = np.sqrt(((xx - 540) / 700.0) ** 2 + ((yy - 760) / 900.0) ** 2); dist = np.clip(dist, 0, 1.2)
    arr = np.zeros((H, W, 3), np.float32)
    for k, (c0, c1) in enumerate(zip((255, 240, 70), (255, 196, 0))): arr[..., k] = c0 + (c1 - c0) * np.clip(dist, 0, 1)
    im = Image.fromarray(arr.astype(np.uint8), "RGB"); d = ImageDraw.Draw(im)
    for gy in range(0, H + 40, 46):                       # halftone dots, strongest bottom-left and top-right
        for gx in range(0, W + 40, 46):
            f = max(0.0, 1 - math.hypot(gx - 0, gy - 1920) / 900) + max(0.0, 1 - math.hypot(gx - 1080, gy - 0) / 700)
            r = 17 * min(1.0, f)
            if r > 1.5: d.ellipse([gx - r, gy - r, gx + r, gy + r], fill=(255, 190, 0))
    # hero number, fitted to width
    hs = 640; hero = cv["hero"]
    while ImageDraw.Draw(Image.new("L", (10, 10))).textlength(hero, font=ImageFont.truetype(ANTON, hs)) > 900: hs -= 10
    fh = ImageFont.truetype(ANTON, hs)
    tw = d.textlength(hero, font=fh)
    hm = Image.new("RGBA", (W, H), (0, 0, 0, 0)); hd = ImageDraw.Draw(hm)
    xl = 540 - tw / 2; cy = 700
    pct_x = xl + d.textlength(hero[:-1], font=fh)
    hd.text((xl, cy), hero[:-1], font=fh, fill=BLK + (255,), anchor="lm")
    hd.text((pct_x, cy), hero[-1], font=fh, fill=RED + (255,), anchor="lm")
    sticker(im, hm, (0, 0), outline=20, shadow=(16, 20))
    d = ImageDraw.Draw(im)
    # top tag (black pill, tilted) and alert dot
    tg = Image.new("RGBA", (760, 120), (0, 0, 0, 0)); td = ImageDraw.Draw(tg)
    td.rounded_rectangle([0, 10, 750, 110], 50, fill=BLK + (255,))
    td.text((375, 62), cv["tag"], font=ImageFont.truetype(ANTON, 58), fill=YEL + (255,), anchor="mm")
    tg = tg.rotate(4, expand=True, resample=Image.BICUBIC); im.paste(tg.convert("RGB"), (70, 300), tg.split()[3])
    d = ImageDraw.Draw(im); d.ellipse([890, 310, 990, 410], fill=RED, outline=BLK, width=7)
    d.text((940, 362), "!", font=ImageFont.truetype(ANTON, 86), fill=WHITE, anchor="mm")
    # headline
    f1 = ImageFont.truetype(POPB, 128); f2 = ImageFont.truetype(POPB, 150)
    d.text((86, 1040), cv["l1"], font=f1, fill=BLK, anchor="lm", language="hi")
    mk = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); md = ImageDraw.Draw(mk)
    t2w = d.textlength(cv["l2"], font=f2, language="hi")
    rnd = [3, -4, 5, -2, 4, -3]
    md.polygon([(60 + rnd[0], 30 + rnd[1]), (110 + t2w + rnd[2], 22 + rnd[3]), (118 + t2w + rnd[4], 214 + rnd[5]), (52 + rnd[1], 226 + rnd[2])], fill=RED + (255,))
    md.text((86, 126), cv["l2"], font=f2, fill=WHITE + (255,), anchor="lm", language="hi")
    mk = mk.rotate(-3, expand=False, resample=Image.BICUBIC)
    sh2 = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); sh2.paste(Image.new("RGBA", (W, 260), BLK + (255,)), (10, 12), mk.split()[3])
    im.paste(sh2.convert("RGB"), (0, 1100), sh2.split()[3]); im.paste(mk.convert("RGB"), (0, 1100), mk.split()[3])
    d = ImageDraw.Draw(im)
    rrect(d, [86, 1368, 86 + int(d.textlength(cv["src"], font=F(30), language="hi")) + 44, 1428], 30, WHITE, BLK, 4)
    d.text((108, 1398), cv["src"], font=F(30), fill=BLK, anchor="lm", language="hi")
    d.text((92, 1470), cv.get("chips_head", ""), font=F(30), fill=BLK, anchor="lm", language="hi")
    for k, ch in enumerate(cv.get("chips", [])):
        cw = int(d.textlength(ch, font=ImageFont.truetype(POPB, 34))) + 44; y0 = 1495 + k * 56
        rrect(d, [90, y0, 90 + cw, y0 + 46], 23, WHITE, BLK, 4)
        d.text((90 + cw // 2, y0 + 23), ch, font=ImageFont.truetype(POPB, 34), fill=BLK, anchor="mm")
    # face sticker
    pc = person_cutout(); fw = 760; fh2 = int(pc.height * fw / pc.width)
    pc = pc.resize((fw, fh2), Image.LANCZOS); pc = pc.rotate(3, expand=True, resample=Image.BICUBIC)
    sticker(im, pc, (470, 1236), outline=18, shadow=(14, 16))
    d = ImageDraw.Draw(im)
    # brand ribbon
    bw = int(d.textlength(SPEC["brand"], font=ImageFont.truetype(ANTON, 62))) + 70
    br = Image.new("RGBA", (bw, 110), (0, 0, 0, 0)); bd = ImageDraw.Draw(br)
    bd.rounded_rectangle([0, 8, bw - 6, 100], 22, fill=BLK + (255,)); bd.text((bw // 2 - 3, 56), SPEC["brand"], font=ImageFont.truetype(ANTON, 62), fill=YEL + (255,), anchor="mm")
    br = br.rotate(3, expand=True, resample=Image.BICUBIC); im.paste(br.convert("RGB"), (50, 1688), br.split()[3])
    d = ImageDraw.Draw(im); d.text((60, 1830), cv.get("foot", "शैक्षणिक जानकारी · निवेश सलाह नहीं"), font=F(30, False), fill=BLK, anchor="lm", language="hi")
    im.save(path, quality=94)


LORA = "/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf"
def SER(size):
    f = ImageFont.truetype(LORA, size)
    try: f.set_variation_by_axes([700])
    except Exception: pass
    return f

def fit_size(d, txt, font_fn, maxw, start=230, lang=None):
    sz = start
    while sz > 40 and d.textlength(txt, font=font_fn(sz), **({"language": lang} if lang else {})) > maxw: sz -= 4
    return sz

def venn_layer(r, dist, scale=3):
    """RGBA layer with two overlapping circles (navy / gold) and a darker lens; returns (img, lens_center_xy, left_c, right_c)"""
    from PIL import ImageFilter
    Wd, Hd = int((2 * r + dist) + 40), int(2 * r + 40); S = scale
    cL = (20 + r, 20 + r); cR = (20 + r + dist, 20 + r)
    def circ(c):
        m = Image.new("L", (Wd * S, Hd * S), 0); ImageDraw.Draw(m).ellipse([(c[0] - r) * S, (c[1] - r) * S, (c[0] + r) * S, (c[1] + r) * S], fill=255); return m
    mL, mR = circ(cL), circ(cR)
    lens = Image.fromarray(np.minimum(np.array(mL), np.array(mR)))
    out = Image.new("RGBA", (Wd * S, Hd * S), (0, 0, 0, 0))
    out.paste(Image.new("RGBA", out.size, (20, 34, 84, 244)), (0, 0), mL)
    out.paste(Image.new("RGBA", out.size, (214, 160, 62, 244)), (0, 0), mR)
    out.paste(Image.new("RGBA", out.size, (112, 74, 40, 255)), (0, 0), lens)
    od = ImageDraw.Draw(out)
    for c in (cL, cR): od.ellipse([(c[0] - r) * S, (c[1] - r) * S, (c[0] + r) * S, (c[1] + r) * S], outline=(255, 255, 255, 235), width=5 * S)
    return out.resize((Wd, Hd), Image.LANCZOS), cL, cR

def cover_s5(path):
    from PIL import ImageFilter
    cv = SPEC["cover"]; NAVY = (18, 30, 74); GOLDN = (190, 138, 46); IV0 = (254, 250, 243); IV1 = (243, 232, 212)
    t = (np.arange(H) / H)[:, None, None]
    arr = (np.array(IV0, np.float32) * (1 - t) + np.array(IV1, np.float32) * t) * np.ones((H, W, 3), np.float32)
    im = Image.fromarray(arr.astype(np.uint8), "RGB")
    g = glow_mask(1300); im.paste(Image.new("RGB", g.size, (255, 226, 150)), (900 - 650, 260 - 650), g.point(lambda v: int(v * .55)))
    g2 = glow_mask(1000); im.paste(Image.new("RGB", g2.size, (255, 238, 205)), (300 - 500, 1300 - 500), g2.point(lambda v: int(v * .5)))
    d = ImageDraw.Draw(im)
    for k, rr in enumerate((340, 470, 600)):      # faint arcs behind the venn
        d.ellipse([300 - rr, 1390 - rr, 300 + rr, 1390 + rr], outline=(226, 205, 160), width=2)
    serif = cv.get("serif", True)
    fnt = SER if serif else (lambda sz: ImageFont.truetype(POPB, sz))
    lg = None if serif else "hi"
    kw = {"language": lg} if lg else {}
    # brand tag
    d.text((80, 332), SPEC["brand"], font=ImageFont.truetype(POPB, 42), fill=NAVY, anchor="lm")
    bw = d.textlength(SPEC["brand"], font=ImageFont.truetype(POPB, 42))
    d.ellipse([80 + bw + 20, 326, 80 + bw + 32, 338], fill=GOLDN)
    d.text((80 + bw + 48, 332), cv["tag"], font=ImageFont.truetype(POPB, 30), fill=GOLDN, anchor="lm")
    # headline
    maxw = 920
    s1 = fit_size(d, cv["l1"], fnt, maxw, 230, lg); s2 = fit_size(d, cv["l2"], fnt, maxw, 230, lg)
    sz = min(s1, s2, 176 if serif else 150)
    d.text((80, 520), cv["l1"], font=fnt(sz), fill=NAVY, anchor="lm", **kw)
    d.text((80, 520 + int(sz * 1.12)), cv["l2"], font=fnt(sz), fill=GOLDN, anchor="lm", **kw)
    yb = 520 + int(sz * 1.12) + int(sz * 0.92)
    if not serif: yb += 26
    # divider
    mid = cv["mid"]; mf = SER(50); mw = d.textlength(mid, font=mf)
    cx0 = 80 + 460
    d.line([(80, yb), (cx0 - mw / 2 - 26, yb)], fill=GOLDN, width=3); d.line([(cx0 + mw / 2 + 26, yb), (80 + 920, yb)], fill=GOLDN, width=3)
    d.text((cx0, yb), mid, font=mf, fill=NAVY, anchor="mm")
    # hindi hook
    hf = ImageFont.truetype(POPB, 58); y0 = yb + 100
    for i, (txt, hl) in enumerate(cv["hook"]):
        x = 80
        for part, is_hl in hl:
            d.text((x, y0 + i * 84), part, font=hf, fill=GOLDN if is_hl else NAVY, anchor="lm", language="hi"); x += d.textlength(part, font=hf, language="hi")
    # venn
    vl, cL, cR = venn_layer(150, 120)
    vx, vy = 6, 1290
    shadow = vl.split()[3].filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * .30))
    im.paste(Image.new("RGB", vl.size, (60, 50, 30)), (vx + 6, vy + 14), shadow)
    im.paste(vl.convert("RGB"), (vx, vy), vl.split()[3])
    d = ImageDraw.Draw(im)
    lx = vx + (cL[0] + cR[0]) / 2; ly = vy + cL[1]
    d.text((lx, ly - 8), cv["badge"], font=SER(60), fill=WHITE, anchor="mm")
    d.text((lx, ly + 40), "OVERLAP", font=ImageFont.truetype(POPB, 19), fill=(255, 232, 190), anchor="mm")
    d.text((vx + cL[0] - 30, vy + 4), cv["va"], font=ImageFont.truetype(POPB, 30), fill=NAVY, anchor="mm")
    d.text((vx + cR[0] + 30, vy + 4), cv["vb"], font=ImageFont.truetype(POPB, 30), fill=(150, 104, 30), anchor="mm")
    d.text((80, 1634), cv["src"], font=ImageFont.truetype(POPB, 22), fill=(110, 100, 80), anchor="lm", language="hi")
    # person (no outline, soft shadow, bleeds off the bottom like a magazine cover)
    if cv.get("face") == "card":
        ph_ = face_img().convert("RGB"); cw = 540; ch = int(ph_.height * cw / ph_.width)
        ph_ = ph_.resize((cw, ch), Image.LANCZOS)
        pc = Image.new("RGBA", (cw + 24, ch + 24), (0, 0, 0, 0)); pcd = ImageDraw.Draw(pc)
        pcd.rounded_rectangle([0, 0, cw + 23, ch + 23], 44, fill=(255, 255, 255, 255))
        mk_ = Image.new("L", (cw, ch), 0); ImageDraw.Draw(mk_).rounded_rectangle([0, 0, cw - 1, ch - 1], 34, fill=255)
        pc.paste(ph_, (12, 12), mk_)
        px, py = 498, 1290
    else:
        pc = person_cutout(); fw = 770; fh2 = int(pc.height * fw / pc.width); pc = pc.resize((fw, fh2), Image.LANCZOS)
        a = pc.split()[3].filter(ImageFilter.GaussianBlur(1.1)); pc.putalpha(a)
        px, py = 400, 1134
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); lay.paste(pc, (px, py), pc)
    sh = lay.split()[3].filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * .30))
    im.paste(Image.new("RGB", (W, H), (70, 55, 30)), (-14, 8), sh)
    im.paste(lay.convert("RGB"), (0, 0), lay.split()[3])
    d = ImageDraw.Draw(im)
    d.text((80, 1830), "शैक्षणिक जानकारी · निवेश सलाह नहीं", font=ImageFont.truetype(POPB, 23), fill=NAVY, anchor="lm", language="hi")
    d.text((80, 1866), "We are not SEBI registered", font=ImageFont.truetype(POPB, 22), fill=(110, 100, 80), anchor="lm")
    im.save(path, quality=94)

def cover(path):
    cv = SPEC["cover"]
    if cv.get("style") == "s2": return cover_s2(path)
    if cv.get("style") == "s3": return cover_s3(path)
    if cv.get("style") == "s4": return cover_s4(path)
    if cv.get("style") == "s5": return cover_s5(path)
    im = base_bg().copy(); g = glow_mask(1100)
    im.paste(Image.new("RGB", g.size, GOLD), (540 - 550, 1240 - 550), g.point(lambda v: int(v * 0.30)))
    im.paste(Image.new("RGB", g.size, BLUE), (200 - 550, 420 - 550), g.point(lambda v: int(v * 0.16)))
    d = ImageDraw.Draw(im)
    if cv.get("candles"):
        draw_series(d, 150, 90, 52, 1010, 1500, lambda i: 1.0, a=0.6)
    if cv.get("levels"):
        yr, ys = 1040, 1480
        dashed(d, 100, yr, 980, RED, .75, width=4); dashed(d, 100, ys, 980, GREEN, .75, width=4)
        text(d, 100, yr - 30, "RESISTANCE", 28, RED, anchor="lm", a=.9); text(d, 100, ys + 32, "SUPPORT", 28, GREEN, anchor="lm", a=.9)
        pr = [64, 69.6, 60.4, 69.8, 60.3, 69.5, 60.6, 66]
        pts = [(120 + int(i * 115), int(ys - (p - 60) / 10 * (ys - yr))) for i, p in enumerate(pr)]
        for i in range(len(pts) - 1): d.line([pts[i], pts[i + 1]], fill=C(WHITE, .55), width=7)
    rrect(d, [200, 290, 880, 360], 35, CARD, GOLD, 3)
    text(d, 540, 325, cv["pill"], 34, GOLD)
    text(d, 540, 520, cv["l1"], cv.get("s1", 178), WHITE)
    text(d, 540, 735, cv["l2"], cv.get("s2", 210), GOLD)
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
