#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""信濃大町駅・穂高駅を起点にする6山の運賃と経路の検算（2026-10-06）。
出典：Yahoo!路線情報（2026-10-17 発）
  →信濃大町：新宿・大宮・横浜とも7,610円（あずさ5号 新宿08:00→信濃大町11:14 直通。大宮は新宿、横浜は八王子08:33で同じ列車に乗る）
  →穂高：新宿・大宮・横浜とも7,170円（あずさ5号 新宿08:00→穂高10:59）
  アルピコ交通「信濃大町駅ー扇沢線 運賃表」（2026年4月15日改正）：信濃大町駅〜扇沢 2,000円、所要約40分
  裏銀座登山バス 1,500円、中房温泉行き定期バス 1,500円
"""
import json, os, sys, copy
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))
def leg(station, icon=None, line=None, minutes=None):
    if icon is None: return {'station': station}
    return {'station': station, 'method': {'icon': icon, 'line': line}, 'durationMin': minutes, 'fareYen': None}
def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')
def rebuild(m, gw, t_shinjuku, t_hachioji, fare, bus_min=None):
    """鉄道区間を特急あずさ（直通）に揃え、運賃を入れ直す。gw 以降の区間（バスなど）は既存のまま使う"""
    R = m['trainRoutes']['routes']
    tail = None
    for dep, _ in DEPS:
        legs = R[dep]['legs']
        idx = [i for i, l in enumerate(legs) if l['station'] == gw]
        assert len(idx) == 1, (m['id'], dep)
        t = copy.deepcopy(legs[idx[0]:])
        if bus_min: t[0]['durationMin'] = bus_min
        if tail is None: tail = t
    R['shinjuku']['legs'] = [leg('新宿駅', 'train', 'JR特急あずさ', t_shinjuku)] + copy.deepcopy(tail)
    R['omiya']['legs'] = [leg('大宮駅', 'train', 'JR湘南新宿ライン', 31), leg('新宿駅', 'train', 'JR特急あずさ', t_shinjuku)] + copy.deepcopy(tail)
    R['yokohama']['legs'] = [leg('横浜駅', 'train', 'JR横浜線', 60), leg('八王子駅', 'train', 'JR特急あずさ', t_hachioji)] + copy.deepcopy(tail)
    for dep, K in DEPS:
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
        m['fare' + K] = fare
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['mountainUpdated'] = '2026-10-06'
def finish(m, extra_note, faq_text):
    n0 = m['trainRoutes'].get('note') or ''
    m['trainRoutes']['note'] = n0.rstrip('。') + '。' + extra_note if n0 else '💡 ' + extra_note
    hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
    assert len(hit) == 1, m['id']
    hit[0]['answer'] = faq_text
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
DIRECT = '直通の特急あずさ（白馬行き）は1日1本だけ。ほかの列車は松本で大糸線に乗り換える'
def times(m):
    return (hm(m['trainTimeShinjuku']), hm(m['trainTimeOmiya']), hm(m['trainTimeYokohama']))

# 扇沢（針ノ木岳・鹿島槍ヶ岳）：7,610＋2,000＝9,610円
for mid in ('harinokidake', 'kashimayari'):
    m = N[mid]
    rebuild(m, '信濃大町駅', 194, 161, 9610, bus_min=40)
    a, b, c = times(m)
    finish(m, DIRECT + '。信濃大町駅〜扇沢のバスは約40分・2,000円（2026年4月改正）',
           f'JR大糸線の信濃大町駅からアルピコ交通の扇沢線（2026年は4月15日〜11月30日）で扇沢へ向かいます。'
           f'新宿からは特急あずさで{a}、大宮からは新宿で特急に乗り{b}、横浜からは八王子で特急に乗り{c}が目安で、運賃はいずれも9,610円です（乗り換えの待ち時間は別）。')
# 七倉・高瀬ダム（烏帽子岳・野口五郎岳）：7,610＋1,500＝9,110円（タクシー代は別）
for mid in ('eboshidake_kita', 'noguchigoro'):
    m = N[mid]
    rebuild(m, '信濃大町駅', 194, 161, 9110)
    a, b, c = times(m)
    m['trainRoutes']['summaryNote'] = '※運賃は七倉までの片道（七倉〜高瀬ダムのタクシー代は別）'
    finish(m, DIRECT,
           f'{m["name"]}へは、特急あずさで信濃大町駅へ行き、裏銀座登山バスで七倉へ、そこから許可車両のタクシーで高瀬ダムへ入ります。'
           f'新宿から{a}、大宮から{b}、横浜から{c}が目安で、運賃はいずれも9,110円です（七倉までの額。タクシー代と乗り換えの待ち時間は別）。'
           'バスは2026年は7月17日〜10月25日の特定日だけの運行です。')
# 中房温泉（有明山・大天井岳）：7,170＋1,500＝8,670円
for mid in ('arikayama', 'otenshoudake'):
    m = N[mid]
    rebuild(m, '穂高駅', 179, 146, 8670)
    a, b, c = times(m)
    finish(m, DIRECT,
           f'特急あずさで穂高駅へ行き、中房温泉行きの定期バスで約55分です。'
           f'新宿から{a}、大宮からは新宿で特急に乗り{b}、横浜からは八王子で特急に乗り{c}が目安で、運賃はいずれも8,670円です（乗り換えの待ち時間は別）。'
           'バスは2026年は4月24日〜11月3日の所定日だけの運行です。')
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ('harinokidake', 'kashimayari', 'eboshidake_kita', 'noguchigoro', 'arikayama', 'otenshoudake'):
    x = N[i]; print(i, x['trainTimeShinjuku'], x['trainTimeOmiya'], x['trainTimeYokohama'], x['fareShinjuku'], x['fareOmiya'], x['fareYokohama'])
