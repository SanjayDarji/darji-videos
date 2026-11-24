import json, wave, os
HERE = os.path.dirname(os.path.abspath(__file__))
TEMPO, LEAD, PAD = 1.08, 0.12, 0.15

def vdur(i):
    w = wave.open(os.path.join(HERE, "voice", f"s{i}.wav")); return w.getnframes() / w.getframerate() / TEMPO

def starts(i, subs, tail=0.0, early=0.0):
    """return (list of absolute-in-scene seconds when each sub starts, dur)"""
    vd = vdur(i); dur = LEAD + vd + PAD + tail
    wts = [len(x.replace("*", "")) for x in subs]; tot = float(sum(wts)); out = []; c = 0
    for w in wts:
        out.append(max(0.0, LEAD + vd * (c / tot) - early)); c += w
    return out, dur

def rev(i, subs, idxs, tail=0.0, early=0.12, delay=None):
    st, dur = starts(i, subs, tail, early)
    return [round(st[k] / dur, 4) for k in idxs]

S = []
# 1 hook
subs = ["पोर्टफोलियो में *8 फंड* और *15 शेयर*?", "यह निवेश है या *भेल-पूरी*?", "ज़्यादा फंड मतलब ज़्यादा *सेफ़्टी*, ऐसा सोचते हैं?", "चलिए, *असली डेटा* देखते हैं।"]
st, _ = starts(1, subs, early=0.1)
S.append(dict(type="isohook", line1="8 फंड + 15 शेयर?", line2="निवेश या भेल-पूरी?", size1=64, size2=84,
              chips=["ज़्यादा फंड", "ज़्यादा सेफ़्टी?"], chip_t=[round(st[2], 2), round(st[2] + 1.0, 2)],
              note="चित्र सिर्फ़ उदाहरण के लिए · काल्पनिक", rev=rev(1, subs, [0, 1]), subs=subs))
# 2 overlap
subs = ["देश के दो सबसे बड़े *फ्लेक्सी-कैप* फंड: पराग पारीख और HDFC।",
        "अप्रैल 2026 के डेटा में पराग पारीख का करीब *43%* हिस्सा HDFC के साथ *ओवरलैप* करता है।",
        "दोनों में HDFC बैंक, ICICI बैंक और *Axis बैंक* बड़े शेयर हैं।"]
st, dur = starts(2, subs, early=0.1)
S.append(dict(type="isocmp", vs=["पराग पारीख", "HDFC"], badge=43, badge_cap="HDFC फ्लेक्सी कैप के साथ ओवरलैप", col_name="पराग पारीख फ्लेक्सी कैप · पूरा पोर्टफोलियो = 100%",
              seg1="HDFC से ओवरलैप", seg2="बाकी हिस्सा", chips_head="साझा बड़े शेयर · वज़न: पराग पारीख | HDFC",
              chips=[["HDFC Bank", "7.68% | 5.88%"], ["ICICI Bank", "5.12% | 4.95%"], ["Axis Bank", "4.15% | 2.62%"]],
              note="डेटा: अप्रैल 2026 · स्रोत: Business Today (9 जून 2026)",
              rev=[0.0, round(st[1] / dur, 4), round((st[1] + (st[2] - st[1]) * 0.55) / dur, 4), round(st[2] / dur, 4)], subs=subs))
# 3 same AMC
subs = ["और एक ही फंड हाउस के अंदर?", "30 सितंबर 2026 के डेटा में HDFC फ्लेक्सी कैप का HDFC लार्ज कैप से ओवरलैप करीब *43%* है।",
        "और टैक्स सेवर फंड से *63%* से ज़्यादा।", "यानी फंड दो, पर *कई शेयर वही*।"]
S.append(dict(type="isobars", title="HDFC फ्लेक्सी कैप का ओवरलैप", sub="एक ही फंड हाउस की दूसरी स्कीमों के साथ", step=118, hl=[0, 2], fmt="{:.2f}%",
              rows=[["vs Tax Saver", 63.22], ["vs Value", 44.66], ["vs Large Cap", 43.29], ["vs Dividend Yield", 41.71], ["vs Multi Cap", 38.39]],
              note="डेटा: 30 सितंबर 2026 · स्रोत: Upstox", rev=rev(3, subs, [0, 1]), subs=subs))
# 4 lesson
subs = ["ध्यान रखिए। *ओवरलैप* का मतलब फंड खराब होना नहीं है।", "पर दो फंड रखने से *दुगनी डाइवर्सिफ़िकेशन* नहीं मिलती।",
        "अगस्त 2026 से हर फंड हाउस अपनी स्कीमों का ओवरलैप *हर महीने* बताता है।", "अपने फंड्स के *टॉप 10 शेयर* मिलाकर देखिए।"]
S.append(dict(type="lesson", rows=[dict(t="ओवरलैप ≠ खराब फंड", s="OVERLAP ≠ A BAD FUND"), dict(t="2 फंड ≠ 2× फ़ैलाव", s="TWO FUNDS ≠ 2× SPREAD"),
              dict(t="हर महीने ओवरलैप रिपोर्ट", s="CHECK YOUR TOP-10 OVERLAP")], rev=rev(4, subs, [0, 1, 2]), subs=subs))
# 5 poll
subs = ["आज का *पोल*।", "आपके पास कितने *म्यूचुअल फंड* हैं?", "*A*: 1 से 3।", "*B*: 4 से 7।", "*C*: 8 या ज़्यादा।", "*कमेंट* में लिखिए।"]
st, dur = starts(5, subs, early=0.1)
S.append(dict(type="poll", head="आज का पोल", q="आपके पास कितने म्यूचुअल फंड हैं?", opts=[["A", "1 से 3 फंड"], ["B", "4 से 7 फंड"], ["C", "8 या ज़्यादा"]],
              ask="कमेंट में A, B या C लिखिए", note="सिर्फ़ जानने के लिए · कोई सलाह नहीं",
              rev=[0.0, round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[5] / dur, 4)], opt_rev=[round(st[2] / dur, 4), round(st[3] / dur, 4), round(st[4] / dur, 4)], subs=subs))
# 6 outro
subs = ["काम का लगा तो *Save* कीजिए।", "ये वीडियो किसी ऐसे दोस्त को *Send* कीजिए, जिसके पास बहुत सारे फंड हैं।", "Follow कीजिए *TheSDTrader*।",
        "हम *SEBI रजिस्टर्ड नहीं* हैं। जानकारी सिर्फ़ *शैक्षणिक* है, निवेश सलाह नहीं।"]
S.append(dict(type="outro", tag="Reality Check · हिंदी में", cta=["SAVE", "SEND", "FOLLOW"], notice_hi="हम SEBI रजिस्टर्ड नहीं हैं।",
              notice_en="Educational purposes only · Not investment advice", tail=0.8, rev=[0.04, rev(6, subs, [3], tail=0.8)[0]], subs=subs))

spec = dict(brand="TheSDTrader", tagline="शैक्षणिक जानकारी · निवेश सलाह नहीं", face="assets/face_original.png",
            voice_tempo=TEMPO, lead=LEAD, pad=PAD, music_vol=0.2, sfx_vol=0.4, voice_vol=1.5, day_tag="REALITY CHECK · DAY 1",
            theme=dict(BG=[254, 250, 243], bg_delta=[-10, -18, -31], WHITE=[18, 30, 74], MUTED=[112, 102, 84], GOLD=[190, 138, 46], CARD=[255, 255, 255],
                       CARD2=[232, 218, 188], DARK=[18, 30, 74], BLUE=[255, 236, 200], ORANGE=[217, 89, 38], GREEN=[13, 159, 110], RED=[214, 60, 60],
                       PW=[255, 255, 255], SUB_HL=[255, 214, 120], BRANDC=[18, 30, 74], SLAB=[226, 214, 194],
                       SER3=[[42, 120, 214], [217, 89, 38], [13, 159, 110]]),
            cover=dict(style="s5", serif=True, face="card", tag="REALITY CHECK · EP 1", l1="Diversified", l2="or Duplicated?", mid="43% OVERLAP", badge="43%", va="PPFAS", vb="HDFC",
                       src="Data: Business Today · Apr 2026", hook=[["", [["आपके 8 फंड, कहीं ", False]]], ["", [["एक जैसे", True], [" तो नहीं?", False]]]]),
            scenes=S)
json.dump(spec, open(os.path.join(HERE, "spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", sum(vdur(i) + LEAD + PAD for i in range(1, 7)) + 0.8)
