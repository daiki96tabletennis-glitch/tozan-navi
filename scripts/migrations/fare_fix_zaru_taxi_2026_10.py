#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""笊ヶ岳：大島〜老平（馬場）の乗合タクシー200円を運賃に入れる（2026-10-08）。
出典：乗合タクシー200円はサイト運営者が確認。身延駅〜大島のバス600円は早川町乗合バス運賃表。
身延まで 新宿5,100円／大宮4,540円／横浜5,430円（Yahoo!路線情報）
"""
import json, os, sys, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
m = [x for x in D if x['id'] == 'yarigatake2'][0]
V = '2026-10-08'
assert (m['fareShinjuku'], m['fareOmiya'], m['fareYokohama']) == (5700, 5140, 6030)
F = (5900, 5340, 6230)
m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'] = F
tr = m['trainRoutes']
tr['summaryNote'] = '※身延駅〜大島のバスは600円、大島〜老平の乗合タクシーは200円。早川町乗合バスは1日4往復で、乗合タクシーは前日19時までの予約制（角瀬タクシー運行）'
m['trainAccessHtml'] = render_ts_section(tr, m)
hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
assert len(hit) == 1
a, c = re.subn(r'大島バス停までの運賃は新宿から5,700円、大宮から5,140円、横浜から6,030円で、乗合タクシー代は別にかかります。',
               '運賃は新宿から5,900円、大宮から5,340円、横浜から6,230円です（乗合タクシーを含む）。', hit[0]['answer'])
assert c == 1
hit[0]['answer'] = a
m['verifyNotes'] = [n for n in (m.get('verifyNotes') or []) if '乗合タクシーの運賃' not in n]
m['needsVerification'] = bool(m['verifyNotes'])
m['mountainUpdated'] = V
m['fareCheckedAt'] = V
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(F, m['verifyNotes'])
