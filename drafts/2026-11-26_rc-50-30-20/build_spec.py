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
S = []
# 1 hook
subs = ["हर *finfluencer* बोलता है, *50-30-20 rule* follow करो।", "पर *₹40,000* की salary, और *Bengaluru* में किराया?", "यहाँ यह rule पहले ही महीने में *fail* हो सकता है।", "*Let's do a reality check.*"]
st, _ = starts(1, subs, early=0.1)
S.append(dict(type="isohook", line1="50-30-20 rule?", line2="₹40K पर fail?", size1=64, size2=88,
              chips=["Rent ~48%", "Needs ~67%"], chip_t=[round(st[1] + 0.4, 2), round(st[2] + 0.4, 2)],
              note="चित्र सिर्फ़ उदाहरण के लिए · काल्पनिक", rev=rev(1, subs, [0, 1]), subs=subs))
# 2 the rule
subs = ["Rule *simple* है।", "Salary का *50%* needs, यानी किराया, राशन और bills।", "*30%* wants, यानी shopping और outing।", "और *20%* savings।", "*Template* अच्छा है, पर असली सवाल है, क्या यह आपके *शहर* में fit होता है?"]
S.append(dict(type="lesson", rows=[dict(t="50% Needs", s="RENT · RATION · BILLS"), dict(t="30% Wants", s="SHOPPING · OUTING"),
              dict(t="20% Savings", s="FIRST GOAL, NOT A LAW")], rev=rev(2, subs, [1, 2, 3]), subs=subs))
# 3 rent data
subs = ["अब *real data* देखिए।", "*CREDAI-MCHI* की report के मुताबिक़ *1BHK* का औसत किराया,", "*Bengaluru* में करीब *₹19,000*, *Delhi-NCR* में भी करीब *₹19,000*,", "और *Mumbai* में करीब *₹43,000*।", "यानी Mumbai में *अकेला किराया* ही ₹40,000 की salary से ज़्यादा।", "और एक report के मुताबिक़, इस साल की पहली तिमाही में बड़े शहरों में किराए साल भर में करीब *14%* बढ़े।"]
st, dur = starts(3, subs, early=0.1); t1 = st[2]
S.append(dict(type="isobars", title="1BHK औसत मासिक किराया", sub="CREDAI-MCHI report · salary ₹40,000 से तुलना", step=108, hl=[2], fmt="₹{:,.0f}",
              offs=[0.0, 1.4, round(st[3] - t1, 2)],
              rows=[["Bengaluru", 19228], ["Delhi-NCR", 19058], ["Mumbai", 43138]],
              gap="Mumbai > ₹40K salary", gap_sub="Q1 2026: बड़े शहरों में किराए ~14% ऊपर",
              note="स्रोत: CREDAI-MCHI (Free Press Journal) · Outlook Money (Q1 2026)",
              rev=[0.03, round(t1 / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 4 needs maths
subs = ["अब *₹40,000* की salary पर *math*।", "Rule कहता है, needs पर *₹20,000*।", "पर Bengaluru में 1BHK करीब *₹19,000*, ऊपर से राशन, travel और bills का कम से कम *₹7,500*।", "Total करीब *₹26,700*, यानी salary का *67%*।", "Wants और savings के लिए बचे सिर्फ़ *33%*।"]
st, dur = starts(4, subs, early=0.1); t1 = st[1]
S.append(dict(type="isobars", title="₹40,000 salary पर needs", sub="Bengaluru 1BHK + कम से कम खर्च · काल्पनिक", step=130, hl=[1], fmt="₹{:,.0f}",
              offs=[0.0, round(st[3] - t1, 2)],
              rows=[["Rule: 50%", 20000], ["असली: ~67%", 26728]],
              gap="सिर्फ़ 33% बचा", gap_sub="wants + savings दोनों के लिए",
              note="किराया ₹19,228 + राशन ₹4,000 + travel ₹1,500 + bills ₹2,000 · हमारी गणना",
              rev=[0.03, round(t1 / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 5 fixes
subs = ["तो rule छोड़ें? *नहीं*, उसे *smart* तरीके से adjust करें।", "पहला, *pay yourself first*। Salary आते ही, जितना हो सके, पहले बचत अलग कीजिए, चाहे *10%* से ही शुरू हो।", "दूसरा, सबसे बड़ा खर्च *किराया* है, तो *flat share* करना या office के थोड़ा दूर रहना, यह सबसे बड़ा *lever* है।", "तीसरा, जब salary बढ़े, तो *lifestyle* नहीं, *savings* का percent बढ़ाइए। इसे कहते हैं *lifestyle creep* से बचना।"]
S.append(dict(type="lesson", rows=[dict(t="Pay yourself first", s="SAVE ON SALARY DAY · EVEN 10%"), dict(t="Rent = biggest lever", s="FLAT SHARE · SMART LOCATION"),
              dict(t="Raise = savings ↑", s="AVOID LIFESTYLE CREEP")], rev=rev(5, subs, [1, 2, 3]), subs=subs))
# 6 poll
subs = ["आज का *poll*।", "आप अपनी salary का कितना percent *बचा* पाते हैं?", "*A*: 10% से कम।", "*B*: 10 से 20%।", "*C*: 20% से ज़्यादा।", "*Comment* में लिखिए।"]
st, dur = starts(6, subs, early=0.1)
S.append(dict(type="poll", head="आज का Poll", q="Salary का कितना % बचता है?", opts=[["A", "10% से कम"], ["B", "10 से 20%"], ["C", "20% से ज़्यादा"]],
              ask="Comment में A, B या C लिखिए", note="सिर्फ़ जानने के लिए · कोई सलाह नहीं",
              rev=[0.0, round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[5] / dur, 4)], opt_rev=[round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 7 outro
subs = ["काम का लगा तो *Save* कीजिए।", "यह video उस दोस्त को *Send* कीजिए, जिसकी salary *महीने के बीच* में ही ख़त्म हो जाती है।", "*Follow* कीजिए *TheSDTrader*।",
        "हम *SEBI registered नहीं* हैं। यह जानकारी सिर्फ़ *educational* है, *financial advice नहीं*।"]
S.append(dict(type="outro", tag="Reality Check · Hindi + English", cta=["SAVE", "SEND", "FOLLOW"], notice_hi="हम SEBI registered नहीं हैं।",
              notice_en="Educational purposes only · Not financial advice", tail=0.8, rev=[0.04, rev(7, subs, [3], tail=0.8)[0]], subs=subs))
spec = dict(brand="TheSDTrader", tagline="Educational · शैक्षणिक जानकारी · Not advice", face="assets/face_original.png",
            voice_tempo=TEMPO, lead=LEAD, pad=PAD, music_vol=0.2, sfx_vol=0.4, voice_vol=1.5, day_tag="REALITY CHECK · DAY 9",
            theme=dict(BG=[254, 250, 243], bg_delta=[-10, -18, -31], WHITE=[18, 30, 74], MUTED=[112, 102, 84], GOLD=[190, 138, 46], CARD=[255, 255, 255],
                       CARD2=[232, 218, 188], DARK=[18, 30, 74], BLUE=[255, 236, 200], ORANGE=[217, 89, 38], GREEN=[13, 159, 110], RED=[214, 60, 60],
                       PW=[255, 255, 255], SUB_HL=[255, 214, 120], BRANDC=[18, 30, 74], SLAB=[226, 214, 194],
                       SER3=[[42, 120, 214], [217, 89, 38], [13, 159, 110]]),
            cover=dict(style="s5", serif=True, face="card", tag="REALITY CHECK · EP 9", l1="50-30-20?", l2="Not on 40K.", mid="THE BUDGET RULE", graphic="steps",
                       gtitle="NEEDS ON ₹40K SALARY", gvals=[20.0, 26.7], glabs=["RULE: 50%", "REAL: ~67%"], gfmt="₹{:.1f}K", gfoot="ILLUSTRATIVE · NOT ADVICE",
                       badge="", va="", vb="", src="Own calculation",
                       hook=[["", [["किराया ही ", False], ["48%", True], [" salary का?", False]]], ["", [["Rule का ", False], ["reality check", True]]]]),
            scenes=S)
json.dump(spec, open(os.path.join(HERE, "spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", sum(vdur(i) + LEAD + PAD for i in range(1, 8)) + 0.8)
