import sys, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
BOLD = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
REG = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
_fc = {}
def F(size, bold=True):
    k = (size, bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(BOLD if bold else REG, size, layout_engine=ImageFont.Layout.RAQM)
    return _fc[k]

BG = (10, 15, 31)
WHITE = (245, 247, 250); MUTED = (148, 163, 184)
GREEN = (34, 197, 94); RED = (239, 68, 68); GOLD = (251, 191, 36); CARD = (22, 31, 58)

# background gradient
base = Image.new("RGB", (W, H), BG)
bd = ImageDraw.Draw(base)
for y in range(H):
    t = y / H
    bd.line([(0, y), (W, y)], fill=(int(10 + 8 * t), int(15 + 14 * t), int(31 + 30 * t)))

ALPHA = 1.0
def C(rgb, a=1.0):
    k = max(0.0, min(1.0, ALPHA * a))
    return tuple(int(BG[i] + (rgb[i] - BG[i]) * k) for i in range(3))

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def prog(t, t0, dur): return clamp((t - t0) / dur)

def wrap(text, font, maxw):
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.getlength(test, language="hi") <= maxw or not cur:
            cur = test
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def text(d, x, y, s, size, color, bold=True, anchor="mm", a=1.0, maxw=None, lh=1.3):
    f = F(size, bold)
    lines = wrap(s, f, maxw) if maxw else [s]
    total = (len(lines) - 1) * size * lh
    y0 = y - total / 2 if anchor[1] == "m" else y
    for i, ln in enumerate(lines):
        d.text((x, y0 + i * size * lh), ln, font=f, fill=C(color, a), anchor=anchor, language="hi")
    return len(lines)

def rrect(d, box, r, fill=None, outline=None, width=0, a=1.0):
    d.rounded_rectangle(box, r, fill=C(fill, a) if fill else None,
                        outline=C(outline, a) if outline else None, width=width)

def tri(d, cx, cy, s, color, up=True, a=1.0):
    pts = [(cx, cy - s), (cx - s, cy + s), (cx + s, cy + s)] if up else [(cx, cy + s), (cx - s, cy - s), (cx + s, cy - s)]
    d.polygon(pts, fill=C(color, a))

D = "/tmp/claude-tool-results/1dd25017-7e22-5f07-99f7-d910bfa027c0/"
NARR = [D + n for n in [
 "mcp-Speko-blob-1795338496514-7rpc26-0c030422.wav", "mcp-Speko-blob-1795338498911-4bbjt8-f1cd4e14.wav",
 "mcp-Speko-blob-1795338501247-ox3e5b-1bea5f42.wav", "mcp-Speko-blob-1795338503451-7jtntm-8f3194a9.wav",
 "mcp-Speko-blob-1795338505169-pqhhlt-364c9cdc.wav", "mcp-Speko-blob-1795338507300-yh2pme-bda18ebe.wav",
 "mcp-Speko-blob-1795338509458-fz7vrq-0754c815.wav"]]
def _dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).decode().strip())
LEAD, PAD = 0.4, 0.9
NDUR = [_dur(p) for p in NARR]
SEG, _t = [], 0.0
for _d in NDUR:
    SEG.append((_t, _t + _d + PAD)); _t += _d + PAD
TOTAL = _t

def chrome(d, src=None):
    d.rectangle([60, 96, 72, 150], fill=C(GOLD))
    text(d, 92, 112, "TheSDTrader", 44, GOLD, anchor="lm")
    text(d, 92, 158, "शैक्षणिक जानकारी · निवेश सलाह नहीं", 28, MUTED, bold=False, anchor="lm")
    if src:
        text(d, 540, 1575, src, 30, MUTED, bold=False, maxw=900)

def s0(d, t):
    chrome(d, "स्रोत: Kotak Neo (क्लोजिंग बेल, 19 नवंबर 2026)")
    text(d, 540, 330, "19 नवंबर 2026 · बंद भाव", 50, MUTED, a=eo(prog(t, 0.1, 0.5)))
    y = 560 + (1 - eo(prog(t, 0.1, 0.6))) * 50
    text(d, 540, y, "सेंसेक्स", 180, WHITE, a=eo(prog(t, 0.1, 0.6)))
    v = 80000 + (83021.75 - 80000) * eo(prog(t, 0.5, 2.4))
    text(d, 540, 830, f"{v:,.2f}", 170, GREEN, a=eo(prog(t, 0.4, 0.5)))
    a = eo(prog(t, 2.6, 0.6))
    rrect(d, (300, 980, 780, 1090), 40, fill=GREEN, a=a)
    tri(d, 372, 1035, 24, WHITE, True, a)
    text(d, 560, 1035, "1.21%", 76, WHITE, a=a)
    text(d, 540, 1200, "करीब 1,000 अंक की छलांग", 58, WHITE, a=eo(prog(t, 3.0, 0.6)))
    text(d, 540, 1420, "5 बड़े डेटा पॉइंट्स · 1 मिनट से कम में", 56, GOLD, a=eo(prog(t, 3.2, 0.6)), maxw=860)

PTS = [("6 नव", 81028.02), ("13 नव", 81592.45), ("17 नव", 82532.19), ("18 नव", 82031.81), ("19 नव", 83021.75)]
def s1(d, t):
    chrome(d, "स्रोत: Kotak Neo, Navia Weekly Roundup (चुनिंदा बंद भाव)")
    text(d, 540, 290, "13 दिन में सेंसेक्स", 82, WHITE, a=eo(prog(t, 0, 0.5)))
    text(d, 540, 385, "6 नवंबर से 19 नवंबर तक", 42, MUTED, a=eo(prog(t, 0.2, 0.5)))
    x0, x1, yt, yb = 130, 950, 600, 1150
    vmin, vmax = 80700, 83500
    xy = [(x0 + i * (x1 - x0) / 4, yb - (v - vmin) / (vmax - vmin) * (yb - yt)) for i, (_, v) in enumerate(PTS)]
    for g in range(4):
        gy = yt + g * (yb - yt) / 3
        d.line([(x0 - 20, gy), (x1 + 20, gy)], fill=C(CARD), width=2)
    f = eo(prog(t, 0.6, 5.0)) * 4.0
    path = []
    for i in range(4):
        seg = clamp(f - i)
        if seg <= 0: break
        (ax, ay), (bx, by) = xy[i], xy[i + 1]
        if not path: path.append((ax, ay))
        path.append((ax + (bx - ax) * seg, ay + (by - ay) * seg))
    if len(path) >= 2:
        poly = path + [(path[-1][0], yb), (path[0][0], yb)]
        d.polygon(poly, fill=C((14, 60, 42)))
        d.line(path, fill=C(GREEN), width=12, joint="curve")
    for i, (lab, v) in enumerate(PTS):
        text(d, xy[i][0], yb + 60, lab, 36, MUTED)
        if f >= i - 0.001 and f > 0 or i == 0 and f > 0:
            d.ellipse([xy[i][0] - 16, xy[i][1] - 16, xy[i][0] + 16, xy[i][1] + 16], fill=C(WHITE))
            text(d, xy[i][0], xy[i][1] - 52, f"{v:,.0f}", 36, WHITE)
    a = eo(prog(t, 6.0, 0.6))
    text(d, 540, 1340, "+1,994 अंक", 130, GREEN, a=a)
    text(d, 540, 1470, "(+2.46%) · सिर्फ 13 दिन में", 54, WHITE, a=a)

def s2(d, t):
    chrome(d, "स्रोत: Multibagg Market Pulse (2–6 नवंबर 2026)")
    text(d, 540, 320, "2–6 नवंबर का हफ्ता", 64, MUTED, a=eo(prog(t, 0, 0.5)))
    v = 8.58 * eo(prog(t, 0.3, 2.0))
    text(d, 540, 640, f"+{v:.2f}%", 260, GOLD, a=eo(prog(t, 0.3, 0.4)))
    text(d, 540, 880, "निफ्टी 50 का साप्ताहिक उछाल", 62, WHITE, a=eo(prog(t, 2.0, 0.6)), maxw=880)
    text(d, 540, 1030, "फरवरी 2021 के बाद सबसे मज़बूत हफ्ता", 56, GREEN, a=eo(prog(t, 2.8, 0.6)), maxw=880)
    for i, (txt, col) in enumerate([("लगातार 7 सत्र की तेज़ी", GOLD), ("सेंसेक्स भी +8.82%", GREEN)]):
        a = eo(prog(t, 4.0 + i * 0.6, 0.6))
        y = 1230 + i * 150
        rrect(d, (130, y - 55, 950, y + 55), 30, fill=CARD, outline=col, width=4, a=a)
        text(d, 540, y, txt, 56, WHITE, a=a)

def s3(d, t):
    chrome(d, "स्रोत: HDFC Sky, The Hans India (14 नवंबर तक, अनंतिम आँकड़े)")
    text(d, 540, 290, "FII की वापसी", 96, WHITE, a=eo(prog(t, 0, 0.5)))
    v = 79302 * eo(prog(t, 0.4, 1.8))
    text(d, 540, 470, f"₹{v:,.0f} करोड़", 120, GREEN, a=eo(prog(t, 0.4, 0.4)))
    text(d, 540, 610, "नवंबर में अब तक FII की शुद्ध खरीद", 46, MUTED, a=eo(prog(t, 2.0, 0.5)), maxw=860)
    bw, gap, x0 = 60, 12, 78
    for i in range(13):
        a = eo(prog(t, 2.6 + i * 0.22, 0.3))
        col = RED if i < 10 else GREEN
        h = 170 * a
        x = x0 + i * (bw + gap)
        rrect(d, (x, 960 - h / 2 - 0, x + bw, 960 + h / 2), 10, fill=col, a=1.0 if a > 0.05 else 0)
    a1 = eo(prog(t, 5.6, 0.5)); a2 = eo(prog(t, 6.2, 0.5))
    rrect(d, (130, 1160, 170, 1200), 8, fill=RED, a=a1); text(d, 200, 1180, "10 हफ्ते FII बिकवाली", 50, WHITE, anchor="lm", a=a1)
    rrect(d, (130, 1260, 170, 1300), 8, fill=GREEN, a=a2); text(d, 200, 1280, "फिर 3 हफ्ते लगातार खरीदारी", 50, WHITE, anchor="lm", a=a2)

def s4(d, t):
    chrome(d, "स्रोत: Kotak Neo (क्लोजिंग बेल, 19 नवंबर 2026)")
    text(d, 540, 290, "19 नवंबर: सेक्टर स्कोरकार्ड", 72, WHITE, a=eo(prog(t, 0, 0.5)), maxw=880)
    rows = [("निफ्टी PSU बैंक", 2.29, GREEN), ("निफ्टी FMCG", 2.09, GREEN), ("निफ्टी IT", -1.10, RED)]
    for i, (name, val, col) in enumerate(rows):
        y = 640 + i * 250
        a = eo(prog(t, 0.6 + i * 0.7, 0.5))
        text(d, 100, y, name, 54, WHITE, anchor="lm", a=a)
        w = 640 * abs(val) / 2.4 * eo(prog(t, 0.9 + i * 0.7, 1.2))
        rrect(d, (100, y + 50, 100 + max(w, 8), y + 120), 18, fill=col, a=a)
        s = f"{val:+.2f}%".replace("-", "−")
        text(d, 100 + w + 20, y + 85, s, 56, col, anchor="lm", a=a)
    text(d, 540, 1440, "FMCG और PSU बैंक में खरीदारी, IT में बिकवाली", 52, GOLD, a=eo(prog(t, 3.8, 0.6)), maxw=860)

def s5(d, t):
    chrome(d, "स्रोत: HDFC Sky (अक्टूबर 2026 की खुदरा महंगाई)")
    a = eo(prog(t, 0, 0.5))
    tri(d, 540, 340, 62, GOLD, True, a)
    text(d, 540, 365, "!", 80, BG, a=a)
    text(d, 540, 520, "ध्यान दें", 96, GOLD, a=a)
    text(d, 540, 640, "अक्टूबर की खुदरा महंगाई", 52, MUTED, a=eo(prog(t, 0.5, 0.5)))
    v = 6.09 * eo(prog(t, 0.8, 1.5))
    text(d, 540, 880, f"{v:.2f}%", 270, RED, a=eo(prog(t, 0.8, 0.4)))
    text(d, 540, 1120, "RBI की 6% की ऊपरी सीमा के पार", 58, WHITE, a=eo(prog(t, 2.4, 0.6)), maxw=860)
    text(d, 540, 1290, "RBI की अगली नीति पर नज़र रखें", 52, GOLD, a=eo(prog(t, 3.4, 0.6)), maxw=860)

def s6(d, t):
    chrome(d)
    text(d, 540, 290, "आज की सीख", 92, WHITE, a=eo(prog(t, 0, 0.5)))
    items = ["तेज़ी में भी जोखिम पहले तय करें", "FII/DII के आँकड़ों पर नज़र रखें", "सेक्टर का ट्रेंड समझें"]
    for i, s in enumerate(items):
        a = eo(prog(t, 0.5 + i * 0.5, 0.5))
        y = 480 + i * 180
        rrect(d, (90, y - 70, 990, y + 70), 28, fill=CARD, outline=GREEN, width=3, a=a)
        text(d, 150, y, str(i + 1), 64, GREEN, anchor="lm", a=a)
        text(d, 560, y, s, 48, WHITE, a=a, maxw=700)
    a = eo(prog(t, 2.6, 0.5))
    rrect(d, (80, 1010, 1000, 1290), 28, fill=CARD, outline=GOLD, width=4, a=a)
    text(d, 540, 1085, "ज़रूरी सूचना", 46, GOLD, a=a)
    text(d, 540, 1190, "हम SEBI रजिस्टर्ड नहीं हैं। यह वीडियो केवल शैक्षणिक उद्देश्य के लिए है, निवेश सलाह नहीं।", 42, WHITE, bold=False, a=a, maxw=820)
    text(d, 540, 1410, "रोज़ भारतीय बाज़ार का डेटा पाने के लिए TheSDTrader को फॉलो करें", 54, GREEN, a=eo(prog(t, 3.6, 0.6)), maxw=860)

SCENES = [s0, s1, s2, s3, s4, s5, s6]

def render(t):
    global ALPHA
    img = base.copy(); d = ImageDraw.Draw(img)
    for i, (a, b) in enumerate(SEG):
        if a <= t < b or (i == len(SEG) - 1 and t >= a):
            lt = t - a
            fin = clamp(lt / 0.25)
            fout = clamp((b - t) / 0.25) if i < len(SEG) - 1 else 1.0
            ALPHA = min(fin, fout)
            SCENES[i](d, lt)
            break
    ALPHA = 1.0
    d.rectangle([0, 0, W * t / TOTAL, 8], fill=GOLD)
    return img

def make_audio(path):
    sr = 44100; n = int(sr * TOTAL); t = np.arange(n) / sr
    out = np.zeros(n)
    beat = 0.5
    for k in range(int(TOTAL / beat)):
        s = int(k * beat * sr); L = int(0.25 * sr)
        tt = np.arange(L) / sr
        kick = np.sin(2 * np.pi * (110 * np.exp(-tt * 18) + 45) * tt) * np.exp(-tt * 14)
        out[s:s + L] += kick[:max(0, min(L, n - s))] * 0.55
        hs = s + int(0.25 * sr)
        if hs + int(0.06 * sr) < n:
            hl = int(0.05 * sr)
            out[hs:hs + hl] += np.random.RandomState(k).randn(hl) * np.exp(-np.arange(hl) / sr * 90) * 0.12
    for fq, g in [(110.0, .09), (130.81, .07), (164.81, .07), (220.0, .05)]:
        out += np.sin(2 * np.pi * fq * t) * g * (0.75 + 0.25 * np.sin(2 * np.pi * 0.25 * t))
    out *= np.minimum(1, t / 0.5) * np.minimum(1, (TOTAL - t) / 2.0)
    out = out / (np.abs(out).max() + 1e-9) * 0.5
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())


def make_audio_in(path):
    sr = 44100; n = int(sr * TOTAL); t = np.arange(n) / sr
    out = np.zeros(n); rs = np.random.RandomState(7)
    bpm = 104; step = 60.0 / bpm / 2  # eighth notes
    def add(sig, s):
        e = min(n, s + len(sig))
        if e > s: out[s:e] += sig[:e - s]
    # dhol-style rhythm: low thump on 1 and 5, high "tin" on off-beats, shaker on every step
    for k in range(int(TOTAL / step)):
        s = int(k * step * sr); pos = k % 8
        if pos in (0, 4, 6):
            L = int(0.28 * sr); tt = np.arange(L) / sr
            add(np.sin(2 * np.pi * (95 * np.exp(-tt * 20) + 52) * tt) * np.exp(-tt * 11) * 0.8, s)
        if pos in (2, 3, 5, 7):
            L = int(0.12 * sr); tt = np.arange(L) / sr
            tone = np.sin(2 * np.pi * 420 * tt) * 0.5 + rs.randn(L) * 0.5
            add(tone * np.exp(-tt * 38) * 0.28, s)
        L = int(0.04 * sr)
        add(rs.randn(L) * np.exp(-np.arange(L) / sr * 120) * (0.10 if pos % 2 else 0.06), s)
    # sitar-like plucks (Karplus-Strong) on a Bhairav-style scale
    def midi(m): return 440.0 * 2 ** ((m - 69) / 12)
    def pluck(freq, dur=0.6):
        N = int(sr * dur); d = int(sr / freq); buf = rs.uniform(-1, 1, d); y = np.zeros(N)
        for i in range(N):
            y[i] = buf[i % d]
            buf[i % d] = 0.5 * (buf[i % d] + buf[(i + 1) % d]) * 0.997
        return y * np.exp(-np.arange(N) / sr * 3.0)
    phrase = [74, 75, 78, 75, 74, 73, 74, None, 78, 79, 81, 79, 78, 75, 74, None]
    cache = {}
    for k in range(int(TOTAL / step)):
        m = phrase[k % 16]
        if m is None or k < 8: continue
        if m not in cache: cache[m] = pluck(midi(m))
        add(cache[m] * 0.35, int(k * step * sr))
    # tanpura-like drone
    for fq, g in [(73.42, .10), (110.0, .08), (146.83, .05)]:
        out += (np.sin(2 * np.pi * fq * t) + 0.4 * np.sin(2 * np.pi * 2 * fq * t)) * g * (0.8 + 0.2 * np.sin(2 * np.pi * 0.3 * t))
    out *= np.minimum(1, t / 0.4) * np.minimum(1, (TOTAL - t) / 2.0)
    out = out / (np.abs(out).max() + 1e-9) * 0.6
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((out * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        times = [1.5, 3.5, 8.5, 11.5, 17.0, 23.0, 26.5, 32.0, 40.0, 49.0]
        tiles = [render(t).resize((360, 640)) for t in times]
        sheet = Image.new("RGB", (360 * 5, 640 * 2))
        for i, im in enumerate(tiles): sheet.paste(im, ((i % 5) * 360, (i // 5) * 640))
        sheet.save("/home/claude/out/preview.png")
    else:
        make_audio_in("/home/claude/out/music.wav")
        ins = ["-i", "/home/claude/out/music.wav"]
        for pth in NARR: ins += ["-i", pth]
        fc = "[0:a]volume=0.22[m];"
        for i, (a, b) in enumerate(SEG):
            ms = int((a + LEAD) * 1000)
            fc += f"[{i+1}:a]aresample=44100,adelay={ms}|{ms},volume=1.6[c{i}];"
        fc += "[m]" + "".join(f"[c{i}]" for i in range(len(SEG))) + f"amix=inputs={len(SEG)+1}:normalize=0:duration=first,alimiter=limit=0.95[out]"
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error"] + ins + ["-filter_complex", fc, "-map", "[out]", "-ac", "1", "/home/claude/out/mix.wav"])
        out = sys.argv[2]
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-i", "/home/claude/out/mix.wav", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
                              "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for fr in range(int(TOTAL * FPS)):
            p.stdin.write(render(fr / FPS).tobytes())
        p.stdin.close(); p.wait()
