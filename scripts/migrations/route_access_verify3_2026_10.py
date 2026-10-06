#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ルート別アクセス（accessNote）の追加確認：男体山・武尊山・剱岳・飯豊山・荒船山・平ヶ岳・恵那山（2026-10-06）。

verified=True は自治体の公式ページで確認できたもの。False は登山情報サイト・宿の案内が出典。
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
FIX = [
    ('tsurugi', 1, True,
     '路線バスはない。富山地方鉄道の上市駅からタクシーで約37分（23km）。'
     '車は馬場島の駐車場（約150台）。'
     '利用できるのは5月中旬〜11月中旬で、積雪の状況で変わる',
     'https://www.town.kamiichi.toyama.jp/page/2045.html', '上市町公式（2026-04-01更新）'),
    ('iide', 1, True,
     '車は祓川駐車場（約30台・仮設トイレ）。そこまでの町道は砂利道で、車高の低い車は底を擦るおそれがある。'
     '町のデマンドバスは弥平四郎の集落までで、そこから登山口まで歩いて約1時間。'
     '2026年8月時点で新長坂ルートは登山道の崩落で通行止め。上ノ越ルートを使う',
     'https://www.town.nishiaizu.fukushima.jp/site/kanko/797.html', '西会津町公式（2026-08-10現在）'),
    ('arafune', 1, True,
     '車は相沢登山口の駐車場（4台ほど）。相沢橋まわりの道路や空き地には停めない。'
     'バスは下仁田駅から下仁田町営「しもにたバス」市野萱線の三ツ瀬バス停で降りて歩く（徒歩時間は未確認）',
     'https://www.town.shimonita.lg.jp/kanko/m03/m05/05.html', '下仁田町公式（2026-03-03更新。駐車場）。バス停名は登山口案内サイト'),
    ('nantaisan', 1, False,
     '路線バスはない。車は裏男体林道の梵字飯場跡（路肩に約20台・無料）まで。'
     'その先は一般車通行止めで、志津乗越まで林道を約5km・1時間10分歩く',
     'https://www.yamakei-online.com/trailhead/detail.php?id=1553', '山と溪谷オンライン・登山口案内サイト'),
    ('takeson', 1, False,
     '路線バスは確認できていない。車はオグナほたかスキー場の駐車場（無料との情報）。'
     '夏に使える駐車場の区画と時間は現地の案内に従う',
     'https://www.yamakei-online.com/trailhead/detail.php?id=1556', '山と溪谷オンライン・登山口案内サイト'),
    ('hiragadake', 1, False,
     '中ノ岐林道は一般車が入れず、公共交通もない。'
     '銀山平などの宿に泊まり、翌朝の送迎で登山口へ入る（宿泊者だけが対象）',
     'https://www.okutadami.jp/wp/trekking/post_34/', '送迎を行う宿の案内'),
    ('enasan', 1, False,
     '車は峰越林道ゲートの駐車場（約20台＋路肩・無料・トイレあり）。ゲートから広河原登山口まで林道を約30分歩く。'
     '直通の公共交通はなく、昼神温泉からタクシー',
     'https://www.yamakei-online.com/trailhead/detail.php?id=1540', '山と溪谷オンライン・登山口案内サイト'),
]
for mid, idx, verified, text, url, src in FIX:
    r = N[mid]['routes'][idx]
    assert r.get('accessNote'), mid
    r['accessNote'] = text
    r['accessNeedsVerification'] = not verified
    r['accessSource'] = src
    r['accessSourceUrl'] = url
    r['accessLastChecked'] = '2026-10-06'
    N[mid]['mountainUpdated'] = '2026-10-06'
# 飯豊山：登山道の通行止めはルートの状態としても持つ（弥平四郎ルートのうち新長坂ルート）
N['iide']['routes'][1]['statusNote'] = '新長坂ルートは崩落で通行止め（2026-08-10現在・西会津町）。上ノ越ルートへ迂回'
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
