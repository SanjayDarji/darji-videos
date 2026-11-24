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
subs = ["आपके फंड के आगे *'Regular'* लिखा है?", "तो हर दिन एक *खर्च* आपके पैसे से कट रहा है।", "*बिना किसी अलग बिल* के।", "चलिए, *असली डेटा* देखते हैं।"]
st, _ = starts(1, subs, early=0.1)
S.append(dict(type="isohook", line1="फंड के आगे 'Regular'?", line2="बिना बिल का खर्च!", size1=60, size2=84,
              chips=["Regular प्लान", "रोज़ की कटौती"], chip_t=[round(st[1], 2), round(st[2], 2)],
              note="चित्र सिर्फ़ उदाहरण के लिए · काल्पनिक", rev=rev(1, subs, [0, 1]), subs=subs))
# 2 same portfolio, extra commission slice
subs = ["रेगुलर और डायरेक्ट प्लान का *पोर्टफोलियो एक ही* होता है।", "फ़र्क़ बस इतना, कि रेगुलर के खर्च में *डिस्ट्रीब्यूटर का कमीशन* जुड़ा होता है।",
        "यह खर्च हर दिन फंड की *NAV* से कटता है, *मुनाफ़े से नहीं*, फंड की पूरी वैल्यू के प्रतिशत के हिसाब से।", "और मार्केट गिरे या चढ़े, यह *कटता रहता* है।"]
st, dur = starts(2, subs, early=0.1)
S.append(dict(type="isosplit", title="एक ही पोर्टफोलियो · दो प्लान", names=["Direct", "Regular"], coin_cap="रोज़ कटौती",
              chips_head="दोनों प्लान में क्या है", chips=[["पोर्टफोलियो", "दोनों में एक ही"], ["फंड का खर्च", "दोनों में"], ["कमीशन", "सिर्फ़ रेगुलर में"]],
              note="चित्र सिर्फ़ समझाने के लिए · ऊँचाई काल्पनिक", rev=[0.0, round(st[0] / dur + 0.01, 4), round(st[1] / dur, 4), round(st[2] / dur, 4)], subs=subs))
# 3 SIP example (own calculation, labelled illustrative)
subs = ["अब एक *उदाहरण*।", "मान लीजिए, *₹10,000* की SIP, *20 साल* तक।", "डायरेक्ट में *12%* और रेगुलर में *11%* रिटर्न मानें, यानी *1%* का फ़र्क़।",
        "कुल निवेश *₹24 लाख*, और अंत में लगभग *₹99 लाख* बनाम *₹87 लाख*।", "फ़र्क़ करीब *₹12 लाख*। यह सिर्फ़ एक *काल्पनिक उदाहरण* है, गारंटी नहीं।"]
st, dur = starts(3, subs, early=0.1)
S.append(dict(type="isobars", title="₹10,000/माह SIP · 20 साल", sub="काल्पनिक उदाहरण · L = लाख रुपये", step=118, hl=[0], fmt="₹{:.1f}L",
              offs=[0.0, 1.8, round(st[3] - st[2], 2)],
              rows=[["Direct · 12%", 98.93], ["Regular · 11%", 86.56], ["कुल निवेश", 24.0]],
              gap="फ़र्क़ ≈ ₹12 लाख", gap_sub="सिर्फ़ 1% के फ़र्क़ की धारणा पर · गारंटी नहीं",
              note="गणना: माह-अंत SIP, मासिक चक्रवृद्धि · स्रोत-धारणा: Business Today (13 नवं. 2026)",
              rev=[0.03, round(st[2] / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 4 lesson
subs = ["ध्यान रखिए। रेगुलर में *सलाह और सेवा* भी शामिल होती है।", "अगर आपको वह चाहिए, तो *जानकर चुनिए*।", "अपने फंड का रेगुलर और डायरेक्ट खर्च, *फंड हाउस की साइट* पर देखिए।",
        "और याद रखिए, रेगुलर से डायरेक्ट में *स्विच को बिक्री* माना जाता है, इसलिए *मुनाफ़े पर टैक्स* लग सकता है।", "पहले *हिसाब* लगाइए, फिर फ़ैसला कीजिए।"]
S.append(dict(type="lesson", rows=[dict(t="सलाह + सेवा भी शामिल", s="REGULAR INCLUDES ADVICE & SERVICE"), dict(t="खर्च खुद देखिए", s="CHECK TER ON FUND HOUSE SITE"),
              dict(t="स्विच = बिक्री", s="SWITCH = SALE · TAX MAY APPLY")], rev=rev(4, subs, [0, 2, 3]), subs=subs))
# 5 poll
subs = ["आज का *पोल*।", "आपके ज़्यादातर फंड *रेगुलर* हैं या *डायरेक्ट*?", "*A*: रेगुलर।", "*B*: डायरेक्ट।", "*C*: पता नहीं।", "*कमेंट* में लिखिए।"]
st, dur = starts(5, subs, early=0.1)
S.append(dict(type="poll", head="आज का पोल", q="आपके ज़्यादातर फंड रेगुलर हैं या डायरेक्ट?", opts=[["A", "रेगुलर"], ["B", "डायरेक्ट"], ["C", "पता नहीं"]],
              ask="कमेंट में A, B या C लिखिए", note="सिर्फ़ जानने के लिए · कोई सलाह नहीं",
              rev=[0.0, round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[5] / dur, 4)], opt_rev=[round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 6 outro
subs = ["काम का लगा तो *Save* कीजिए।", "ये वीडियो किसी ऐसे दोस्त को *Send* कीजिए, जिसकी *SIP* चल रही है।", "Follow कीजिए *TheSDTrader*।",
        "हम *SEBI रजिस्टर्ड नहीं* हैं। यह जानकारी सिर्फ़ *शैक्षणिक* है, निवेश सलाह नहीं।"]
S.append(dict(type="outro", tag="Reality Check · हिंदी में", cta=["SAVE", "SEND", "FOLLOW"], notice_hi="हम SEBI रजिस्टर्ड नहीं हैं।",
              notice_en="Educational purposes only · Not investment advice", tail=0.8, rev=[0.04, rev(6, subs, [3], tail=0.8)[0]], subs=subs))

spec = dict(brand="TheSDTrader", tagline="शैक्षणिक जानकारी · निवेश सलाह नहीं", face="assets/face_original.png",
            voice_tempo=TEMPO, lead=LEAD, pad=PAD, music_vol=0.2, sfx_vol=0.4, voice_vol=1.5, day_tag="REALITY CHECK · DAY 2",
            theme=dict(BG=[254, 250, 243], bg_delta=[-10, -18, -31], WHITE=[18, 30, 74], MUTED=[112, 102, 84], GOLD=[190, 138, 46], CARD=[255, 255, 255],
                       CARD2=[232, 218, 188], DARK=[18, 30, 74], BLUE=[255, 236, 200], ORANGE=[217, 89, 38], GREEN=[13, 159, 110], RED=[214, 60, 60],
                       PW=[255, 255, 255], SUB_HL=[255, 214, 120], BRANDC=[18, 30, 74], SLAB=[226, 214, 194],
                       SER3=[[42, 120, 214], [217, 89, 38], [13, 159, 110]]),
            cover=dict(style="s5", serif=True, face="card", tag="REALITY CHECK · EP 2", l1="Same Fund,", l2="Higher Cost?", mid="REGULAR vs DIRECT",
                       badge="SAME", badge_cap="PORTFOLIO", venn_dist=100, va="REGULAR", vb="DIRECT",
                       src="Source: AMFI · Value Research",
                       hook=[["", [["आपके फंड के आगे ", False]]], ["", [["'Regular'", True], [" लिखा है?", False]]]]),
            scenes=S)
json.dump(spec, open(os.path.join(HERE, "spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", sum(vdur(i) + LEAD + PAD for i in range(1, 7)) + 0.8)
