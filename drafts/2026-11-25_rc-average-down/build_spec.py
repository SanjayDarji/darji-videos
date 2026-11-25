import json, wave, os
HERE = os.path.dirname(os.path.abspath(__file__))
TEMPO, LEAD, PAD = 1.12, 0.12, 0.15

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
subs = ["*Stop!* शेयर *40%* गिर गया है?", "*Break-even* के लिए उसे करीब *67%* ऊपर जाना पड़ेगा।", "और आप सोच रहे हैं, 'थोड़ा और ख़रीद लूँ, *average down* हो जाएगा'?", "रुकिए। पहले *यह* देख लीजिए।"]
st, _ = starts(1, subs, early=0.1)
S.append(dict(type="isohook", line1="Stock 40% down?", line2="Average Down = Trap?", size1=64, size2=76,
              chips=["40% down", "67% चाहिए!"], chip_t=[round(st[0] + 0.3, 2), round(st[1] + 0.5, 2)],
              note="चित्र सिर्फ़ उदाहरण के लिए · काल्पनिक", rev=rev(1, subs, [0, 1]), subs=subs))
# 2 asymmetry table (pure maths)
subs = ["सबसे पहले, *गणित*। Falls और recoveries *बराबर नहीं* होते।", "*20%* गिरा, तो *25%* चाहिए।", "*50%* गिरा, तो पूरे *100%*।", "और *80%* गिरा, तो *400%*।", "The deeper the hole, the *longer the climb*."]
st, dur = starts(2, subs, early=0.1)
S.append(dict(type="isobars", title="गिरावट vs ज़रूरी रिकवरी", sub="Fall vs gain needed to break even", step=100, hl=[0, 1, 2, 3], fmt="+{:.0f}%",
              offs=[0.0, round((st[2] - st[1]) * 0.55, 2), round(st[2] - st[1], 2), round(st[3] - st[1], 2)],
              rows=[["20% गिरावट", 25], ["40% गिरावट", 66.7], ["50% गिरावट", 100], ["80% गिरावट", 400]],
              gap="Deeper = Harder", gap_sub="गिरावट जितनी गहरी, रिकवरी उतनी मुश्किल",
              note="गणित: 1/(1 − गिरावट) − 1 · हमारी गणना",
              rev=[0.03, round(st[1] / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 3 average-down example (illustrative)
subs = ["अब *average down* को एक *example* से देखिए।", "मान लीजिए आपने *₹100* पर *100 शेयर* लिए, यानी *₹10,000*।", "शेयर *₹60* पर आ गया। आपने *100 शेयर और* ले लिए,",
        "तो आपकी *average cost* हो गई *₹80*।", "अब break-even के लिए सिर्फ़ *33%* चाहिए, *67%* नहीं।", "*Sounds smart, right?*"]
st, dur = starts(3, subs, early=0.1); t1 = st[1]
S.append(dict(type="isobars", title="Average down · काल्पनिक उदाहरण", sub="100 शेयर + 100 शेयर · कीमत ₹ में", step=108, hl=[2], fmt="₹{:.0f}",
              offs=[0.0, round(st[2] - t1 + 0.6, 2), round(st[3] - t1, 2)],
              rows=[["पहली खरीद", 100], ["गिरने के बाद", 60], ["नई average cost", 80]],
              gap="67% → 33%", gap_sub="Break-even के लिए ज़रूरी बढ़त",
              note="चित्र सिर्फ़ समझाने के लिए · कोई सिफ़ारिश नहीं · हमारी गणना",
              rev=[0.03, round(t1 / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 4 the catch (exposure doubles)
subs = ["लेकिन *catch* सुनिए। आपका *exposure* भी *double* हो गया: *₹10,000* से *₹16,000*।", "अब अगर शेयर *₹30* तक गिर जाए,", "तो बिना average down के नुक़सान *₹7,000*, और average down के बाद *₹10,000*।", "*Percentage* कम दिखता है, पर *rupee loss* बड़ा होता है।"]
st, dur = starts(4, subs, early=0.1); d1 = st[2] - st[1]
S.append(dict(type="isobars", title="अगर शेयर ₹30 तक गिरे", sub="कुल नुक़सान · काल्पनिक उदाहरण", step=130, hl=[1], fmt="-₹{:,.0f}",
              offs=[0.0, round(st[2] - st[1] + 0.9, 2)],
              rows=[["सिर्फ़ पहली खरीद", 7000], ["Average down के बाद", 10000]],
              gap="₹3,000 ज़्यादा", gap_sub="% नुक़सान 70% से 62.5%, पर रुपये में ज़्यादा",
              note="निवेश: ₹10,000 बनाम ₹16,000 · हमारी गणना, कोई सिफ़ारिश नहीं",
              rev=[0.03, round(st[1] / dur, 4), round(st[3] / dur, 4)], subs=subs))
# 5 real historical example: Yes Bank (price levels)
subs = ["*Real example?* Yes Bank।", "*20 अगस्त 2018* को इसका शिखर *₹404* था।", "*नवंबर 2026* में भाव करीब *₹17.6*, यानी करीब *96%* नीचे।", "*Cheap दिखना* और *value होना*, दो अलग बातें हैं।", "यह सिर्फ़ *ऐतिहासिक डेटा* है, कोई सलाह नहीं।"]
st, dur = starts(5, subs, early=0.1)
S.append(dict(type="isocmp", badge=95.6, badge_cap="शिखर से गिरावट · अगस्त 2018 से नवंबर 2026", col_name="Yes Bank · अगस्त 2018 का शिखर = 100%",
              seg1="गिरावट", seg2="बचा हुआ", chips_head="भाव (₹)",
              chips=[["20 अग. 2018", "शिखर ₹404"], ["13 नवं. 2026", "लगभग ₹17.6"], ["अंतर", "करीब 96%"]],
              note="स्रोत: Business Standard (शिखर) · Upstox (13 नवं. 2026) · % गणना हमारी",
              rev=[0.0, round(st[1] / dur, 4), round((st[2] + 0.3) / dur, 4), round(st[2] / dur, 4)], subs=subs))
# 6 lesson / filter question
subs = ["तो *filter* क्या है? खुद से पूछिए:", "अगर यह शेयर आज मेरे पास *न होता*, तो क्या मैं इसे *इसी price* पर नए सिरे से खरीदता?", "और देखिए, पूरा *market* गिर रहा है, या सिर्फ़ *यही stock*?", "*Market dip* और *broken business* में फ़र्क़ होता है।", "यह सलाह नहीं, *सोचने का तरीक़ा* है।"]
S.append(dict(type="lesson", rows=[dict(t="Fresh-buy test", s="BUY AGAIN TODAY, AT THIS PRICE?"), dict(t="Market या सिर्फ़ stock?", s="MARKET-WIDE DIP OR STOCK-SPECIFIC?"),
              dict(t="Dip ≠ broken business", s="THINKING FRAMEWORK · NOT ADVICE")], rev=rev(6, subs, [1, 2, 3]), subs=subs))
# 7 poll
subs = ["आज का *poll*।", "क्या आपने कभी किसी गिरते *stock* में *average down* किया है?", "*A*: हाँ, काम आया।", "*B*: हाँ, फँस गया।", "*C*: कभी नहीं किया।", "*Comment* में लिखिए।"]
st, dur = starts(7, subs, early=0.1)
S.append(dict(type="poll", head="आज का Poll", q="कभी average down किया है?", opts=[["A", "हाँ, काम आया"], ["B", "हाँ, फँस गया"], ["C", "कभी नहीं किया"]],
              ask="Comment में A, B या C लिखिए", note="सिर्फ़ जानने के लिए · कोई सलाह नहीं",
              rev=[0.0, round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[5] / dur, 4)], opt_rev=[round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 8 outro
subs = ["काम का लगा तो *Save* कीजिए।", "ये video उस दोस्त को *Send* कीजिए, जो हर *dip* पर *average down* करता है।", "*Follow* कीजिए *TheSDTrader*।",
        "हम *SEBI registered नहीं* हैं। यह जानकारी सिर्फ़ *educational* है, *investment advice नहीं*।"]
S.append(dict(type="outro", tag="Reality Check · Hindi + English", cta=["SAVE", "SEND", "FOLLOW"], notice_hi="हम SEBI registered नहीं हैं।",
              notice_en="Educational purposes only · Not investment advice", tail=0.8, rev=[0.04, rev(8, subs, [3], tail=0.8)[0]], subs=subs))

spec = dict(brand="TheSDTrader", tagline="Educational · शैक्षणिक जानकारी · Not advice", face="assets/face_original.png",
            voice_tempo=TEMPO, lead=LEAD, pad=PAD, music_vol=0.2, sfx_vol=0.4, voice_vol=1.5, day_tag="REALITY CHECK · DAY 5",
            theme=dict(BG=[254, 250, 243], bg_delta=[-10, -18, -31], WHITE=[18, 30, 74], MUTED=[112, 102, 84], GOLD=[190, 138, 46], CARD=[255, 255, 255],
                       CARD2=[232, 218, 188], DARK=[18, 30, 74], BLUE=[255, 236, 200], ORANGE=[217, 89, 38], GREEN=[13, 159, 110], RED=[214, 60, 60],
                       PW=[255, 255, 255], SUB_HL=[255, 214, 120], BRANDC=[18, 30, 74], SLAB=[226, 214, 194],
                       SER3=[[42, 120, 214], [217, 89, 38], [13, 159, 110]]),
            cover=dict(style="s5", serif=True, face="card", tag="REALITY CHECK · EP 5", l1="Down 40%?", l2="Buy More?", mid="THE AVERAGE-DOWN TRAP", graphic="steps",
                       gtitle="FALL vs GAIN NEEDED", gvals=[40, 66.7], glabs=["FALL", "NEEDED"], gfmt="{:.0f}%", gfoot="ILLUSTRATIVE MATHS · NOT ADVICE",
                       badge="", va="", vb="", src="Own calculation",
                       hook=[["", [["शेयर 40% गिरा?", False]]], ["", [["और ", False], ["ख़रीदें", True], ["? Think twice.", False]]]]),
            scenes=S)
json.dump(spec, open(os.path.join(HERE, "spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", sum(vdur(i) + LEAD + PAD for i in range(1, 9)) + 0.8)
