#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""紹介文の誤りを直す（2026-10-10）。
  - 草戸山：「相模湖を望む」→ 山頂の松見平から見えるのは城山湖（BE-PAL https://www.bepal.net/archives/258060 ）
  - 嵐山（埼玉）：「都名勝の嵐山渓谷」→ 埼玉県の渓谷なので「都名勝の」を外す
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
FIX = {
    'kusatoriyama': ('高尾山周辺の山並みや相模湖を望む眺望スポットがある', '山頂の松見平から城山湖を見下ろせる'),
    'ranzan_saitama': ('都名勝の嵐山渓谷は', '嵐山渓谷は'),
}
for mid, (a, b) in FIX.items():
    m = N[mid]
    for k in ('description', 'introHtml'):
        assert m[k].count(a) == 1, (mid, k)
        m[k] = m[k].replace(a, b)
    assert a not in json.dumps(m, ensure_ascii=False), mid
    m['mountainUpdated'] = '2026-10-10'
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok')
