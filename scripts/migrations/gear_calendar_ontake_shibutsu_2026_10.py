#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""装備カレンダー：閉鎖期間の監査で確認できた分を反映する（2026-10-08）。
- 御嶽山：剣ヶ峰への登山道は立入規制が続いており、通れるのは規制緩和期間だけ。
  2026年は黒沢口 7月1日8時〜10月14日正午、王滝口 7月1日6時〜10月14日正午。
  出典：木曽町「御嶽山立ち入り規制の情報について」https://www.town-kiso.com/bousai/bousai/100378/101704/
  代表ルート（田の原〜剣ヶ峰）は期間外は登れないので、1〜6月・10月15日以降・11〜12月を入山不可にする
- 至仏山：5月前半（5/1〜5/6）は軽アイゼン等のまま（サイト運営者が確認）。データの変更なし
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import gear_calendar as G
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
m = [x for x in D if x['id'] == 'ontakesan'][0]
V = '2026-10-08'
old = list(m['gearCalendar'])
assert old[6:9] == ['no_crampons'] * 3 and old[9] == 'light_crampons', old
cal = ['closed'] * 6 + ['no_crampons'] * 3 + [{'split': True, 'before': 'light_crampons', 'after': 'closed', 'changeDate': 15}] + ['closed'] * 2
assert not G.validate(cal)
m['gearCalendar'] = cal
# 旧フィールドも同期（トップの絞り込み用）
m['seasonCalendar'] = ['s-closed'] * 6 + ['s-ok'] * 3 + ['s-gear'] + ['s-closed'] * 2
m['calLegend'] = [G.LABEL[k] for k in G.KEYS if k in ('no_crampons', 'light_crampons', 'closed')]
# seasonNoGear / season6Crampons（「規制確認要」などの注記つき）と、登録済みの「山頂まで登れる期間」（annualItems）はそのまま使う
m['mountainUpdated'] = V
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ontakesan', old, '->', [e if isinstance(e, str) else 'split' for e in cal])
