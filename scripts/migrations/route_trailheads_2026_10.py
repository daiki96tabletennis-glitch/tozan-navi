#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""旧構造の山のルートに「どの登山口から歩くか」（trailheadName）を付ける（2026-10-06）。

ルート名に起点が書かれているものだけを手で対応付けた。起点が読み取れないルートは None のまま残す。
あわせて、登山口欄が食い違っていた 明神ヶ岳・小金沢山・苗場山・弘法山・草戸山 を直す。
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text, map_urls

PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
TODAY = '2026-10-06'

TH = {
    'tsukuba': ['筑波山神社', '筑波山神社'],
    'kumotori': ['鴨沢', '三峯神社'],
    'amagi': ['天城縦走登山口（天城高原ゴルフ場）', '天城縦走登山口（天城高原ゴルフ場）'],
    'kobushigatake': ['毛木平', '西沢渓谷入口'],
    'mizugaki': ['瑞牆山荘', '瑞牆山荘'],
    'akagi': ['黒檜山登山口', None, None],
    'houou': ['夜叉神峠登山口', '青木鉱泉'],
    'nantaisan': ['二荒山神社中宮祠', '志津乗越'],
    'kitadake': ['広河原', '広河原'],
    'keirisan': ['竜源橋（蓼科山登山口）', '七合目登山口'],
    'kirigamine': [None, '八島ヶ原湿原'],
    'asama': ['車坂峠', '車坂峠'],
    'nasu': ['峠の茶屋', '峠の茶屋'],
    'takeson': ['川場スキー場', 'オグナほたかスキー場'],
    'tateyama': ['室堂', '室堂'],
    'tsurugi': ['室堂', '馬場島'],
    'myoko': ['燕温泉', '笹ヶ峰'],
    'makihata': ['清水（桜坂駐車場）', '清水（桜坂駐車場）'],
    'iide': ['川入（御沢野営場）', '弥平四郎'],
    'aizu_koma': ['滝沢登山口', '滝沢登山口'],
    'shirane_gunma': ['弓池', '草津温泉'],
    'bandai': ['八方台', '猪苗代スキー場'],
    'takao': ['清滝駅前', '清滝駅前'],
    'oyama': ['大山ケーブル駅', '大山ケーブルバス停'],
    'jinba': ['陣馬登山口', '高尾山口駅'],
    'kayagatake': ['深田記念公園', '深田記念公園'],
    'kentoku': ['乾徳山登山口（徳和）', '乾徳山登山口（徳和）'],
    'bonori': ['白谷沢登山口', None],
    'yakedake': ['中の湯', '上高地'],
    'kashimayari': ['扇沢', '扇沢'],
    'koganzan': ['上日川峠', '上日川峠'],
    'arafune': ['内山峠', '相沢登山口'],
    'iwasugesan': ['聖平登山口', None],
    'kurohimesan': ['大橋登山口', None],
    'adatara': ['奥岳登山口', '奥岳登山口'],
    'echigokoma': ['枝折峠', '枝折峠'],
    'hiragadake': ['鷹ノ巣登山口', '中ノ岐登山口（宿の送迎利用者のみ）'],
    'naeba': ['祓川登山口（和田小屋）', '小赤沢（長野県栄村側）'],
    'amakazari': ['雨飾高原キャンプ場', None],
    'takatsuma': ['戸隠キャンプ場', '戸隠キャンプ場'],
    'utsukushigahara': ['山本小屋', '三城いこいの広場'],
    'enasan': ['神坂峠', '広河原登山口'],
    'shiomidake': ['鳥倉登山口', '鳥倉登山口'],
    'akaisidake': ['椹島', '椹島'],
    'yakushidake': ['折立', '折立'],
    'hakusan': ['別当出合', '別当出合'],
    'karisaka': ['道の駅みとみ', '道の駅みとみ'],
    'chogatake': ['上高地', '三股'],
    'harinokidake': ['扇沢', '扇沢'],
    'izugatake': ['正丸駅', '正丸駅'],
    'bukosan': ['一ノ鳥居', '一ノ鳥居'],
    'nabewari': ['大倉', '大倉'],
    'sannotou': ['大倉', '大倉'],
    'koubousan': ['秦野駅', '鶴巻温泉駅'],
    'kagenobusan': ['小仏バス停', '小仏バス停', '相模湖駅'],
    'takagawayama': ['初狩駅', '初狩駅'],
    'kobotokeshiroyama': ['小仏バス停', '高尾山口駅', '相模湖駅'],
    'kusatoriyama': ['高尾山口駅', '高尾山口駅'],
    'nakimushiyama': ['東武日光駅', '東武日光駅'],
    'tairappyo': ['平標登山口', '平標登山口'],
    'iyogatake': ['平群天神社', '平群天神社'],
    'myojingatake': [None, '金時山から縦走'],
    'kawanoriyama': ['川乗橋バス停', '奥多摩駅'],
    'takanosuyama': ['東日原バス停', '奥多摩駅'],
    'azumayasan': ['菅平牧場', '菅平牧場'],
    'gozenyama': ['奥多摩湖バス停', '奥多摩湖バス停'],
}
touched = set()
for mid, names in TH.items():
    m = N[mid]
    assert len(names) == len(m['routes']), mid
    for r, nm in zip(m['routes'], names):
        if nm and not r.get('trailheadName'):
            r['trailheadName'] = nm; touched.add(mid)

def resync(m):
    R = m['trainRoutes']['routes']
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)

def flag(m, notes):
    m['needsVerification'] = True
    m['verifyNotes'] = (m.get('verifyNotes') or []) + notes

# 明神ヶ岳：登山口・住所・駐車場が矢倉岳（南足柄市矢倉沢）の内容だった。電車の経路どおり箱根町宮城野に合わせる
m = N['myojingatake']
m['trailhead'] = '宮城野（明神ヶ岳登山口）'
m['address'] = m['trailheadAddress'] = '神奈川県足柄下郡箱根町宮城野'
m['parking'] = '登山口に専用の駐車場はありません（周辺の駐車場は要確認）'
m['gmapUrl'], m['amapUrl'], m['mapBtnsHtml'] = map_urls({'name': '宮城野支所前 バス停', 'lat': None, 'lng': None})
m['trainAccessLabel'] = '宮城野（明神ヶ岳登山口）'
flag(m, ['ルート「矢倉沢登山口 往復」は明神ヶ岳の登山口として確認できない（時間・距離の出典不明）。宮城野・道了尊からの値で作り直しが必要', '宮城野周辺の駐車場', '地図ボタンは座標未確認のため名称検索'])
touched.add(m['id'])

# 小金沢山：登山口欄が縦走区間の名前だった
m = N['koganzan']
m['trailhead'] = '上日川峠'
touched.add(m['id'])

# 苗場山：登山口欄（和田小屋）と電車の終点（祓川登山口）の表記を揃える
m = N['naeba']
m['trailhead'] = '祓川登山口（和田小屋）'
flag(m, ['駐車場の表記が2通りある（かぐらスキー場駐車場／祓川登山口駐車場 約150台）。町の案内で未確認'])
touched.add(m['id'])

# 弘法山：運賃（692円）は秦野駅までの額。乗換駅の「鶴巻温泉駅または秦野駅」を秦野駅に統一
m = N['koubousan']
m['trailhead'] = '秦野駅'
for dep in ('shinjuku', 'omiya'):
    hit = [l for l in m['trainRoutes']['routes'][dep]['legs'] if l['station'] == '鶴巻温泉駅または秦野駅']
    assert len(hit) == 1, dep
    hit[0]['station'] = '秦野駅'
resync(m)
flag(m, ['横浜発だけ降車駅が鶴巻温泉駅（運賃600円）で、新宿・大宮発（秦野駅）と揃っていない。海老名→鶴巻温泉「8分」も未確認'])
touched.add(m['id'])

# 草戸山：FAQの「徒歩約15分」は経路データ（徒歩5分）と食い違い。Googleマップの徒歩経路は4分・240m
m = N['kusatoriyama']
hit = [q for q in m['faq'] if '徒歩約15分で登山口' in q['answer']]
assert len(hit) == 1
hit[0]['answer'] = hit[0]['answer'].replace('徒歩約15分で登山口', '徒歩約5分で登山口')
touched.add(m['id'])

for mid in touched:
    N[mid]['mountainUpdated'] = TODAY
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(' '.join(sorted(touched)))
