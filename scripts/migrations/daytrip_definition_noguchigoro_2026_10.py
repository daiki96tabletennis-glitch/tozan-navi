#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""野口五郎岳の本文に残る「日帰り可能」を直す（daytrip_definition_2026_10.py の続き・2026-10-12）。"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
V = '2026-10-12'
# ── 野口五郎岳：本文に残る「日帰り可能」を直す ──
D = json.load(open(P, encoding='utf-8'))
n = [x for x in D if x['id'] == 'noguchigoro'][0]
REP = [
    ('faq0', '日帰り可能。', '山小屋に泊まる1泊2日の計画が基本です。'),
    ('faq1', '野口五郎岳は日帰り登山が可能です。コース定数44〜58を参考に体力に合ったプランを選んでください。',
     '野口五郎岳は、山小屋に泊まる1泊2日が基本です。代表コース（高瀬ダム〜ブナ立尾根〜烏帽子岳〜野口五郎岳）は2日間・22.0km・標高差1,900mで、歩く時間が8時間程度以下の日帰りコースはありません。'),
    ('vibesHtml', '<strong>日帰り登山がしたい人</strong>——新宿から車5時間40分、日帰り可能', '<strong>山小屋泊でじっくり歩きたい人</strong>——1泊2日の縦走が基本'),
    ('introHtml', '日帰りでの登山が可能。', '山小屋に泊まる1泊2日が基本。'),
]
for k, old, new in REP:
    if k.startswith('faq'):
        q = n['faq'][int(k[3])]
        assert q['answer'].count(old) == 1, k
        q['answer'] = q['answer'].replace(old, new)
    else:
        assert n[k].count(old) == 1, k
        n[k] = n[k].replace(old, new)
assert n['faq'][1]['question'] == '野口五郎岳の所要時間は？日帰りできますか？'
n['faq'][1]['question'] = '野口五郎岳は日帰りできますか？所要時間の目安'
vp = [v for v in n['vibePoints'] if v['who'] == '日帰り登山がしたい人']
assert len(vp) == 1
vp[0]['who'], vp[0]['why'] = '山小屋泊でじっくり歩きたい人', '1泊2日の縦走が基本'
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('noguchigoro ok')
