#!/usr/bin/env python3
"""御岳山・大岳山の駐車場を御岳登山鉄道の公式の値にする（2026-11-23）。御岳山の「御岳平駐車場」はケーブルカーの上の駅の名前で、
地図の行き先（滝本駅）と食い違っていた。出典 https://www.mitaketozan.co.jp/accessmap.html（2025-04-01 改正の料金）。何度流しても同じ結果"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
TEXT = '滝本駅駐車場（136台・7:10〜19:00・普通車は平日1時間400円/1日上限1,500円、土日と特定日は1時間450円/1日上限2,000円。繁忙期は満車の場合あり）'
with open(P, encoding='utf-8') as f:
    ms = json.load(f)
for m in ms:
    if m['id'] in ('mitakesan', 'otake') and m.get('parking') != TEXT:
        m['parking'] = TEXT
        m['mountainUpdated'] = '2026-11-23'
        print(m['id'])
with open(P, 'w', encoding='utf-8') as f:
    json.dump(ms, f, ensure_ascii=False, indent=2)
