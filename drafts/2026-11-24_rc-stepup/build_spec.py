import json, wave, os
HERE = os.path.dirname(os.path.abspath(__file__))
TEMPO, LEAD, PAD = 1.08, 0.12, 0.15

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
subs = ["सैलरी *हर साल* बढ़ती है।", "तो आपकी *SIP* हर साल वही की वही क्यों?", "चलिए, *₹5,000* की SIP पर *गणित* देखते हैं।"]
st, _ = starts(1, subs, early=0.1)
S.append(dict(type="isohook", line1="सैलरी हर साल बढ़ती है,", line2="SIP क्यों नहीं?", size1=58, size2=92,
              chips=["सैलरी बढ़ी", "SIP वही?"], chip_t=[round(st[0] + 0.4, 2), round(st[1], 2)],
              note="चित्र सिर्फ़ उदाहरण के लिए · काल्पनिक", rev=rev(1, subs, [0, 1]), subs=subs))
# 2 salary hikes (Aon / Deloitte surveys)
subs = ["आपकी सैलरी हर साल कितनी बढ़ती है?", "*एऑन* के सर्वे में, *2026* में भारत में औसत बढ़ोतरी करीब *9%* रही, और *2027* के लिए अनुमान *9.1%* है।",
        "*डेलॉइट* का 2026 का अनुमान भी *9.1%* था।", "यह *औसत* है, आपकी अपनी बढ़ोतरी *अलग* हो सकती है।"]
st, dur = starts(2, subs, early=0.1)
S.append(dict(type="isocmp", badge=9, badge_cap="औसत सालाना बढ़ोतरी · Aon, 2026", col_name="सैलरी = 100%",
              seg1="बढ़ोतरी", seg2="पुरानी सैलरी", chips_head="सर्वे के आँकड़े (औसत)",
              chips=[["Aon 2026", "लगभग 9% (असल)"], ["Aon 2027", "9.1% (अनुमान)"], ["Deloitte 2026", "9.1% (अनुमान)"]],
              note="स्रोत: Aon · Deloitte India · औसत, आपकी अपनी अलग हो सकती है",
              rev=[0.0, round(st[1] / dur, 4), round((st[1] + (st[2] - st[1]) * 0.45) / dur, 4), round((st[1] + (st[2] - st[1]) * 0.55) / dur, 4)], subs=subs))
# 3 corpus (own calculation, illustrative)
subs = ["अब *गणित*।", "*₹5,000* की फ़िक्स्ड SIP, *20 साल*, और *12%* रिटर्न मानें,", "तो अंत में करीब *₹49.5 लाख*।", "हर साल *5%* बढ़ाएँ, तो करीब *₹68 लाख*।",
        "और हर साल *10%* बढ़ाएँ, तो करीब *₹98.5 लाख*, यानी करीब *दोगुना*।", "पर ध्यान दीजिए, *कुल निवेश* भी ₹12 लाख से बढ़कर करीब *₹34 लाख* हो जाता है।",
        "यह सिर्फ़ एक *काल्पनिक उदाहरण* है, गारंटी नहीं।"]
st, dur = starts(3, subs, early=0.1); t1 = st[1] + 0.6 * (st[2] - st[1])
S.append(dict(type="isobars", title="₹5,000/माह SIP · 20 साल · 12% मान्यता", sub="काल्पनिक उदाहरण · L = लाख रुपये", step=100, hl=[1, 2], fmt="₹{:.1f}L",
              offs=[0.0, round(st[3] - t1, 2), round(st[4] - t1, 2)],
              rows=[["फ़िक्स्ड SIP", 49.5], ["हर साल +5%", 68.0], ["हर साल +10%", 98.5]],
              gap="करीब दोगुना", gap_sub="पर कुल निवेश भी ₹12 लाख से ₹34 लाख · गारंटी नहीं",
              note="गणना: माह-अंत SIP, मासिक चक्रवृद्धि · हमारी गणना, अनुमान",
              rev=[0.03, round(t1 / dur, 4), round(st[5] / dur, 4)], subs=subs))
# 4 monthly amounts at 10% step-up
subs = ["इसकी *क़ीमत* क्या है?", "*10%* सालाना स्टेप-अप पर आपकी मासिक SIP, *5वें साल* में करीब *₹7,300*,", "*10वें साल* में करीब *₹11,800*, और *20वें साल* में करीब *₹30,600* हो जाएगी।",
        "इसलिए स्टेप-अप का *प्रतिशत*, अपनी *आय और बजट* के हिसाब से ही तय होता है।", "ज़्यादातर *फंड हाउस और ऐप्स* में स्टेप-अप की सुविधा मिलती है।"]
st, dur = starts(4, subs, early=0.1); d1 = st[2] - st[1]; d2 = st[3] - st[2]
S.append(dict(type="isobars", title="10% सालाना स्टेप-अप · मासिक SIP की राशि", sub="शुरुआत ₹5,000 · काल्पनिक उदाहरण", step=100, hl=None, fmt="₹{:,.0f}",
              offs=[0.0, round(d1 * 0.6, 2), round(d1 + d2 * 0.15, 2), round(d1 + d2 * 0.62, 2)],
              rows=[["साल 1", 5000], ["साल 5", 7321], ["साल 10", 11790], ["साल 20", 30580]],
              gap="₹5,000 से ₹30,580", gap_sub="20वें साल की मासिक SIP · अपनी आय के हिसाब से तय करें",
              note="गणना: हमारी, हर साल 10% की बढ़ोतरी मानकर · सलाह नहीं",
              rev=[0.03, round(st[1] / dur, 4), round(st[3] / dur, 4)], subs=subs))
# 5 poll
subs = ["आज का *पोल*।", "आपकी SIP हर साल *बढ़ती* है, या *फ़िक्स्ड* है?", "*A*: हर साल बढ़ती है।", "*B*: फ़िक्स्ड है।", "*C*: अभी SIP नहीं है।", "*कमेंट* में लिखिए।"]
st, dur = starts(5, subs, early=0.1)
S.append(dict(type="poll", head="आज का पोल", q="आपकी SIP बढ़ती है या फ़िक्स्ड?", opts=[["A", "हर साल बढ़ती है"], ["B", "फ़िक्स्ड है"], ["C", "अभी SIP नहीं है"]],
              ask="कमेंट में A, B या C लिखिए", note="सिर्फ़ जानने के लिए · कोई सलाह नहीं",
              rev=[0.0, round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[5] / dur, 4)], opt_rev=[round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 6 outro
subs = ["काम का लगा तो *Save* कीजिए।", "ये वीडियो किसी ऐसे दोस्त को *Send* कीजिए, जिसकी *SIP फ़िक्स्ड* है।", "Follow कीजिए *TheSDTrader*।",
        "हम *SEBI रजिस्टर्ड नहीं* हैं। यह जानकारी सिर्फ़ *शैक्षणिक* है, निवेश सलाह नहीं।"]
S.append(dict(type="outro", tag="Reality Check · हिंदी में", cta=["SAVE", "SEND", "FOLLOW"], notice_hi="हम SEBI रजिस्टर्ड नहीं हैं।",
              notice_en="Educational purposes only · Not investment advice", tail=0.8, rev=[0.04, rev(6, subs, [3], tail=0.8)[0]], subs=subs))

spec = dict(brand="TheSDTrader", tagline="शैक्षणिक जानकारी · निवेश सलाह नहीं", face="assets/face_original.png",
            voice_tempo=TEMPO, lead=LEAD, pad=PAD, music_vol=0.2, sfx_vol=0.4, voice_vol=1.5, day_tag="REALITY CHECK · DAY 4",
            theme=dict(BG=[254, 250, 243], bg_delta=[-10, -18, -31], WHITE=[18, 30, 74], MUTED=[112, 102, 84], GOLD=[190, 138, 46], CARD=[255, 255, 255],
                       CARD2=[232, 218, 188], DARK=[18, 30, 74], BLUE=[255, 236, 200], ORANGE=[217, 89, 38], GREEN=[13, 159, 110], RED=[214, 60, 60],
                       PW=[255, 255, 255], SUB_HL=[255, 214, 120], BRANDC=[18, 30, 74], SLAB=[226, 214, 194],
                       SER3=[[42, 120, 214], [217, 89, 38], [13, 159, 110]]),
            cover=dict(style="s5", serif=True, face="card", tag="REALITY CHECK · EP 4", l1="Salary Grows,", l2="Does Your SIP?", mid="FIXED vs STEP-UP SIP", graphic="steps",
                       gvals=[49.5, 98.5], glabs=["FIXED", "+10% / YR"], gfmt="₹{:.1f}L",
                       badge="", va="", vb="", src="Own calculation",
                       hook=[["", [["सैलरी हर साल बढ़ती है,", False]]], ["", [["SIP ", False], ["क्यों नहीं", True], ["?", False]]]]),
            scenes=S)
json.dump(spec, open(os.path.join(HERE, "spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", sum(vdur(i) + LEAD + PAD for i in range(1, 7)) + 0.8)
