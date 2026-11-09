#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全山の地図ボタン（駐車場）の行き先を見直した（2026-11-10。運営者の指示「mapリンク先が本当に駐車場になっているか確かめて修正して」）。

確かめ方：全165山の地図ボタンの位置について、OpenStreetMap で100m以内に駐車場があるか・逆ジオコーダー（Nominatim）で何を指しているかを調べ、
駐車場から離れていた79山を、駐車場の欄の名前と照らした。直す先は Google マップの施設の位置で、Nominatim でも確かめた。

直したもの（すべて旧い形式の山。地図ボタンだけを直し、駐車場の欄の文はそのまま。御前山だけ欄の文に場所を足した）
- 北岳・間ノ岳・農鳥岳：広河原山荘（車では行けない）→ 市営芦安第2駐車場（芦安駐車場のバス停の隣）
- 赤石岳・荒川岳：椹島ロッヂ（車では行けない）→ 畑薙ダム夏季臨時駐車場
- 蝶ヶ岳：上高地のバス停（車では行けない）→ 沢渡駐車場（槍ヶ岳・奥穂高岳と同じ位置）
- 大山（丹沢）：大山ケーブル駅 → 伊勢原市営大山第2駐車場（約550m）
- 焼岳：中の湯のバス停 → 焼岳 新中の湯登山口（約900m）
- 御前山：奥多摩湖のバス停（名前だけのリンク）→ 奥多摩 水と緑のふれあい館の駐車場（小河内ダムの駐車場）
- 経ヶ岳：仲仙寺の本堂 → 山門の脇の駐車場（約200m。OpenStreetMap の駐車場）
- 天城山：天城高原ゴルフコース → 天城高原ハイカー専用駐車場（約180m）
- 茅ヶ岳：住宅地の道 → 深田記念公園駐車場（約120m）
- 天覧山・多峯主山：遊歩道 → 飯能中央公園第一駐車場（約420m）
- 黒部五郎岳・薬師岳：折立ヒュッテ → 有峰林道 折立駐車場（約200m）
- 荒沢岳：かもしかの湯 → 荒沢岳 登山口 駐車場（約1.1km。同じ銀山平の国道352号沿い）

車の所要時間：北岳・間ノ岳・農鳥岳・赤石岳・荒川岳・蝶ヶ岳は、2026-10 に乗り換えの駐車場（芦安・畑薙・沢渡）まで測ってあり（driveTarget）、
地図ボタンがそれに合った。ほかは数百m〜1.1kmの移動で、測り直していない。

  python3 scripts/migrations/fix_parking_maps_all_2026_11.py
何度流しても同じ結果。
"""
import json
import os
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, 'data', 'mountains.json')
TODAY = '2026-11-10'

ASHIYASU = (35.6329859, 138.3621244, '市営芦安第2駐車場')
HATANAGI = (35.3136899, 138.1871557, '畑薙ダム夏季臨時駐車場')
ORITATE = (36.483347, 137.4731576, '有峰林道 折立駐車場')

# 山ID: (緯度, 経度, 地図アプリに出す名前)
MAPS = {
    'kitadake': ASHIYASU,
    'ainodake': ASHIYASU,
    'noutori': ASHIYASU,
    'akaisidake': HATANAGI,
    'arakawadake': HATANAGI,
    'chogatake': (36.1646, 137.65594, '沢渡駐車場'),
    'oyama': (35.4246342, 139.2490029, '伊勢原市営大山第2駐車場'),
    'yakedake': (36.2041818, 137.598716, '焼岳 新中の湯登山口 駐車場'),
    'gozenyama': (35.7923553, 139.0472861, '奥多摩 水と緑のふれあい館 駐車場'),
    'keizandake': (35.8886084, 137.9170092, '仲仙寺 駐車場'),
    'amagi': (34.8731775, 139.0234112, '天城高原ハイカー専用駐車場'),
    'kayagatake': (35.7702527, 138.5066921, '深田記念公園駐車場'),
    'tenzandake': (35.8584029, 139.3107548, '飯能中央公園第一駐車場'),
    'kurobegorodam': ORITATE,
    'yakushidake': ORITATE,
    'arasawadake': (37.1359303, 139.1563233, '荒沢岳 登山口 駐車場'),
}

# 車で行けない登山口（前の地図ボタンの位置）。山小屋のページの「登山口の近く」の判定に使う（gen_huts_page.py）
HIROGAWARA = {'lat': 35.6968864, 'lng': 138.2715174, 'name': '広河原'}
SAWARAJIMA = {'lat': 35.4306835, 'lng': 138.207313, 'name': '椹島'}
TRAILHEAD = {
    'kitadake': HIROGAWARA, 'ainodake': HIROGAWARA, 'noutori': HIROGAWARA,
    'akaisidake': SAWARAJIMA, 'arakawadake': SAWARAJIMA,
    'chogatake': {'lat': 36.2461, 'lng': 137.6353, 'name': '上高地バスターミナル'},
}

PARKING = {
    'gozenyama': '小河内ダム駐車場（奥多摩 水と緑のふれあい館の駐車場・無料）',
}


def links(lat, lng, q):
    g = 'https://www.google.com/maps/search/?api=1&query=%s%%2C%s' % (lat, lng)
    a = 'https://maps.apple.com/?ll=%s,%s&q=%s' % (lat, lng, quote(q))
    btn = ('<div class="map-btns"><a href="%s" target="_blank" class="map-btn-link">Googleマップ</a>\n'
           '<a href="%s" target="_blank" class="map-btn-link">Apple Maps</a>\n</div>' % (g, a))
    return g, a, btn


D = json.load(open(PATH, encoding='utf-8'))
by = dict((m['id'], m) for m in D)
changed = []
for i, (lat, lng, q) in sorted(MAPS.items()):
    m = by[i]
    assert m.get('dataModel') != 'ssot-v1', i  # 新しい形式は trailheads.json を直す
    g, a, btn = links(lat, lng, q)
    before = (m.get('gmapUrl'), m.get('amapUrl'), m.get('mapBtnsHtml'), m.get('parking'))
    if i in TRAILHEAD:
        m['trailheadLatLng'] = TRAILHEAD[i]
    m['gmapUrl'], m['amapUrl'], m['mapBtnsHtml'] = g, a, btn
    m['mapTargetNote'] = '地図ボタンは駐車場（%s）。%s に Google マップ・OpenStreetMap で確認' % (q, TODAY)
    if i in PARKING:
        m['parking'] = PARKING[i]
    if before != (m.get('gmapUrl'), m.get('amapUrl'), m.get('mapBtnsHtml'), m.get('parking')):
        m['mountainUpdated'] = TODAY
        changed.append(i)
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok', len(changed), changed)
