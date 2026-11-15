#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日帰りのまとめ（新宿・大船）で、日帰りできない山（daytrip が false）の「日帰り可」のバッジを「宿泊推奨」にする（2026-11-15。運営者の指示）。
雲取山（鴨沢から往復9時間56分）・和名倉山（10時間46分）。ページは手で作ったもの。何度流しても同じ結果。前のページは .claude/backup/daytrip_badges_2026_11_15/"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
M = {m['id']: m for m in json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))}
for slug in ('shinjuku-daytrip', 'ofuna-daytrip'):
    p = os.path.join(ROOT, 'search', slug, 'index.html')
    s = open(p, encoding='utf-8').read()
    for mid in ('kumotori', 'nakawarayama'):
        if M[mid].get('daytrip'):
            sys.exit('%s は daytrip が true になった。バッジを戻すか確かめる' % mid)
        m = re.search(r'<div class="mountain-card">(?:(?!<div class="mountain-card">).)*?href="/mountains/%s/".*?class="mc-link">' % mid, s, re.S)
        if not m:
            sys.exit('%s: %s のカードが無い' % (slug, mid))
        c, n = re.subn(r'<span class="sb sb-day">[^<]*</span>', '<span class="sb sb-day">宿泊推奨</span>', m.group(0))
        if n != 1:
            sys.exit('%s: %s のバッジが %d 件' % (slug, mid, n))
        s = s[:m.start()] + c + s[m.end():]
    open(p, 'w', encoding='utf-8').write(s)
    print('ok', slug)
