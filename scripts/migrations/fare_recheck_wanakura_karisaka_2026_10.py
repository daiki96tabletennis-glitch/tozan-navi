#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""和名倉山・雁坂嶺の運賃を検算する（2026-10-07）。
出典：
- 和名倉山：Yahoo!路線情報 →三峰口 新宿1,499円（池袋・飯能乗換）／大宮1,666円（熊谷乗換）／横浜2,015円（池袋・飯能乗換）＋西武観光バス580円（確認済み）
- 雁坂嶺：Yahoo!路線情報 →塩山 新宿3,670円（特急）／大宮2,090円／横浜2,090円（普通列車）、NAVITIME 塩山駅南口→西沢渓谷入口 1,220円・63分。現行額のまま
"""
import json, os, sys, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-07'
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))


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


m = N['nakawarayama']
old = (m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'])
sync(m, {'shinjuku': 2079, 'omiya': 2246, 'yokohama': 2595}, ['運賃合計が未検算'])
hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
assert len(hit) <= 1
if hit:
    a = hit[0]['answer']
    for o, n in zip(old, (2079, 2246, 2595)):
        a, c = re.subn(format(o, ','), format(n, ','), a)
        assert c == 1, (o, c)
    hit[0]['answer'] = a

m = N['karisaka']
for dep in m['trainRoutes']['routes']:
    b = m['trainRoutes']['routes'][dep]['legs'][-2]
    assert b['station'] == '塩山駅'
    b['durationMin'] = 63
t_old = (m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'])
sync(m, {'shinjuku': 4890, 'omiya': 3310, 'yokohama': 3310}, ['運賃'])
print('karisaka times', t_old, '->', m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'])
for q in m['faq']:
    if 'アクセス方法' in q['question']:
        print(q['answer'])
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
