#!/usr/bin/env python3
"""紹介文の古いアクセスの一文を外す（2026-11-23。外部レビューの指摘：雲取山の紹介文「バス15分」とアクセス欄「バス35分」）。
「公共交通機関でのアクセス可（◯◯駅→バス◯分→…）。」は経路データと別に手で持っていた文で、26山に残り多くが古い。
新しい形の山（build_derived.py）と同じく文を外し、時間はアクセス欄（trainRoutes）だけを正にする。何度流しても同じ結果。"""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
TODAY = '2026-11-23'
with open(P, encoding='utf-8') as f:
    raw = json.load(f)
ms = raw if isinstance(raw, list) else raw['mountains']
changed = []
for m in ms:
    before = json.dumps(m, ensure_ascii=False, sort_keys=True)
    if m.get('introHtml'):
        m['introHtml'], n = re.subn(r'\s*公共交通機関でのアクセス可（.*?）。', '', m['introHtml'])
    if m['id'] == 'akagi':
        m['introHtml'], n = re.subn(r'前橋駅からバスで約75分（土日は直通）', '前橋駅からバス（土日は直通）', m['introHtml'])
        assert n == 1 or '前橋駅からバス（土日は直通）' in m['introHtml']
    if m['id'] in ('nabewari', 'sannotou'):
        m['trainAccessYokohama'] = re.sub(r'渋沢駅→バス約30分', '渋沢駅→バス約15分', m['trainAccessYokohama'])
    if json.dumps(m, ensure_ascii=False, sort_keys=True) != before:
        m['mountainUpdated'] = TODAY
        changed.append(m['id'])
with open(P, 'w', encoding='utf-8') as f:
    json.dump(raw, f, ensure_ascii=False, indent=2)
print(len(changed), ' '.join(changed))
