#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""浅間山・白砂山・筑波山の運賃検算と、高速バスの山の確認記録（方針B）。2026-10-07
出典：Yahoo!路線情報（2026-10-17 発）
  →佐久平：大宮5,060円（自由席、07:17→08:13）／横浜6,370円（東京07:52発はくたか553号→09:08）
  →つくば：新宿1,489円（JR秋葉原まで209＋TX1,280）／大宮1,529円（JR南流山まで616＋TX913）／横浜1,896円（JR秋葉原まで616＋TX1,280）
  NAVITIME：JRバス関東 高峰高原線 佐久平駅→高峰高原ホテル前 1,450円・54分、小諸駅→同 1,100円・34分
  関東鉄道 筑波山シャトル：つくばセンター〜筑波山神社入口 770円
"""
import json, os, sys
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
def resync(m, times=True):
    R = m['trainRoutes']['routes']
    if times:
        for dep, K in DEPS:
            m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    m['mountainUpdated'] = V; m['fareCheckedAt'] = V
def faq_one(m):
    hit = [q for q in m['faq'] if 'アクセス' in q['question']]
    assert len(hit) == 1, m['id']
    return hit[0]

# 浅間山：大宮・横浜発が「佐久平→しなの鉄道→小諸」になっていた（佐久平はしなの鉄道の駅ではない）。佐久平駅から直通のバスに直す
m = N['asama']
tail = [leg('佐久平駅', 'bus', 'JRバス関東「高峰高原線」', 54), leg('車坂峠（高峰高原ホテル前）')]
m['trainRoutes']['routes']['omiya']['legs'] = [leg('大宮駅', 'train', '北陸新幹線', 56)] + [dict(x) for x in tail]
m['trainRoutes']['routes']['yokohama']['legs'] = [leg('横浜駅', 'train', 'JR上野東京ライン', 29), leg('東京駅', 'train', '北陸新幹線', 76)] + [dict(x) for x in tail]
assert (m['fareShinjuku'], m['fareOmiya'], m['fareYokohama']) == (3100, 6325, 7635)
m['fareOmiya'], m['fareYokohama'] = 6510, 7820
m['trainRoutes']['summaryNote'] = '※大宮・横浜発の運賃は新幹線（自由席）＋佐久平駅からのバス1,450円の合計。新宿発は高速バスの額'
resync(m)
q = faq_one(m)
q['answer'] = (f'新宿からはバスタ新宿発の高速バスで小諸駅へ行き、JRバス関東「高峰高原線」に乗り換えて車坂峠（高峰高原ホテル前）へ。{hm(m["trainTimeShinjuku"])}・3,100円が目安です。'
               f'大宮からは北陸新幹線で佐久平駅へ行き、駅から同じバスで約54分、{hm(m["trainTimeOmiya"])}・6,510円。横浜からは東京で新幹線に乗り換えて{hm(m["trainTimeYokohama"])}・7,820円が目安です（乗り換えの待ち時間は別）。'
               'バスは1日数便のみです。車の場合は都心から約3時間15分が目安です。')
m['verifyNotes'] = (m.get('verifyNotes') or []) + ['新宿発の高速バス（新宿〜小諸）の運賃は注記の値で、事業者では未再確認']

# 白砂山：大宮・横浜発は新宿までのJR（530円・620円）を足す。現行は2出発地とも5,550円だった
m = N['shirasunayama']
assert (m['fareShinjuku'], m['fareOmiya'], m['fareYokohama']) == (4970, 5550, 5550)
m['fareOmiya'], m['fareYokohama'] = 5500, 5590
resync(m, times=False)
q = faq_one(m)
a = '大宮・横浜からは新宿経由でさらに30〜35分プラス。'
assert a in q['answer']
q['answer'] = q['answer'].replace(a, '大宮からは新宿まで出て約5,500円、横浜からは約5,590円で、新宿発より30〜35分多くかかります。')

# 筑波山：横浜発だけ古いつくばエクスプレスの運賃で計算されていた
m = N['tsukuba']
assert (m['fareShinjuku'], m['fareOmiya'], m['fareYokohama']) == (2259, 2299, 2608)
m['fareYokohama'] = 2666
m['trainRoutes']['summaryNote'] = ('※運賃は電車＋筑波山シャトル770円の合計。新宿・横浜は秋葉原、大宮は南流山でつくばエクスプレスに乗り換える。'
                                   '筑波山シャトルは通年運行で、時期により本数が変わる')
resync(m, times=False)
q = faq_one(m)
assert '運賃約2,608円' in q['answer']
q['answer'] = q['answer'].replace('運賃約2,608円', '運賃約2,666円')

for name in ('金時山', '笠ヶ岳'):
    x = [y for y in D if y['name'] == name][0]
    x['fareCheckedAt'] = V
    x['verifyNotes'] = (x.get('verifyNotes') or []) + ['高速バスの運賃は注記の値で、事業者では未再確認。大宮・横浜発は新宿までのJR（530円・620円）を足す計算で整合']
x = [y for y in D if y['name'] == '空木岳'][0]
x['needsVerification'] = True
x['verifyNotes'] = (x.get('verifyNotes') or []) + ['運賃合計が未検算。高速バス（新宿〜駒ヶ根）は日によって運賃が変わり、駒ヶ根駅〜菅の台のバス運賃も未確認']
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ('asama', 'shirasunayama', 'tsukuba'):
    x = N[i]; print(i, x['trainTimeShinjuku'], x['trainTimeOmiya'], x['trainTimeYokohama'], x['fareShinjuku'], x['fareOmiya'], x['fareYokohama'])
