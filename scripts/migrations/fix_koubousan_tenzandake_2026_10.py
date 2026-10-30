#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""弘法山の閉鎖と、天覧山・多峯主山の標高を直す（2026-10-30。運営者の指示）。

弘法山
- 秦野市「弘法山公園の閉鎖について」（2026-10-22 更新）
  https://www.city.hadano.kanagawa.jp/kanko/tozan-hiking/2452.html
  ツキノワグマの再出没に伴い、令和8年10月24日（土）から弘法山公園（弘法山・権現山・浅間山）を閉鎖。再開の時期は書かれていない
- status.level を restricted にし、注意のバナーを出す。期限が無いので annualItems は期間なしの closure（出典の見張りだけに使う）

天覧山・多峯主山
- 前の標高 304m は誤り。山名の高いほうの多峯主山は 271m（西武鉄道「多峯主山」のハイキング案内、飯能市の資料）。天覧山は 195〜197m で資料により違う
- 山ページの標高は高いほうの 271m にする

  python3 scripts/migrations/fix_koubousan_tenzandake_2026_10.py
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, 'data', 'mountains.json')
TODAY = '2026-10-30'
SRC = 'https://www.city.hadano.kanagawa.jp/kanko/tozan-hiking/2452.html'

D = json.load(open(PATH, encoding='utf-8'))
BY = {m['id']: m for m in D}

k = BY['koubousan']
k['status'] = {
    'level': 'restricted',
    'summary': '弘法山公園（弘法山・権現山・浅間山）は、ツキノワグマの再出没のため2026年10月24日から閉鎖中です（秦野市。再開の時期は未定）。',
    'checkedAt': TODAY,
    'sourceUrl': SRC,
}
k['warnBanner'] = {
    'type': 'red',
    'title': '弘法山公園は閉鎖中',
    'text': 'ツキノワグマの再出没のため、秦野市が2026年10月24日から弘法山公園（弘法山・権現山・浅間山）を閉鎖しています。再開の時期は未定です。出かける前に秦野市の案内を確認してください。',
    'url': SRC,
    'linkText': '秦野市の案内を見る',
}
items = [x for x in (k.get('annualItems') or []) if x.get('sourceUrl') != SRC]
items.append({'kind': 'closure', 'label': '弘法山公園の閉鎖（クマの出没）', 'validFrom': None, 'validTo': None,
              'seasonYear': None, 'sourceUrl': SRC, 'lastVerified': TODAY,
              'note': '2026-10-24 から閉鎖。再開の時期は未定'})
k['annualItems'] = items
k['mountainUpdated'] = TODAY

t = BY['tenzandake']
t['elevation'] = 271
n = 0
for f in ('metaDescription', 'ogDescription', 'metaDescriptionManual'):
    if isinstance(t.get(f), str):
        t[f], c = re.subn(r'304m', '271m', t[f])
        n += c
t['mountainUpdated'] = TODAY

json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok', n)
