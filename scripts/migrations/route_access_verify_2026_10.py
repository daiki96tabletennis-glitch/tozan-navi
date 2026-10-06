#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ルート別アクセス（accessNote）のうち、事業者・自治体の情報で確認できた3本を確定に書き換える（2026-10-06）。"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
FIX = [
    ('chogatake', 1,
     '穂高駅から安曇野市の路線バス「三股線」で三股第一駐車場へ。'
     '2026年は7月17日〜10月13日のうち63日間だけの運行で、日によって便が違う。'
     '大人2,000円。WEBでの事前予約と事前決済が必須（乗車2か月前から）。'
     'バスが走らない日は車かタクシーで入る',
     'https://www.city.azumino.nagano.jp/soshiki/6/129486.html', '安曇野市（2026-08-14更新）'),
    ('kumotori', 1,
     '西武秩父駅5番乗り場から西武観光バス「三峯神社線」の終点まで約1時間20分・1,100円（三峰口駅からは800円）。'
     '西武秩父駅発は平日6便・土日祝9便。'
     '連休などは特別ダイヤになり、大幅に遅れることがある',
     'https://www.seibubus.co.jp/sp/rosen/mitsumine/', '西武バス 三峯神社線'),
    ('houou', 1,
     '韮崎駅から茅ヶ岳観光バスの「鳳凰三山登山バス」（青木鉱泉・御座石温泉行き）。'
     '2026年は6月20日〜10月12日の土日と三連休だけで、1日2往復。'
     '完全予約制（乗車の1か月前〜2日前）で当日は乗れない。'
     '車は青木鉱泉の駐車場（1日800円）',
     'https://houougoya.jp/access/', '鳳凰小屋のアクセス案内（運賃は未確認）'),
]
for mid, idx, text, url, src in FIX:
    r = N[mid]['routes'][idx]
    assert r.get('accessNote'), mid
    r['accessNote'] = text
    r['accessNeedsVerification'] = False
    r['accessSource'] = src
    r['accessSourceUrl'] = url
    r['accessLastChecked'] = '2026-10-06'
    N[mid]['mountainUpdated'] = '2026-10-06'
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
