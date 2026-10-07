#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""荒沢岳の運賃検算、安達太良山のバス所要時間の修正、雨飾山ほかの確認記録（2026-10-07）。
出典：Yahoo!路線情報（2026-10-17 発、新幹線は自由席）
  →浦佐：新宿6,820円（大宮乗換）／大宮6,160円／横浜8,360円（東京08:48発とき309号→10:32）
  →二本松：新宿7,260円（大宮・郡山乗換）／大宮6,490円／横浜8,800円
  →南小谷：大宮8,490円／横浜8,270円（特急あずさ5号、白馬乗換）
  南越後交通バス 運賃表「特急・急行 浦佐駅東口〜折立〜奥只見ダム線」：浦佐駅東口〜銀山平舟付場 1,200円（奥只見ダムまでは1,500円）
  福島交通：二本松駅前→奥岳 800円・45分（08:13発→08:58着）
"""
import json, os, sys, copy
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-07'
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))
def leg(station, icon=None, line=None, minutes=None):
    if icon is None: return {'station': station}
    return {'station': station, 'method': {'icon': icon, 'line': line}, 'durationMin': minutes, 'fareYen': None}
def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')
def resync(m):
    R = m['trainRoutes']['routes']
    for dep, K in DEPS:
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    m['mountainUpdated'] = V; m['fareCheckedAt'] = V

# 荒沢岳：バスは銀山平まで1,200円（1,500円は奥只見ダムまでの額）。横浜発は東京で新幹線に乗る
m = N['arasawadake']
tail = [leg('浦佐駅', 'bus', '南越後交通バス急行(浦佐駅－奥只見ダム線)', 58), leg('銀山平(舟付場)')]
R = m['trainRoutes']['routes']
R['shinjuku']['legs'] = [leg('新宿駅', 'train', 'JR埼京線・湘南新宿ライン', 30), leg('大宮駅', 'train', 'JR上越新幹線(とき)', 52)] + copy.deepcopy(tail)
R['omiya']['legs'] = [leg('大宮駅', 'train', 'JR上越新幹線(とき)', 52)] + copy.deepcopy(tail)
R['yokohama']['legs'] = [leg('横浜駅', 'train', 'JR上野東京ライン', 29), leg('東京駅', 'train', 'JR上越新幹線(とき)', 104)] + copy.deepcopy(tail)
m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'] = 8020, 7360, 9560
m['trainRoutes']['summaryNote'] = '※運賃はJR（新幹線は自由席）＋バス1,200円の合計。銀山平に停まるのは午後の急行便だけ（朝の特急便は通過）'
resync(m)
hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
assert len(hit) == 1
hit[0]['answer'] = (f'上越新幹線で浦佐駅へ行き、南越後交通バスの急行（浦佐駅〜奥只見ダム線）で銀山平まで約58分です。'
                    f'新宿からは大宮で新幹線に乗り換えて{hm(m["trainTimeShinjuku"])}・8,020円、大宮から{hm(m["trainTimeOmiya"])}・7,360円、横浜からは東京で新幹線に乗り換えて{hm(m["trainTimeYokohama"])}・9,560円が目安です（乗り換えの待ち時間は別）。'
                    'バスは2026年は6月1日〜11月3日の土日祝と8月13〜16日だけの運行です。')

# 安達太良山：運賃は現行で整合（JR＋バス800円）。バスの所要時間だけ30分→45分
m = N['adatara']
old = {K: m['trainTime' + K] for _, K in DEPS}
for dep, _ in DEPS:
    hit = [l for l in m['trainRoutes']['routes'][dep]['legs'] if l['station'] == '二本松駅']
    assert len(hit) == 1 and hit[0]['durationMin'] == 30, dep
    hit[0]['durationMin'] = 45
resync(m)
q = [q for q in m['faq'] if 'アクセス方法' in q['question']][0]
for a_, K in (('約2時間55分', 'Shinjuku'), ('約2時間10分', 'Omiya'), ('約3時間15分', 'Yokohama')):
    assert a_ in q['answer'], a_
    q['answer'] = q['answer'].replace(a_, hm(m['trainTime' + K]))

# 雨飾山：大宮・横浜発はJR分が一致。バス「約600円」は未確認
m = N['amakazari']
m['fareCheckedAt'] = V
m['needsVerification'] = True
m['verifyNotes'] = (m.get('verifyNotes') or []) + ['南小谷駅〜雨飾高原の村営バスの運賃（約600円）が未確認。新宿発のJR運賃は未照合（大宮8,490円・横浜8,270円は一致）']
for mid, text in (('echigokoma', '運賃合計が未検算。小出駅までの運賃と、小出駅〜枝折峠のバス（680円・運行の有無）が未確認'),
                  ('makihata', '運賃合計が未検算。六日町駅までの運賃と、MOSSの運賃（距離別。約300円との記載は未確認）が未確認')):
    N[mid]['needsVerification'] = True
    N[mid]['verifyNotes'] = (N[mid].get('verifyNotes') or []) + [text]
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ('arasawadake', 'adatara'):
    x = N[i]; print(i, x['trainTimeShinjuku'], x['trainTimeOmiya'], x['trainTimeYokohama'], x['fareShinjuku'], x['fareOmiya'], x['fareYokohama'])
