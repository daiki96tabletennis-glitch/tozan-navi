#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JRで乗り通す近郊4山の運賃検算（方針B：今の経路のまま、その経路の正しい運賃にする）。2026-10-07
出典：Yahoo!路線情報（2026-10-17 発、IC運賃、乗換回数順でJRだけの経路を確認）
  →北鎌倉：新宿1,034円（湘南新宿ライン直通56分）／大宮1,408円（直通86分）／横浜341円（横須賀線21分）
  →逗子：新宿1,034円（直通65分）／大宮1,595円（直通95分）／横浜440円（30分）
  →湯河原：新宿2,090円（湘南新宿ライン＋東海道線）／大宮2,420円（上野東京ライン直通 07:08→09:24）／横浜1,408円
  →岩井：新宿2,090円／大宮2,750円（東京・木更津乗換 07:12→10:22）／横浜2,750円（木更津乗換 07:33→10:22）
  バス：逗子駅→前田橋 377円（IC）・23分（京急バス）、湯河原駅→幕山公園 290円・18分（箱根登山バス）、岩井駅→天神郷 200円（南房総市営バス富山線）
大宮発が「新宿発＋528円」の足し算になっていたのを、通しの運賃に直す。
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
def rebuild(m, gw, heads, fares, bus_min=None):
    R = m['trainRoutes']['routes']
    for dep, K in DEPS:
        legs = R[dep]['legs']
        idx = [i for i, l in enumerate(legs) if l['station'] == gw]
        assert len(idx) == 1, (m['id'], dep)
        tail = legs[idx[0]:]
        if bus_min: tail[0]['durationMin'] = bus_min
        R[dep]['legs'] = heads[dep] + tail
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
        m['fare' + K] = fares[dep]
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    m['mountainUpdated'] = V; m['fareCheckedAt'] = V
    m['verifyNotes'] = [x for x in (m.get('verifyNotes') or []) if '単純な足し算' not in x]
def faq(m, text):
    hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
    assert len(hit) == 1, m['id']
    hit[0]['answer'] = text
def T(m): return hm(m['trainTimeShinjuku']), hm(m['trainTimeOmiya']), hm(m['trainTimeYokohama'])

m = N['kamakura_alps']
rebuild(m, '北鎌倉駅', {'shinjuku': [leg('新宿駅', 'train', 'JR湘南新宿ライン', 56)], 'omiya': [leg('大宮駅', 'train', 'JR湘南新宿ライン（直通）', 86)],
                       'yokohama': [leg('横浜駅', 'train', 'JR横須賀線', 21)]}, {'shinjuku': 1034, 'omiya': 1408, 'yokohama': 341})
a, b, c = T(m)
faq(m, f'JR北鎌倉駅から徒歩約10分で天園ハイキングコースの入口です。新宿からは湘南新宿ラインの逗子行きで乗り換えなし、{a}・1,034円。'
       f'大宮からも同じ列車で{b}・1,408円、横浜からは横須賀線で{c}・341円が目安です。直通の逗子行きがない時間帯は、戸塚か大船で横須賀線に乗り換えます。')

m = N['okusuyama']
rebuild(m, '逗子駅', {'shinjuku': [leg('新宿駅', 'train', 'JR湘南新宿ライン', 65)], 'omiya': [leg('大宮駅', 'train', 'JR湘南新宿ライン（直通）', 95)],
                      'yokohama': [leg('横浜駅', 'train', 'JR横須賀線', 30)]}, {'shinjuku': 1411, 'omiya': 1972, 'yokohama': 817}, bus_min=23)
a, b, c = T(m)
faq(m, f'JR逗子駅から京急バス（長井方面行き）で前田橋まで約23分、そこから登山口まで歩きます。'
       f'新宿からは湘南新宿ラインの逗子行きで{a}・1,411円、大宮から{b}・1,972円、横浜からは横須賀線で{c}・817円が目安です（徒歩を含む。乗り換えの待ち時間は別）。')

m = N['makuyama']
rebuild(m, '湯河原駅', {'shinjuku': [leg('新宿駅', 'train', 'JR湘南新宿ライン・東海道本線', 109)], 'omiya': [leg('大宮駅', 'train', 'JR上野東京ライン（直通）', 136)],
                        'yokohama': [leg('横浜駅', 'train', 'JR東海道線', 82)]}, {'shinjuku': 2380, 'omiya': 2710, 'yokohama': 1698}, bus_min=18)
a, b, c = T(m)
faq(m, f'JR湯河原駅から箱根登山バスで幕山公園まで約18分です。新宿からは湘南新宿ラインと東海道線で{a}・2,380円、大宮からは上野東京ラインの熱海行きで乗り換えなし、{b}・2,710円、横浜から{c}・1,698円が目安です。'
       'バスが「鍛冶屋橋」止まりの場合も、そこから徒歩約8分で幕山公園に着きます。新宿からは小田急線で小田原に出ると安くなります。')

m = N['iyogatake']
rebuild(m, '岩井駅', {'shinjuku': [leg('新宿駅', 'train', 'JR中央線・総武線快速', 55), leg('千葉駅', 'train', 'JR内房線', 114)],
                      'omiya': [leg('大宮駅', 'train', 'JR上野東京ライン・総武線快速・内房線（東京・木更津乗換）', 190)],
                      'yokohama': [leg('横浜駅', 'train', 'JR横須賀線・総武線快速直通・内房線（木更津乗換）', 169)]},
        {'shinjuku': 2290, 'omiya': 2950, 'yokohama': 2950})
a, b, c = T(m)
hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
assert len(hit) == 1
hit[0]['answer'] = (f'JR内房線の岩井駅から南房総市営バス「トミー号」で約20分、天神郷バス停で降り、徒歩5分で平群天神社（登山口）です。'
                    f'新宿から{a}・2,290円、大宮からは東京と木更津で乗り換えて{b}・2,950円、横浜からは横須賀線・総武線快速の直通で木更津へ出て{c}・2,950円が目安です。')
N['tomisan']['fareCheckedAt'] = V
N['tomisan']['verifyNotes'] = [x for x in (N['tomisan'].get('verifyNotes') or []) if '単純な足し算' not in x]
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ('kamakura_alps', 'okusuyama', 'makuyama', 'iyogatake'):
    x = N[i]; print(i, x['trainTimeShinjuku'], x['trainTimeOmiya'], x['trainTimeYokohama'], x['fareShinjuku'], x['fareOmiya'], x['fareYokohama'])
