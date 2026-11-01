#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""バスに乗る山で、時刻表のリンクが無い・電車のリンクに見える山を直す（2026-11-01。運営者の指示「バスの時刻表リンクがない山もある」）。

- 種類が「other」の時刻表リンク（13件）は、電車の印・乗換案内の色で出ていて、バスの時刻表に見えなかった → 「bus」にする
  （五竜岳のテレキャビン運行カレンダーと、黒姫山の「信濃町の交通案内」はバスの時刻表ではないので、そのまま）
  飯豊山の「喜多方市の登山口情報」は、飯豊山登山アクセスバスの案内のページなので、表示名もそう直す
- 谷川岳：関越交通「水上線」の時刻表が無かった → 関越交通の公式の路線ページ（上毛高原駅〜水上駅〜谷川岳ヨッホ。時刻表のPDFが並ぶ）
- 笊ヶ岳：早川町乗合バス・雨畑大島線の乗合タクシーの時刻表が無かった → 早川町の「公共交通」のページ（両方の時刻表がある）
- 苗場山：越後湯沢駅〜祓川はタクシー（路線バスなし）なのに、バスの印になっていた → タクシーの印にする

旧い形式の山は mountains.json の trainRoutes.links、新しい形式の山は accesses.json（このあと build_derived.py）。

  python3 scripts/migrations/fix_bus_timetable_links_2026_11.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section  # noqa: E402

MP = os.path.join(ROOT, 'data', 'mountains.json')
AP = os.path.join(ROOT, 'data', 'accesses.json')
TODAY = '2026-11-01'
KEEP_OTHER = ('テレキャビン', '信濃町の交通案内')
RELABEL = {'喜多方市の登山口情報': '飯豊山登山アクセスバスの案内（喜多方市）'}
ADD_OLD = {'yarigatake2': {'type': 'bus', 'label': 'はやかわ乗合バス・雨畑大島線乗合タクシー 時刻表（早川町）',
                           'url': 'https://www.town.hayakawa.yamanashi.jp/people/taffic.html'}}
ADD_NEW = {'tanigawadake-joch': {'type': 'bus', 'label': '関越交通バス 水上線 時刻表（上毛高原駅〜谷川岳ヨッホ）',
                                 'url': 'https://kan-etsu.net/pages/20/'}}


def fix_links(links):
    n = 0
    for l in links:
        if l.get('type') == 'other' and not any(k in l.get('label', '') for k in KEEP_OTHER):
            l['type'] = 'bus'
            if l.get('label') in RELABEL:
                l['label'] = RELABEL[l['label']]
            n += 1
    return n


M = json.load(open(MP, encoding='utf-8'))
changed = set()
n_old = 0
for m in M:
    tr = m.get('trainRoutes')
    if not isinstance(tr, dict) or m.get('dataModel') == 'ssot-v1':
        continue
    k = fix_links(tr.get('links') or [])
    if m['id'] in ADD_OLD:
        assert not any(l.get('url') == ADD_OLD[m['id']]['url'] for l in tr.get('links') or [])
        tr.setdefault('links', []).append(ADD_OLD[m['id']])
        k += 1
    if m['id'] == 'naeba':
        for r in tr['routes'].values():
            for lg in r['legs']:
                meth = lg.get('method') or {}
                if meth.get('icon') == 'bus' and 'タクシー' in meth.get('line', ''):
                    meth['icon'] = 'taxi'
                    k += 1
    if k:
        n_old += k
        m['trainAccessHtml'] = render_ts_section(tr, m)
        m['mountainUpdated'] = TODAY
        changed.add(m['id'])
json.dump(M, open(MP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

A = json.load(open(AP, encoding='utf-8'))
n_new = 0
for aid, a in A.items():
    tr = a.get('trainRoutes') if isinstance(a, dict) else None
    if not isinstance(tr, dict):
        continue
    k = fix_links(tr.get('links') or [])
    if aid in ADD_NEW:
        assert not any(l.get('url') == ADD_NEW[aid]['url'] for l in tr.get('links') or [])
        tr.setdefault('links', []).append(ADD_NEW[aid])
        k += 1
    if k:
        n_new += k
        changed.add('access:' + aid)
json.dump(A, open(AP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('旧い形式', n_old, '件／新しい形式', n_new, '件', sorted(changed))
