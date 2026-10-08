#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""装備カレンダーを4区分（アイゼン不要／軽アイゼン等／冬山装備／入山不可）＋月途中の切替に移行する（2026-10-08）。
旧構造の山：seasonCalendar（s-ok / s-gear / s-hard / s-closed）を gearCalendar に写す。
  s-ok→no_crampons、s-gear→light_crampons、s-hard→winter_gear、s-closed→closed
  ここでは機械的に写すだけ。区分の妥当性と閉鎖期間は、別途一次情報で監査する（推測で直さない）。
新構造（ssot-v1）の山：build_derived.py が conditions.gearMonthly と trailPeriods から作る。
旧フィールド（seasonCalendar / calLegend / seasonNoGear / season6Crampons）は変えない（トップの絞り込み・診断が使っている）。
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import gear_calendar
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
n = 0
for m in D:
    if m.get('dataModel') == 'ssot-v1':
        continue
    m['gearCalendar'] = gear_calendar.from_legacy(m['seasonCalendar'])
    assert not gear_calendar.validate(m['gearCalendar']), m['id']
    n += 1
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('旧構造の山に gearCalendar を設定:', n)
