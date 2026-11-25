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
subs = ["बाज़ार *33%* गिरा, और उसी हफ़्ते आपकी *job* चली गई।", "अब पैसे चाहिए, और आपका *एक ही सहारा* है, आपका *portfolio*।", "*Think about it.*", "यही है सबसे बड़ा *hidden risk*।"]
st, _ = starts(1, subs, early=0.1)
S.append(dict(type="isohook", line1="Market down 33%?", line2="Job gone too?", size1=64, size2=88,
              chips=["Market -33%", "Job loss"], chip_t=[round(st[0] + 0.4, 2), round(st[0] + 2.4, 2)],
              note="चित्र सिर्फ़ उदाहरण के लिए · काल्पनिक", rev=rev(1, subs, [0, 1]), subs=subs))
# 2 survey: emergency fund + insurance
subs = ["और यह सिर्फ़ *कहानी* नहीं है।", "*Finsafe India* की रिपोर्ट, जो *Business Today* में छपी, के मुताबिक़", "सिर्फ़ *31%* working professionals के पास *emergency fund* और *insurance*, दोनों हैं।", "पिछले साल यह *26%* था।", "यानी करीब *7 में से 10* लोग अब भी आधे-अधूरे *protected* हैं।"]
st, dur = starts(2, subs, early=0.1)
S.append(dict(type="isocmp", badge=31, badge_cap="के पास fund + insurance दोनों हैं", col_name="Finsafe India रिपोर्ट · 4,532 लोग",
              seg1="दोनों हैं", seg2="बाकी", chips_head="Finsafe India रिपोर्ट",
              chips=[["पिछले साल", "26%"], ["इस साल", "31%"], ["बाकी", "~69%"]],
              note="स्रोत: Finsafe India रिपोर्ट, Business Today (2 अगस्त 2026)",
              rev=[0.0, round(st[2] / dur, 4), round((st[2] + 0.8) / dur, 4), round(st[3] / dur, 4)], subs=subs))
# 3 Covid crash: real data
subs = ["अब एक *real example*। *मार्च 2020*।", "*Sensex* सिर्फ़ *13 trading sessions* में करीब *33%* गिरा,", "और *23 मार्च* को *25,981* पर बंद हुआ।", "जिन्हें उस समय बेचना पड़ा, उन्होंने *bottom* के पास बेचा।", "*Sensex* नवंबर 2020 तक, यानी करीब *आठ महीने* में, पुराने स्तर पर लौट आया।", "*History is not a promise*, पर यह दिखाती है कि *timing* कितनी मायने रखती है।"]
st, dur = starts(3, subs, early=0.1)
S.append(dict(type="isocmp", badge=33, badge_cap="13 trading sessions में गिरावट", col_name="Sensex · मार्च 2020 का क्रैश",
              seg1="गिरावट", seg2="बचा", chips_head="Sensex · कोविड क्रैश",
              chips=[["23 मार्च 2020", "25,981 बंद"], ["गिरावट", "~33%"], ["वापसी", "~8 महीने"]],
              note="स्रोत: Business Standard · Business Today · इतिहास गारंटी नहीं",
              rev=[0.0, round(st[1] / dur, 4), round((st[1] + 0.8) / dur, 4), round(st[2] / dur, 4)], subs=subs))
# 4 forced selling maths (own, illustrative)
subs = ["अब *math* देखिए।", "मान लीजिए आपको *₹2.4 लाख* चाहिए, यानी *₹40,000* के खर्च के *छह महीने*।", "*Normal* समय में, आप *₹2.4 लाख* के units बेचते।", "पर *33%* गिरावट में, उतने ही पैसे के लिए आपको करीब *49%* ज़्यादा units बेचने पड़ते।", "*Same need*, ज़्यादा नुक़सान।"]
st, dur = starts(4, subs, early=0.1); t1 = st[1] + 0.6 * (st[2] - st[1])
S.append(dict(type="isobars", title="एक ही ज़रूरत: ₹2.4 लाख", sub="बेचने पड़ने वाले units (pre-crash value) · काल्पनिक", step=130, hl=[1], fmt="₹{:.1f}L",
              offs=[0.0, round(st[3] - t1, 2)],
              rows=[["सामान्य समय", 2.4], ["33% गिरावट के बाद", 3.58]],
              gap="49% ज़्यादा", gap_sub="उतने ही पैसे के लिए ज़्यादा units बेचने पड़ते हैं",
              note="ज़रूरत: ₹40,000 x 6 महीने · 2.4 / 0.67 = 3.58 · हमारी गणना",
              rev=[0.03, round(t1 / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 5 shield rule
subs = ["तो *Shield* का *rule* क्या है?", "बड़ा पैसा market में लगाने से पहले, ज़रूरी खर्चों के *तीन से छह महीने* अलग रखना एक आम *thumb rule* है।", "अगर *आमदनी अनियमित* है, या घर में *एक ही कमाने वाला* है, तो और ज़्यादा।", "इसे रखने की आम जगहें हैं, *savings account*, *FD* और *liquid fund*।", "*Liquid fund* का return *guaranteed नहीं* होता, और redemption में आम तौर पर *T+1* लगता है।"]
S.append(dict(type="lesson", rows=[dict(t="3-6 months expenses", s="COMMON RULE OF THUMB, NOT ADVICE"), dict(t="Irregular income = more", s="VARIABLE PAY OR ONE EARNER: MORE"),
              dict(t="Safe + liquid", s="SAVINGS A/C · FD · LIQUID FUND")], rev=rev(5, subs, [1, 2, 3]), subs=subs))
# 6 poll
subs = ["आज का *poll*।", "आपके पास अभी कितने महीने का *emergency fund* है?", "*A*: ज़ीरो।", "*B*: एक से तीन महीने।", "*C*: चार महीने या ज़्यादा।", "*Comment* में लिखिए।"]
st, dur = starts(6, subs, early=0.1)
S.append(dict(type="poll", head="आज का Poll", q="कितने महीने का emergency fund?", opts=[["A", "ज़ीरो"], ["B", "1 से 3 महीने"], ["C", "4 महीने या ज़्यादा"]],
              ask="Comment में A, B या C लिखिए", note="सिर्फ़ जानने के लिए · कोई सलाह नहीं",
              rev=[0.0, round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[5] / dur, 4)], opt_rev=[round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 7 outro
subs = ["काम का लगा तो *Save* कीजिए।", "ये video उस दोस्त को *Send* कीजिए, जो market में पैसा लगाता है, पर *emergency fund* नहीं रखता।", "*Follow* कीजिए *TheSDTrader*।",
        "हम *SEBI registered नहीं* हैं। यह जानकारी सिर्फ़ *educational* है, *investment advice नहीं*।"]
S.append(dict(type="outro", tag="Reality Check · Hindi + English", cta=["SAVE", "SEND", "FOLLOW"], notice_hi="हम SEBI registered नहीं हैं।",
              notice_en="Educational purposes only · Not investment advice", tail=0.8, rev=[0.04, rev(7, subs, [3], tail=0.8)[0]], subs=subs))

spec = dict(brand="TheSDTrader", tagline="Educational · शैक्षणिक जानकारी · Not advice", face="assets/face_original.png",
            voice_tempo=TEMPO, lead=LEAD, pad=PAD, music_vol=0.2, sfx_vol=0.4, voice_vol=1.5, day_tag="REALITY CHECK · DAY 6",
            theme=dict(BG=[254, 250, 243], bg_delta=[-10, -18, -31], WHITE=[18, 30, 74], MUTED=[112, 102, 84], GOLD=[190, 138, 46], CARD=[255, 255, 255],
                       CARD2=[232, 218, 188], DARK=[18, 30, 74], BLUE=[255, 236, 200], ORANGE=[217, 89, 38], GREEN=[13, 159, 110], RED=[214, 60, 60],
                       PW=[255, 255, 255], SUB_HL=[255, 214, 120], BRANDC=[18, 30, 74], SLAB=[226, 214, 194],
                       SER3=[[42, 120, 214], [217, 89, 38], [13, 159, 110]]),
            cover=dict(style="s5", serif=True, face="card", tag="REALITY CHECK · EP 6", l1="Crash Came,", l2="Cash Ready?", mid="THE EMERGENCY SHIELD", graphic="steps",
                       gtitle="SAME ₹2.4L NEED", gvals=[2.4, 3.58], glabs=["NORMAL", "AFTER -33%"], gfmt="₹{:.1f}L", gfoot="UNITS SOLD · ILLUSTRATIVE",
                       badge="", va="", vb="", src="Own calculation",
                       hook=[["", [["बाज़ार गिरा, job गई,", False]]], ["", [["अब ", False], ["cash", True], [" कहाँ है?", False]]]]),
            scenes=S)
json.dump(spec, open(os.path.join(HERE, "spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", sum(vdur(i) + LEAD + PAD for i in range(1, 8)) + 0.8)
