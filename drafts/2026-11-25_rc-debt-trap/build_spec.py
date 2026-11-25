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
subs = ["*₹1 लाख* का credit card bill।", "हर महीने बस *minimum due* भर रहे हैं?", "तो सुनिए। यह bill करीब *19 साल* चलेगा, और आप करीब *₹3 लाख* चुकाएँगे।", "*Shocking?* *Let's do the math.*"]
st, _ = starts(1, subs, early=0.1)
S.append(dict(type="isohook", line1="Paying only minimum due?", line2="19-year trap.", size1=60, size2=88,
              chips=["₹1 लाख bill", "~19 साल"], chip_t=[round(st[0] + 0.4, 2), round(st[2] + 0.4, 2)],
              note="चित्र सिर्फ़ उदाहरण के लिए · काल्पनिक", rev=rev(1, subs, [0, 1]), subs=subs))
# 2 rate compare
subs = ["पहले *rate* देखिए।", "India में ज़्यादातर *credit cards* महीने का करीब *3 से 3.5%* interest लेते हैं,", "यानी साल का करीब *42%* तक।", "Compare कीजिए, *SBI* की 1 साल की *FD*, *6.25%*।", "और *minimum due* आम तौर पर बस *5%* होता है।", "Minimum भरने पर, *बाकी पूरी रकम* पर interest लगता रहता है।"]
st, dur = starts(2, subs, early=0.1); t1 = st[2]
S.append(dict(type="isobars", title="साल का rate · % (आम तौर पर)", sub="Credit card ~3.5%/महीना · SBI 1 साल FD", step=130, hl=[1], fmt="{:g}%",
              offs=[round(st[3] - t1, 2), 0.0],
              rows=[["SBI 1 साल FD", 6.25], ["Credit card (आम)", 42]],
              gap="~6.7x महँगा", gap_sub="Minimum due ~5% · बाकी पर interest जारी",
              note="स्रोत: बैंक MITC / Bankbazaar · Business Today (FD, अग. 2026) · card के हिसाब से अलग",
              rev=[0.03, round(t1 / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 3 min-due trap
subs = ["अब *trap* देखिए।", "मान लीजिए *₹1 लाख* बकाया है, interest *3.5% महीना*, और आप हर महीने सिर्फ़ *5% minimum* भरते हैं।", "कोई *नया खर्च* नहीं।", "फिर भी पूरा चुकाने में करीब *19 साल* लगेंगे, और कुल करीब *₹3 लाख* जाएँगे।", "*GST* और *fees* अलग। यही है *debt trap*।"]
st, dur = starts(3, subs, early=0.1); t1 = st[1] + 0.5 * (st[2] - st[1])
S.append(dict(type="isobars", title="सिर्फ़ minimum भरने पर", sub="₹1 लाख · 3.5%/महीना · 5% minimum · काल्पनिक", step=130, hl=[1], fmt="₹{:.2f}L",
              offs=[0.0, round(st[3] - t1, 2)],
              rows=[["उधार", 1.0], ["कुल चुकाया", 3.04]],
              gap="~19 साल", gap_sub="कोई नया खर्च नहीं · GST और fees अलग",
              note="हमारी गणना · min ₹200 · 226 महीने · कोई सिफ़ारिश नहीं",
              rev=[0.03, round(t1 / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 4 two methods
subs = ["तो *निकलें कैसे*? दो popular तरीके हैं।", "पहला, *Snowball*। सबसे *छोटे loan* को पहले ख़त्म कीजिए, *quick win* मिलती है।", "दूसरा, *Avalanche*। सबसे *ज़्यादा interest* वाले loan को पहले target कीजिए।", "दोनों में, बाकी सब loans की *minimum* भरते रहिए, और बचा हुआ *extra पैसा* एक ही target पर लगाइए।"]
S.append(dict(type="lesson", rows=[dict(t="Snowball: छोटा loan पहले", s="QUICK WINS · MOTIVATION"), dict(t="Avalanche: महँगा interest पहले", s="MATHS · LESS INTEREST"),
              dict(t="बाकी पर minimum जारी", s="EXTRA MONEY → ONE TARGET")], rev=rev(4, subs, [1, 2, 3]), subs=subs))
# 5 example
subs = ["एक *example* लेते हैं।", "Card पर *₹60,000*, 42% पर। Bike loan *₹20,000*, 24% पर। Personal loan *₹1.5 लाख*, 14% पर।", "और हर महीने *₹12,000* का budget।", "*Avalanche* में कुल interest करीब *₹44,000*, *snowball* में करीब *₹47,000*।", "लेकिन snowball में पहला loan *5वें महीने* ख़त्म, avalanche में *11वें*।", "*Maths says avalanche, motivation says snowball.* जो तरीका आप *निभा सकें*, वही काम करेगा।"]
st, dur = starts(5, subs, early=0.1); t1 = st[3]
S.append(dict(type="isobars", title="कुल interest · 3 loans · ₹12,000/महीना", sub="काल्पनिक उदाहरण · हमारी गणना", step=130, hl=[0], fmt="₹{:,.0f}",
              offs=[0.0, 1.6],
              rows=[["Avalanche · 23 महीने", 44253], ["Snowball · 24 महीने", 47158]],
              gap="~₹2,900 फ़र्क़", gap_sub="Snowball: पहला loan 5वें महीने · Avalanche: 11वें",
              note="Card ₹60k@42% · Bike ₹20k@24% · PL ₹1.5L@14% · हमारी गणना",
              rev=[0.03, round(t1 / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 6 poll
subs = ["आज का *poll*।", "आपका *style* कौन सा है?", "*A*: Snowball।", "*B*: Avalanche।", "*C*: अभी कोई debt नहीं।", "*Comment* में लिखिए।"]
st, dur = starts(6, subs, early=0.1)
S.append(dict(type="poll", head="आज का Poll", q="आपका style कौन सा है?", opts=[["A", "Snowball"], ["B", "Avalanche"], ["C", "अभी कोई debt नहीं"]],
              ask="Comment में A, B या C लिखिए", note="सिर्फ़ जानने के लिए · कोई सलाह नहीं",
              rev=[0.0, round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[5] / dur, 4)], opt_rev=[round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 7 outro
subs = ["काम का लगा तो *Save* कीजिए।", "यह video उस दोस्त को *Send* कीजिए, जो हर महीने बस *minimum due* भरता है।", "*Follow* कीजिए *TheSDTrader*।",
        "हम *SEBI registered नहीं* हैं। यह जानकारी सिर्फ़ *educational* है, *financial advice नहीं*।"]
S.append(dict(type="outro", tag="Reality Check · Hindi + English", cta=["SAVE", "SEND", "FOLLOW"], notice_hi="हम SEBI registered नहीं हैं।",
              notice_en="Educational purposes only · Not financial advice", tail=0.8, rev=[0.04, rev(7, subs, [3], tail=0.8)[0]], subs=subs))
spec = dict(brand="TheSDTrader", tagline="Educational · शैक्षणिक जानकारी · Not advice", face="assets/face_original.png",
            voice_tempo=TEMPO, lead=LEAD, pad=PAD, music_vol=0.2, sfx_vol=0.4, voice_vol=1.5, day_tag="REALITY CHECK · DAY 8",
            theme=dict(BG=[254, 250, 243], bg_delta=[-10, -18, -31], WHITE=[18, 30, 74], MUTED=[112, 102, 84], GOLD=[190, 138, 46], CARD=[255, 255, 255],
                       CARD2=[232, 218, 188], DARK=[18, 30, 74], BLUE=[255, 236, 200], ORANGE=[217, 89, 38], GREEN=[13, 159, 110], RED=[214, 60, 60],
                       PW=[255, 255, 255], SUB_HL=[255, 214, 120], BRANDC=[18, 30, 74], SLAB=[226, 214, 194],
                       SER3=[[42, 120, 214], [217, 89, 38], [13, 159, 110]]),
            cover=dict(style="s5", serif=True, face="card", tag="REALITY CHECK · EP 8", l1="Minimum Due?", l2="19-Yr Trap.", mid="THE DEBT TRAP", graphic="steps",
                       gtitle="₹1L CARD · MIN DUE ONLY", gvals=[1.0, 3.04], glabs=["BORROWED", "TOTAL PAID"], gfmt="₹{:.1f}L", gfoot="ILLUSTRATIVE · NOT ADVICE",
                       badge="", va="", vb="", src="Own calculation",
                       hook=[["", [["बस ", False], ["minimum due", True], [" भरते हैं?", False]]], ["", [["₹1 लाख = ", False], ["₹3 लाख", True], [" का जाल।", False]]]]),
            scenes=S)
json.dump(spec, open(os.path.join(HERE, "spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", sum(vdur(i) + LEAD + PAD for i in range(1, 8)) + 0.8)
