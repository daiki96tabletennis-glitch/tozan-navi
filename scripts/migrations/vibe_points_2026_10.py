#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""診断の「おすすめの理由」に山の特徴を出すため、山ページの「こんな気分の人に」（vibesHtml）を構造化して vibePoints に持つ（2026-10-09）。
既に手で書かれている文をそのまま取り出すだけで、新しい文は作らない。
vibePoints: [{"who": "ブナ原生林の美しさを楽しみたい人", "why": "四季を通じて表情を変えるブナの原生林が見どころ"}, ...]
"""
import json, os, re, html
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
n = 0
for m in D:
    h = m.get('vibesHtml') or ''
    cnt = h.count('<div class="rec-item">')
    pts = []
    for it in re.findall(r'<div class="rec-item">(.*?)</div>', h, flags=re.S):
        body = re.sub(r'<svg.*?</svg>', '', it, flags=re.S)
        mm = re.search(r'<strong>(.*?)</strong>(?:——|—|－|-)+(.*)', body, flags=re.S)
        if mm:
            pts.append({'who': html.unescape(re.sub(r'<[^>]+>', '', mm.group(1))).strip(),
                        'why': html.unescape(re.sub(r'<[^>]+>', '', mm.group(2))).strip()})
        else:
            # 「◯◯な人——理由」の形になっていない項目は、文全体を理由として持つ
            pts.append({'who': None, 'why': html.unescape(re.sub(r'<[^>]+>', '', body)).strip()})
    assert cnt == len(pts) and cnt >= 2, (m['id'], cnt, len(pts))
    assert all(p['why'] for p in pts), m['id']
    m['vibePoints'] = pts
    n += 1
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('vibePoints を設定:', n)
