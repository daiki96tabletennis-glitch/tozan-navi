#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""太平山・鋸山の運賃検算と、東武東上線・秩父鉄道・宇都宮の組の確認記録（方針B）。2026-10-07
出典：Yahoo!路線情報（2026-10-17 発、IC運賃、JRだけの経路）
  →栃木（小山・両毛線経由）：新宿1,595円／大宮1,221円／横浜2,420円
  →浜金谷：新宿2,090円（錦糸町・木更津乗換 07:41→10:10）／大宮2,420円（東京・木更津乗換 07:12→10:10）／横浜2,420円（木更津乗換 07:33→10:10）
  →宇都宮：新宿2,090円／大宮1,408円／横浜2,420円（＋関東自動車バス640円＝古賀志山の現行額と一致）
  東武東上線：池袋〜武蔵嵐山743円・小川町827円、大宮〜武蔵嵐山770円・小川町822円（川越乗換）
  秩父鉄道：大宮→長瀞1,466円（JR616＋秩父鉄道850）、熊谷〜皆野900円、横浜→熊谷1,782円
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
def resync(m, fares):
    R = m['trainRoutes']['routes']
    for dep, K in DEPS:
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
        m['fare' + K] = fares[dep]
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    m['mountainUpdated'] = V; m['fareCheckedAt'] = V
def faq(m, text):
    hit = [q for q in m['faq'] if 'アクセス' in q['question']]
    assert len(hit) == 1, m['id']
    hit[0]['answer'] = text
def T(m): return hm(m['trainTimeShinjuku']), hm(m['trainTimeOmiya']), hm(m['trainTimeYokohama'])

# 太平山：3出発地とも1,000円以上高く載っていた
m = N['taiheizan']
assert (m['fareShinjuku'], m['fareOmiya'], m['fareYokohama']) == (3100, 2730, 3716)
resync(m, {'shinjuku': 1595, 'omiya': 1221, 'yokohama': 2420}); a, b, c = T(m)
faq(m, f'JR宇都宮線の小山駅で両毛線に乗り換えて栃木駅へ行き、駅から歩いて約30分で謙信平です。新宿からは湘南新宿ラインで{a}・1,595円、大宮から{b}・1,221円、横浜から{c}・2,420円が目安です（徒歩を含む。乗り換えの待ち時間は別）。')

# 鋸山：新宿発・横浜発が110円安く載っていた。大宮・横浜発の経路表記と所要時間も実際の乗り継ぎに合わせる
m = N['nokogiriyama_chiba']
R = m['trainRoutes']['routes']
def tail(dep):
    legs = R[dep]['legs']; idx = [i for i, l in enumerate(legs) if l['station'] == '浜金谷駅']; assert len(idx) == 1
    return legs[idx[0]:]
R['omiya']['legs'] = [leg('大宮駅', 'train', 'JR上野東京ライン・総武線快速・内房線（東京・木更津乗換）', 178)] + tail('omiya')
R['yokohama']['legs'] = [leg('横浜駅', 'train', 'JR横須賀線・総武線快速直通・内房線（木更津乗換）', 157)] + tail('yokohama')
resync(m, {'shinjuku': 2090, 'omiya': 2420, 'yokohama': 2420}); a, b, c = T(m)
faq(m, f'JR内房線の浜金谷駅が最寄りで、駅から登山口まで歩いて約15分です。新宿からは総武線快速で木更津に出て内房線に乗り換え、{a}・2,090円。'
       f'大宮からは東京と木更津で乗り換えて{b}・2,420円、横浜からは横須賀線・総武線快速の直通で木更津に出て{c}・2,420円が目安です。車の場合は都心から約1時間15分が目安です。')

ok = [x['id'] for x in D if x['name'] in ('嵐山', '官ノ倉山', '宝登山', '破風山', '古賀志山')]
assert len(ok) == 5, ok
for i in ok: N[i]['fareCheckedAt'] = V
for name in ('宝登山', '破風山'):
    x = [y for y in D if y['name'] == name][0]
    x['verifyNotes'] = (x.get('verifyNotes') or []) + ['新宿発（東武東上線で寄居、秩父鉄道）の運賃は未照合。大宮発・横浜発（熊谷経由）は一致']
x = [y for y in D if y['name'] == '官ノ倉山'][0]
x['verifyNotes'] = (x.get('verifyNotes') or []) + ['小川町駅〜パトリアおがわのバス運賃（現行の合計からは約240円）は未確認']
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ('taiheizan', 'nokogiriyama_chiba'):
    x = N[i]; print(i, x['trainTimeShinjuku'], x['trainTimeOmiya'], x['trainTimeYokohama'], x['fareShinjuku'], x['fareOmiya'], x['fareYokohama'])
