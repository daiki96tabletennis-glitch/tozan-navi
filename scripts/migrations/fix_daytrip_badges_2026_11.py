#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""まとめの山のカードの「日帰り可／宿泊推奨」のバッジを、山の日帰りの区分（daytrip）に合わせる（2026-11-15。運営者の指示）。
- 新宿・大船の日帰りのまとめ：雲取山（鴨沢から往復9時間56分）・和名倉山（10時間46分）は日帰り不可 → 宿泊推奨（一覧には残す）
- 信濃のまとめ：妙高山はスカイケーブル山頂駅からの往復が7時間28分で日帰り可 → 日帰り可
ページは手で作ったもの。何度流しても同じ結果。前のページは .claude/backup/daytrip_badges_2026_11_15/"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
M = {m['id']: m for m in json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))}
PAGES = {'shinjuku-daytrip': ['kumotori', 'nakawarayama'], 'ofuna-daytrip': ['kumotori', 'nakawarayama'], 'shinano-hiking': ['myoko']}
for slug, ids in PAGES.items():
    p = os.path.join(ROOT, 'search', slug, 'index.html')
    s = open(p, encoding='utf-8').read()
    for mid in ids:
        badge = '日帰り可' if M[mid].get('daytrip') else '宿泊推奨'
        m = re.search(r'<div class="mountain-card">(?:(?!<div class="mountain-card">).)*?href="/mountains/%s/".*?class="mc-link"[^>]*>' % mid, s, re.S)
        if not m:
            sys.exit('%s: %s のカードが無い' % (slug, mid))
        c, n = re.subn(r'<span class="sb sb-day">[^<]*</span>', '<span class="sb sb-day">%s</span>' % badge, m.group(0))
        if n != 1:
            sys.exit('%s: %s のバッジが %d 件' % (slug, mid, n))
        s = s[:m.start()] + c + s[m.end():]
        print(slug, mid, badge)
    open(p, 'w', encoding='utf-8').write(s)
