#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""乾徳山：バス運賃を確定し、時刻表リンクを山梨市の市民バスのページに統一する（2026-10-08）。
出典：山梨市「市民バス 西沢渓谷線」https://www.city.yamanashi.yamanashi.jp/site/city-bus/9090.html
  料金表（平成30年7月1日改定。以後変更なし＝サイト運営者が確認）山梨市駅〜乾徳山登山口 400円
  時刻表 山梨市駅9:12→乾徳山登山口9:44（32分）
  Yahoo!路線情報 →山梨市 新宿4,000円（特急、2,420＋1,580）／大宮2,420円／横浜2,090円（普通列車）
  合計は現行の 4,400／2,820／2,490円のまま
"""
import json, os, sys, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
m = [x for x in D if x['id'] == 'kentoku'][0]
V = '2026-10-08'
URL = 'https://www.city.yamanashi.yamanashi.jp/site/city-bus/9090.html'


def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')


assert (m['fareShinjuku'], m['fareOmiya'], m['fareYokohama']) == (4400, 2820, 2490)
tr = m['trainRoutes']
q = [x for x in m['faq'] if 'アクセス方法' in x['question']]
assert len(q) == 1
a = q[0]['answer']
for dep, K in (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama')):
    L = tr['routes'][dep]['legs']
    assert L[-2]['station'] == '山梨市駅' and L[-2]['durationMin'] == 30
    old = hm(m['trainTime' + K])
    L[-2]['durationMin'] = 32
    m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in L)
    a, c = re.subn(old, hm(m['trainTime' + K]), a)
    assert c == 1, (dep, old)
q[0]['answer'] = a
bus = [l for l in tr['links'] if l['type'] == 'bus']
assert len(bus) == 1
bus[0]['url'] = URL
m['busScheduleLinks'] = [URL]
tr['note'] = tr['note'].rstrip('。') + '。山梨市駅〜乾徳山登山口は約32分・400円'
m['trainAccess'] = legs_text(tr['routes']['shinjuku']['legs'])
m['trainAccessOmiya'] = legs_text(tr['routes']['omiya']['legs'])
m['trainAccessYokohama'] = legs_text(tr['routes']['yokohama']['legs'])
m['trainAccessHtml'] = render_ts_section(tr, m)
m['verifyNotes'] = [n for n in (m.get('verifyNotes') or []) if 'バス運賃が未確認' not in n]
m['needsVerification'] = bool(m['verifyNotes'])
m['mountainUpdated'] = V
m['fareCheckedAt'] = V
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'], a)
