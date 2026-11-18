#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""三頭山の都民の森へのバスを季節運行にする（2026-11-18。運営者の指示「季節運行とする（その期間はバスが他にないのか調べて）」）

前は annualItems が kind=info（期間なし）で、季節運行に数えていなかった（冬の山選び診断・アクセス難易度で冬も都民の森まで行ける扱い）。
檜原都民の森の公式（https://www.hinohara-mori.jp/access_bus/ 2026-04-01 改定の時刻表）：都民の森へのバス（武蔵五日市駅からの急行便・
数馬からの連絡バス）は4〜11月（休園日を除く毎日）と3月の土日祝だけ。都民の森発の表では平日は12/1〜3/31、休日は12/1〜2月末が運休。
冬に都民の森へ行くほかのバスは、公式の案内に無い（冬の行き方は管理事務所に確かめる、とある）。武蔵五日市駅〜数馬の西東京バス（数馬行）は
都民の森のバスとは別の路線で、そこから都民の森へは歩く（前からの注記のとおり。数馬からの歩く時間は公式に記載なし）。
奥多摩駅からの西東京バス（鴨沢西行きなど）の深山橋から登るコース3（ヌカザス山経由）は、都民の森のバスを使わない。
2026年度の運行（4/1〜11/30）を transport として入れる。3月の土日祝の分は来季（2027年3月）の発表を見て足す。何度流しても同じ結果。
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
raw = open(P, encoding='utf-8').read()
D = json.loads(raw)
m = next(x for x in D if x['id'] == 'mitosaan')
NEW = {
    'kind': 'transport',
    'label': '武蔵五日市駅・数馬〜都民の森のバス（急行便・連絡バス）',
    'validFrom': '2026-04-01',
    'validTo': '2026-11-30',
    'seasonYear': 2026,
    'sourceUrl': 'https://www.hinohara-mori.jp/access_bus/',
    'lastVerified': '2026-11-18',
    'note': '4〜11月の開園日は毎日、3月は土日祝だけ。12〜2月（3月の平日）は運休で、数馬までの路線バスで行き数馬から歩く。都民の森の休園日（月曜・祝日は翌日）も運休',
}
items = m.get('annualItems') or []
items = [a for a in items if not (a.get('kind') == 'info' and '都民の森' in (a.get('label') or ''))]
items = [a for a in items if a.get('label') != NEW['label']] + [NEW]
m['annualItems'] = items
m['mountainUpdated'] = '2026-11-18'
open(P, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=2) + ('\n' if raw.endswith('\n') else ''))
print('ok')
