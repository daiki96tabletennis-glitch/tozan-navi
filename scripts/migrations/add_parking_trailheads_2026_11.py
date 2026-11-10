#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""駐車場がどの登山口・どのコースに対応しているかを持たせる（2026-11-10。運営者の指示「駐車場がどこの登山口に対応しているのかわかる様にしたい」）。

mountains.json の各山に parkingTrailheads を足す：
  [{"name": 登山口の名前, "routes": [コースの番号（1から）], "by": 乗り換える乗り物（無ければ空）}]
山ページの車のタブの「駐車場」の欄に「対応する登山口」の行として出す（gen_mountain_pages.py の parking_trailheads_row）。
対応しないコースは「別の登山口」として登山口の名前だけ添える。

決め方：地図ボタンの行き先（駐車場）と、各コースの登山口（trailheadName）・歩き始め（waypoints の最初）・コース名の最初の地名を照らし、
山ごとに目で確かめた。歩いて数分〜数十分の登山口も「対応する」に入れた（鳥倉林道ゲート→鳥倉登山口、芝沢ゲート→易老渡など。コース名・登山口の名前に書いてあるもの）。
乗り換える山（芦安・畑薙・沢渡・戸台パーク・立山駅など）は、乗り換えた先の登山口と乗り物を書く。

入れていない山（要確認。駐車場の欄の文と地図の行き先が食い違う・どのコースも駐車場から始まらない）：
- 陣馬山：欄は和田峠駐車場、地図は陣馬高原下のバス停。コースは陣馬高原下から
- 御岳山：欄は御岳平駐車場、地図は滝本駅（ケーブルカーの下の駅）
- 日和田山：欄は高麗神社周辺、地図は日和田山登山口
- 高尾山：欄は高尾山IC周辺の駐車場（場所が広い）
- 弘法山：欄は秦野中井IC付近
- 蓼科山：駐車場は竜源橋、コースは七合目登山口・すずらん峠から
- 岩菅山：駐車場は聖平登山口、コースは一の瀬・東館山から
- 聖岳：駐車場は芝沢ゲート（長野側）、コースは静岡側（聖沢登山口・椹島）から
- 太平山：駐車場は山頂近くの謙信平、コースは表参道入口・大中寺・岩舟駅から
- 鋸山（千葉）：駐車場はロープウェイの山麓駅、コースは浜金谷から
- 鷹ノ巣山：地図は東日原、コースは峰谷・水根から（CLAUDE.md の要確認）
- 駐車場の欄が空・「確認できていない」の山

  python3 scripts/migrations/add_parking_trailheads_2026_11.py
何度流しても同じ結果。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH = os.path.join(ROOT, 'data', 'mountains.json')


def T(name, routes, by=''):
    return {'name': name, 'routes': routes, 'by': by}


PT = {
    'tanzawa': [T('大倉', [1])],
    'fuji': [T('富士宮口五合目', [1], 'マイカー規制の期間はシャトルバスに乗り換え')],
    'tsukuba': [T('筑波山神社', [1])],
    'kumotori': [T('鴨沢（小袖登山口）', [1, 3])],
    'amagi': [T('天城縦走登山口（天城高原）', [1, 2, 3])],
    'okutama': [T('上日川峠', [1, 3])],
    'ryokami': [T('日向大谷口', [1])],
    'kobushigatake': [T('毛木平', [1, 2])],
    'mizugaki': [T('瑞牆山荘', [1, 3])],
    'akagi': [T('黒檜山登山口', [1, 2])],
    'kinpusan': [T('大弛峠', [1])],
    'houou': [T('夜叉神峠登山口', [1, 3])],
    'nantaisan': [T('二荒山神社中宮祠（登拝門）', [1, 3])],
    'kitadake': [T('広河原', [1, 2, 3], 'バスに乗り換え')],
    'yatsugatake': [T('美濃戸口', [2])],
    'kirigamine': [T('霧ヶ峰（チャプリン）', [4])],
    'asama': [T('車坂峠（高峰高原）', [1, 2])],
    'tanigawa': [T('天神平', [1], 'ロープウェイに乗り換え'), T('西黒尾根登山口', [2, 3])],
    'nasu': [T('峠の茶屋登山口', [1, 2, 3])],
    'nikko_shirane': [T('丸沼高原ロープウェイ山頂駅', [1], 'ロープウェイに乗り換え')],
    'takeson': [T('川場スキー場リフト終点', [2], 'リフトに乗り換え')],
    'komagatake': [T('北沢峠', [1], '南アルプス林道バスに乗り換え')],
    'senjogatake': [T('北沢峠', [1], '南アルプス林道バスに乗り換え')],
    'shirouma': [T('栂池自然園', [1], 'ゴンドラ・ロープウェイに乗り換え')],
    'norikura': [T('畳平', [1], 'シャトルバスに乗り換え')],
    'tateyama': [T('室堂', [1, 2], 'ケーブルカー・バスに乗り換え')],
    'tsurugi': [T('室堂', [1, 3], 'ケーブルカー・バスに乗り換え')],
    'yari': [T('上高地バスターミナル', [1], 'バスに乗り換え')],
    'hotaka': [T('上高地バスターミナル', [1, 2], 'バスに乗り換え')],
    'chogatake': [T('上高地バスターミナル', [1], 'バスに乗り換え')],
    'myoko': [T('燕温泉', [1, 3])],
    'makihata': [T('清水（桜坂駐車場）', [1, 2, 3])],
    'iide': [T('川入（御沢野営場）', [1, 3])],
    'shibutsu': [T('鳩待峠', [1, 2], '乗合バス・タクシーに乗り換え')],
    'aizu_koma': [T('滝沢登山口', [1, 2, 3])],
    'shirane_gunma': [T('草津温泉', [2])],
    'bandai': [T('八方台', [1])],
    'hiuchigatake': [T('御池', [1, 2, 3])],
    'oyama': [T('大山ケーブルバス停', [2]), T('大山ケーブルカー 阿夫利神社駅', [1], 'ケーブルカーに乗り換え')],
    'tonosaki': [T('大倉', [1, 3])],
    'hirugata': [T('大倉', [1])],
    'kintoki': [T('金時神社入口', [1, 2])],
    'kayagatake': [T('深田記念公園', [1, 2, 3])],
    'kentoku': [T('乾徳山登山口（徳和）', [1, 2])],
    'hinata': [T('矢立石登山口', [1, 3])],
    'bonori': [T('さわらびの湯', [1, 3])],
    'otake': [T('御岳山駅', [1], 'ケーブルカーに乗り換え')],
    'jonengatake': [T('一ノ沢', [1], 'タクシーに乗り換え')],
    'yakedake': [T('新中の湯登山口', [1, 3])],
    'kashimayari': [T('柏原新道登山口（扇沢）', [1, 3])],
    'koganzan': [T('上日川峠', [1])],
    'arafune': [T('内山峠', [1])],
    'asamamakurayama': [T('浅間隠山登山口（二度上峠側）', [1, 3])],
    'kazahariyama': [T('栗生登山口', [1])],
    'iizunasan': [T('一ノ鳥居登山口（一ノ鳥居苑地）', [1, 3])],
    'kurohimesan': [T('大橋登山口（大橋林道口）', [1, 3])],
    'kenashiyama': [T('麓登山口', [1, 2, 3])],
    'shirasunayama': [T('白砂山登山口（野反湖）', [1, 2])],
    'nanaitsurasan': [T('羽衣（表参道入口）', [1, 2, 3])],
    'arasawadake': [T('銀山平登山口', [1, 2])],
    'nakawarayama': [T('三ノ瀬登山口', [1])],
    'yarigatake2': [T('老平登山口', [1, 2])],
    'gakedake': [T('白沢登山口', [1, 2])],
    'arikayama': [T('有明荘', [2])],
    'keizandake': [T('仲仙寺登山口', [1])],
    'adatara': [T('あだたら山ロープウェイ山頂駅', [1], 'ロープウェイに乗り換え'), T('奥岳登山口', [2])],
    'azuma': [T('西吾妻山登山口（天元台・リフト終点）', [1], 'ロープウェイ・リフトに乗り換え')],
    'echigokoma': [T('枝折峠', [1])],
    'hiragadake': [T('平ヶ岳登山口（鷹ノ巣）', [1])],
    'naeba': [T('祓川登山口（和田小屋）', [1])],
    'amakazari': [T('雨飾高原登山口', [1])],
    'hiuchi': [T('笹ヶ峰', [1, 2])],
    'takatsuma': [T('戸隠キャンプ場', [1, 2])],
    'kasagatake': [T('新穂高温泉', [1, 2])],
    'ontakesan': [T('田の原', [1])],
    'goryudake': [T('アルプス平（地蔵の頭）', [1, 2], 'テレキャビンに乗り換え')],
    'sukai': [T('銀山平（皇海山登山口）', [1, 2])],
    'kisokoma': [T('千畳敷', [1, 2], 'バス・ロープウェイに乗り換え')],
    'utsukushigahara': [T('山本小屋', [2])],
    'karamatsu': [T('八方池山荘（リフト終点）', [1, 2, 3], 'ゴンドラ・リフトに乗り換え')],
    'utsugi': [T('空木岳登山口（駒ヶ根高原）', [1])],
    'enasan': [T('神坂峠登山口', [2])],
    'shiomidake': [T('鳥倉登山口', [1, 2])],
    'arakawadake': [T('椹島', [1, 2], '送迎バスに乗り換え')],
    'akaisidake': [T('椹島', [1, 2], '送迎バスに乗り換え')],
    'terkari': [T('易老渡', [1])],
    'yakushidake': [T('折立', [1])],
    'kurobegorodam': [T('折立', [1, 3])],
    'ainodake': [T('広河原', [1, 2], 'バスに乗り換え')],
    'noutori': [T('広河原', [2], 'バスに乗り換え')],
    'hakusan': [T('別当出合', [1, 2])],
    'zaosan': [T('蔵王山頂レストハウス（刈田）', [1])],
    'karisaka': [T('雁坂峠登山口（道の駅みとみ）', [1, 2])],
    'nokogiriyama': [T('戸台', [1])],
    'minamikomagatake': [T('伊奈川ダム登山口', [1, 2])],
    'otenshoudake': [T('中房温泉（燕岳登山口）', [1, 2, 3])],
    'tsubakurodake': [T('中房温泉（燕岳登山口）', [1, 2])],
    'harinokidake': [T('扇沢（針ノ木岳登山口）', [1, 2, 3])],
    'eboshidake_kita': [T('高瀬ダム（ブナ立尾根登山口）', [1, 2], 'タクシーに乗り換え')],
    'noguchigoro': [T('高瀬ダム（ブナ立尾根登山口）', [1, 2], 'タクシーに乗り換え')],
    'takamizusanzan': [T('軍畑駅', [1, 2, 3])],
    'tenzandake': [T('飯能中央公園', [2])],
    'izugatake': [T('正丸駅', [1, 2, 3])],
    'bukosan': [T('一ノ鳥居', [1, 2])],
    'nabewari': [T('大倉', [1, 2])],
    'sannotou': [T('大倉', [3])],
    'kagenobusan': [T('小仏バス停', [1, 3])],
    'takagawayama': [T('初狩駅', [1, 2, 3])],
    'tairappyo': [T('平標登山口', [1, 2, 3])],
    'tomisan': [T('富山登山口（福満寺）', [1, 3])],
    'iyogatake': [T('平群天神社', [1, 2, 3])],
    'yaguradake': [T('地蔵堂', [1, 2])],
    'kawanoriyama': [T('川乗橋バス停', [1])],
    'momakurasan': [T('大月市営総合グラウンド（百蔵山登山口）', [2])],
    'ogiyama': [T('梨ノ木平登山口', [1, 3])],
    'mitosaan': [T('檜原都民の森', [1, 2])],
    'azumayasan': [T('菅平牧場', [1, 2])],
    'gozenyama': [T('奥多摩湖', [1, 2, 3])],
    'tengudake': [T('渋の湯', [1, 3])],
    'kitayokodake': [T('北八ヶ岳ロープウェイ山頂駅', [1, 2, 3], 'ロープウェイに乗り換え')],
    'nyukasayama': [T('ゴンドラ山頂駅', [1, 2], 'ゴンドラに乗り換え')],
    'nishihotaka': [T('新穂高ロープウェイ西穂高口駅', [1, 2], 'ロープウェイに乗り換え')],
    'myogisan': [T('妙義神社', [1, 2, 3])],
    'sennokurayama': [T('平標登山口', [1])],
    'houkyozan': [T('宝篋山小田休憩所', [1, 2])],
    'ryugatake': [T('本栖湖キャンプ場（竜ヶ岳登山道入口）', [1, 3])],
    'narukamiyama': [T('駒形登山口', [1, 3])],
    'bukkasan': [T('仏果山登山口', [1])],
    'dodairasan': [T('剣ヶ峰駐車場', [2])],
    'mitsutoge': [T('三ツ峠登山口', [1, 3])],
}

D = json.load(open(PATH, encoding='utf-8'))
by = dict((m['id'], m) for m in D)
n = 0
for mid, ents in sorted(PT.items()):
    m = by[mid]
    nr = len(m.get('routes') or [])
    seen = set()
    for e in ents:
        for r in e['routes']:
            assert 1 <= r <= nr and r not in seen, (mid, r)
            seen.add(r)
    if m.get('parkingTrailheads') != ents:
        m['parkingTrailheads'] = ents
        n += 1
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok', len(PT), 'mountains,', n, 'changed')
