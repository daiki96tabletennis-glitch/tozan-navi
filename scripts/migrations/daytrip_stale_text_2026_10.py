#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""コースの時間を出典の値に直したのに合わせて、よくある質問・難易度の欄に残った古い数字を直す（2026-10-12）。"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
REP = [
    ('houou', '9時間・18.0km・標高差+1700m', '15時間30分・24.3km・標高差+2400m', 2),
    ('houou', '青木鉱泉ルート（周回）（10時間）', '青木鉱泉ルート（周回）（12時間）', 1),
    ('hirugata', '9時間・22.0km・標高差+1700m', '12時間30分・26.0km・標高差+1700m', 2),
    ('kasagatake', '往復13時間前後かかり', '往復のコースタイムは15時間15分で', 1),
]
for mid, old, new, want in REP:
    m, n = N[mid], 0
    for q in m['faq']:
        n += q['answer'].count(old)
        q['answer'] = q['answer'].replace(old, new)
    for k in ('dlNoteHtml', 'dlReasonsHtml', 'dlNoteHtmlOld'):
        if isinstance(m.get(k), str):
            if k != 'dlNoteHtmlOld':
                n += m[k].count(old)
            m[k] = m[k].replace(old, new)
    assert n == want, (mid, old, n, want)
    print(mid, old, '→', new, n)
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
