#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日向山：運賃からタクシー代の概算を外し、小淵沢駅までの正式な額にする。
光岳：飯田駅〜遠山郷のバスの事業者名と所要時間を直す（運賃は確定できず、要確認のまま）。2026-10-06

出典：Yahoo!路線情報（2026-10-17 新宿・大宮→小淵沢 5,430円／横浜→小淵沢 4,770円、あずさ1号 新宿07:00→小淵沢08:53）、
      NAVITIME 遠山郷線[信南交通]（飯田駅前09:30→かぐらの湯10:53）
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))

def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')

def sync(m):
    R = m['trainRoutes']['routes']
    for dep, K in DEPS:
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)

m = N['hinata']
m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'] = 5430, 5430, 4770
m['trainRoutes']['summaryNote'] = '※運賃は小淵沢駅までの片道（タクシー代は別）。小淵沢駅から先に路線バスはない'
sync(m)
hit = [q for q in m['faq'] if 'タクシー代込みの目安' in q['answer']]
assert len(hit) == 1
hit[0]['answer'] = ('JR小淵沢駅からタクシーで尾白川渓谷駐車場まで約20分、そこから矢立石登山口まで徒歩約50分です。'
                    f'新宿からは特急あずさで{hm(m["trainTimeShinjuku"])}・5,430円、大宮からは新宿で特急あずさに乗り{hm(m["trainTimeOmiya"])}・5,430円、'
                    f'横浜からは八王子で特急あずさに乗り{hm(m["trainTimeYokohama"])}・4,770円が目安です（運賃は小淵沢駅まで。タクシー代は別）。')
m['verifyNotes'] = [x for x in m.get('verifyNotes', []) if 'タクシー代の概算' not in x] + ['小淵沢駅〜尾白川渓谷駐車場のタクシー料金']

m = N['terkari']
for dep, _ in DEPS:
    legs = m['trainRoutes']['routes'][dep]['legs']
    hit = [i for i, l in enumerate(legs) if l['station'] == '飯田駅']
    assert len(hit) == 1 and legs[hit[0] + 1]['station'] == '道の駅遠山郷', dep
    legs[hit[0]]['method']['line'] = '信南交通「遠山郷線」'
    legs[hit[0]]['durationMin'] = 83
    legs[hit[0] + 1]['station'] = 'かぐらの湯（道の駅遠山郷）'
n0 = m['trainRoutes']['note']
assert '運賃・時間は概算（メーター制、1.5〜2万円程度）。' in n0
m['trainRoutes']['note'] = n0.replace('運賃・時間は概算（メーター制、1.5〜2万円程度）。',
    '飯田駅前〜かぐらの湯は信南交通「遠山郷線」で約1時間23分、1日数本。表示の運賃は高速バス・路線バス・タクシーを合わせた概算で、正式な額は未確認（タクシーはメーター制）。')
sync(m)
hit = [q for q in m['faq'] if 'アクセス方法' in q['question']][0]
hit['answer'] = (f'光岳へは新宿から高速バスで飯田駅まで約4時間10分、信南交通の遠山郷線でかぐらの湯（道の駅遠山郷）まで約1時間23分、そこから予約制タクシーで芝沢ゲートまで約45分です。'
                 f'新宿から{hm(m["trainTimeShinjuku"])}・運賃約24,800円が目安（大宮・横浜は新宿経由でほぼ同程度）。'
                 '車とタクシーが入れるのは芝沢ゲートまでで、易老渡へは林道を約5km歩きます。タクシーは早朝発の事前予約制（メーター制、1.5〜2万円程度）のため前泊が必要です。')
m['verifyNotes'] = m.get('verifyNotes', []) + ['高速バス（新宿〜飯田）は日によって運賃が変わる。遠山郷線の運賃は未確認']
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(N['hinata']['trainTimeShinjuku'], N['terkari']['trainTimeShinjuku'], N['terkari']['trainTimeOmiya'], N['terkari']['trainTimeYokohama'])
