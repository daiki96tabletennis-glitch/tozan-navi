#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小田急線・東海道線の組の運賃検算（方針B）。2026-10-07
出典：Yahoo!路線情報（2026-10-17 発、IC運賃）
  →渋沢：新宿692円（小田急）／横浜648円（相鉄＋小田急）。渋沢駅北口〜大倉 270円（神奈川中央交通）
  →伊勢原：新宿607円／横浜554円（相鉄で海老名、小田急に乗換。07:27→08:15）。伊勢原駅北口〜大山ケーブル 370円
  →二宮（JRのみ）：新宿1,408円（湘南新宿ライン直通75分）／大宮2,090円（上野東京ライン直通100分）／横浜803円（43分）
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
def leg(station, icon, line, minutes):
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
def tail_from(m, dep, gw):
    legs = m['trainRoutes']['routes'][dep]['legs']
    idx = [i for i, l in enumerate(legs) if l['station'] == gw]
    assert len(idx) == 1, (m['id'], dep)
    return legs[idx[0]:]

# 大山：横浜発が「JR東海道線で伊勢原」になっていた（伊勢原は東海道線の駅ではない）。相鉄＋小田急に直す
m = N['oyama']
m['trainRoutes']['routes']['yokohama']['legs'] = [leg('横浜駅', 'train', '相鉄本線特急', 28), leg('海老名駅', 'train', '小田急小田原線', 14)] + tail_from(m, 'yokohama', '伊勢原駅')
assert (m['fareShinjuku'], m['fareOmiya'], m['fareYokohama']) == (980, 1508, 1023)
m['fareYokohama'] = 924
m['trainRoutes']['summaryNote'] = '※運賃は電車＋バス370円（伊勢原駅北口〜大山ケーブル）の合計。バスは約20〜30分間隔で運行'
resync(m)
q = [q for q in m['faq'] if 'アクセス' in q['question']]
assert len(q) == 1
q[0]['answer'] = (f'小田急線の伊勢原駅から神奈川中央交通バスで大山ケーブルまで約25分です。新宿からは小田急線で{hm(m["trainTimeShinjuku"])}・980円、'
                  f'大宮からは新宿で小田急線に乗り換えて{hm(m["trainTimeOmiya"])}・1,508円、横浜からは相鉄線で海老名に出て小田急線に乗り換え、{hm(m["trainTimeYokohama"])}・924円が目安です。'
                  '車の場合は都心から約45分が目安です。')

# 吾妻山：経路表はJR東海道線なのに、運賃が小田急経由の額だった。JR直通の運賃に直す
m = N['azumayama_ninomiya']
R = m['trainRoutes']['routes']
R['shinjuku']['legs'] = [leg('新宿駅', 'train', 'JR湘南新宿ライン（東海道線直通）', 75)] + tail_from(m, 'shinjuku', '二宮駅')
R['omiya']['legs'] = [leg('大宮駅', 'train', 'JR上野東京ライン（東海道線直通）', 100)] + tail_from(m, 'omiya', '二宮駅')
R['yokohama']['legs'] = [leg('横浜駅', 'train', 'JR東海道線', 43)] + tail_from(m, 'yokohama', '二宮駅')
m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'] = 1408, 2090, 803
m['trainRoutes']['note'] = '💡 新宿・大宮からは東海道線に直通する列車で乗り換えなし。新宿からは小田急線で藤沢に出て東海道線に乗り換えると、約1,050円と安くなる（所要約1時間30分）'
resync(m)
q = [q for q in m['faq'] if 'アクセス' in q['question']]
assert len(q) == 1
q[0]['answer'] = (f'JR東海道線の二宮駅から徒歩約5分で吾妻山公園の入口です。新宿からは湘南新宿ラインの東海道線直通で{hm(m["trainTimeShinjuku"])}・1,408円、'
                  f'大宮からは上野東京ラインで{hm(m["trainTimeOmiya"])}・2,090円、横浜からは{hm(m["trainTimeYokohama"])}・803円が目安です。')

ok = [x['id'] for x in D if x['name'] in ('丹沢山', '塔ノ岳', '蛭ヶ岳', '鍋割山', '三ノ塔')]
assert len(ok) == 5, ok
for i in ok: N[i]['fareCheckedAt'] = V
for name, note in (('矢倉岳', '新松田まで新宿796円／横浜711円（小田急・相鉄）は確認。新松田駅〜地蔵堂のバス運賃と、横浜発（大雄山駅経由）の運賃が未確認'),
                   ('大野山', '新松田まで796円は確認。松田〜山北のJR運賃と横浜発（国府津経由）が未確認')):
    x = [y for y in D if y['name'] == name][0]
    x['needsVerification'] = True; x['verifyNotes'] = (x.get('verifyNotes') or []) + [note]
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ('oyama', 'azumayama_ninomiya'):
    x = N[i]; print(i, x['trainTimeShinjuku'], x['trainTimeOmiya'], x['trainTimeYokohama'], x['fareShinjuku'], x['fareOmiya'], x['fareYokohama'])
