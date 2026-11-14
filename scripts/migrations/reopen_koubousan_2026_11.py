#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""弘法山公園の閉鎖の解除を反映する（2026-11-15。運営者の指示「弘法山の制限は解除されている。サイト内の該当箇所を直して」）

出典：秦野市「弘法山公園」（更新日 2026年11月01日）
  https://www.city.hadano.kanagawa.jp/kanko/tozan-hiking/2452.html
  「【解除しました】ツキノワグマ再出没に伴う一時閉鎖 … 令和8年10月24日（土曜日）から弘法山公園（弘法山、権現山、浅間山）を
   一時閉鎖していましたが、11月3日（火曜日）から解放します。」（2026-11-15 に確認）

- mountains.json の弘法山：status（restricted）・warnBanner・annualItems の閉鎖の項目を外す（scripts/migrations/fix_koubousan_tenzandake_2026_10.py で入れたもの）
- 手で作ったページ3つ（冬でも登れる山・JR湘南・丹沢のまとめ）のカードの閉鎖の注意（data-closed="koubousan"）を外す
何度流しても同じ結果。このあと gen_mountain_pages.py --id koubousan・gen_line_articles.py odakyu-hiking・gen_winter_specials.py・check_pages.py
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = 'https://www.city.hadano.kanagawa.jp/kanko/tozan-hiking/2452.html'
TODAY = '2026-11-15'

path = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(path, encoding='utf-8'))
k = next(m for m in D if m['id'] == 'koubousan')
changed = False
if (k.get('status') or {}).get('sourceUrl') == SRC:
    del k['status']
    changed = True
if (k.get('warnBanner') or {}).get('url') == SRC:
    del k['warnBanner']
    changed = True
items = [x for x in (k.get('annualItems') or []) if not (x.get('kind') == 'closure' and x.get('sourceUrl') == SRC)]
if items != (k.get('annualItems') or []):
    k['annualItems'] = items
    changed = True
if changed:
    k['mountainUpdated'] = TODAY
    json.dump(D, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('mountains.json', '直した' if changed else '変わらない')

PAT = re.compile(r'<div class="mc-closed" data-closed="koubousan"[^>]*>.*?</div>', re.S)
for rel in ('articles/winter-no-crampons/index.html', 'search/jr-shonan-hiking/index.html', 'search/tanzawa-hiking/index.html'):
    p = os.path.join(ROOT, rel)
    s = open(p, encoding='utf-8').read()
    s2, n = PAT.subn('', s)
    if n not in (0, 1):
        raise SystemExit('想定外の数：%s %d' % (rel, n))
    if n:
        open(p, 'w', encoding='utf-8').write(s2)
    print(rel, '外した' if n else '無い')
