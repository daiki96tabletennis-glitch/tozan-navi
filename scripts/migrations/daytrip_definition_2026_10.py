#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「日帰り可」の定義（運営者・2026-10-12）：歩く時間が8時間程度以下のコースがある山。
全156山をこの定義で見直した結果、区分（daytrip）が変わるのは2山。
- 妙高山：燕温泉〜燕登山道の往復は7時間50分（登り4時間30分・下り3時間20分。japanesealps.net）。サイトの9時間は長すぎたので直し、日帰り可にする
- 野口五郎岳：コースは1泊2日の縦走だけなのに日帰り可になっていた。日帰り不可にする
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
V = '2026-10-12'
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}

m = N['myoko']
r = [x for x in m['routes'] if '燕温泉' in x['name']]
assert len(r) == 1 and r[0]['time'] == '9時間' and not m.get('daytrip')
r = r[0]
r['time'] = '7時間50分'
r['timeSource'] = '登山ガイドのコースタイム（燕登山道：登り4時間30分・下り3時間20分）'
r['timeSourceUrl'] = 'https://www.japanesealps.net/100moutains/myokosan/'
r['timeCheckedAt'] = V
r['status'] = {'state': 'caution', 'label': '日帰りは早朝出発で'}
m['daytrip'] = True
q = [x for x in m['faq'] if '日帰りできますか' in x['question']]
assert len(q) == 1
q[0]['answer'] = 'はい、妙高山は日帰りできます。燕温泉から燕登山道の往復はコースタイムで7時間50分（燕新道を使うと8時間50分）、妙高高原スカイケーブルの山頂駅からは往復約7時間、笹ヶ峰からは約10時間です。どのコースも歩く時間が長いので、早朝の出発が前提です。ゆとりを持つなら、高谷池ヒュッテや黒沢池ヒュッテに泊まる計画にしてください。'
old = '標高差1,300m超・往復8時間以上と行程が長く、日帰りは健脚者向け'
assert m['dlReasonsHtml'].count(old) == 1
m['dlReasonsHtml'] = m['dlReasonsHtml'].replace(old, '標高差1,300m超・往復約8時間と行程が長く、日帰りは早朝の出発が前提')
m['mountainUpdated'] = V

n = N['noguchigoro']
assert n.get('daytrip') and all('泊' in x['name'] for x in n['routes'])
n['daytrip'] = False
n['mountainUpdated'] = V
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok')
