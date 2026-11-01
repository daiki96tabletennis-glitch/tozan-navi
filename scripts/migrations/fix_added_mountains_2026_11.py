#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""追加した7山の見直しで見つかった点を直す（2026-11-01。運営者の指示「追加した山の情報やリンクを確認」）。

北横岳
- 気象庁の活火山「横岳」（火山名コード 334。北緯36°05′15″ 東経138°19′12″ 標高2,480m＝北横岳の山頂）
  https://www.data.jma.go.jp/vois/data/tokyo/334_Yokodake/334_index.html
- volcanoCodes を入れ、火山のタグ（vibes の volcano）を付ける（決まり：火山タグ＝volcanoCodes がある山）

仙ノ倉山・平標山（同じ平標登山口のバス）
- 南越後交通「湯沢〜三俣〜貝掛温泉〜浅貝〜西武クリスタル線」は 2026-10-10 に時刻改正。湯沢駅前→平標登山口は34分・660円（運賃表）で変わらず、
  本数は平日8便・土日祝9便（10/10〜11/8 は一部の便が苗場スキー場（シュネー）経由）
  https://www.minamiechigo.co.jp/

  python3 scripts/migrations/fix_added_mountains_2026_11.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section  # noqa: E402

PATH = os.path.join(ROOT, 'data', 'mountains.json')
TODAY = '2026-11-01'

D = json.load(open(PATH, encoding='utf-8'))
BY = {m['id']: m for m in D}

k = BY['kitayokodake']
k['volcanoCodes'] = ['334']
k['volcanoScope'] = 'summit'
if 'volcano' not in (k.get('vibes') or []):
    k['vibes'] = (k.get('vibes') or []) + ['volcano']
k['mountainUpdated'] = TODAY

OLD = r'通年運行で1日8便（2026年4月改正）。'
NEW = '通年運行。2026年10月10日改正の時刻表では平日8便・土日祝9便（11月8日までは一部の便が苗場スキー場を経由）。'
for mid in ('sennokurayama', 'tairappyo'):
    m = BY[mid]
    note, n = re.subn(OLD, NEW, m['trainRoutes']['note'])
    if n != 1:
        sys.exit(mid + '：注記の置き換えが1か所でない（%d）' % n)
    m['trainRoutes']['note'] = note
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    m['mountainUpdated'] = TODAY

json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok')
