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
subs = ["आपका *fund manager*, market को *beat* कर रहा है?", "*SPIVA* का data कहता है, *10 साल* में, *4 में से 3* large-cap funds अपने *benchmark* से पीछे रहे।", "और *fees*? वो आप *हर साल* दे रहे हैं।", "*Let's check the scoreboard.*"]
st, _ = starts(1, subs, early=0.1)
S.append(dict(type="isohook", line1="Fund manager vs Index?", line2="3 out of 4 lost.", size1=60, size2=88,
              chips=["10 yrs: 74%", "5 yrs: 85%"], chip_t=[round(st[1] + 0.6, 2), round(st[1] + 2.6, 2)],
              note="स्रोत: SPIVA India Mid-Year 2026 · large-cap funds", rev=rev(1, subs, [0, 1]), subs=subs))
# 2 SPIVA
subs = ["*S&P Dow Jones Indices* की *SPIVA India* report, *June 2026* तक का data।", "Large-cap *active funds* में से, *1 साल* में करीब *79%*,", "*3 साल* में *80%*,", "*5 साल* में करीब *85%*,", "और *10 साल* में करीब *74%* funds, अपने *benchmark* से पीछे रहे।"]
st, dur = starts(2, subs, early=0.1); t1 = st[1]
S.append(dict(type="isobars", title="Benchmark से पीछे large-cap funds", sub="SPIVA India · 30 जून 2026 तक · vs S&P India LargeMidCap", step=100, hl=[3], fmt="{:.0f}%",
              offs=[0.0, round(st[2] - t1, 2), round(st[3] - t1, 2), round(st[4] - t1, 2)],
              rows=[["1 साल", 78.79], ["3 साल", 80.0], ["5 साल", 84.85], ["10 साल", 74.03]],
              gap="10 साल: ~3 में से 4", gap_sub="active large-cap funds पीछे",
              note="स्रोत: S&P Dow Jones Indices, SPIVA India Scorecard Mid-Year 2026",
              rev=[0.03, round(t1 / dur, 4), round(min(0.96, (st[4] + 1.2) / dur), 4)], subs=subs))
# 3 fees
subs = ["अब *fees*।", "*SEBI* के नए rules के बाद, *active equity fund* का *base expense ratio* आम तौर पर करीब *1.8%*,", "और *index fund* का करीब *0.3 से 0.5%* माना जा रहा है।", "यह fee *हर साल* कटती है, return अच्छा हो या बुरा।"]
st, dur = starts(3, subs, early=0.1); t1 = st[1]
S.append(dict(type="isobars", title="सालाना fee (BER) · आम अनुमान", sub="SEBI 2026 framework के बाद · fund के हिसाब से अलग", step=130, hl=[0], fmt="{:.1f}%",
              offs=[0.0, round(st[2] - t1, 2)],
              rows=[["Active equity fund", 1.8], ["Index fund", 0.3]],
              gap="~6x फ़र्क़", gap_sub="fee हर साल कटती है, return चाहे जो हो",
              note="स्रोत: Upstox / INDmoney (SEBI MF Regulations 2026 पर) · index cap 0.90%",
              rev=[0.03, round(t1 / dur, 4), round(st[3] / dur, 4)], subs=subs))
# 4 SIP maths
subs = ["अब *math* देखिए।", "*₹10,000* की SIP, *20 साल*, और मान लीजिए fees से पहले दोनों का return *12%*।", "Fee *1.8%* पर, final amount करीब *₹78 लाख*।", "और *0.3%* पर, करीब *₹96 लाख*।", "सिर्फ़ fee का फ़र्क़, करीब *₹17 लाख*।", "यह सिर्फ़ *example* है, return *guaranteed नहीं*।"]
st, dur = starts(4, subs, early=0.1); t1 = st[2]
S.append(dict(type="isobars", title="₹10,000 SIP · 20 साल · final value", sub="fee से पहले 12% मान कर · काल्पनिक", step=130, hl=[1], fmt="₹{:.1f}L",
              offs=[0.0, round(st[3] - t1, 2)],
              rows=[["1.8% fee", 78.6], ["0.3% fee", 95.9]],
              gap="~₹17 लाख फ़र्क़", gap_sub="निवेश ₹24 लाख · सिर्फ़ fee का असर",
              note="हमारी गणना · 10.2% vs 11.7% net · return guaranteed नहीं",
              rev=[0.03, round(t1 / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 5 balance
subs = ["पर *ध्यान रहे*।", "*Index fund* आपको *market का return* देता है, उससे ज़्यादा नहीं, और गिरावट में वह भी *गिरता* है।", "कुछ *active funds* benchmark को *beat* भी करते हैं, बस *पहले से पहचानना* मुश्किल है।", "तो कोई भी fund चुनने से पहले, उसका *expense ratio*, और पिछले सालों में *benchmark से तुलना*, ज़रूर देखिए।"]
S.append(dict(type="lesson", rows=[dict(t="Index = market return", s="NOT MORE · FALLS WITH MARKET"), dict(t="कुछ active funds जीतते हैं", s="HARD TO PICK IN ADVANCE"),
              dict(t="Check: fee + benchmark", s="COMPARE BEFORE YOU CHOOSE")], rev=rev(5, subs, [1, 2, 3]), subs=subs))
# 6 poll
subs = ["आज का *poll*।", "आपके *portfolio* में ज़्यादा क्या है?", "*A*: Active funds।", "*B*: Index funds।", "*C*: दोनों बराबर।", "*Comment* में लिखिए।"]
st, dur = starts(6, subs, early=0.1)
S.append(dict(type="poll", head="आज का Poll", q="Portfolio में ज़्यादा क्या है?", opts=[["A", "Active funds"], ["B", "Index funds"], ["C", "दोनों बराबर"]],
              ask="Comment में A, B या C लिखिए", note="सिर्फ़ जानने के लिए · कोई सलाह नहीं",
              rev=[0.0, round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[5] / dur, 4)], opt_rev=[round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 7 outro
subs = ["काम का लगा तो *Save* कीजिए।", "यह video उस दोस्त को *Send* कीजिए, जो सिर्फ़ *star rating* देखकर fund चुनता है।", "*Follow* कीजिए *TheSDTrader*।",
        "हम *SEBI registered नहीं* हैं। यह जानकारी सिर्फ़ *educational* है, *investment advice नहीं*।"]
S.append(dict(type="outro", tag="Reality Check · Hindi + English", cta=["SAVE", "SEND", "FOLLOW"], notice_hi="हम SEBI registered नहीं हैं।",
              notice_en="Educational purposes only · Not investment advice", tail=0.8, rev=[0.04, rev(7, subs, [3], tail=0.8)[0]], subs=subs))
spec = dict(brand="TheSDTrader", tagline="Educational · शैक्षणिक जानकारी · Not advice", face="assets/face_original.png",
            voice_tempo=TEMPO, lead=LEAD, pad=PAD, music_vol=0.2, sfx_vol=0.4, voice_vol=1.5, day_tag="REALITY CHECK · DAY 10",
            theme=dict(BG=[254, 250, 243], bg_delta=[-10, -18, -31], WHITE=[18, 30, 74], MUTED=[112, 102, 84], GOLD=[190, 138, 46], CARD=[255, 255, 255],
                       CARD2=[232, 218, 188], DARK=[18, 30, 74], BLUE=[255, 236, 200], ORANGE=[217, 89, 38], GREEN=[13, 159, 110], RED=[214, 60, 60],
                       PW=[255, 255, 255], SUB_HL=[255, 214, 120], BRANDC=[18, 30, 74], SLAB=[226, 214, 194],
                       SER3=[[42, 120, 214], [217, 89, 38], [13, 159, 110]]),
            cover=dict(style="s5", serif=True, face="card", tag="REALITY CHECK · EP 10", l1="Fund Manager", l2="vs Index?", mid="THE SCOREBOARD", graphic="steps",
                       gtitle="₹10K SIP · 20 YRS", gvals=[78.6, 95.9], glabs=["1.8% FEE", "0.3% FEE"], gfmt="₹{:.0f}L", gfoot="12% PRE-FEE ASSUMED · ILLUSTRATIVE",
                       badge="", va="", vb="", src="SPIVA India · own calc",
                       hook=[["", [["10 साल में ", False], ["74%", True], [" funds पीछे", False]]], ["", [["Fees ", False], ["हर साल", True], [" कटती है", False]]]]),
            scenes=S)
json.dump(spec, open(os.path.join(HERE, "spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", sum(vdur(i) + LEAD + PAD for i in range(1, 8)) + 0.8)
