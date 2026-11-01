#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""山の区分（category）を、日本二百名山・三百名山の一覧に合わせる（2026-11-01。運営者の指示）。

サイトの区分は「百名山・二百名山・人気の山」の3つ（三百名山の区分は無い。三百名山だけの山は「人気の山」）。
出典は data/peak_lists.json（Wikipedia「日本二百名山」「日本三百名山」）。
- 大岳山・武甲山：日本二百名山 → 二百名山（前は人気の山）
- 唐松岳・野口五郎岳：日本三百名山（二百名山ではない）→ 人気の山（前は二百名山）
- 蝶ヶ岳：百・二百・三百名山のどれでもない → 人気の山（前は二百名山）

  python3 scripts/migrations/fix_categories_2026_11.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, 'data', 'mountains.json')
TODAY = '2026-11-01'
NEW = {'otake': '二百名山', 'bukosan': '二百名山', 'karamatsu': '人気の山', 'noguchigoro': '人気の山', 'chogatake': '人気の山'}

D = json.load(open(PATH, encoding='utf-8'))
n = 0
for m in D:
    if m['id'] in NEW:
        m['category'] = NEW[m['id']]
        m['mountainUpdated'] = TODAY
        n += 1
assert n == len(NEW), n
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok', n)
