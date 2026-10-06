#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""別の登山口から出る2本目ルートに、そこへの行き方（accessNote）を付ける（2026-10-06）。

verified=True は、サイト内で検証済みの他山データ、または駅がそのまま起点のもの。
verified=False は観光情報サイト・登山記録が出典で、事業者や自治体の情報では未確認。
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}

NOTES = [
    # (山ID, ルート番号, 文章, verified, 出典)
    ('kobushigatake', 1, '塩山駅から山梨交通「西沢渓谷線」で西沢渓谷入口まで約1時間。車は道の駅みとみ（無料）', True, 'サイト内：雁坂嶺の検証済み経路'),
    ('myoko', 1, '妙高高原駅から頸南バス「笹ヶ峰直行バス」（2026年は7月11日〜10月25日）。車は笹ヶ峰キャンプ場駐車場（約200台・500円）', True, 'サイト内：火打山の検証済み経路'),
    ('yakedake', 1, '上高地バスターミナルから歩く。マイカーは入れないので、沢渡か平湯でバスに乗り換える', True, 'サイト内：槍ヶ岳・奥穂高岳の検証済み経路'),
    ('kawanoriyama', 1, 'JR青梅線の奥多摩駅から歩き始める', True, '駅が起点'),
    ('takanosuyama', 1, 'JR青梅線の奥多摩駅から歩き始める', True, '駅が起点'),
    ('kagenobusan', 2, 'JR中央本線の相模湖駅から歩き始める', True, '駅が起点'),
    ('kobotokeshiroyama', 1, '京王線の高尾山口駅から歩き始める', True, '駅が起点'),
    ('kobotokeshiroyama', 2, 'JR中央本線の相模湖駅から歩き始める', True, '駅が起点'),
    ('jinba', 1, '京王線の高尾山口駅から歩き始める', True, '駅が起点'),
    ('koubousan', 1, '小田急線の鶴巻温泉駅から歩き始める', True, '駅が起点'),
    ('kumotori', 1, '西武秩父駅から西武観光バス「三峯神社線」の終点。車は三峯神社の市営駐車場（250台・1日520円との情報）', False, '埼玉県（路線名）、観光情報サイト（駐車場）'),
    ('houou', 1, '韮崎駅からバスがあるとの情報（事業者と運行日は未確認）。青木鉱泉の駐車場は有料', False, '登山記録'),
    ('nantaisan', 1, '路線バスはない。車は梵字飯場跡の駐車場までで、その先は林道を歩く', False, '登山記録'),
    ('keirisan', 1, '蓼科牧場から白樺高原ゴンドラで御泉水自然園へ上がり、歩いて登山口へ。車は七合目駐車場（約100台・無料・トイレあり）', False, '観光情報サイト'),
    ('takeson', 1, '路線バスは未確認。車はスキー場の駐車場（夏に使えるかは要確認）', False, '未確認'),
    ('tsurugi', 1, '路線バスはない。上市駅からタクシー（約23km）。馬場島に無料の駐車場がある', False, '観光情報サイト・登山記録'),
    ('iide', 1, '公共交通は未確認。登山口手前の林道は未舗装', False, '登山記録'),
    ('bandai', 1, '猪苗代駅から路線バス約20分、またはタクシー約10分との情報', False, '観光情報サイト'),
    ('arafune', 1, '下仁田駅から南牧村方面のバスを降りて、徒歩約90分との情報。登山口の駐車スペースは2台ほど', False, '登山記録'),
    ('hiragadake', 1, '登山口周辺で送迎をしている宿に泊まった人だけが使えるルート', False, '新潟県観光協会の案内（検索結果の記載）'),
    ('naeba', 1, '津南駅方面から路線バスとタクシーで約60分との情報。三合目の駐車場は50〜100台と情報に幅がある', False, '観光情報サイト'),
    ('utsukushigahara', 1, '車は三城いこいの広場の駐車場（50台・無料・夜間は駐車不可との情報）。松本駅からのバスは未確認', False, '観光情報サイト'),
    ('enasan', 1, '登山口へ直通の公共交通はなく、飯田駅や昼神温泉からタクシー。車は広河原駐車場（無料との情報）', False, '観光情報サイト'),
    ('chogatake', 1, '穂高駅から路線バス「三股線」（2026年は7月17日〜10月13日・WEB予約との情報）。三股第1駐車場（約80台・無料）から登山口まで徒歩約15分', False, '登山情報サイト'),
]
ids = set()
for mid, idx, text, verified, src in NOTES:
    r = N[mid]['routes'][idx]
    assert r.get('trailheadName'), (mid, idx)
    r['accessNote'] = text
    r['accessNeedsVerification'] = not verified
    r['accessSource'] = src
    r['accessLastChecked'] = '2026-10-06'
    N[mid]['mountainUpdated'] = '2026-10-06'
    ids.add(mid)
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(' '.join(sorted(ids)))
