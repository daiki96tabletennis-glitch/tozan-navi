#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""鳳凰山・男体山の運賃検算、鳴虫山・天城山の確認記録（2026-10-07）。
出典：Yahoo!路線情報（2026-10-17 発）→甲府 4,000円／4,000円／3,440円（横浜は横浜線で八王子、特急は八王子乗車）
      山梨交通 甲府駅〜夜叉神峠登山口 1,760円・約1時間25分（2026年は6月26日〜11月3日）
      東武バス日光 東武日光駅〜二荒山神社中宮祠 1,400円・53分（NAVITIME）
      Yahoo!路線情報 →東武日光：横浜4,700円（新宿から特急日光21号）、→伊東：新宿4,090円／大宮4,450円（新幹線こだま利用）
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
def leg(station, icon, line, minutes):
    return {'station': station, 'method': {'icon': icon, 'line': line}, 'durationMin': minutes, 'fareYen': None}
def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')
def resync(m):
    R = m['trainRoutes']['routes']
    for dep, K in (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama')):
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    m['mountainUpdated'] = V; m['fareCheckedAt'] = V

# 鳳凰山：大宮・横浜発が新宿発より高く載っていた。大宮は同額、横浜は八王子乗車で安い
m = N['houou']
legs = m['trainRoutes']['routes']['yokohama']['legs']
idx = [i for i, l in enumerate(legs) if l['station'] == '甲府駅']; assert len(idx) == 1
m['trainRoutes']['routes']['yokohama']['legs'] = [leg('横浜駅', 'train', 'JR横浜線', 60), leg('八王子駅', 'train', 'JR特急あずさ・かいじ', 55)] + legs[idx[0]:]
m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'] = 5760, 5760, 5200
m['trainRoutes']['summaryNote'] = ('※運賃はJR＋バス1,760円の合計。バスの運行は2026年は6月26日〜11月3日。'
                                   '夜叉神ゲート〜広河原間は南アルプス山岳交通適正化協議会への利用者協力金300円が別途必要')
resync(m)
q = [q for q in m['faq'] if 'アクセス方法' in q['question']][0]
q['answer'] = (f'特急あずさ・かいじで甲府駅へ行き、山梨交通の登山バスで夜叉神峠登山口まで約1時間25分です。'
               f'新宿から{hm(m["trainTimeShinjuku"])}・5,760円、大宮からは新宿で特急に乗り{hm(m["trainTimeOmiya"])}・5,760円、横浜からは八王子で特急に乗り{hm(m["trainTimeYokohama"])}・5,200円が目安です（乗り換えの待ち時間は別）。'
               '車の場合は都心から約3時間が目安です。')

# 男体山：バス代が旧運賃（1,150円）で計算されていた。現行は1,400円
m = N['nantaisan']
old = (m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'])
assert old == (5290, 4780, 5870)
m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'] = 5540, 5030, 6120
m['trainRoutes']['summaryNote'] = '※運賃は特急「日光」利用＋バス1,400円の合計。日光のバスは20〜30分間隔'
resync(m)
q = [q for q in m['faq'] if 'アクセス方法' in q['question']][0]
for a_, b_ in (('運賃約5,290円', '運賃約5,540円'), ('運賃約5,870円', '運賃約6,120円')):
    assert a_ in q['answer']; q['answer'] = q['answer'].replace(a_, b_)

for mid, note in (('nakimushiyama', None), ('amagi', '新宿発は特急踊り子、横浜発は普通列車の経路で、額の付き方は整合。伊東駅〜天城縦走登山口のバス1,340円は注記の値で、事業者では未再確認')):
    N[mid]['fareCheckedAt'] = V
    if note:
        N[mid]['verifyNotes'] = (N[mid].get('verifyNotes') or []) + [note]
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ('houou', 'nantaisan'):
    x = N[i]; print(i, x['trainTimeShinjuku'], x['trainTimeOmiya'], x['trainTimeYokohama'], x['fareShinjuku'], x['fareOmiya'], x['fareYokohama'])
