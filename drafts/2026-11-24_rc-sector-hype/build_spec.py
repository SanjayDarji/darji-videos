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
subs = ["जो *सेक्टर* हर जगह चमक रहा हो,", "यूट्यूब पर, न्यूज़ में, दोस्तों की बातों में,", "कहीं आप उसमें *सबसे आख़िर* में तो नहीं घुस रहे?", "चलिए, *असली डेटा* देखते हैं।"]
st, _ = starts(1, subs, early=0.1)
S.append(dict(type="isohook", line1="हर जगह चमकता सेक्टर?", line2="कहीं आप लेट तो नहीं?", size1=58, size2=78,
              chips=["हाइप ऊपर", "पैसा देर से?"], chip_t=[round(st[1], 2), round(st[2], 2)],
              note="चित्र सिर्फ़ उदाहरण के लिए · काल्पनिक", rev=rev(1, subs, [0, 1]), subs=subs))
# 2 flows (Value Research category-level data)
subs = ["*वैल्यू रिसर्च* के डेटा में, *PSU फंड* अप्रैल 2020 से जनवरी 2024 तक करीब *283%* चढ़े।",
        "रैली के दौरान उनसे *₹2,616 करोड़* निकले, और रैली पुरानी होने के बाद *₹5,356 करोड़* आए।",
        "*इन्फ्रा फंड* में भी यही दिखा। रैली में *₹405 करोड़* निकले, फिर *₹16,041 करोड़* आए।",
        "और सितंबर 2024 के करेक्शन के बाद, मार्च 2025 की शुरुआत तक, यह श्रेणी करीब *24%* गिरी।"]
st, dur = starts(2, subs, early=0.1)
half = lambda a, b: round((st[a] + (st[b] - st[a]) * 0.5) / dur, 4)
S.append(dict(type="isoflow", title="श्रेणी में नेट फ़्लो (₹ करोड़)", sub="बाएँ: नेट निकासी · दाएँ: नेट आमद · cr = करोड़", vmax=16041,
              blocks=[dict(name="PSU फंड श्रेणी", sub="रैली: अप्रैल 2020 – जन. 2024 · लगभग +283%", ix=[1, 2, 3],
                           bars=[["रैली के दौरान (नेट निकासी)", -2616], ["रैली पुरानी होने के बाद · जन.–सित. 2024 (नेट आमद)", 5356]]),
                      dict(name="इन्फ्रा फंड श्रेणी", sub="रैली: अप्रैल 2020 – जुल. 2023 · लगभग +213%", ix=[4, 4, 5],
                           bars=[["रैली के दौरान (नेट निकासी)", -405], ["रैली पुरानी होने के बाद · अग. 2023–सित. 2024 (नेट आमद)", 16041]])],
              pill=dict(ix=6, t="इन्फ्रा श्रेणी: करीब −24%", s="सितंबर 2024 के करेक्शन के बाद, मार्च 2025 की शुरुआत तक"),
              note="स्रोत: Value Research (श्रेणी-स्तर के आँकड़े)",
              rev=[0.0, round(st[0] / dur, 4), round(st[1] / dur, 4), half(1, 2), round(st[2] / dur, 4), half(2, 3), round(st[3] / dur, 4)], subs=subs))
# 3 realty example (levels from ANAROCK / GoodReturns, % drop my own calculation)
subs = ["गिरने के बाद *रिकवरी* में कितना वक़्त लगता है?", "एक उदाहरण, *रियल्टी*। BSE रियल्टी इंडेक्स जनवरी 2008 में *13,647* पर था, और मार्च 2009 में *1,347* पर।",
        "यानी करीब *90%* की गिरावट।", "अक्टूबर 2021 में भी यह करीब *4,000* पर था।", "यह सिर्फ़ एक उदाहरण है, *हर सेक्टर ऐसा नहीं* करता।"]
st, dur = starts(3, subs, early=0.1)
S.append(dict(type="isocmp", badge=90, badge_cap="गिरावट · जन. 2008 से मार्च 2009", col_name="BSE रियल्टी · जनवरी 2008 का शिखर = 100%",
              seg1="गिरावट", seg2="बचा हुआ", chips_head="इंडेक्स लेवल",
              chips=[["जन. 2008", "13,647"], ["मार्च 2009", "1,347"], ["अक्टू. 2021", "~4,000"]],
              note="स्रोत: ANAROCK (शिखर, 2021) · GoodReturns (मार्च 2009) · % गणना हमारी",
              rev=[0.0, round((st[1] + (st[2] - st[1]) * 0.6) / dur, 4), round((st[2] + 0.3) / dur, 4), round(st[1] / dur, 4)], subs=subs))
# 4 lesson
subs = ["तो सबक क्या है? पिछली रैली का मतलब, *अगली रैली नहीं* होता।", "सेक्टर फंड *एक ही सेक्टर* में बंधे रहते हैं, फंड मैनेजर सेक्टर बदल नहीं सकता।",
        "कई जानकार ऐसे फंड को पोर्टफोलियो का *छोटा हिस्सा* ही रखने की बात करते हैं।", "यह सलाह नहीं, सिर्फ़ जानकारी है। पैसा लगाने से पहले, अपना *रिस्क* समझिए।"]
S.append(dict(type="lesson", rows=[dict(t="पिछली रैली ≠ अगली रैली", s="PAST RALLY ≠ NEXT RALLY"), dict(t="एक ही सेक्टर में बंधे", s="MANAGER CAN'T SWITCH SECTORS"),
              dict(t="कई जानकार: छोटा हिस्सा", s="SOME EXPERTS: KEEP IT SMALL · NOT ADVICE")], rev=rev(4, subs, [0, 1, 2]), subs=subs))
# 5 poll
subs = ["आज का *पोल*।", "क्या आपने कभी किसी *ट्रेंडिंग सेक्टर* में पैसा लगाया है?", "*A*: हाँ, फ़ायदा हुआ।", "*B*: हाँ, फँस गया।", "*C*: कभी नहीं।", "*कमेंट* में लिखिए।"]
st, dur = starts(5, subs, early=0.1)
S.append(dict(type="poll", head="आज का पोल", q="क्या आपने कभी किसी ट्रेंडिंग सेक्टर में पैसा लगाया है?", opts=[["A", "हाँ, फ़ायदा हुआ"], ["B", "हाँ, फँस गया"], ["C", "कभी नहीं"]],
              ask="कमेंट में A, B या C लिखिए", note="सिर्फ़ जानने के लिए · कोई सलाह नहीं",
              rev=[0.0, round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[5] / dur, 4)], opt_rev=[round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 6 outro
subs = ["काम का लगा तो *Save* कीजिए।", "ये वीडियो किसी ऐसे दोस्त को *Send* कीजिए, जो हर *ट्रेंडिंग सेक्टर* के पीछे भागता है।", "Follow कीजिए *TheSDTrader*।",
        "हम *SEBI रजिस्टर्ड नहीं* हैं। यह जानकारी सिर्फ़ *शैक्षणिक* है, निवेश सलाह नहीं।"]
S.append(dict(type="outro", tag="Reality Check · हिंदी में", cta=["SAVE", "SEND", "FOLLOW"], notice_hi="हम SEBI रजिस्टर्ड नहीं हैं।",
              notice_en="Educational purposes only · Not investment advice", tail=0.8, rev=[0.04, rev(6, subs, [3], tail=0.8)[0]], subs=subs))

spec = dict(brand="TheSDTrader", tagline="शैक्षणिक जानकारी · निवेश सलाह नहीं", face="assets/face_original.png",
            voice_tempo=TEMPO, lead=LEAD, pad=PAD, music_vol=0.2, sfx_vol=0.4, voice_vol=1.5, day_tag="REALITY CHECK · DAY 3",
            theme=dict(BG=[254, 250, 243], bg_delta=[-10, -18, -31], WHITE=[18, 30, 74], MUTED=[112, 102, 84], GOLD=[190, 138, 46], CARD=[255, 255, 255],
                       CARD2=[232, 218, 188], DARK=[18, 30, 74], BLUE=[255, 236, 200], ORANGE=[217, 89, 38], GREEN=[13, 159, 110], RED=[214, 60, 60],
                       PW=[255, 255, 255], SUB_HL=[255, 214, 120], BRANDC=[18, 30, 74], SLAB=[226, 214, 194],
                       SER3=[[42, 120, 214], [217, 89, 38], [13, 159, 110]]),
            cover=dict(style="s5", serif=True, face="card", tag="REALITY CHECK · EP 3", l1="Hot Sector,", l2="Late Money?", mid="RALLY vs INFLOWS", graphic="peak",
                       badge="", va="", vb="", src="Source: Value Research",
                       hook=[["", [["हर जगह चमकता सेक्टर,", False]]], ["", [["कहीं आप ", False], ["लेट", True], [" तो नहीं?", False]]]]),
            scenes=S)
json.dump(spec, open(os.path.join(HERE, "spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", sum(vdur(i) + LEAD + PAD for i in range(1, 7)) + 0.8)
