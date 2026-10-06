#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""登山口・駐車場・電車の行き先が食い違っていた16山＋光岳の修正（2026-10-06）。

一度きりの移行スクリプト。出典は各山のブロックのコメントに記載。
確認できなかった値は書き換えず、needsVerification / verifyNotes に残す。
"""
import json, os, sys, copy

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text, map_urls

PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
TODAY = '2026-10-06'
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))


def leg(station, icon=None, line=None, minutes=None):
    if icon is None:
        return {'station': station}
    return {'station': station, 'method': {'icon': icon, 'line': line}, 'durationMin': minutes, 'fareYen': None}


def sync(m, fares=None):
    """trainRoutes から旧フィールド（文章・所要時間・HTML）を作り直す"""
    R = m['trainRoutes']['routes']
    for dep, K in DEPS:
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
        if fares:
            m['fare' + K] = fares[dep]
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)


def rename_last(m, name, drop_walk=False):
    for dep, _ in DEPS:
        legs = m['trainRoutes']['routes'][dep]['legs']
        if drop_walk:
            assert legs[-2]['method']['icon'] == 'walk', m['id']
            del legs[-1]
            legs[-1] = {'station': legs[-1]['station']}
        legs[-1] = {'station': name}


def set_map(m, name, lat, lng):
    m['gmapUrl'], m['amapUrl'], m['mapBtnsHtml'] = map_urls({'name': name, 'lat': lat, 'lng': lng})


def faq_access(m, text):
    hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
    assert len(hit) == 1, m['id']
    hit[0]['answer'] = text


def replace_in(m, key, old, new):
    assert old in m[key], (m['id'], key, old)
    m[key] = m[key].replace(old, new)


def done(m, notes=None):
    m['mountainUpdated'] = TODAY
    if notes:
        m['needsVerification'] = True
        m['verifyNotes'] = notes


def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')


# ── 丹沢山：電車は大倉行きなのに、ルートが塩水橋（車向け）だけだった ──
# 出典：YAMAPモデルコース 94542（大倉〜塔ノ岳〜丹沢山 往復 10時間49分・18.0km・+1,751m・定数43）
m = N['tanzawa']
for r in m['routes']:
    r['trailheadName'] = '塩水橋（マイカー向け）'
m['routes'].insert(0, {
    'name': '大倉〜塔ノ岳〜丹沢山（往復）', 'time': '10時間49分', 'distance': '18.0km', 'elevation': '+1751m',
    'coeff': 43, 'waypoints': '大倉 → 塔ノ岳 → 丹沢山', 'trailheadName': '大倉',
    'source': 'YAMAPモデルコース（model-courses/94542）'})
R = m['trainRoutes']['routes']
R['shinjuku']['legs'] = [leg('新宿駅', 'train', '小田急小田原線', 70), leg('渋沢駅', 'bus', '神奈川中央交通バス', 15), leg('大倉バス停')]
R['omiya']['legs'] = [leg('大宮駅', 'train', 'JR湘南新宿ライン', 30)] + copy.deepcopy(R['shinjuku']['legs'])
R['yokohama']['legs'] = [leg('横浜駅', 'train', '相鉄本線特急', 28), leg('海老名駅', 'train', '小田急小田原線急行', 30),
                         leg('渋沢駅', 'bus', '神奈川中央交通バス', 15), leg('大倉バス停')]
m['trainRoutes']['note'] = '💡 大倉から大倉尾根を登り、塔ノ岳を経て丹沢山へ。往復18kmの長い行程なので、日帰りは健脚向け。山小屋泊も検討を'
m['trainAccessLabel'] = '大倉（塔ノ岳経由のルート）'
m['dlNoteHtml'] = m['dlNoteHtml'].replace('代表コースの塩水橋ルート（周回）は6時間・13.4km・標高差+1100m',
                                         '電車・バスで行ける大倉〜塔ノ岳〜丹沢山（往復）は10時間49分・18.0km・標高差+1751m')
for q in m['faq']:
    q['answer'] = q['answer'].replace('標準コースタイムは往復7〜8時間程度で、', 'YAMAPのモデルコースでは往復10時間49分・18.0kmの長い行程で、')
sync(m)
done(m)

# ── 蛭ヶ岳・黒部五郎岳：登山口が「A or B」表記だった ──
m = N['hirugata']
m['trailhead'] = '大倉'
m['parking'] = N['tanzawa']['parking']
m['routes'][0]['trailheadName'] = '大倉'
done(m)
m = N['kurobegorodam']
m['trailhead'] = '折立'
m['routes'][0]['trailheadName'] = '折立'
done(m, ['折立駐車場の台数・有峰林道の通行料は未確認'])

# ── 高尾山・高水三山・矢倉岳：終点が「登山口」とだけ書かれていた ──
m = N['takao']
rename_last(m, '清滝駅前（1号路・6号路・稲荷山コース入口）')
sync(m); done(m)
m = N['takamizusanzan']
rename_last(m, '高水山登山口（高源寺）')
sync(m); done(m)
m = N['yaguradake']          # 地蔵堂バス停がそのまま登山口。「徒歩20分→登山口」は根拠のない区間だった
rename_last(m, '地蔵堂バス停（登山口）', drop_walk=True)
m['trailhead'] = '地蔵堂'
sync(m); done(m)

# ── 西吾妻山：登山口が「浄土平」（東吾妻・一切経山側）になっていた ──
# 出典：Yahoo!路線情報（2026-10-17 新宿・大宮・横浜→米沢）、Googleマップ経路（米沢駅前→湯元駅 山交バス50分・970円）
m = N['azuma']
m['trailhead'] = '天元台ロープウェイ湯元駅（白布温泉）'
m['address'] = m['trailheadAddress'] = '山形県米沢市関（白布温泉）'
m['parking'] = '天元台ロープウェイ湯元駅駐車場（約300台・無料）'
m['routes'][0]['trailheadName'] = '天元台（ロープウェイとリフトで北望台へ）'
m['routes'][1]['trailheadName'] = 'グランデコ（福島県側・別の登山口）'
tail = [leg('米沢駅', 'bus', '山交バス 米沢〜白布温泉線', 50), leg('白布湯元', 'ropeway', '天元台ロープウェイ', 6), leg('天元台高原駅')]
R = m['trainRoutes']['routes']
R['shinjuku']['legs'] = [leg('新宿駅', 'train', 'JR湘南新宿ライン', 32), leg('大宮駅', 'train', '山形新幹線つばさ', 99)] + copy.deepcopy(tail)
R['omiya']['legs'] = [leg('大宮駅', 'train', '山形新幹線つばさ', 99)] + copy.deepcopy(tail)
R['yokohama']['legs'] = [leg('横浜駅', 'train', 'JR上野東京ライン', 27), leg('東京駅', 'train', '山形新幹線つばさ', 124)] + copy.deepcopy(tail)
m['trainRoutes']['note'] = ('💡 米沢駅前から山交バス「白布温泉」行きで約50分・970円。'
                            '白布湯元で降りて天元台ロープウェイに乗り、さらに夏山リフト3本で北望台へ上がる。'
                            '新宿からは大宮で山形新幹線に乗り換えるのが速くて安い')
m['trainRoutes']['summaryNote'] = '※運賃は白布湯元までの片道（ロープウェイ・リフト代は別）。ロープウェイと夏山リフトの運行期間・時刻は天元台高原の公式サイトで確認する'
m['trainAccessLabel'] = '天元台高原（ロープウェイ利用）'
sync(m, {'shinjuku': 11510, 'omiya': 11180, 'yokohama': 12270})
faq_access(m, '新宿からは大宮で山形新幹線つばさに乗り換えて米沢駅へ行き、山交バスで白布湯元まで約50分、天元台ロープウェイに乗り継ぎます。'
              f'新宿から{hm(m["trainTimeShinjuku"])}・11,510円、大宮から{hm(m["trainTimeOmiya"])}・11,180円、'
              f'横浜から{hm(m["trainTimeYokohama"])}・12,270円が目安です（乗り換えの待ち時間、ロープウェイ・リフト代は別）。'
              '車の場合は都心から約5時間が目安です。')
done(m, ['駐車場の台数・料金は観光情報サイトの記載。天元台高原の公式情報で未確認', 'ロープウェイ・夏山リフトの2026年の運行期間は未確認'])

# ── 蔵王山・和名倉山・御座山：電車の行き先が、表示している登山口と別ルートのもの ──
m = N['zaosan']
m['routes'][0]['trailheadName'] = '刈田岳（蔵王エコーライン・マイカー向け）'
m['routes'][1]['trailheadName'] = '蔵王温泉（蔵王ロープウェイで地蔵山頂駅へ）'
m['trainAccessLabel'] = '蔵王温泉（ロープウェイで地蔵山へ上がる縦走ルート）'
m['trainRoutes']['note'] = ('💡 電車・バスで行けるのは山形県側の蔵王温泉。蔵王ロープウェイで地蔵山頂駅へ上がり、地蔵山〜熊野岳〜刈田岳を歩く。'
                            '登山口欄の刈田岳（蔵王エコーライン）は車向けの入口')
sync(m); done(m, ['刈田岳（エコーライン）側へ行く路線バスの有無は未確認'])

m = N['nakawarayama']
m['routes'][0]['trailheadName'] = '三ノ瀬（マイカー向け）'
m['trainAccessLabel'] = '秩父湖（二瀬尾根ルート）'
sync(m); done(m, ['二瀬尾根ルートの時間・距離は未登録'])

m = N['kazahariyama']       # 栗生は南相木村。住所が北相木村になっていた
m['address'] = m['trailheadAddress'] = '長野県南佐久郡南相木村'
m['parking'] = '栗生登山口の駐車スペース（無料・トイレなし。台数は数台〜15台と情報に幅あり）'
m['routes'][0]['trailheadName'] = '栗生（南相木村側）'
m['trainAccessLabel'] = '白岩登山口（北相木村側・別ルート）'
m['trainRoutes']['note'] = (m['trainRoutes']['note'].rstrip('。') +
                            '。この経路は北相木村側の白岩登山口へ向かうもので、登山口欄の栗生（南相木村側）とは別の入口')
sync(m); done(m, ['栗生登山口の駐車台数', '南相木村営バスで栗生へ行く経路（バス停から登山口まで徒歩約50分との報告）は未確認', '白岩登山口ルートの時間・距離は未登録'])

# ── 南駒ヶ岳：ルートは木曽側（伊奈川ダム）なのに、登山口・電車が伊那側（菅の台）だった ──
# 出典：Yahoo!路線情報（2026-10-17 →須原：新宿7,830円／大宮7,830円／横浜7,190円）、Googleマップ（須原駅→伊奈川ダム 15分・6.9km、各出発地からの車の所要時間）
m = N['minamikomagatake']
m['trailhead'] = '伊奈川ダム上登山口'
m['address'] = m['trailheadAddress'] = '長野県木曽郡大桑村'
m['parking'] = '伊奈川ダム付近の駐車スペース（無料・トイレなし。ゲートの位置と台数は要確認）'
m['routes'][0]['trailheadName'] = '伊奈川ダム上登山口（木曽側）'
set_map(m, '伊奈川ダム', 35.6912816, 137.738549)
tail = [leg('塩尻駅', 'train', 'JR中央本線（中津川行）', 80), leg('須原駅', 'taxi', 'タクシー', 15), leg('伊奈川ダム')]
m['trainRoutes'] = {
    'badge': {'type': 'year', 'style': None, 'icon': 'check', 'label': '年中運行（駅から先はタクシー）'},
    'lineName': 'JR中央本線（須原駅）・タクシー',
    'routes': {
        'shinjuku': {'legs': [leg('新宿駅', 'train', 'JR特急あずさ', 147)] + copy.deepcopy(tail)},
        'omiya': {'legs': [leg('大宮駅', 'train', 'JR湘南新宿ライン', 31), leg('新宿駅', 'train', 'JR特急あずさ', 147)] + copy.deepcopy(tail)},
        'yokohama': {'legs': [leg('横浜駅', 'train', 'JR横浜線', 60), leg('八王子駅', 'train', 'JR特急あずさ', 114)] + copy.deepcopy(tail)},
    },
    'note': ('💡 最寄りは木曽側のJR中央本線・須原駅。駅から伊奈川ダムまで路線バスはなく、タクシーで約15分（約7km）。'
             '須原駅にタクシーが待機しているとは限らないので、事前に予約する。'
             '塩尻〜須原の普通列車は本数が少ない。'
             'ダム手前のゲートが閉まっていると、登山口まで林道を歩く'),
    'summaryNote': '※運賃は須原駅までの片道（タクシー代は別）',
    'links': [{'type': 'yahoo', 'label': '乗換案内で検索', 'url': 'https://transit.yahoo.co.jp/search/result?from=新宿&to=須原&type=1'}],
}
m['busLinks'] = ['https://transit.yahoo.co.jp/search/result?from=新宿&to=須原&type=1']
m['busScheduleLinks'] = []
m['trainAccessLabel'] = '伊奈川ダム（須原駅からタクシー）'
m['driveTimeShinjuku'] = m['driveShinjuku'] = 235
m['driveTimeOmiya'] = m['driveOmiya'] = 275
m['driveTimeYokohama'] = m['driveYokohama'] = 265
m['driveOfuna'] = m['driveTime'] = 260
m['driveTimeTachikawa'] = m['driveTachikawa'] = 225
m['driveDistance'] = 271
sync(m, {'shinjuku': 7830, 'omiya': 7830, 'yokohama': 7190})
faq_access(m, '南駒ヶ岳（越百山経由）の登山口は木曽側の伊奈川ダムです。新宿から特急あずさで塩尻へ行き、中央本線の普通列車で須原駅へ、駅からタクシーで約15分です。'
              f'新宿から{hm(m["trainTimeShinjuku"])}・7,830円、大宮から{hm(m["trainTimeOmiya"])}・7,830円、'
              f'横浜からは八王子で特急あずさに乗り{hm(m["trainTimeYokohama"])}・7,190円が目安です（乗り換えの待ち時間とタクシー代は別）。'
              '車の場合は新宿から約3時間55分です。')
replace_in(m, 'introHtml', '公共交通機関でのアクセス可（駒ヶ根駅→バス25分→菅の台バスセンター）', '公共交通は木曽側の須原駅からタクシー約15分で伊奈川ダムへ')
done(m, ['須原駅で使えるタクシー会社・料金', '伊奈川ダム手前ゲートの開閉状況と駐車台数（登山記録では上下2か所・各15台程度、ゲートから登山口まで徒歩約40分との報告）'])

# ── 聖岳・光岳：一般車は芝沢ゲートまで。便ヶ島・易老渡へは歩く ──
# 出典：環境省 南アルプス国立公園アクセス（便ヶ島登山口は平成27年秋の路肩決壊以降、通行止めが継続）、
#       Googleマップ（道の駅遠山郷→芝沢ゲート駐車場 45分・27km）
BANNER_URL = 'https://www.env.go.jp/park/minamialps/access/index.html'
m = N['hijiridade']
m['trailhead'] = '便ヶ島（芝沢ゲートから徒歩）'
m['address'] = m['trailheadAddress'] = '長野県飯田市南信濃木沢'
m['parking'] = '芝沢ゲート駐車場（約30台。料金は要確認）'
set_map(m, '芝沢ゲート駐車場', 35.3889788, 138.0414655)
m['routes'][0]['trailheadName'] = '便ヶ島（長野県側）'
m['trainAccessLabel'] = '聖沢登山口（静岡県側・別ルート）'
m['warnBanner'] = {
    'type': 'yellow', 'title': '便ヶ島へは車で入れません',
    'text': ('便ヶ島登山口へ向かう林道は、2015年秋の路肩決壊から一般車の通行止めが続いています（環境省）。'
             '車は芝沢ゲートまでで、その先は林道を歩きます。'
             '便ヶ島〜西沢渡の区間は歩行者も通行止めとの情報があり（2025年時点）、2026年の状況は未確認です。'
             '出発前に飯田市の最新情報を必ず確認してください。'),
    'url': BANNER_URL, 'linkText': '環境省のアクセス情報'}
m['trainRoutes']['note'] = (m['trainRoutes']['note'].rstrip('。') +
                            '。この経路は静岡県側の聖沢登山口へ向かうもので、登山口欄の便ヶ島（長野県側）とは別の入口')
hit = [q for q in m['faq'] if 'アクセス方法' in q['question']][0]
hit['answer'] = '電車・バスで行けるのは静岡県側の聖沢登山口です。' + hit['answer'] + '長野県側の便ヶ島へは、車で芝沢ゲートまで入り、その先を歩きます。'
sync(m); done(m, ['便ヶ島〜西沢渡の2026年の通行可否', '芝沢ゲート駐車場の料金', '聖沢登山口ルートの時間・距離は未登録'])

m = N['terkari']
m['trailhead'] = '易老渡（芝沢ゲートから徒歩約5km）'
m['address'] = m['trailheadAddress'] = '長野県飯田市南信濃木沢'
m['parking'] = '芝沢ゲート駐車場（約30台。料金は要確認）'
set_map(m, '芝沢ゲート駐車場', 35.3889788, 138.0414655)
m['routes'][0]['trailheadName'] = '易老渡'
for dep, _ in DEPS:
    legs = m['trainRoutes']['routes'][dep]['legs']
    assert legs[-2]['method']['icon'] == 'taxi' and legs[-1]['station'] == '易老渡'
    legs[-2]['durationMin'] = 45
    legs[-1] = {'station': '芝沢ゲート', 'method': {'icon': 'walk', 'line': '徒歩（林道 約5km）'}, 'durationMin': None, 'fareYen': None}
    legs.append({'station': '易老渡'})
replace_in(m['trainRoutes'], 'note', '易老渡・便ヶ島へは道の駅遠山郷等から', '一般車・タクシーは芝沢ゲートまで（道の駅遠山郷から約45分）。その先の易老渡までは林道を約5km歩く。芝沢ゲートへは道の駅遠山郷等から')
m['trainAccessLabel'] = '芝沢ゲート（易老渡へは徒歩）'
sync(m)
hit = [q for q in m['faq'] if 'アクセス方法' in q['question']][0]
hit['answer'] = (f'光岳へは新宿から高速バスで飯田駅まで約4時間10分、南信州バスで道の駅遠山郷まで約1時間10分、そこから予約制タクシーで芝沢ゲートまで約45分です。'
                 f'新宿から{hm(m["trainTimeShinjuku"])}・運賃約24,800円が目安（大宮・横浜は新宿経由でほぼ同程度）。'
                 '車とタクシーが入れるのは芝沢ゲートまでで、易老渡へは林道を約5km歩きます。タクシーは早朝発の事前予約制（メーター制、1.5〜2万円程度）のため前泊が必要です。')
done(m, ['芝沢ゲート駐車場の料金', '芝沢ゲート〜易老渡の徒歩時間', '運賃にタクシー代の概算が含まれている（正式な額は未確認）'])

# ── 農鳥岳：ルートは広河原発なのに、電車が下山口の奈良田行きだった ──
m = N['noutori']
k = N['kitadake']
m['trainRoutes'] = copy.deepcopy(k['trainRoutes'])
m['trainRoutes']['note'] = (k['trainRoutes']['note'].rstrip('。') +
                            '。農鳥岳は広河原から北岳・間ノ岳を経て歩き、奈良田（大門沢）へ下るのが一般的。'
                            '下山後は奈良田温泉から、はやかわ乗合バスで身延駅へ出る（前日19時までの予約制・1日4往復）')
for key in ('busLinks', 'busScheduleLinks'):
    m[key] = copy.deepcopy(k.get(key))
m['routes'][0]['trailheadName'] = '広河原（下山は奈良田）'
m['trainAccessLabel'] = '広河原（入山口）'
sync(m, {'shinjuku': k['fareShinjuku'], 'omiya': k['fareOmiya'], 'yokohama': k['fareYokohama']})
for dep, K in DEPS:
    m['trainTime' + K] = k['trainTime' + K]
m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
faq_access(m, '農鳥岳は広河原から北岳・間ノ岳を経て縦走し、奈良田へ下山するのが一般的です。行きは新宿から特急あずさ・かいじで甲府駅へ、山梨交通の南アルプス登山バスで広河原まで約1時間50分です。'
              f'新宿から{hm(m["trainTimeShinjuku"])}・{m["fareShinjuku"]:,}円、大宮から{hm(m["trainTimeOmiya"])}・{m["fareOmiya"]:,}円、'
              f'横浜から{hm(m["trainTimeYokohama"])}・{m["fareYokohama"]:,}円が目安です。'
              '下山後は奈良田温泉から、はやかわ乗合バス（前日19時までの予約制）で身延駅へ出ます。')
done(m)

# ── 日向山：タクシーは尾白川渓谷駐車場まで。矢立石登山口へは徒歩約50分 ──
# 出典：やまなし観光推進機構（矢立石 約10台／尾白川渓谷 約100台・矢立石まで徒歩約50分／林道は12月初旬〜4月下旬に冬季閉鎖／
#       矢立石〜錦滝の県営林道は大規模崩落で歩行者も通行禁止）、Googleマップ（小淵沢駅→尾白川渓谷駐車場 18分・11.1km）
m = N['hinata']
m['parking'] = '矢立石登山口（約10台・無料）／尾白川渓谷駐車場（約100台・トイレあり。矢立石まで徒歩約50分）'
m['routes'][0]['trailheadName'] = '矢立石'
m['routes'][1]['trailheadName'] = '矢立石'
m['routes'][1]['status'] = {'state': 'closed', 'label': '通行禁止（林道崩落）'}
for dep, _ in DEPS:
    legs = m['trainRoutes']['routes'][dep]['legs']
    assert legs[-1]['station'] == '尾白川渓谷駐車場'
    legs[-1] = leg('尾白川渓谷駐車場', 'walk', '徒歩', 50)
    legs.append({'station': '矢立石登山口'})
m['trainRoutes']['note'] = ('💡 小淵沢駅からタクシーで尾白川渓谷駐車場まで約20分。そこから矢立石登山口まで徒歩約50分。'
                            '矢立石までの林道は狭く、例年12月初旬〜4月下旬は冬季閉鎖。'
                            '長坂駅・日野春駅から市民バスを使う方法もあるが、バス停から登山口まで徒歩約2時間かかる')
m['trainAccessLabel'] = '尾白川渓谷駐車場（矢立石登山口へは徒歩）'
m['warnBanner'] = {
    'type': 'yellow', 'title': '錦滝方面は通行禁止',
    'text': ('矢立石登山口から錦滝へ向かう県営林道は、大規模な崩落のため歩行者も通行禁止です。錦滝経由の周回はできません。'
             '矢立石までの林道は例年12月初旬〜4月下旬に冬季閉鎖されます。'),
    'url': 'https://www.yamanashi-kankou.jp/kankou/spot/p2_2225.html', 'linkText': '山梨県の観光案内'}
sync(m)
faq_access(m, 'JR小淵沢駅からタクシーで尾白川渓谷駐車場まで約20分、そこから矢立石登山口まで徒歩約50分です。'
              f'新宿からは特急あずさで{hm(m["trainTimeShinjuku"])}・7,930円、大宮からは新宿で特急あずさに乗り{hm(m["trainTimeOmiya"])}・7,930円、'
              f'横浜からは八王子で特急あずさに乗り{hm(m["trainTimeYokohama"])}・7,270円が目安です（タクシー代込みの目安）。')
done(m, ['運賃にタクシー代の概算が含まれている（正式な額は未確認）', '錦滝方面の通行禁止が現在も続いているか'])

# ── 黒姫山：「黒姫高原シャトルバスで古池登山口」は確認できない経路。駅からタクシーで大橋登山口へ ──
# 出典：Yahoo!路線情報（2026-10-17 →黒姫：新宿7,999円／大宮7,339円／横浜9,539円）、Googleマップ（黒姫駅→大橋林道口駐車場 18分・11.6km）
m = N['kurohimesan']
m['trailhead'] = '大橋登山口（大橋林道口）'
m['parking'] = '大橋林道口駐車場（無料。台数は要確認）'
m['routes'][0]['trailheadName'] = '大橋登山口'
tail = [leg('長野駅', 'train', 'しなの鉄道北しなの線', 35), leg('黒姫駅', 'taxi', 'タクシー', 18), leg('大橋登山口')]
R = m['trainRoutes']['routes']
R['shinjuku']['legs'] = [leg('新宿駅', 'train', 'JR湘南新宿ライン', 31), leg('大宮駅', 'train', '北陸新幹線かがやき', 54)] + copy.deepcopy(tail)
R['omiya']['legs'] = [leg('大宮駅', 'train', '北陸新幹線かがやき', 54)] + copy.deepcopy(tail)
R['yokohama']['legs'] = [leg('横浜駅', 'train', 'JR上野東京ライン', 26), leg('東京駅', 'train', '北陸新幹線かがやき', 77)] + copy.deepcopy(tail)
m['trainRoutes']['badge'] = {'type': 'year', 'style': None, 'icon': 'check', 'label': '年中運行（駅から先はタクシー）'}
m['trainRoutes']['note'] = ('💡 黒姫駅から大橋登山口まで路線バスはなく、タクシーで約18分（約12km）。'
                            '帰りのタクシーも行きの時点で予約しておく。'
                            '長野駅での北しなの線への乗り継ぎは、待ち時間が長くなることがある')
m['trainRoutes']['summaryNote'] = '※運賃は黒姫駅までの片道（タクシー代は別）'
m['trainAccessLabel'] = '大橋登山口（黒姫駅からタクシー）'
sync(m, {'shinjuku': 7999, 'omiya': 7339, 'yokohama': 9539})
faq_access(m, '最寄りはしなの鉄道北しなの線の黒姫駅で、駅から大橋登山口まではタクシーで約18分です（路線バスはありません）。'
              f'新宿からは大宮で北陸新幹線に乗り換えて{hm(m["trainTimeShinjuku"])}・7,999円、大宮から{hm(m["trainTimeOmiya"])}・7,339円、'
              f'横浜から{hm(m["trainTimeYokohama"])}・9,539円が目安です（乗り換えの待ち時間とタクシー代は別）。'
              '車の場合は都心から約4時間10分が目安です。')
replace_in(m, 'introHtml', '公共交通機関でのアクセス可（黒姫駅→バス20分→古池登山口（季節））', '公共交通は黒姫駅からタクシー約18分で大橋登山口へ')
done(m, ['大橋林道口駐車場の台数', '黒姫駅のタクシー料金'])

# ── 金時山：住所が静岡県小山町、駐車場が「乙女峠駐車場」になっていた（バス停・地図は箱根町仙石原の金時神社入口） ──
# 出典：環境省 富士箱根伊豆国立公園 金時山コース（金時神社入口→公時神社→金時山→矢倉沢峠→金時登山口 2時間30分・4.6km）
m = N['kintoki']
m['trailhead'] = '金時神社入口・乙女口（箱根町仙石原）'
m['address'] = m['trailheadAddress'] = '神奈川県足柄下郡箱根町仙石原'
m['parking'] = '金時神社入口周辺の駐車場（無料・有料あり。台数と料金は要確認）'
m['routes'][0]['trailheadName'] = '乙女口'
m['routes'].append({
    'name': '公時神社〜金時山〜矢倉沢峠', 'time': '2時間30分', 'distance': '4.6km',
    'waypoints': '金時神社入口 → 公時神社 → 金時山 → 矢倉沢峠 → 金時登山口', 'trailheadName': '金時神社入口',
    'source': '環境省 富士箱根伊豆国立公園 コース06'})
rename_last(m, '金時神社入口（金時登山口・乙女口にも停車）')
m['trainAccessLabel'] = '金時神社入口・金時登山口・乙女口'
sync(m); done(m, ['駐車場の台数・料金（無料約30台・有料800円/日との情報）', '公時神社ルートの累積標高'])

# ── 鋸岳：林道バスの拠点は仙流荘前から「戸台パーク」に変わっている ──
m = N['nokogiriyama']
m['trailhead'] = '戸台パーク'
m['address'] = m['trailheadAddress'] = '長野県伊那市長谷黒河内'
m['parking'] = '戸台パーク駐車場（有料。台数と料金は要確認）'
m['routes'][0]['trailheadName'] = '戸台パーク（戸台河原へは徒歩）'
rename_last(m, '戸台パーク')
m['trainAccessLabel'] = '戸台パーク'
m['warnBanner'] = {
    'type': 'yellow', 'title': '戸台河原駐車場は使えません',
    'text': ('戸台河原駐車場は利用不可で、戸台河原へ向かう市道黒河内線は通行止め、周辺の路上駐車も禁止との情報があります（長野県の山岳情報）。'
             '車は戸台パークに停め、そこから歩く計画にしてください。'
             'コースの時間・距離は戸台河原を起点にした値のため、戸台パークからの歩きが加わります。'
             '最新の状況は伊那市の案内で確認してください。'),
    'url': BANNER_URL, 'linkText': '環境省のアクセス情報'}
sync(m); done(m, ['戸台パーク駐車場の台数・料金（約700台・1,000円との情報）', '市道黒河内線の通行止めが現在も続いているか', '戸台パーク〜戸台河原の徒歩時間'])

json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('updated', sum(1 for x in D if x.get('mountainUpdated') == TODAY))
