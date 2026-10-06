#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ルート別アクセス（accessNote）の追加確認：磐梯山・蓼科山・苗場山・美ヶ原（2026-10-06）。

4本とも一部しか裏が取れていないため、accessNeedsVerification は True のまま（「未確認の情報を含みます」を表示）。
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
FIX = [
    ('naeba', 1,
     '車は小赤沢三合目の駐車場（約100台・舗装・トイレあり）。'
     'バスは越後湯沢駅から津南町役場前で乗り継いで小赤沢へ（44分＋56分）。小赤沢バス停から三合目登山口まで歩いて約90分。'
     '津南〜小赤沢は予約制のデマンド交通になる区間があるとの情報があり、事前に確認する',
     'https://snow-country.jp/archives/3101', '雪国観光圏（駐車場・バス停からの徒歩）。デマンド交通の区間は未確認'),
    ('keirisan', 1,
     '車は七合目登山口の駐車場（トイレは冬季以外）。'
     'バスは茅野駅からアルピコ交通で東白樺湖へ行き、たてしなスマイル交通「シラカバ線」に乗り継いで蓼科牧場へ。'
     '蓼科牧場からはゴンドラリフトで上がって歩くか、車道を歩く。'
     'ゴンドラは夏も休業期間があるので、営業日を確認する',
     'https://shirakabakogen.jp/feature/tateshinayama-tozan/', '信州たてしな観光協会（行き方の種類・トイレ）。台数・ゴンドラ営業日・バス時刻は未確認'),
    ('utsukushigahara', 1,
     '車は三城いこいの広場の駐車場（50台・無料・夜間は駐車不可との情報）。'
     '松本駅からは「美ケ原高原直行バス」があるが（2026年は6月6日〜10月12日の土日祝、7月13日〜8月31日は毎日）、終点は美ヶ原自然保護センターで、三城に停まるかは未確認',
     'https://visitmatsumoto.com/news/detail_22.html', '松本市公式観光サイト（直行バスの運行日）。三城の停車・駐車場は未確認'),
    ('bandai', 1,
     '猪苗代駅からタクシー。'
     '夏に猪苗代スキー場へ行く路線バスは確認できていない（確認できたのはスキーシーズンの無料シャトルバスだけ）',
     'https://www.inawashiro-ski.com/access/', '猪苗代スキー場アクセス案内（検索結果の記載）'),
]
for mid, idx, text, url, src in FIX:
    r = N[mid]['routes'][idx]
    assert r.get('accessNote'), mid
    r['accessNote'] = text
    r['accessNeedsVerification'] = True
    r['accessSource'] = src
    r['accessSourceUrl'] = url
    r['accessLastChecked'] = '2026-10-06'
    N[mid]['mountainUpdated'] = '2026-10-06'
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
