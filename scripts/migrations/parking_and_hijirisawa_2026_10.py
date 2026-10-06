#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""空欄だった駐車場の記入（裏が取れた3山＋駅から歩く山の注記）と、聖岳・聖沢登山口ルートの枠の追加（2026-10-06）。

駐車場の出典：栃木市の資料（謙信平駐車場 普通車26台・無料）、東京都の観光公式サイト（都民の森 100台・無料・月曜休園）、
富士河口湖町観光課の掲載情報（三つ峠 裏登山口 普通車10台）。
聖沢登山口ルートは時間・距離の出典が揃わなかったため、数値は入れていない。
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}

def note(m, text):
    m['needsVerification'] = True
    m['verifyNotes'] = (m.get('verifyNotes') or []) + [text]

VERIFIED = {
    'taiheizan': '謙信平駐車場（普通車26台・無料）。桜まつり・あじさいまつりの期間は一部有料',
    'mitosaan': '都民の森駐車場（100台・無料）。月曜休園（祝日は翌日。繁忙期は開園）で、開門は8時',
    'mitsutoge': '三つ峠登山口（裏登山口）の駐車場（普通車 約10台）',
}
# 駅やバス停から歩き始めるコースで、登山者用の駐車場を確認できていない山
STATION = ['kobotokeshiroyama', 'kusatoriyama', 'nakimushiyama', 'iwadonoyama', 'maruyama_okubusuma', 'ohnoyama',
           'kuratakeyama', 'sasakogarigaburiyama', 'shodosan_namatate', 'kukiyama', 'honitayama', 'futagoyama_okumusa',
           'azumayama_ninomiya', 'hafuzan_chichibu', 'ranzan_saitama', 'kamakura_alps', 'kannokura', 'ishirousan', 'okusuyama']
# 駐車場がある施設だが、台数・料金の裏が取れていない山（空欄のまま、要確認に記録）
PENDING = {
    'makuyama': '幕山公園の駐車場（通常期の台数に情報の幅あり。梅の宴の期間は有料）',
    'hodosan': '宝登山ロープウェイ山麓駅の駐車場（約150台・料金に情報の幅あり）',
    'kogashiyama': '宇都宮市森林公園駐車場の台数・利用時間',
    'ishiwariyama': '石割神社前の駐車場（トイレあり。台数・料金）',
    'sengenrei': '払沢の滝の駐車場（台数・料金）',
    'hinodesaan': '御岳山ケーブル滝本駅の駐車場（台数・料金）',
    'juunigadake': '文化洞トンネル脇の駐車スペース（台数）',
}
ids = set()
for mid, text in VERIFIED.items():
    assert not N[mid].get('parking'), mid
    N[mid]['parking'] = text; ids.add(mid)
for mid in STATION:
    assert not N[mid].get('parking'), mid
    N[mid]['parking'] = '駅・バス停から歩くコースです。登山者用の駐車場は確認できていません'
    note(N[mid], '登山者用の駐車場の有無'); ids.add(mid)
for mid, text in PENDING.items():
    assert not N[mid].get('parking'), mid
    note(N[mid], '駐車場：' + text)

# 聖岳：代表ルート（便ヶ島）が通行止めのため、歩けるルートの枠を追加
m = N['hijiridade']
assert len(m['routes']) == 1
m['routes'].append({
    'name': '聖沢登山口〜聖平小屋〜聖岳（往復・山小屋泊）',
    'waypoints': '聖沢登山口 → 聖沢吊橋 → 聖平小屋 → 小聖岳 → 聖岳',
    'trailheadName': '聖沢登山口（静岡県側）',
    'accessNote': '静岡駅から畑薙第一ダムへ行き、特種東海フォレストの送迎バス（予約制・宿泊者限定）で聖沢登山口へ。下の「電車・バスでのアクセス」と同じ経路',
    'accessNeedsVerification': False, 'accessSource': 'サイト内：聖岳の経路データ', 'accessLastChecked': '2026-10-06',
    'needsVerification': True})
m['verifyNotes'] = ['便ヶ島〜西沢渡の通行止めの解除時期', '聖沢登山口ルートの時間・距離（資料により15時間45分〜16時間50分・23〜28kmと幅があり未登録）']
ids.add('hijiridade')
for mid in ids:
    N[mid]['mountainUpdated'] = '2026-10-06'
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(' '.join(sorted(ids)))
