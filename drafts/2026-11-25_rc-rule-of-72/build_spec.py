import json, wave, os
HERE = os.path.dirname(os.path.abspath(__file__))
TEMPO, LEAD, PAD = 1.14, 0.12, 0.15

def vdur(i):
    w = wave.open(os.path.join(HERE, "voice", f"s{i}.wav")); return w.getnframes() / w.getframerate() / TEMPO

def starts(i, subs, tail=0.0, early=0.0):
    vd = vdur(i); dur = LEAD + vd + PAD + tail
    wts = [len(x.replace("*", "")) for x in subs]; tot = float(sum(wts)); out = []; c = 0
    for w in wts:
        out.append(max(0.0, LEAD + vd * (c / tot) - early)); c += w
    return out, dur

def rev(i, subs, idxs, tail=0.0, early=0.12):
    st, dur = starts(i, subs, tail, early)
    return [round(st[k] / dur, 4) for k in idxs]

S = []
# 1 hook
subs = ["कोई बोले, पैसा *3 साल* में *double*?", "*Stop!* *72* का यह एक *test* कर लीजिए।", "दस सेकंड में *सच* सामने आ जाएगा।", "यह है, *Rule of 72*।"]
st, _ = starts(1, subs, early=0.1)
S.append(dict(type="isohook", line1="Double in 3 years?", line2="Do the 72 test.", size1=64, size2=88,
              chips=["72 ÷ 3 = 24%", "Every year"], chip_t=[round(st[1] + 0.2, 2), round(st[2] + 0.2, 2)],
              note="चित्र सिर्फ़ उदाहरण के लिए · काल्पनिक", rev=rev(1, subs, [0, 1]), subs=subs))
# 2 the rule
subs = ["Rule बहुत *simple* है।", "*72* को अपने *return rate* से *divide* कीजिए,", "और जवाब मिलेगा, पैसा करीब कितने साल में *double* होगा।", "*6%* पर, *12 साल*।", "*8%* पर, *9 साल*।", "और *12%* पर, *6 साल*।", "यह सिर्फ़ *math* का example है, *वादा नहीं*।"]
st, dur = starts(2, subs, early=0.1); t1 = st[3]
S.append(dict(type="isobars", title="72 ÷ return = double होने के साल", sub="अनुमानित · सिर्फ़ गणित का उदाहरण, कोई return नहीं", step=108, hl=[2], fmt="{:.0f} साल",
              offs=[0.0, round(st[4] - t1, 2), round(st[5] - t1, 2)],
              rows=[["6% सालाना", 12], ["8% सालाना", 9], ["12% सालाना", 6]],
              gap="Return 2x = समय आधा", gap_sub="उदाहरण के लिए · expected return नहीं",
              note="Rule of 72 एक अनुमान है · 6-10% के आसपास सबसे सटीक",
              rev=[0.03, round(t1 / dur, 4), round(st[6] / dur, 4)], subs=subs))
# 3 red flag
subs = ["अब उस *वादे* पर आइए।", "*3 साल* में double? *72 ÷ 3* = करीब *24%* हर साल,", "बिना एक भी बुरे साल के। असली गणित में करीब *26%*।", "*SEBI* साफ़ कहता है, securities market में *assured returns* की कोई guarantee नहीं हो सकती।", "तो *guarantee* वाला वादा, सबसे बड़ा *red flag* है।", "किसी की *registration*, SEBI की website पर *check* कीजिए।"]
S.append(dict(type="lesson", rows=[dict(t="72 ÷ 3 = 24% हर साल", s="EXACT MATH ~26% · NO BAD YEARS"), dict(t="Guarantee = Red flag", s="SEBI: NO ASSURED RETURNS"),
              dict(t="Registration check करें", s="VERIFY ON SEBI WEBSITE")], rev=rev(3, subs, [1, 3, 5]), subs=subs))
# 4 inflation halves
subs = ["अब rule का *उल्टा चेहरा*।", "*महँगाई* भी compound होती है।", "सरकारी data के मुताबिक़ इस अक्टूबर में *retail inflation*, *6.09%* रही।", "*72 ÷ 6.09*, यानी करीब *12 साल*।", "अगर महँगाई यही रहे, तो आज के *₹100* की खरीदने की ताक़त, *12 साल* में करीब *आधी* रह जाएगी।"]
st, dur = starts(4, subs, early=0.1); t1 = st[2]
S.append(dict(type="isobars", title="₹100 की खरीदने की ताक़त", sub="अगर महँगाई 6.09% बनी रहे · काल्पनिक", step=130, hl=[1], fmt="₹{:.0f}",
              offs=[0.0, round(st[4] - t1, 2)],
              rows=[["आज", 100], ["~12 साल बाद", 50]],
              gap="~आधी", gap_sub="72 ÷ 6.09 ≈ 12 साल · काल्पनिक",
              note="स्रोत: MoSPI CPI, अक्टू. 2026 (प्रोविज़नल) · हमारी गणना",
              rev=[0.03, round(t1 / dur, 4), round((st[4] + 1.0) / dur, 4)], subs=subs))
# 5 FD vs inflation
subs = ["अब *FD* देखिए।", "*Business Today* के मुताबिक़ अगस्त में *SBI* की *1 साल* की FD, *6.25%* थी।", "*72 ÷ 6.25*, यानी करीब *साढ़े 11 साल* में पैसा double।", "लेकिन *महँगाई* *6.09%* है।", "फ़र्क़ सिर्फ़ *0.16%*, और वह भी *tax से पहले*।", "अगर ये दरें बनी रहें, तो *नंबर* double होता है, पर *खरीदने की ताक़त* लगभग वहीं रहती है।"]
st, dur = starts(5, subs, early=0.1); t1 = st[1] + 0.5 * (st[2] - st[1])
S.append(dict(type="isobars", title="FD बनाम महँगाई · % सालाना", sub="SBI 1 साल FD (अग. 2026) · CPI (अक्टू. 2026)", step=130, hl=[1], fmt="{:.2f}%",
              offs=[0.0, round(st[3] - t1, 2)],
              rows=[["SBI 1 साल FD", 6.25], ["CPI महँगाई", 6.09]],
              gap="सिर्फ़ 0.16 pt", gap_sub="tax से पहले · असली बढ़त लगभग शून्य",
              note="स्रोत: Business Today (अग. 2026) · MoSPI · हमारी गणना, कोई सिफ़ारिश नहीं",
              rev=[0.03, round(t1 / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 6 poll
subs = ["आज का *poll*।", "कोई *3 साल* में double का वादा करे, तो आप क्या करेंगे?", "*A*: भरोसा करूँगा।", "*B*: पहले SEBI पर check करूँगा।", "*C*: Ignore करूँगा।", "*Comment* में लिखिए।"]
st, dur = starts(6, subs, early=0.1)
S.append(dict(type="poll", head="आज का Poll", q="3 साल में double का वादा?", opts=[["A", "भरोसा करूँगा"], ["B", "पहले SEBI पर check"], ["C", "Ignore करूँगा"]],
              ask="Comment में A, B या C लिखिए", note="सिर्फ़ जानने के लिए · कोई सलाह नहीं",
              rev=[0.0, round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[5] / dur, 4)], opt_rev=[round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 7 outro
subs = ["काम का लगा तो *Save* कीजिए।", "यह video उस दोस्त को *Send* कीजिए, जिसे कोई *double money* का वादा करता रहता है।", "*Follow* कीजिए *TheSDTrader*।",
        "हम *SEBI registered नहीं* हैं। यह जानकारी सिर्फ़ *educational* है, *investment advice नहीं*।"]
S.append(dict(type="outro", tag="Reality Check · Hindi + English", cta=["SAVE", "SEND", "FOLLOW"], notice_hi="हम SEBI registered नहीं हैं।",
              notice_en="Educational purposes only · Not investment advice", tail=0.8, rev=[0.04, rev(7, subs, [3], tail=0.8)[0]], subs=subs))

spec = dict(brand="TheSDTrader", tagline="Educational · शैक्षणिक जानकारी · Not advice", face="assets/face_original.png",
            voice_tempo=TEMPO, lead=LEAD, pad=PAD, music_vol=0.2, sfx_vol=0.4, voice_vol=1.5, day_tag="REALITY CHECK · DAY 7",
            theme=dict(BG=[254, 250, 243], bg_delta=[-10, -18, -31], WHITE=[18, 30, 74], MUTED=[112, 102, 84], GOLD=[190, 138, 46], CARD=[255, 255, 255],
                       CARD2=[232, 218, 188], DARK=[18, 30, 74], BLUE=[255, 236, 200], ORANGE=[217, 89, 38], GREEN=[13, 159, 110], RED=[214, 60, 60],
                       PW=[255, 255, 255], SUB_HL=[255, 214, 120], BRANDC=[18, 30, 74], SLAB=[226, 214, 194],
                       SER3=[[42, 120, 214], [217, 89, 38], [13, 159, 110]]),
            cover=dict(style="s5", serif=True, face="card", tag="REALITY CHECK · EP 7", l1="2x in 3 Yrs?", l2="Check 72.", mid="THE RULE OF 72", graphic="steps",
                       gtitle="YEARS TO DOUBLE", gvals=[12, 6], glabs=["AT 6%", "AT 12%"], gfmt="{:.0f} YRS", gfoot="ILLUSTRATIVE · NOT ADVICE",
                       badge="", va="", vb="", src="Own calculation",
                       hook=[["", [["कोई बोले ", False], ["3 साल", True], [" में double?", False]]], ["", [["पहले ", False], ["72", True], [" से check करें।", False]]]]),
            scenes=S)
json.dump(spec, open(os.path.join(HERE, "spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", sum(vdur(i) + LEAD + PAD for i in range(1, 8)) + 0.8)
