#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""装備カレンダー：男体山の閉山期間を入山不可にする（2026-10-09）。
出典：日光市観光協会「男体山」https://www.nikko-kankou.org/spot/14
  開山期間 4月25日〜11月11日（二荒山神社中宮祠で受付 6:00〜12:00、登拝料 大人1,000円）。「上記期間以外は閉山となります」
代表ルート（二荒山神社ルート）は開山期間だけ登れる。1〜3月・12月を入山不可、4月は25日から、11月は11日まで。
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import gear_calendar as G
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
m = [x for x in D if x['id'] == 'nantaisan'][0]
V = '2026-10-09'
old = m['gearCalendar']
assert old[3] == 'light_crampons' and old[10] == 'winter_gear'
cal = list(old)
for i in (0, 1, 2, 11):
    cal[i] = 'closed'
    m['seasonCalendar'][i] = 's-closed'
cal[3] = {'split': True, 'before': 'closed', 'after': 'light_crampons', 'changeDate': 25}
cal[10] = {'split': True, 'before': 'winter_gear', 'after': 'closed', 'changeDate': 12}
assert not G.validate(cal)
m['gearCalendar'] = cal
m['calLegend'] = [G.LABEL[k] for k in G.KEYS]
SRC = 'https://www.nikko-kankou.org/spot/14'
m['annualItems'] = (m.get('annualItems') or []) + [
    {'kind': 'trail', 'label': '男体山の開山期間（二荒山神社ルート。期間外は閉山）', 'validFrom': '2026-04-25', 'validTo': '2026-11-11',
     'seasonYear': 2026, 'sourceUrl': SRC, 'lastVerified': V, 'note': '受付は6時〜12時。登拝料 大人1,000円'}]
hit = [q for q in m['faq'] if 'シーズン' in q['question']]
assert len(hit) == 1
hit[0]['answer'] = ('男体山に登れるのは開山期間の4月25日〜11月11日です（二荒山神社中宮祠で6時〜12時に受付）。期間外は閉山で、登れません。'
                    '4月下旬〜5月と10月は残雪や凍結があり、軽アイゼン等が必要になることがあります。11月は積雪期に入るため冬山装備が必要です。直前の最新情報を確認してください。')
m['mountainUpdated'] = V
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print([e if isinstance(e, str) else 'split' for e in cal])
