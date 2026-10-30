#!/usr/bin/env python3
"""宝篋山・竜ヶ岳・鳴神山・仏果山・堂平山・高松山を data/mountains.json に足す（2026-10-31。運営者の指示。
「関東近郊で冬もアイゼンなしで登りやすく、景色が良く、そこそこ歩きごたえのある有名な山」。6山を足したときと同じやり方）。

出典と判断
- コース：YAMAP の山のページのモデルコース（時間・距離・累積標高差。2026-10-31 に各コースのページで確認）。
  電車・バスで着く場所から歩けるコースを各山1本以上入れた（高松山は新松田駅から山北駅へ歩く縦走を代表にした）。
- 難易度：YAMAP の山の難易度（技術的難易度・体力度）と、サイトの似た山（大野山・高川山・官ノ倉山）の区分に合わせた。
  宝篋山・仏果山・鳴神山＝初級。竜ヶ岳・堂平山・高松山＝初〜中級（代表コースが4時間半〜6時間半）。
- 電車：Yahoo!路線情報（2026-11-07(土)朝発で検索。きっぷの運賃。新幹線・有料特急を使わない経路。竜ヶ岳の大宮発だけ特急「富士回遊」）。
- バス：
  宝篋山＝つくば市「つくバス小田シャトル」休日時刻表・運賃表（令和8年4月）。つくばセンター〜小田東部は直行の便で40分（大穂窓口センターを回る便は約1時間）、
    運賃300円。小田東部〜宝篋山小田休憩所は徒歩約7分（YAMA HACK のアクセス案内・登山記録）。
  竜ヶ岳＝富士急バス「鳴沢・精進湖・本栖湖周遊バス（ブルーライン）」の公式の時刻表（河口湖駅〜本栖湖 57分）。運賃は公式サイトに区間ごとの額が無く
    （区間制運賃・大人最低180円）、Yahoo!路線情報の 1,470円。「本栖湖」バス停は県営本栖湖駐車場の前（国土交通省 関東の富士見百景【111】）。
  鳴神山＝桐生市「おりひめバス川内線時刻表」（令和6年5月10日改正）。桐生駅北口〜吹上は直行の便で32分（川内町を回る便は約55分）。
    運賃は全線200円（桐生市の案内）。吹上〜駒形登山口は徒歩約20分（登山記録。山と溪谷オンライン）。
  仏果山＝神奈川中央交通「厚20」本厚木駅〜仏果山登山口 43分・790円（Yahoo!路線情報）。
  堂平山＝東秩父村路線バス（イーグルバス）土日祝時刻表（令和6年4月1日改正）・運賃表（令和元年10月1日）。小川町駅〜皆谷 31分・510円（小川町ゾーン〜落合ゾーン）。
  高松山＝新松田駅から歩く。山北駅〜高松山入口は山北町の町内循環バスで約5分（神奈川県の資料）。
- 車：Googleマップの経路検索（車）で 2026-10-31 の深夜に測った最速ルートの時間を5分単位に丸めた。記録は drive_times_low_six_2026_10.json。
  行き先は宝篋山第二駐車場・本栖湖駐車場・駒形登山口・大棚沢広場駐車場・剣ヶ峰駐車場・高松山入口バス停（高松山は登山口の駐車場を確認できていない）。
- 装備の時期：関東の低山は標高1,200mが目安（サイトの決まり）なので、竜ヶ岳（1,485m）以外の5山は通年アイゼン不要。
  竜ヶ岳は現地の情報で確かめられず、同じ富士五湖の石割山（1,413m）と同じ区分にした（12〜2月は軽アイゼン等。要確認）。
- 紹介文・特徴：YAMAP の山の紹介文（宝篋山・竜ヶ岳・鳴神山・仏果山・堂平山）、YAMAP の山のデータの高松山の説明、神奈川県の資料、
  国土交通省 関東の富士見百景、YAMAP マガジン（鳴神山）に書かれていることだけ。YAMAP の AI の要約は使っていない。

  python3 scripts/migrations/add_low_six_2026_10.py
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section  # noqa: E402
from build_derived import ranges  # noqa: E402

PATH = os.path.join(ROOT, 'data', 'mountains.json')
TODAY = '2026-10-31'
D = json.load(open(PATH, encoding='utf-8'))
BY = {m['id']: m for m in D}
NEW = ['houkyozan', 'ryugatake', 'narukamiyama', 'bukkasan', 'dodairasan', 'takamatsuyama']
if any(i in BY for i in NEW):
    sys.exit('すでにあります')

W, L, N = 'winter_gear', 'light_crampons', 'no_crampons'
CLS = {W: 's-hard', L: 's-gear', N: 's-ok'}
FIELDS = [('driveTimeShinjuku', 'driveShinjuku'), ('driveTimeOmiya', 'driveOmiya'), ('driveTimeYokohama', 'driveYokohama'),
          ('driveOfuna', 'driveTime'), ('driveTimeTachikawa', 'driveTachikawa')]
CHECK = ('<svg class="rec-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
         'stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>')
TPL = BY['tsubakurodake']
LOW = BY['ohnoyama']      # 関連するまとめは低山の大野山の形を使う
ALLN = [N] * 12


def leg(st, icon=None, line=None, mins=None):
    d = {'station': st}
    if icon:
        d['method'] = {'icon': icon, 'line': line}
        d['durationMin'] = mins
        d['fareYen'] = None
    return d


def gmap(lat, lng, q):
    from urllib.parse import quote
    g = 'https://www.google.com/maps/search/?api=1&query=%s%%2C%s' % (lat, lng)
    a = 'https://maps.apple.com/?ll=%s,%s&q=%s' % (lat, lng, quote(q))
    btn = ('<div class="map-btns"><a href="%s" target="_blank" class="map-btn-link">Googleマップ</a>\n'
           '<a href="%s" target="_blank" class="map-btn-link">Apple Maps</a>\n</div>' % (g, a))
    return g, a, btn


def route(name, time, dist, up, down, wp, th, cid):
    return {'name': name, 'time': time, 'distance': dist, 'elevation': '+%dm' % up, 'descent': '-%dm' % down, 'waypoints': wp,
            'trailheadName': th, 'source': 'YAMAPモデルコース（model-courses/%s）' % cid,
            'sourceUrl': 'https://yamap.com/model-courses/%s' % cid, 'lastVerified': TODAY}


def fmt(v):
    h, mi = divmod(v, 60)
    if not h:
        return '%d分' % mi
    return '%d時間%d分' % (h, mi) if mi else '%d時間' % h


def arrow(legs):
    out = ''
    for x in legs:
        out += x['station']
        if x.get('method'):
            out += '→%s約%s→' % (x['method']['line'], fmt(x['durationMin']))
    return out


def yahoo(frm, to):
    return 'https://transit.yahoo.co.jp/search/result?from=%s&to=%s&type=1' % (frm, to)


YEAR = {'type': 'year', 'style': None, 'icon': 'check', 'label': '年中運行'}
M = {}

# ---------------- 宝篋山 ----------------
TSUKU = [leg('つくば駅', 'walk', '徒歩', 5), leg('つくばセンター', 'bus', 'つくバス「小田シャトル」', 40),
         leg('小田東部', 'walk', '徒歩', 7), leg('宝篋山小田休憩所')]
M['houkyozan'] = dict(
    name='宝篋山', kana='ほうきょうさん', elevation=461, area='茨城県', category='人気の山', difficulty='初級', daytrip=True,
    lat=36.167503, lng=140.130073, yamapUrl='https://yamap.com/mountains/469', yamapName='宝篋山',
    map=(36.152955, 140.119073, '宝篋山第二駐車場'), trailhead='宝篋山小田休憩所',
    parking='宝篋山小田休憩所の駐車場（無料・約20台）と第二駐車場（無料・約50〜70台）。休日の朝は満車になりやすい',
    address='茨城県つくば市小田',
    drive=[69, 69, 84, 105, 95],
    legs={'shinjuku': [leg('新宿駅', 'train', 'JR中央線快速・総武線（御茶ノ水乗換）', 11), leg('秋葉原駅', 'train', 'つくばエクスプレス', 46)] + copy.deepcopy(TSUKU),
          'omiya': [leg('大宮駅', 'train', 'JR京浜東北線', 13), leg('南浦和駅', 'train', 'JR武蔵野線', 25), leg('南流山駅', 'train', 'つくばエクスプレス', 23)] + copy.deepcopy(TSUKU),
          'yokohama': [leg('横浜駅', 'train', 'JR上野東京ライン', 34), leg('上野駅', 'train', 'JR常磐線', 10), leg('北千住駅', 'train', 'つくばエクスプレス', 35)] + copy.deepcopy(TSUKU)},
    fares={'shinjuku': 1790, 'omiya': 1840, 'yokohama': 2150},
    transfers={'shinjuku': 2, 'omiya': 3, 'yokohama': 3},
    badge=YEAR, lineName='つくばエクスプレス・つくバス「小田シャトル」',
    note=('💡 つくば駅前のつくばセンターから、つくバス「小田シャトル」で小田東部まで約40分・300円（大穂窓口センターを回る便は約1時間）。'
          '小田東部から宝篋山小田休憩所まで歩いて約7分'),
    links=[{'type': 'yahoo', 'label': '乗換案内で検索', 'url': yahoo('新宿', 'つくば')},
           {'type': 'bus', 'label': 'つくバス 時刻表（つくば市）', 'url': 'https://www.city.tsukuba.lg.jp/soshikikarasagasu/toshikeikakubusogokotsuseisakuka/gyomuannai/2/1/1001471.html'}],
    gear=ALLN, season='通年', seasonOk=['spring', 'fall', 'winter'],
    routes=[route('宝篋山小田休憩所〜極楽寺コース〜宝篋山〜常願寺コース（周回）', '3時間34分', '6.2km', 500, 498,
                  '宝篋山小田休憩所 → 極楽寺コース → 宝篋山 → 尖浅間山 → 常願寺コース → 宝篋山小田休憩所', '宝篋山小田休憩所', '19236'),
            route('宝篋山小田休憩所〜尖浅間山〜宝篋山〜要害展望所（周回）', '3時間31分', '6.5km', 525, 524,
                  '宝篋山第二駐車場 → 尖浅間山 → 宝篋山 → 要害展望所 → 宝篋山第二駐車場', '宝篋山小田休憩所', '1126'),
            route('小町の館〜小町山〜鬼越山〜宝篋山〜東城寺（周回）', '4時間36分', '9.4km', 667, 669,
                  '小町の館 → 朝日峠ハイキングコース入口 → 小町山 → 鬼越山 → 宝篋山 → 東城寺 → 小町山登山口 → 小町の館', '小町の館（土浦市）', '19237')],
    description=('筑波山から南東に連なる筑波連山の支峰で、つくば市と土浦市の境にある標高461mの山。山頂に山名の由来になった宝篋印塔（鎌倉時代中期ごろ）が立ち、'
                 '筑波山や関東平野、霞ヶ浦を一望できる。空気の澄んだ日は東京の高層ビル群や富士山も見え、関東の富士見百景に選ばれている。'
                 '地元の有志が登山道を整え、年間10万人以上が訪れる。'),
    recommendReason='筑波山の隣で関東平野と霞ヶ浦を一望。登山道がよく整った年間10万人の人気の山',
    metaManual='宝篋山（ほうきょうさん・461m）は筑波山の隣の人気の低山。小田休憩所からの極楽寺・常願寺コース、つくば駅からのバス、駐車場を解説。',
    nearby=['tsukuba'], vibes=['view', 'historic'], types=['easy'],
    vibePoints=[{'who': '初めて山に登る人', 'why': '地元の有志が整えた登山道が何本もあり、登山口に小田休憩所がある'},
                {'who': '広い景色を見たい人', 'why': '山頂から筑波山・関東平野・霞ヶ浦を一望でき、澄んだ日は富士山も見える'},
                {'who': '歴史の跡を歩きたい人', 'why': '山頂の宝篋印塔や、麓の小田城（国の史跡）に関わる城郭跡がある'}],
    features=[{'tag': 'view', 'label': '関東の富士見百景', 'text': '山頂から筑波山や関東平野、霞ヶ浦を一望。空気の澄んだ日は東京の高層ビル群や富士山も見える'},
              {'tag': 'historic', 'label': '宝篋印塔', 'text': '山名の由来になった宝篋印塔（鎌倉時代中期ごろの造立とされる）が山頂に立つ'},
              {'tag': 'historic', 'label': '小田城の城郭跡', 'text': '南西の尾根の小田前山に、麓の小田城（国の史跡）に関わる城郭跡が残る'},
              {'tag': 'easy', 'label': '整った登山道', 'text': '地元の有志が登山道を開きベンチを置いて整えた。年間10万人以上が訪れる'}],
    featureSources=['https://yamap.com/mountains/469', 'https://www.ktr.mlit.go.jp/chiiki/chiiki00000117.html'],
    dl=['<li>小田休憩所から山頂まで標高差は約400mで、登山道がよく整っている</li>',
        '<li>極楽寺・常願寺・尖浅間山など、何本ものコースから選べる</li>',
        '<li class="minus">指定のコースの外は保護区域で、立ち入りが禁じられている</li>'],
    dlSources=['https://yamap.com/mountains/469'],
    faq1='宝篋山は初心者でも登りやすい山で、小田休憩所から山頂まで標高差は約400m、登山道がよく整っています。指定のコースの外は保護区域なので、道から外れないようにしましょう。',
    faq3=('つくばエクスプレスでつくば駅へ行き、駅前のつくばセンターから、つくバス「小田シャトル」で小田東部まで約40分、そこから小田休憩所まで歩いて約7分です。'
          '新宿から約1時間49分、大宮から約1時間53分、横浜から約2時間11分が目安で、運賃は新宿から1,790円、大宮から1,840円、横浜から2,150円です（乗り換えの待ち時間は別）。'),
    faq4=('宝篋山は標高461mの低山で、一年を通して登れます。冬も雪や凍結は少なく、空気の澄んだ冬の日は富士山も見えます。夏は暑いので、朝早い時間がおすすめです。'),
)

# ---------------- 竜ヶ岳 ----------------
BLUE = [leg('河口湖駅', 'bus', '富士急バス「鳴沢・精進湖・本栖湖周遊バス（ブルーライン）」', 57), leg('本栖湖')]
M['ryugatake'] = dict(
    name='竜ヶ岳', kana='りゅうがたけ', elevation=1485, area='山梨県・静岡県', category='人気の山', difficulty='初〜中級', daytrip=True,
    lat=35.446876, lng=138.583539, yamapUrl='https://yamap.com/mountains/15954', yamapName='竜ヶ岳',
    map=(35.460790, 138.602007, '県営本栖湖駐車場'), trailhead='本栖湖キャンプ場（竜ヶ岳登山道入口）',
    parking='県営本栖湖駐車場（無料・約80台）。本栖湖キャンプ場の駐車場は冬は閉まる',
    address='山梨県南都留郡富士河口湖町本栖',
    drive=[98, 123, 113, 110, 90],
    legs={'shinjuku': [leg('バスタ新宿', 'bus', '高速バス「新宿〜河口湖線」', 105)] + copy.deepcopy(BLUE),
          'omiya': [leg('大宮駅', 'train', 'JR湘南新宿ライン', 32), leg('新宿駅', 'train', 'JR特急「富士回遊」', 121)] + copy.deepcopy(BLUE),
          'yokohama': [leg('横浜駅前', 'bus', '高速バス「レイクライナー」', 112)] + copy.deepcopy(BLUE)},
    fares={'shinjuku': 3670, 'omiya': 5860, 'yokohama': 3770},
    transfers={'shinjuku': 1, 'omiya': 2, 'yokohama': 1},
    badge=YEAR, lineName='高速バス・富士急バス「鳴沢・精進湖・本栖湖周遊バス（ブルーライン）」',
    note=('💡 河口湖駅から富士急バス「鳴沢・精進湖・本栖湖周遊バス（ブルーライン）」で本栖湖まで約57分・1,470円。本栖湖バス停は県営本栖湖駐車場の前。'
          '河口湖駅発の午前の便は9時35分・10時35分・11時35分'),
    links=[{'type': 'yahoo', 'label': '乗換案内で検索', 'url': yahoo('新宿', '河口湖')},
           {'type': 'bus', 'label': '周遊バス 時刻表（富士急バス）', 'url': 'https://bus.fujikyu.co.jp/fujitour/kawaguchiko/'}],
    gear=[L, L, N, N, N, N, N, N, N, N, N, L], season='通年（冬は凍結・積雪に注意）', seasonOk=['spring', 'fall', 'winter'],
    routes=[route('本栖湖キャンプ場〜竜ヶ岳〜湖畔登山口（周回）', '4時間7分', '6.6km', 621, 619,
                  '本栖湖駐車場 → 本栖湖キャンプ場 → 竜ヶ岳登山道入口 → 見晴台 → 竜ヶ岳 → 湖畔登山口 → 本栖湖駐車場', '本栖湖キャンプ場（竜ヶ岳登山道入口）', '11093'),
            route('湖畔登山口〜竜ヶ岳（往復）', '3時間20分', '4.0km', 584, 584,
                  '湖畔登山口 → 竜ヶ岳', '湖畔登山口', '19720'),
            route('本栖湖キャンプ場〜竜ヶ岳〜端足峠〜湖畔登山口（周回）', '5時間2分', '9.8km', 727, 726,
                  '本栖湖駐車場 → 本栖湖キャンプ場 → 見晴台 → 竜ヶ岳 → 端足峠 → 湖畔登山口 → 本栖湖駐車場', '本栖湖キャンプ場（竜ヶ岳登山道入口）', '29773')],
    description=('富士五湖でいちばん深い本栖湖の南にそびえる、標高1,485mの山。広い草原状の山頂からは富士山が目の前にそびえ、'
                 '南西の稜線を雨ヶ岳・毛無山へ縦走することもできる。元日には富士山頂から日が昇るダイヤモンド富士が見られ、初日の出とあわせて多くの登山者やカメラマンでにぎわう。'),
    recommendReason='草原の山頂の正面に富士山。元日はダイヤモンド富士で知られる本栖湖の山',
    metaManual='竜ヶ岳（りゅうがたけ・1,485m）は本栖湖の南の山。草原の山頂から富士山を正面に望む。本栖湖キャンプ場からのコース・河口湖駅からのバス・冬の装備を解説。',
    nearby=['kenashiyama', 'juunigadake'], vibes=['view', 'highland', 'accessible'], types=['easy'],
    vibePoints=[{'who': '富士山を正面から見たい人', 'why': '広い草原状の山頂の目の前に富士山がそびえる'},
                {'who': '初日の出を山で見たい人', 'why': '元日には富士山頂から日が昇るダイヤモンド富士が見られる'},
                {'who': 'キャンプと登山を楽しみたい人', 'why': '登山口の本栖湖キャンプ場をはじめ、本栖湖のまわりにキャンプ場がある'}],
    features=[{'tag': 'view', 'label': '目の前の富士山', 'text': '広い草原状の山頂から、富士山が目の前にそびえるパノラマを楽しめる'},
              {'tag': 'view', 'label': 'ダイヤモンド富士', 'text': '元日には富士山頂から日が昇るダイヤモンド富士が見られ、初日の出とあわせて多くの人でにぎわう'},
              {'tag': 'highland', 'label': '草原の山頂', 'text': '山頂は広い草原状で、休憩しやすい'},
              {'tag': 'ridge', 'label': '毛無山への縦走', 'text': '南西の稜線を雨ヶ岳・毛無山と縦走することもできる'}],
    featureSources=['https://yamap.com/mountains/15954', 'https://www.ktr.mlit.go.jp/chiiki/fujimi0111.html'],
    dl=['<li>本栖湖キャンプ場・湖畔登山口から標高差は600m前後で、日帰りで往復できる</li>',
        '<li class="minus">雨や雪のあとは登山道がぬかるみやすい</li>',
        '<li class="minus">標高が1,500m近く、冬は凍結や積雪がある（軽アイゼン等があると安心）</li>'],
    dlSources=['https://yamap.com/mountains/15954'],
    faq1=('竜ヶ岳は本栖湖キャンプ場・湖畔登山口から標高差600m前後の山で、日帰りで往復できます。雨や雪のあとは道がぬかるみやすく、冬は凍結や積雪があるので、軽アイゼン等を用意すると安心です。'),
    faq3=('河口湖駅から富士急バスの周遊バス（ブルーライン）で本栖湖まで約57分です。新宿からは高速バスで河口湖駅へ行き約2時間42分、大宮からは新宿で特急「富士回遊」に乗り約3時間30分、'
          '横浜からは高速バス「レイクライナー」で約2時間49分が目安で、運賃は新宿から3,670円、大宮から5,860円、横浜から3,770円です（乗り換えの待ち時間は別）。'),
    faq4=('竜ヶ岳は一年を通して登られ、元日はダイヤモンド富士を見に来る人でにぎわいます。12月〜2月は凍結や積雪があるので、軽アイゼン等を用意しましょう。'
          '雪の状態は年によって変わるので、直前の最新情報も確認してください。'),
)

# ---------------- 鳴神山 ----------------
ORI = [leg('桐生駅北口', 'bus', 'おりひめバス「川内線」', 32), leg('吹上', 'walk', '徒歩', 20), leg('駒形登山口')]
M['narukamiyama'] = dict(
    name='鳴神山', kana='なるかみやま', elevation=980, area='群馬県', category='人気の山', difficulty='初級', daytrip=True,
    lat=36.49026667, lng=139.3614083, yamapUrl='https://yamap.com/mountains/16732', yamapName='鳴神山',
    map=(36.483573, 139.344686, '駒形登山口'), trailhead='駒形登山口',
    parking='駒形登山口の駐車場（無料・約5〜15台）', address='群馬県桐生市川内町5丁目',
    drive=[118, 100, 140, 157, 127],
    legs={'shinjuku': [leg('新宿駅', 'train', 'JR埼京線', 14), leg('赤羽駅', 'train', 'JR宇都宮線（快速ラビット）', 54), leg('小山駅', 'train', 'JR両毛線', 57)] + copy.deepcopy(ORI),
          'omiya': [leg('大宮駅', 'train', 'JR宇都宮線', 50), leg('小山駅', 'train', 'JR両毛線', 59)] + copy.deepcopy(ORI),
          'yokohama': [leg('横浜駅', 'train', 'JR上野東京ライン（宇都宮線直通）', 113), leg('小山駅', 'train', 'JR両毛線', 66)] + copy.deepcopy(ORI)},
    fares={'shinjuku': 2620, 'omiya': 2290, 'yokohama': 3390},
    transfers={'shinjuku': 3, 'omiya': 2, 'yokohama': 2},
    badge=YEAR, lineName='JR両毛線・おりひめバス「川内線」',
    note=('💡 桐生駅北口からおりひめバス「川内線」で吹上まで約32分（川内町を回る便は約55分）・200円。桐生駅北口発は1日9便で、吹上発の最終は18時49分（2024年5月10日改正）。'
          '吹上から駒形登山口まで歩いて約20分'),
    links=[{'type': 'yahoo', 'label': '乗換案内で検索', 'url': yahoo('新宿', '桐生')},
           {'type': 'bus', 'label': 'おりひめバス 川内線 時刻表（桐生市）', 'url': 'https://www.city.kiryu.lg.jp/kurashi/kotsu/bus/map_schedule/kawauchi-line.html'}],
    gear=ALLN, season='通年', seasonOk=['spring', 'fall', 'winter'],
    routes=[route('駒形登山口〜鳴神山〜椚田峠〜赤柴登山口（周回）', '2時間58分', '5.5km', 585, 585,
                  '駒形登山口 → 肩の広場 → 鳴神山（桐生岳） → 鳴神山（仁田山岳） → 第二展望台 → 椚田峠 → 赤柴登山口 → 駒形登山口', '駒形登山口', '34461'),
            route('大滝登山口〜鳴神山〜椚田峠〜コツナギ橋登山口（周回）', '3時間18分', '5.1km', 605, 605,
                  '大滝登山口 → 肩の広場 → 鳴神山（桐生岳） → 鳴神山（仁田山岳） → 椚田峠 → コツナギ橋登山口 → 大滝登山口', '大滝登山口', '23854'),
            route('駒形登山口〜鳴神山〜三峰山〜大形山〜吾妻山〜桐生駅（縦走）', '7時間41分', '14.0km', 1141, 1402,
                  '駒形登山口 → 鳴神山（桐生岳） → 花台沢ノ頭 → 三峰山 → 金沢峠 → 大形山 → 女吾妻山 → 吾妻山 → 桐生駅', '駒形登山口', '15910')],
    description=('群馬県桐生市の北にある標高980mの山で、桐生岳と仁田山岳の2つの頂からなる。古くから山岳信仰の山で、山頂近くに雷神岳神社がある。'
                 'ミズナラやクヌギなどの天然林が広がり、カッコソウやヤシオツツジなどが咲く豊かな自然から、群馬県の自然環境保全地域に指定されている。'),
    recommendReason='360度の大展望と、カッコソウやアカヤシオが咲く桐生の信仰の山',
    metaManual='鳴神山（なるかみやま・980m）は桐生市の信仰の山。駒形登山口からの周回、桐生駅からのおりひめバス、桐生アルプスの縦走を解説。',
    nearby=['akagi'], vibes=['view', 'historic', 'forest', 'flower', 'accessible'], types=['easy'],
    vibePoints=[{'who': '春の花を見たい人', 'why': 'カッコソウやヤシオツツジなどが咲き、群馬県の自然環境保全地域に指定されている'},
                {'who': '山頂の大展望を楽しみたい人', 'why': '山頂から360度の展望が広がる'},
                {'who': '長く歩きたい人', 'why': '吾妻山まで尾根を歩いて桐生駅に下る縦走ができる'}],
    features=[{'tag': 'view', 'label': '360度の大展望', 'text': '桐生の名山として、山頂の360度の大展望が紹介されている'},
              {'tag': 'flower', 'label': 'カッコソウ・ヤシオツツジ', 'text': 'カッコソウ、ナルカミスミレ、ヤシオツツジ、ニリンソウなどが分布する'},
              {'tag': 'historic', 'label': '雷神岳神社', 'text': '古くから山岳信仰の対象で、山頂付近に雷神岳神社がある'},
              {'tag': 'forest', 'label': '天然林', 'text': 'ミズナラ、クヌギ、クリなどの天然林が広がり、群馬県の自然環境保全地域に指定されている'}],
    featureSources=['https://yamap.com/mountains/16732', 'https://yamap.com/magazine/39743'],
    dl=['<li>駒形登山口から山頂まで標高差は約600mで、周回でも3時間ほど</li>',
        '<li>桐生岳・仁田山岳の2つの頂があり、山頂から大展望が広がる</li>',
        '<li class="minus">吾妻山への縦走は14kmと長く、7時間半以上かかる</li>'],
    dlSources=['https://yamap.com/mountains/16732', 'https://yamap.com/model-courses/15910'],
    faq1='鳴神山は駒形登山口から標高差約600m、周回でも3時間ほどの山で、初心者でも登りやすい山です。吾妻山まで歩く縦走は14km・7時間半以上と長いので、体力に合わせて選びましょう。',
    faq3=('JR両毛線で桐生駅へ行き、桐生駅北口からおりひめバス「川内線」で吹上まで約32分、そこから駒形登山口まで歩いて約20分です。'
          '新宿から約2時間57分、大宮から約2時間41分、横浜から約3時間51分が目安で、運賃は新宿から2,620円、大宮から2,290円、横浜から3,390円です（乗り換えの待ち時間は別）。'),
    faq4=('鳴神山は標高980mで、一年を通して登れます。カッコソウやアカヤシオの咲く春が特に人気です。冬は雪が降ったあとに凍ることがあるので、直前の最新情報も確認してください。'),
)

# ---------------- 仏果山 ----------------
ATSU = [leg('本厚木駅', 'bus', '神奈中バス「厚20」（宮ヶ瀬方面）', 43), leg('仏果山登山口')]
M['bukkasan'] = dict(
    name='仏果山', kana='ぶっかさん', elevation=747, area='神奈川県', category='人気の山', difficulty='初級', daytrip=True,
    lat=35.52054444, lng=139.2581028, yamapUrl='https://yamap.com/mountains/16212', yamapName='仏果山',
    map=(35.516636, 139.241803, '大棚沢広場駐車場'), trailhead='仏果山登山口',
    parking='大棚沢広場駐車場（無料・約15台・8時〜17時）', address='神奈川県愛甲郡清川村宮ヶ瀬',
    drive=[59, 85, 55, 51, 52],
    legs={'shinjuku': [leg('新宿駅', 'train', '小田急小田原線', 58)] + copy.deepcopy(ATSU),
          'omiya': [leg('大宮駅', 'train', 'JR埼京線', 37), leg('新宿駅', 'train', '小田急小田原線', 52)] + copy.deepcopy(ATSU),
          'yokohama': [leg('横浜駅', 'train', '相鉄本線', 27), leg('海老名駅', 'train', '小田急小田原線', 9)] + copy.deepcopy(ATSU)},
    fares={'shinjuku': 1310, 'omiya': 1840, 'yokohama': 1260},
    transfers={'shinjuku': 1, 'omiya': 2, 'yokohama': 2},
    badge=YEAR, lineName='小田急小田原線・神奈中バス「厚20」',
    note='💡 本厚木駅から神奈中バス「厚20」（宮ヶ瀬方面）で仏果山登山口まで約43分・790円',
    links=[{'type': 'yahoo', 'label': '乗換案内で検索', 'url': yahoo('新宿', '仏果山登山口')}],
    gear=ALLN, season='通年', seasonOk=['spring', 'fall', 'winter'],
    routes=[route('仏果山登山口〜宮ヶ瀬越〜仏果山〜高取山（往復）', '3時間41分', '5.7km', 607, 607,
                  '仏果山登山口 → 宮ヶ瀬越 → 仏果山 → 宮ヶ瀬越 → 高取山 → 宮ヶ瀬越 → 仏果山登山口', '仏果山登山口', '16770'),
            route('あいかわ公園〜高取山〜仏果山〜仏果山登山口（周回）', '5時間4分', '9.2km', 821, 822,
                  'あいかわ公園 → 宮ヶ瀬ダム → 水とエネルギー館 → 高取山 → 宮ヶ瀬越 → 仏果山 → 仏果山登山口 → あいかわ公園', 'あいかわ公園', '38475'),
            route('半僧坊前バス停〜経ヶ岳〜仏果山〜高取山〜水とエネルギー館（縦走）', '5時間59分', '8.7km', 1040, 847,
                  '半僧坊前バス停 → 経ヶ岳 → 半原越 → 革籠石山 → 仏果山 → 宮ヶ瀬越 → 高取山 → 水とエネルギー館', '半僧坊前バス停', '20618')],
    description=('丹沢山地の東部、愛川町と清川村の境にある標高747mの山。郷土富士のひとつで半原富士とも呼ばれる。山頂の高さ13mの展望台から東丹沢と関東平野を一望でき、'
                 '西の麓には宮ヶ瀬湖、南には宮ヶ瀬ダムがある。登山道がよく整い、隣の高取山や経ヶ岳とあわせて歩かれる。'),
    recommendReason='山頂の展望台から東丹沢と関東平野を一望。宮ヶ瀬湖の上の歩きやすい山',
    metaManual='仏果山（ぶっかさん・747m）は東丹沢の展望台の山。仏果山登山口からの高取山との往復、本厚木駅からのバス、駐車場を解説。',
    nearby=['oyama', 'ishirousan'], vibes=['view'], types=['easy'],
    vibePoints=[{'who': '展望台から景色を楽しみたい人', 'why': '山頂の高さ13mの展望台から東丹沢と関東平野を一望できる'},
                {'who': '電車とバスで手軽に登りたい人', 'why': '本厚木駅からのバスで登山口まで行ける'},
                {'who': '尾根歩きを楽しみたい人', 'why': '高取山・経ヶ岳と尾根をつないで歩ける'}],
    features=[{'tag': 'view', 'label': '山頂の展望台', 'text': '高さ13mの展望台から東丹沢と関東平野が一望できる'},
              {'tag': 'easy', 'label': '整った登山道', 'text': '登山道がよく整備され、家族連れでも登りやすい'},
              {'tag': 'ridge', 'label': '高取山・経ヶ岳', 'text': '周りの高取山（706m）・経ヶ岳（633m）とあわせて歩くハイキングコースとして知られる'},
              {'tag': 'view', 'label': '宮ヶ瀬湖', 'text': '西の麓に宮ヶ瀬湖、南の麓に宮ヶ瀬ダムがある'}],
    featureSources=['https://yamap.com/mountains/16212'],
    dl=['<li>登山道がよく整い、仏果山登山口から山頂まで標高差は400m台</li>',
        '<li class="minus">春から秋はヤマビルが出るので対策が要る（登山口に塩や忌避剤が置かれている）</li>'],
    dlSources=['https://yamap.com/mountains/16212'],
    faq1='仏果山は登山道がよく整い、家族連れでも登りやすい山です。春から秋はヤマビルが出るので、ヤマビル対策をして登りましょう。',
    faq3=('小田急線で本厚木駅へ行き、神奈中バス「厚20」（宮ヶ瀬方面）で仏果山登山口まで約43分です。'
          '新宿から約1時間41分、大宮から約2時間12分、横浜から約1時間19分が目安で、運賃は新宿から1,310円、大宮から1,840円、横浜から1,260円です（乗り換えの待ち時間は別）。'),
    faq4=('仏果山は標高747mの低山で、一年を通して登れます。YAMAP の記録では1〜2月に登る人の割合が高い山です。春から秋はヤマビルが多いので、涼しい時期が歩きやすいでしょう。'),
)

# ---------------- 堂平山 ----------------
EAGLE = [leg('小川町駅', 'bus', 'イーグルバス「東秩父村路線」（白石車庫行き）', 31), leg('皆谷')]
M['dodairasan'] = dict(
    name='堂平山', kana='どうだいらさん', elevation=876, area='埼玉県', category='人気の山', difficulty='初〜中級', daytrip=True,
    lat=36.00575278, lng=139.1900694, yamapUrl='https://yamap.com/mountains/15415', yamapName='堂平山',
    map=(35.998071, 139.187061, '剣ヶ峰駐車場'), trailhead='皆谷バス停（萩平）', driveTarget='剣ヶ峰駐車場',
    parking='剣ヶ峰駐車場（無料・約100台）', address='埼玉県比企郡ときがわ町大野',
    drive=[98, 90, 120, 123, 99],
    legs={'shinjuku': [leg('新宿駅', 'train', 'JR埼京線', 6), leg('池袋駅', 'train', '東武東上線', 71)] + copy.deepcopy(EAGLE),
          'omiya': [leg('大宮駅', 'train', 'JR川越線', 23), leg('川越駅', 'train', '東武東上線', 42)] + copy.deepcopy(EAGLE),
          'yokohama': [leg('横浜駅', 'train', 'JR湘南新宿ライン', 38), leg('池袋駅', 'train', '東武東上線', 70)] + copy.deepcopy(EAGLE)},
    fares={'shinjuku': 1540, 'omiya': 1350, 'yokohama': 2060},
    transfers={'shinjuku': 2, 'omiya': 2, 'yokohama': 2},
    badge=YEAR, lineName='東武東上線・イーグルバス「東秩父村路線」',
    note=('💡 小川町駅からイーグルバス「東秩父村路線」（白石車庫行き）で皆谷まで約31分・510円。土日祝の白石車庫行きは1日8便で、白石車庫発の最終は17時12分（2024年4月1日改正）。'
          '下りる駅は東武東上線・JR八高線の「小川町駅」（埼玉県）'),
    links=[{'type': 'yahoo', 'label': '乗換案内で検索', 'url': yahoo('新宿', '小川町(埼玉県)')},
           {'type': 'bus', 'label': '東秩父村路線バス 時刻表・運賃表（東秩父村）', 'url': 'https://www.vill.higashichichibu.saitama.jp/soshiki/00/higashichichibumurarosennbasujikokuhyouunnchinnhyou.html'}],
    gear=ALLN, season='通年', seasonOk=['spring', 'fall', 'winter'],
    routes=[route('皆谷バス停〜笠山〜堂平山〜剣ヶ峰〜白石車庫（縦走）', '4時間58分', '9.8km', 916, 780,
                  '皆谷バス停 → 萩平 → 笠山 → 笠山峠 → 七重峠 → 堂平山 → 剣ヶ峰 → 白石峠 → 白石車庫バス停', '皆谷バス停（萩平）', '26472'),
            route('剣ヶ峰駐車場〜堂平山〜笠山（往復）', '3時間5分', '6.0km', 488, 488,
                  '剣ヶ峰駐車場 → 剣ヶ峰 → 堂平山 → 七重峠 → 笠山峠 → 笠山', '剣ヶ峰駐車場', '14486'),
            route('比企三山（笠山〜堂平山〜大霧山）周回', '8時間39分', '17.0km', 1501, 1501,
                  '萩平 → 笠山 → 笠山峠 → 七重峠 → 堂平山 → 剣ヶ峰 → 白石峠 → 定峰峠 → 大霧山 → 大霧山登山口', '皆谷バス停（萩平）', '20062')],
    description=('小川町・ときがわ町・東秩父村の境にある標高876mの山で、笠山・大霧山と並ぶ比企三山のひとつ。山頂はなだらかでほぼ全方位に開け、見晴らしがよい。'
                 '山頂には一等三角点と天測点があり、かつて東京天文台（今の国立天文台）の堂平観測所が置かれた。今は「ときがわ町星と緑の創造センター」として使われている。'),
    recommendReason='ほぼ全方位に開けた山頂の比企三山。笠山とつないで歩きごたえも',
    metaManual='堂平山（どうだいらさん・876m）は比企三山のひとつ。皆谷バス停から笠山を経て登る縦走、剣ヶ峰駐車場からの往復、小川町駅からのバスを解説。',
    nearby=['kannokura', 'bukosan'], vibes=['view', 'accessible'], types=['easy'],
    vibePoints=[{'who': '広い景色を見たい人', 'why': '山頂はほぼ全方位に開け、見晴らしがよい'},
                {'who': 'しっかり歩きたい人', 'why': '笠山とつなぐ縦走や、大霧山まで回る比企三山の周回ができる'},
                {'who': '星や天文が好きな人', 'why': '山頂にかつての東京天文台の観測所があり、今は星と緑の創造センターになっている'}],
    features=[{'tag': 'view', 'label': '全方位の展望', 'text': '山頂付近はなだらかでほぼ全方位に開け、見晴らしがよい'},
              {'tag': 'collector', 'label': '比企三山', 'text': '北の笠山、北西の大霧山とあわせて比企三山に数えられる'},
              {'tag': 'easy', 'label': '旧堂平観測所', 'text': '1962年に東京天文台の堂平観測所が置かれ、今は「ときがわ町星と緑の創造センター」'},
              {'tag': 'view', 'label': '一等三角点と天測点', 'text': '山頂に一等三角点と天測点が置かれている'}],
    featureSources=['https://yamap.com/mountains/15415'],
    dl=['<li>山頂近くまで車道があり、剣ヶ峰駐車場からなら往復3時間ほど</li>',
        '<li class="minus">皆谷バス停から笠山を越える縦走は約5時間で、登りが900mを超える</li>'],
    dlSources=['https://yamap.com/mountains/15415', 'https://yamap.com/model-courses/26472'],
    faq1='堂平山は剣ヶ峰駐車場からなら往復3時間ほどで登れます。電車・バスで行く皆谷バス停からの縦走は笠山を越えて約5時間、登りの合計が900mを超えるので、体力に合わせて選びましょう。',
    faq3=('東武東上線で小川町駅へ行き、イーグルバス「東秩父村路線」（白石車庫行き）で皆谷まで約31分です。'
          '新宿から約1時間48分、大宮から約1時間36分、横浜から約2時間19分が目安で、運賃は新宿から1,540円、大宮から1,350円、横浜から2,060円です（乗り換えの待ち時間は別）。'),
    faq4=('堂平山は標高876mで、一年を通して登れます。冬は空気が澄んで遠くまで見渡せます。雪が降ったあとは道が凍ることがあるので、直前の最新情報も確認してください。'),
)

# ---------------- 高松山 ----------------
M['takamatsuyama'] = dict(
    name='高松山', kana='たかまつやま', elevation=801, area='神奈川県', category='人気の山', difficulty='初〜中級', daytrip=True,
    lat=35.3896121, lng=139.1025282, yamapUrl='https://yamap.com/mountains/16155', yamapName='高松山',
    map=(35.364214, 139.098847, '高松山入口バス停'), trailhead='新松田駅（または高松山入口バス停）', driveTarget='高松山入口バス停の付近',
    parking='登山口の駐車場は確認できていない（電車・バスが便利）', address='神奈川県足柄上郡山北町',
    drive=[64, 88, 56, 52, 74],
    legs={'shinjuku': [leg('新宿駅', 'train', '小田急小田原線', 81), leg('新松田駅')],
          'omiya': [leg('大宮駅', 'train', 'JR湘南新宿ライン', 32), leg('新宿駅', 'train', '小田急小田原線', 75), leg('新松田駅')],
          'yokohama': [leg('横浜駅', 'train', '相鉄本線', 26), leg('海老名駅', 'train', '小田急小田原線', 31), leg('新松田駅')]},
    fares={'shinjuku': 800, 'omiya': 1330, 'yokohama': 720},
    transfers={'shinjuku': 0, 'omiya': 1, 'yokohama': 1},
    badge=YEAR, lineName='小田急小田原線',
    note=('💡 新松田駅から歩いて登れる。下山はJR御殿場線の山北駅へ下りられる。山北駅から高松山入口バス停へは山北町の町内循環バスで約5分'),
    links=[{'type': 'yahoo', 'label': '乗換案内で検索', 'url': yahoo('新宿', '新松田')}],
    gear=ALLN, season='通年', seasonOk=['spring', 'fall', 'winter'],
    routes=[route('新松田駅〜尺里峠〜高松山〜ビリ堂〜山北駅（縦走）', '6時間28分', '14.9km', 1049, 998,
                  '新松田駅 → 尺里峠 → 高松山 → ビリ堂 → 山北駅', '新松田駅', '100614'),
            route('高松山入口バス停〜ビリ堂〜高松山〜尺里峠（周回）', '4時間59分', '10.3km', 776, 775,
                  '高松山入口バス停 → ビリ堂 → 高松山 → 尺里峠 → 高松山入口バス停', '高松山入口バス停', '27954'),
            route('尺里峠〜高松山（往復）', '1時間48分', '3.5km', 288, 288,
                  '尺里峠 → 高松山', '尺里峠', '21854')],
    description=('丹沢大山国定公園に属する、山北町と松田町の境の標高801mの山。急な斜面の多い丹沢のなかで高松山の周りはなだらかで、山頂からは草の間に富士山が見える。'
                 '西の大野山とともに人気のハイキングの山で、新松田駅から歩いて登り、山北駅へ下りることができる。途中には「ビリ堂」と呼ばれる馬頭観音がある。'),
    recommendReason='新松田駅から歩いて登れる西丹沢の入口の山。山頂から富士山',
    metaManual='高松山（たかまつやま・801m）は新松田駅から歩いて登れる丹沢の山。山北駅への縦走・高松山入口からの周回・アクセスを解説。',
    nearby=['ohnoyama', 'yaguradake'], vibes=['historic', 'accessible'], types=['easy'],
    vibePoints=[{'who': '駅から歩いて登りたい人', 'why': '新松田駅から歩き出し、山北駅へ下りられる'},
                {'who': 'なだらかな山を歩きたい人', 'why': '急な斜面の多い丹沢のなかで、高松山の周りはなだらかな地形'},
                {'who': '石仏や里山の道を楽しみたい人', 'why': '途中に「ビリ堂」と呼ばれる馬頭観音がある'}],
    features=[{'tag': 'view', 'label': '山頂から富士山', 'text': '山頂からは草の間に富士山が見える'},
              {'tag': 'historic', 'label': 'ビリ堂', 'text': '高松山へ向かう途中の馬頭観音で、村の安全などを祈って麓から順に建てた観音堂の最後のもの'},
              {'tag': 'easy', 'label': '駅から歩ける', 'text': '新松田駅から歩いて登り、山北駅へ下りる縦走ができる'},
              {'tag': 'forest', 'label': 'なだらかな地形', 'text': '急な斜面や谷の多い丹沢のなかで、高松山の周りはなだらか'}],
    featureSources=['https://yamap.com/mountains/16155', 'https://www.pref.kanagawa.jp/documents/77370/40.pdf'],
    dl=['<li>周りはなだらかな地形で、尺里峠からなら往復2時間ほど</li>',
        '<li class="minus">新松田駅から山北駅への縦走は約15km・6時間半と長い</li>',
        '<li class="minus">登山口の駐車場は確認できておらず、電車・バスで行くのが便利</li>'],
    dlSources=['https://yamap.com/mountains/16155', 'https://yamap.com/model-courses/100614'],
    faq1='高松山はなだらかな山で、尺里峠からなら往復2時間ほどです。電車で行く新松田駅から山北駅への縦走は約15km・6時間半と長いので、高松山入口バス停からの周回（約5時間）も選べます。',
    faq3=('小田急線で新松田駅へ行き、駅から歩いて登ります。新宿から約1時間21分、大宮から約1時間47分、横浜から約57分が目安で、'
          '運賃は新宿から800円、大宮から1,330円、横浜から720円です（乗り換えの待ち時間は別）。下山はJR御殿場線の山北駅へ下りられます。'),
    faq4=('高松山は標高801mの低山で、一年を通して登れます。冬は空気が澄み、山頂から富士山が見えやすい時期です。雪が降ったあとは道が凍ることがあるので、直前の最新情報も確認してください。'),
)

added = []
for mid in NEW:
    c = M[mid]
    m = {'id': mid}
    m.update({k: c[k] for k in ('name', 'kana', 'elevation', 'area', 'category', 'difficulty', 'daytrip', 'lat', 'lng', 'yamapUrl', 'yamapName',
                                'trailhead', 'parking', 'address', 'nearby', 'vibes', 'types', 'season', 'seasonOk', 'description', 'recommendReason')})
    m['coordSource'] = 'YAMAP（山頂の座標）'
    m['metaDescriptionManual'] = c['metaManual']
    m['metaAuto'] = True
    if c.get('driveTarget'):
        m['driveTarget'] = c['driveTarget']
    lat, lng, q = c['map']
    m['gmapUrl'], m['amapUrl'], m['mapBtnsHtml'] = gmap(lat, lng, q)
    for (a, b), v in zip(FIELDS, c['drive']):
        r5 = int(5 * round(v / 5.0))
        m[a] = r5
        m[b] = r5
    m['driveCheckedAt'] = TODAY
    routes = {dep: {'legs': c['legs'][dep]} for dep in ('shinjuku', 'omiya', 'yokohama')}
    m['trainRoutes'] = {'badge': c['badge'], 'lineName': c['lineName'], 'routes': routes, 'note': c['note'], 'summaryNote': None, 'links': c['links']}
    for dep, key in (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama')):
        legs_ = routes[dep]['legs']
        m['trainTime' + key] = sum(x.get('durationMin') or 0 for x in legs_)
        m['fare' + key] = c['fares'][dep]
        m['transfers' + key] = c['transfers'][dep]
    m['trainAccess'] = arrow(routes['shinjuku']['legs'])
    m['trainAccessOmiya'] = arrow(routes['omiya']['legs'])
    m['trainAccessYokohama'] = arrow(routes['yokohama']['legs'])
    m['busLinks'], m['busScheduleLinks'], m['lines'] = [], [], []
    m['fareCheckedAt'] = TODAY
    m['status'] = None
    m['warnBanner'] = None
    m['gearCalendar'] = c['gear']
    sc = [CLS[e] for e in c['gear']]
    m['seasonCalendar'] = sc
    m['calLegend'] = [x for x, k in (('アイゼン不要', 's-ok'), ('軽アイゼン等', 's-gear'), ('冬山装備', 's-hard')) if k in sc]
    m['seasonNoGear'] = ranges([i + 1 for i in range(12) if sc[i] == 's-ok'])
    m['season6Crampons'] = ranges([i + 1 for i in range(12) if sc[i] == 's-gear'])
    m['routes'] = c['routes']
    m['vibePoints'] = c['vibePoints']
    m['featurePoints'] = c['features']
    m['featureSources'] = c['featureSources']
    m['featureCheckedAt'] = TODAY
    m['dlReasonsHtml'] = '<ul class="dl-reasons">\n    ' + '\n    '.join(c['dl']) + '\n  </ul>'
    m['dlReasonsSources'] = c['dlSources']
    m['dlReasonsCheckedAt'] = TODAY
    rep = c['routes'][0]['name']
    m['faq'] = [
        {'question': '%sは初心者でも登れますか？難易度とコース定数を解説' % c['name'],
         'answer': '%sの難易度は%s、コース定数0です。%s代表的な%sは0・0・標高差0が目安。' % (c['name'], c['difficulty'], c['faq1'], rep)},
        {'question': '%sの所要時間は？日帰りできますか？' % c['name'], 'answer': ''},
        {'question': '%sへのアクセス方法は？新宿・横浜からの行き方' % c['name'], 'answer': c['faq3']},
        {'question': '%sの登山シーズンはいつですか？おすすめの時期' % c['name'], 'answer': c['faq4']},
    ]
    m['introHtml'] = TPL['introHtml'].split('<p class="intro-text">')[0] + '<p class="intro-text">' + c['description'] + \
        '%sレベルでコース定数0、日帰りでの登山が可能。代表コース（x）は所要x/x/標高差x。</p></div>' % c['difficulty']
    head = TPL['vibesHtml'].split('<div class="rec-list">')[0]
    items = ''.join('      <div class="rec-item">%s<span><strong>%s</strong>——%s</span></div>\n' % (CHECK, v['who'], v['why']) for v in c['vibePoints'])
    m['vibesHtml'] = head + '<div class="rec-list">\n' + items + '    </div>\n  </div>'
    m['relatedLinksHtml'] = LOW['relatedLinksHtml'].replace('大野山', c['name'])
    m['gearLinks'] = copy.deepcopy(TPL['gearLinks'])
    m['climbedBtnStyle'] = TPL.get('climbedBtnStyle')
    m['hasWeatherWidget'] = False
    m['hasHeroPhotoScript'] = False
    m['photos'] = []
    m['ogUpdatedTime'] = None
    m['mountainUpdated'] = TODAY
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    D.append(m)
    added.append(mid)

json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
rec = {'measuredAt': TODAY, 'source': 'Googleマップの経路検索（車）。表示された最速ルートの時間（分・深夜の測定）。出発地の順は 新宿・大宮・横浜・大船・立川',
       'data': {mid: M[mid]['drive'] for mid in NEW}, 'targets': {mid: list(M[mid]['map'][:2]) + [M[mid]['map'][2]] for mid in NEW}}
json.dump(rec, open(os.path.join(ROOT, 'scripts', 'migrations', 'drive_times_low_six_2026_10.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('追加しました：', added, '（%d山）' % len(D))
