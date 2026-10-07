#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""会津駒ヶ岳・毛無山の運賃を確定する（2026-10-07）。
出典：
- 会津駒ヶ岳：会津バス公式検索（aizubus.info、2026/10/07現在）会津田島駅→駒ヶ岳登山口 2,330円・約1時間28分
  Yahoo!路線情報（リバティ会津113号）新宿→会津田島 6,243円（西日暮里・千代田線経由、乗車券3,553＋特急2,690）、
  大宮→会津田島 5,610円（春日部乗車、3,120＋2,490）、横浜→会津田島 6,530円（上野・常磐線経由、3,840＋2,690）
- 毛無山：Yahoo!路線情報 →富士宮 新宿2,750円（品川・熱海・富士乗換）／大宮3,520円／横浜2,380円、
  NAVITIME 富士宮駅→朝霧高原 1,080円・32分（富士急バス 新富士線 富士山駅行き、1日3便）
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-07'
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))


def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')


def yen(n):
    return format(n, ',') + '円'


def sync(m, fares, drop):
    R = m['trainRoutes']['routes']
    for dep, K in DEPS:
        m['fare' + K] = fares[dep]
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    keep = [n for n in (m.get('verifyNotes') or []) if not any(k in n for k in drop)]
    m['verifyNotes'] = keep
    m['needsVerification'] = bool(keep)
    m['mountainUpdated'] = V
    m['fareCheckedAt'] = V


def set_faq(m, text):
    hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
    assert len(hit) == 1, m['id']
    hit[0]['answer'] = text


def times(m):
    return tuple(hm(m['trainTime' + K]) for _, K in DEPS)


m = N['aizu_koma']
R = m['trainRoutes']['routes']
for dep in R:
    b = [l for l in R[dep]['legs'] if l['station'] == '会津田島駅']
    assert len(b) == 1
    b[0]['durationMin'] = 88
y = R['yokohama']['legs'][0]
assert y['station'] == '横浜駅'
y['method']['line'] = 'JR上野東京ライン・常磐線（上野乗換）'
sync(m, {'shinjuku': 8573, 'omiya': 7940, 'yokohama': 8860}, ['運賃合計が未検算'])
t = times(m)
set_faq(m, '東武特急リバティ会津で会津田島駅へ行き、会津バスで駒ヶ岳登山口バス停まで約1時間30分、そこから滝沢登山口まで徒歩約30分です。'
        f'新宿からは北千住で特急に乗り{t[0]}・{yen(m["fareShinjuku"])}、大宮からは春日部で特急に乗り{t[1]}・{yen(m["fareOmiya"])}、横浜からは{t[2]}・{yen(m["fareYokohama"])}が目安です（乗り換えの待ち時間は別）。'
        'バスは5月1日〜10月31日の運行です。車の場合は都心から約4時間55分が目安です。')

m = N['kenashiyama']
for dep in m['trainRoutes']['routes']:
    b = m['trainRoutes']['routes'][dep]['legs'][-2]
    assert b['station'] == '富士宮駅'
    b['method']['line'] = '富士急バス（新富士線・富士山駅行き）'
sync(m, {'shinjuku': 3830, 'omiya': 4600, 'yokohama': 3460}, ['運賃'])
t = times(m)
set_faq(m, 'JR身延線の富士宮駅から富士急バス（富士山駅行き）で朝霧高原へ向かいます（約32分）。'
        f'新宿からは東海道線・身延線（熱海・富士乗換）で{t[0]}・{yen(m["fareShinjuku"])}、大宮からは上野東京ラインで{t[1]}・{yen(m["fareOmiya"])}、横浜からは東海道線で{t[2]}・{yen(m["fareYokohama"])}が目安です。'
        'バスは1日3便ほどのため、時刻を確認してから出かけてください。')

json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ['aizu_koma', 'kenashiyama']:
    m = N[i]
    print(i, m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'], m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'], m['verifyNotes'])
