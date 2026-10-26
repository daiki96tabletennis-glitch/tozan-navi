#!/usr/bin/env python3
"""天狗岳・北横岳・入笠山・西穂高岳・妙義山・仙ノ倉山を data/mountains.json に足す（2026-10-27。運営者の指示。燕岳と同じやり方）。

出典と判断
- コース：YAMAP の山のページのモデルコース（時間・距離・累積標高差）。ほかの山で使っているコース（西穂の 84914、仙ノ倉の 53）は使わない。
  仙ノ倉山は YAMAP に定番のコースが2つしかないので2本。
- 難易度：信州 山のグレーディング 2026（北横岳（ロープウェイ）1A＝初級、天狗岳（渋ノ湯）3B＝中級、西穂高岳（上高地）5D＝上級）。
  入笠山（グレーディングに無い）＝初級（ゴンドラ山頂駅から往復約2時間）。妙義山＝上級（群馬県：白雲山・金洞山へは険しい岩場が多く大変危険、初心者は決して登らない）。
  仙ノ倉山＝中級（同じ平標登山口の平標山と同じ。YAMAP の難易度も平標山と同じ段階）。
- 電車・バス：JR は Yahoo!路線情報（きっぷの運賃・2026年11月）。茅野駅までは蓼科山の確認済みの区間・時間を使う。
  アルピコ交通（奥蓼科渋の湯線・北八ヶ岳ロープウェイ線）の公式の時刻表・運賃表、北八ヶ岳ロープウェイ・富士見パノラマリゾート・新穂高ロープウェイの公式サイト。
  西穂高岳の新穂高温泉までと、仙ノ倉山の全部は、同じ場所の笠ヶ岳・平標山の確認済みの値。妙義山の松井田駅〜妙義神社はタクシー（約10分。運賃は合計に入れない）。
- 車：Googleマップの経路検索（車）で 2026-10-27 に測った値を5分単位に丸めた（渋の湯・北八ヶ岳ロープウェイ山麓駅・富士見パノラマのゴンドラ山麓駅・妙義神社）。
  西穂高岳は笠ヶ岳（新穂高温泉）、仙ノ倉山は平標山と同じ値。記録は drive_times_six_2026_10.json。
- 装備の時期：天狗岳は黒百合ヒュッテの現地情報（12〜4月はアイゼン、4月は軽アイゼン等必携）。ほかは同じ山域の既存の山と同じ区分（要確認）：
  北横岳＝蓼科山、入笠山＝霧ヶ峰、西穂高岳＝笠ヶ岳、妙義山＝荒船山、仙ノ倉山＝平標山。
- 紹介文・特徴：YAMAP の山の紹介文（山と溪谷社）と、上の公式サイトに書かれていることだけ。

  python3 scripts/migrations/add_six_mountains_2026_10.py
"""
import copy
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section  # noqa: E402
from build_derived import ranges  # noqa: E402

PATH = os.path.join(ROOT, 'data', 'mountains.json')
TODAY = '2026-10-27'
D = json.load(open(PATH, encoding='utf-8'))
BY = {m['id']: m for m in D}
NEW = ['tengudake', 'kitayokodake', 'nyukasayama', 'nishihotaka', 'myogisan', 'sennokurayama']
if any(i in BY for i in NEW):
    sys.exit('すでにあります')

W, L, N = 'winter_gear', 'light_crampons', 'no_crampons'
CLS = {W: 's-hard', L: 's-gear', N: 's-ok'}
FIELDS = [('driveTimeShinjuku', 'driveShinjuku'), ('driveTimeOmiya', 'driveOmiya'), ('driveTimeYokohama', 'driveYokohama'),
          ('driveOfuna', 'driveTime'), ('driveTimeTachikawa', 'driveTachikawa')]
CHECK = ('<svg class="rec-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
         'stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>')
TPL = BY['tsubakurodake']


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
           '<a href="%s" target="_blank" class="map-btn-link">Apple Maps</a>\n</div>' % (g.replace('&', '&'), a))
    return g, a, btn


def route(name, time, dist, up, down, wp, th, cid):
    return {'name': name, 'time': time, 'distance': dist, 'elevation': '+%dm' % up, 'descent': '-%dm' % down, 'waypoints': wp,
            'trailheadName': th, 'source': 'YAMAPモデルコース（model-courses/%s）' % cid,
            'sourceUrl': 'https://yamap.com/model-courses/%s' % cid, 'lastVerified': TODAY}


def arrow(legs):
    out = ''
    for x in legs:
        out += x['station']
        if x.get('method'):
            out += '→%s約%s→' % (x['method']['line'], fmt(x['durationMin']))
    return out


def fmt(v):
    h, mi = divmod(v, 60)
    if not h:
        return '%d分' % mi
    return '%d時間%d分' % (h, mi) if mi else '%d時間' % h


KEI = BY['keirisan']['trainRoutes']['routes']
TO_CHINO = {'shinjuku': copy.deepcopy(KEI['shinjuku']['legs'][:1]), 'omiya': copy.deepcopy(KEI['omiya']['legs'][:2]),
            'yokohama': copy.deepcopy(KEI['yokohama']['legs'][:2])}
JR_CHINO = {'shinjuku': 5760, 'omiya': 5760, 'yokohama': 5100}  # 蓼科山の運賃から茅野駅〜のバス（1,700円）を引いた JR の運賃（確認済み）

M = {}

# ---------------- 天狗岳 ----------------
legs = {}
for dep in ('shinjuku', 'omiya', 'yokohama'):
    legs[dep] = TO_CHINO[dep] + [leg('茅野駅', 'bus', 'アルピコ交通「奥蓼科渋の湯線」', 52), leg('渋の湯（季節運行）')]
M['tengudake'] = dict(
    name='天狗岳', kana='てんぐだけ', elevation=2646, area='長野県', category='二百名山', difficulty='中級', daytrip=True,
    lat=36.01917, lng=138.35545, yamapUrl='https://yamap.com/mountains/1971', yamapName='天狗岳（西天狗岳）',
    map=(36.036108, 138.328731, '渋の湯'), trailhead='渋の湯（渋ノ湯登山口）', parking='渋の湯の駐車場', address='長野県茅野市北山',
    drive=[154, 179, 169, 167, 147],
    legs=legs, fares={d: JR_CHINO[d] + 2000 for d in JR_CHINO},
    transfers={'shinjuku': 1, 'omiya': 2, 'yokohama': 2},
    badge={'type': None, 'style': 'background:#fde8d8;color:#8a5010;', 'icon': 'check', 'label': '⚠️ バス季節運行'},
    lineName='JR特急あずさ・アルピコ交通「奥蓼科渋の湯線」',
    note=('💡 茅野駅〜渋の湯はアルピコ交通「奥蓼科渋の湯線」で約52分・2,000円。2026年は5月2日〜10月25日の土日祝と8月1日〜30日だけの運行で、'
          '茅野駅発は9時40分と14時20分の1日2便。運行日以外は茅野駅からタクシーなどを使う'),
    links=[{'type': 'yahoo', 'label': '乗換案内で検索', 'url': 'https://transit.yahoo.co.jp/search/result?from=新宿&to=茅野駅&type=1'},
           {'type': 'bus', 'label': 'アルピコ交通 奥蓼科渋の湯線 時刻表', 'url': 'https://www.alpico.co.jp/traffic/local/suwa/'}],
    annual=[{'kind': 'transport', 'label': '茅野駅〜渋の湯のバス（奥蓼科渋の湯線）', 'validFrom': '2026-05-02', 'validTo': '2026-10-25', 'seasonYear': 2026,
             'sourceUrl': 'https://www.alpico.co.jp/traffic/datas/files/2026/04/02/2388a3c99697f371a9d8b22b450a7b085505b7f2.pdf',
             'lastVerified': TODAY, 'note': '土日祝と8月1日〜30日のみ運行'}],
    gear=[W, W, W, W, L, N, N, N, N, L, W, W],
    season='6月〜10月', seasonOk=['summer', 'fall'],
    routes=[route('渋の湯〜黒百合ヒュッテ〜中山峠〜東天狗岳（往復）', '7時間31分', '9.4km', 832, 832,
                  '渋ノ湯登山口 → 黒百合ヒュッテ → 中山峠 → … → 東天狗岳', '渋の湯（渋ノ湯登山口）', '1122'),
            route('唐沢鉱泉〜西尾根〜西天狗岳〜東天狗岳〜黒百合ヒュッテ（周回）', '6時間53分', '8.0km', 884, 883,
                  '唐沢鉱泉登山口 → 第1展望台 → 第二展望台 → … → 東天狗岳 → 中山峠 → 黒百合ヒュッテ', '唐沢鉱泉', '1487'),
            route('渋の湯〜東天狗岳〜中山〜高見石小屋（周回）', '9時間26分', '12.0km', 970, 971,
                  '渋ノ湯登山口 → 黒百合ヒュッテ → 中山峠 → … → 中山 → 高見石小屋', '渋の湯（渋ノ湯登山口）', '93134')],
    description=('北八ヶ岳と南八ヶ岳の境に立つ二百名山。鋭い岩峰の東天狗岳と、丸みのある西天狗岳（2,646m・最高点）が並ぶ双耳峰で、'
                 '南北の八ヶ岳から南・中央アルプスまで見渡せる。奥蓼科の渋の湯や唐沢鉱泉から登り、途中の黒百合ヒュッテで休める。'),
    recommendReason='東西2つの頂が並ぶ北八ヶ岳の双耳峰。黒百合ヒュッテを通って登る',
    metaManual='天狗岳（てんぐだけ・2,646m）は東天狗岳と西天狗岳が並ぶ八ヶ岳の双耳峰。渋の湯・唐沢鉱泉からのコース・アクセス・装備を解説。',
    nearby=['yatsugatake', 'keirisan'], vibes=['view', 'forest', 'ridge'], types=['adventure', 'easy'],
    vibePoints=[{'who': '八ヶ岳を初めて歩く人', 'why': '渋の湯から標高差約800m。途中に黒百合ヒュッテがある'},
                {'who': '森と岩の両方を楽しみたい人', 'why': '北の針葉樹の森と、南の岩峰の景色が天狗岳を境に変わる'},
                {'who': '山頂の展望を楽しみたい人', 'why': '南北の八ヶ岳から南・中央アルプスまで見渡せる'}],
    features=[{'tag': 'view', 'label': '山頂の大展望', 'text': '南・北八ヶ岳の山々のほか、天気が良ければ霧ヶ峰や南・中央アルプスまで見渡せる'},
              {'tag': 'ridge', 'label': '東西2つの頂', 'text': '鋭い岩峰の東天狗岳と丸みのある西天狗岳が並ぶ。三角点は西天狗岳（2,646m）'},
              {'tag': 'forest', 'label': '北八ヶ岳の森', 'text': '天狗岳の北は針葉樹の原生林が広がる北八ヶ岳、南は岩稜の南八ヶ岳と景色が変わる'},
              {'tag': 'hut', 'label': '黒百合ヒュッテ', 'text': '渋の湯からのコースの途中にある山小屋。YAMAP のモデルコースでも名物のビーフシチューが紹介されている'}],
    featureSources=['https://yamap.com/mountains/253', 'https://yamap.com/mountains/1971', 'https://yamap.com/model-courses/1122'],
    dl=['<li class="minus">東天狗岳は鋭い岩峰で、山頂付近は岩の多い道になる</li>',
        '<li class="minus">茅野駅から渋の湯へのバスは土日祝などの運行日だけで、1日2便</li>',
        '<li>信州 山のグレーディングでは渋ノ湯・唐沢鉱泉からのコースが体力度3・技術的難易度B</li>',
        '<li>渋の湯・唐沢鉱泉から標高差は800m台で、途中に黒百合ヒュッテがある</li>'],
    dlSources=['https://www.pref.nagano.lg.jp/kankoki/sangyo/kanko/documents/2026_grading_list.pdf', 'https://yamap.com/mountains/253'],
    faq1='天狗岳は八ヶ岳のなかでは登りやすい山で、渋の湯・唐沢鉱泉から標高差は800m台です。山頂付近の東天狗岳は岩の多い道になります。',
    faq3=('特急あずさで茅野駅へ行き、アルピコ交通「奥蓼科渋の湯線」で渋の湯まで約52分です。新宿から約2時間58分、大宮からは立川で特急に乗り約3時間29分、'
          '横浜からは八王子で特急に乗り約3時間33分が目安で、運賃は新宿・大宮から7,760円、横浜から7,100円です（乗り換えの待ち時間は別）。'
          'バスは2026年は5月2日〜10月25日の土日祝と8月1日〜30日だけの運行です。'),
    faq4=('天狗岳の登山シーズンは6月〜10月が目安です。冬も登る人の多い山ですが、12月〜4月は雪と凍結でアイゼンが要り、黒百合ヒュッテより上はアイゼン・ピッケルがあると安心です。'
          '残雪や凍結は年によって変わるので、直前の最新情報も確認してください。'),
)

# ---------------- 北横岳 ----------------
legs = {}
for dep in ('shinjuku', 'omiya', 'yokohama'):
    legs[dep] = TO_CHINO[dep] + [leg('茅野駅', 'bus', 'アルピコ交通「北八ヶ岳ロープウェイ線」', 59),
                                 leg('北八ヶ岳ロープウェイ山麓駅', 'ropeway', '北八ヶ岳ロープウェイ', 7), leg('山頂駅')]
M['kitayokodake'] = dict(
    name='北横岳', kana='きたよこだけ', elevation=2480, area='長野県', category='人気の山', difficulty='初級', daytrip=True,
    lat=36.08746, lng=138.32, yamapUrl='https://yamap.com/mountains/257', yamapName='北横岳',
    map=(36.0683884, 138.3024287, '北八ヶ岳ロープウェイ山麓駅'), trailhead='北八ヶ岳ロープウェイ山頂駅', driveTarget='北八ヶ岳ロープウェイ山麓駅',
    parking='北八ヶ岳ロープウェイ山麓駅の駐車場', address='長野県茅野市北山',
    drive=[160, 183, 175, 173, 153],
    legs=legs, fares={d: JR_CHINO[d] + 2000 + 1400 for d in JR_CHINO},
    transfers={'shinjuku': 2, 'omiya': 3, 'yokohama': 3},
    badge={'type': 'year', 'style': None, 'icon': 'check', 'label': '年中運行'},
    lineName='JR特急あずさ・アルピコ交通「北八ヶ岳ロープウェイ線」・北八ヶ岳ロープウェイ',
    note=('💡 茅野駅〜北八ヶ岳ロープウェイはアルピコ交通「北八ヶ岳ロープウェイ線」で約45〜60分・2,000円（便によって別荘地を回る）。'
          'ロープウェイは片道1,400円・約7分。2026年11月24日〜12月18日は整備点検で運休'),
    links=[{'type': 'yahoo', 'label': '乗換案内で検索', 'url': 'https://transit.yahoo.co.jp/search/result?from=新宿&to=茅野駅&type=1'},
           {'type': 'bus', 'label': 'アルピコ交通 北八ヶ岳ロープウェイ線 時刻表', 'url': 'https://www.alpico.co.jp/traffic/local/search/result/3005/'}],
    annual=[{'kind': 'closure', 'label': '北八ヶ岳ロープウェイの運休（整備点検）', 'validFrom': '2026-11-24', 'validTo': '2026-12-18', 'seasonYear': 2026,
             'sourceUrl': 'https://www.kitayatu.jp/ropeway/', 'lastVerified': TODAY, 'note': 'この期間は山頂駅まで行けない'}],
    gear=[W, W, W, W, L, N, N, N, N, L, W, W],
    season='6月〜10月（冬は雪山）', seasonOk=['summer', 'fall', 'winter'],
    routes=[route('北八ヶ岳ロープウェイ山頂駅〜北横岳（往復）', '2時間12分', '3.7km', 282, 282,
                  '八ヶ岳ロープウェイ山頂駅 → 第一休憩所 → 第二休憩所 → 北横岳ヒュッテ → 北横岳（南峰） → 北横岳（北峰）', '北八ヶ岳ロープウェイ山頂駅', '8016'),
            route('山頂駅〜北横岳〜雨池峠〜縞枯山（周回）', '4時間44分', '7.8km', 548, 548,
                  '八ヶ岳ロープウェイ山頂駅 → 北横岳ヒュッテ → 北横岳 → … → 縞枯山荘 → 雨池峠 → 縞枯山', '北八ヶ岳ロープウェイ山頂駅', '13388'),
            route('山頂駅〜北横岳〜亀甲池〜双子池〜雨池（周回）', '6時間23分', '10.3km', 756, 756,
                  '八ヶ岳ロープウェイ山頂駅 → 北横岳 → 亀甲池 → … → 双子池ヒュッテ → 雨池 → 雨池峠', '北八ヶ岳ロープウェイ山頂駅', '19599')],
    description=('北八ヶ岳の山。南八ヶ岳にも横岳があるので北横岳と呼ばれる。ロープウェイで標高2,200m台まで上がれて、途中に山小屋もあり、'
                 '双耳峰の山頂からは蓼科山や南八ヶ岳、南・中央・北アルプスまで見渡せる。冬は雪山登山を始める人でもにぎわう。'),
    recommendReason='ロープウェイで上がれる北八ヶ岳の展望の山。雪山を始める人にも人気',
    metaManual='北横岳（きたよこだけ・2,480m）はロープウェイで登れる北八ヶ岳の山。山頂駅からのコース・アクセス・冬の装備を解説。',
    nearby=['keirisan', 'tengudake'], vibes=['view', 'forest', 'accessible'], types=['easy', 'casual'],
    vibePoints=[{'who': '体力に自信がない人', 'why': 'ロープウェイ山頂駅から往復約2時間'},
                {'who': '雪山を始めてみたい人', 'why': 'ロープウェイが使え、途中に北横岳ヒュッテがある'},
                {'who': '森と池を歩きたい人', 'why': '原生林と、亀甲池・双子池・雨池などの池をめぐれる'}],
    features=[{'tag': 'view', 'label': '山頂の展望', 'text': '双耳峰の山頂から蓼科山・南八ヶ岳、南・中央アルプス、御嶽山、北アルプス、遠く頸城山塊まで見渡せる'},
              {'tag': 'easy', 'label': 'ロープウェイで上がれる', 'text': '北八ヶ岳ロープウェイ（約7分）で標高2,200m台の山頂駅まで上がれる'},
              {'tag': 'forest', 'label': '原生林と山上の池', 'text': '針葉樹の森に、亀甲池・双子池・雨池などの池が点在する'},
              {'tag': 'season', 'label': '雪山の入門', 'text': '冬も晴れる日が多く雪が比較的少ない八ヶ岳で、雪山を始める人にも人気'}],
    featureSources=['https://yamap.com/mountains/257', 'https://www.kitayatu.jp/ropeway/'],
    dl=['<li>信州 山のグレーディングではロープウェイ山頂駅からのコースが体力度1・技術的難易度A</li>',
        '<li>ロープウェイ山頂駅から往復約2時間で、途中に北横岳ヒュッテがある</li>',
        '<li class="minus">山頂は標高2,480m。冬は雪と凍結でアイゼンなどの雪山の装備が要る</li>',
        '<li class="minus">2026年11月24日〜12月18日はロープウェイが整備点検で運休する</li>'],
    dlSources=['https://www.pref.nagano.lg.jp/kankoki/sangyo/kanko/documents/2026_grading_list.pdf', 'https://www.kitayatu.jp/ropeway/', 'https://yamap.com/mountains/257'],
    faq1='北横岳はロープウェイ山頂駅から往復約2時間で、八ヶ岳のなかでも登りやすい山です。標高は2,480mあるので、夏でも防寒具と雨具は持っていきます。',
    faq3=('特急あずさで茅野駅へ行き、アルピコ交通「北八ヶ岳ロープウェイ線」で約45〜60分、北八ヶ岳ロープウェイ（約7分）で山頂駅へ上がります。'
          '新宿から約3時間12分、大宮からは立川で特急に乗り約3時間43分、横浜からは八王子で特急に乗り約3時間47分が目安で、'
          '運賃はロープウェイ片道を含めて新宿・大宮から9,160円、横浜から8,500円です（乗り換えの待ち時間は別）。'),
    faq4=('北横岳は雪のない6月〜10月のほか、冬の雪山登山でも人気です。12月〜4月は雪と凍結でアイゼンなどの雪山の装備が要ります。'
          'ロープウェイは2026年11月24日〜12月18日に整備点検で運休します。残雪や凍結は年によって変わるので、直前の最新情報も確認してください。'),
)

# ---------------- 入笠山 ----------------
legs = {
    'shinjuku': [leg('新宿駅', 'train', 'JR特急あずさ', 132)],
    'omiya': [leg('大宮駅', 'train', 'JR埼京線・武蔵野線・中央線（立川乗換）', 64), leg('立川駅', 'train', 'JR特急あずさ', 119)],
    'yokohama': [leg('横浜駅', 'train', 'JR横浜線（八王子乗換）', 83), leg('八王子駅', 'train', 'JR特急あずさ', 104)],
}
for dep in legs:
    legs[dep] += [leg('富士見駅', 'bus', '富士見パノラマリゾート 無料シャトルバス', 10),
                  leg('富士見パノラマリゾート（ゴンドラ山麓駅）', 'ropeway', 'ゴンドラ（乗車約15分・目安）', 15), leg('ゴンドラ山頂駅（季節運行）')]
M['nyukasayama'] = dict(
    name='入笠山', kana='にゅうかさやま', elevation=1955, area='長野県', category='人気の山', difficulty='初級', daytrip=True,
    lat=35.89626, lng=138.17168, yamapUrl='https://yamap.com/mountains/16115', yamapName='入笠山',
    map=(35.9132161, 138.2049304, '富士見パノラマリゾート'), trailhead='ゴンドラ山頂駅（富士見パノラマリゾート）', driveTarget='富士見パノラマリゾート（ゴンドラ山麓駅）',
    parking='富士見パノラマリゾートの駐車場（約1,300台・無料）', address='長野県諏訪郡富士見町富士見',
    drive=[130, 155, 145, 143, 123],
    legs=legs, fares={'shinjuku': 5760 + 2000, 'omiya': 5100 + 2000, 'yokohama': 4770 + 2000},
    transfers={'shinjuku': 2, 'omiya': 3, 'yokohama': 3},
    badge={'type': None, 'style': 'background:#fde8d8;color:#8a5010;', 'icon': 'check', 'label': '⚠️ ゴンドラ季節運行'},
    lineName='JR特急あずさ・富士見パノラマリゾート（シャトルバス・ゴンドラ）',
    note=('💡 富士見駅〜富士見パノラマリゾートは無料のシャトルバス（富士見駅10時発・約10分。2026年は4月25日〜11月24日の毎日）。'
          'ゴンドラは片道2,000円で、2026年のグリーンシーズンは4月25日〜11月15日・8時30分〜16時（11月は15時30分まで）。'
          '沢入登山口から歩いて登る道もある'),
    links=[{'type': 'yahoo', 'label': '乗換案内で検索', 'url': 'https://transit.yahoo.co.jp/search/result?from=新宿&to=富士見(長野県)&type=1'},
           {'type': 'bus', 'label': '富士見パノラマリゾート アクセス（シャトルバス）', 'url': 'https://www.fujimipanorama.com/summer/access'}],
    annual=[{'kind': 'transport', 'label': '富士見パノラマリゾートのゴンドラ（グリーンシーズン）', 'validFrom': '2026-04-25', 'validTo': '2026-11-15', 'seasonYear': 2026,
             'sourceUrl': 'https://www.fujimipanorama.com/summer/ticket', 'lastVerified': TODAY, 'note': '8時30分〜16時（11月は15時30分まで）'},
            {'kind': 'transport', 'label': '富士見駅〜富士見パノラマリゾートの無料シャトルバス', 'validFrom': '2026-04-25', 'validTo': '2026-11-24', 'seasonYear': 2026,
             'sourceUrl': 'https://www.fujimipanorama.com/summer/access', 'lastVerified': TODAY, 'note': '毎日運行。富士見駅10時発'}],
    gear=[L, L, L, L, N, N, N, N, N, N, L, L],
    season='5月〜11月', seasonOk=['spring', 'summer', 'fall'],
    routes=[route('ゴンドラ山頂駅〜入笠湿原〜入笠山（往復）', '2時間1分', '3.9km', 290, 290,
                  'ゴンドラ山頂駅 → 山彦荘 → 入笠湿原 → … → 入笠山 → マナスル山荘天文館', 'ゴンドラ山頂駅（富士見パノラマリゾート）', '12180'),
            route('ゴンドラ山頂駅〜入笠山〜大阿原湿原（往復）', '3時間45分', '8.4km', 398, 399,
                  'ゴンドラ山頂駅 → 山彦荘 → 入笠山 → … → 仏平峠 → 大阿原湿原', 'ゴンドラ山頂駅（富士見パノラマリゾート）', '94180'),
            route('沢入登山口〜入笠湿原〜入笠山（往復）', '3時間35分', '6.5km', 533, 533,
                  '沢入登山口 → 山彦荘 → 入笠湿原 → … → 入笠山', '沢入登山口', '9726')],
    description=('南アルプスの北の端にある山。ゴンドラで標高1,780mまで上がれて、山頂からはほぼ360度の大展望で、南・中央アルプスや八ヶ岳、富士山、北アルプスまで見える。'
                 '入笠湿原や大阿原湿原があり、6月は入笠湿原にスズランが群れて咲く。'),
    recommendReason='ゴンドラで上がれる360度の展望の山。入笠湿原のスズランが見ごろの6月が人気',
    metaManual='入笠山（にゅうかさやま・1,955m）はゴンドラで上がれる360度の展望の山。入笠湿原・大阿原湿原をめぐるコース・アクセスを解説。',
    nearby=['kirigamine', 'yatsugatake'], vibes=['view', 'wetland', 'accessible'], types=['easy', 'casual'],
    vibePoints=[{'who': '初めて山に登る人', 'why': 'ゴンドラ山頂駅から往復約2時間'},
                {'who': '花を見たい人', 'why': '6月は入笠湿原の斜面に日本スズランが群れて咲く'},
                {'who': '湿原を歩きたい人', 'why': '入笠湿原と大阿原湿原をめぐれる'}],
    features=[{'tag': 'view', 'label': '360度の大展望', 'text': '山頂からほぼ360度。南・中央アルプス、八ヶ岳、富士山、遠くに北アルプスまで見える'},
              {'tag': 'wetland', 'label': '2つの湿原', 'text': '入笠湿原と大阿原湿原があり、湿原の植物を見られる'},
              {'tag': 'flower', 'label': 'スズラン', 'text': '6月は入笠湿原の斜面に日本スズランの大群落が咲く。すずらん山野草公園にはドイツスズランも'},
              {'tag': 'easy', 'label': 'ゴンドラで上がれる', 'text': '富士見パノラマリゾートのゴンドラで標高1,780mの山頂駅まで上がれる'}],
    featureSources=['https://yamap.com/mountains/16115', 'https://www.fujimipanorama.com/summer/trekking'],
    dl=['<li>ゴンドラ山頂駅から山頂まで徒歩約60分、往復約2時間</li>',
        '<li>山頂駅から入笠湿原まで徒歩10分。道はよく整備されている</li>',
        '<li class="minus">ゴンドラの運行は季節と時間が決まっていて、帰りの最終便に間に合うように歩く</li>'],
    dlSources=['https://www.fujimipanorama.com/summer/trekking', 'https://www.fujimipanorama.com/summer/ticket', 'https://yamap.com/mountains/16115'],
    faq1='入笠山はゴンドラ山頂駅から往復約2時間で、初めての登山にも向いています。帰りのゴンドラの最終便（4〜10月は下り16時30分）に間に合うように歩きます。',
    faq3=('特急あずさで富士見駅へ行き、富士見パノラマリゾートの無料シャトルバス（約10分）とゴンドラで山頂駅へ上がります。'
          '新宿から約2時間37分、大宮からは立川で特急に乗り約3時間28分、横浜からは八王子で特急に乗り約3時間32分が目安で、'
          '運賃はゴンドラ片道を含めて新宿から7,760円、大宮から7,100円、横浜から6,770円です（乗り換えの待ち時間は別）。シャトルバスは富士見駅10時発の1便です。'),
    faq4=('入笠山はゴンドラが動く5月〜11月が登りやすい時期で、2026年のゴンドラは4月25日〜11月15日です。6月は入笠湿原のスズランが見ごろです。'
          '冬は雪が積もり、滑り止めの装備が要ります。'),
)

# ---------------- 西穂高岳 ----------------
KASA = BY['kasagatake']
legs = copy.deepcopy(KASA['trainRoutes']['routes'])
for dep in legs:
    L_ = legs[dep]['legs']
    L_[-1] = leg('新穂高温泉（新穂高ロープウェイ）', 'ropeway', '新穂高ロープウェイ（第1・第2）', 22)
    L_.append(leg('西穂高口駅'))
    legs[dep] = L_
M['nishihotaka'] = dict(
    name='西穂高岳', kana='にしほたかだけ', elevation=2909, area='岐阜県・長野県', category='人気の山', difficulty='上級', daytrip=True,
    lat=36.27899, lng=137.62906, yamapUrl='https://yamap.com/mountains/1409', yamapName='西穂高岳',
    map=None, trailhead='新穂高ロープウェイ西穂高口駅', driveTarget='新穂高温泉（新穂高ロープウェイ）',
    parking='新穂高温泉駐車場（約160台・乗用車800円／6時間）', address='岐阜県高山市奥飛騨温泉郷神坂',
    drive=None,
    legs=legs, fares={'shinjuku': KASA['fareShinjuku'] + 2400, 'omiya': KASA['fareOmiya'] + 2400, 'yokohama': KASA['fareYokohama'] + 2400},
    transfers={'shinjuku': 1, 'omiya': 2, 'yokohama': 2},
    badge={'type': 'year', 'style': None, 'icon': 'check', 'label': '年中運行'},
    lineName='濃飛バス・京王バス 新宿～新穂高温泉線・新穂高ロープウェイ',
    note=('💡 新宿〜新穂高温泉の高速バスは全席指定・要予約（昼行8,000円）。新穂高ロープウェイは第1・第2の通しで片道2,400円・通年営業。'
          '第1は毎時00分・30分、第2は毎時15分・45分発。天候不良や定期点検で運休することがある'),
    links=[{'type': 'yahoo', 'label': '乗換案内で検索', 'url': 'https://transit.yahoo.co.jp/search/result?from=新宿&to=新穂高温泉&type=1'},
           {'type': 'bus', 'label': '新穂高ロープウェイ 料金・時刻', 'url': 'https://shinhotaka-ropeway.jp/price/'}],
    annual=None,
    gear=copy.deepcopy(KASA['gearCalendar']),
    season='7月〜10月', seasonOk=['summer', 'fall'],
    routes=[route('西穂高口駅〜西穂山荘〜西穂独標〜西穂高岳（往復）', '7時間20分', '7.7km', 962, 962,
                  '西穂高口駅 → 西穂山荘 → 西穂丸山 → 西穂独標 → … → ピラミッドピーク → チャンピオンピーク → 西穂高岳', '新穂高ロープウェイ西穂高口駅', '94936'),
            route('西穂高口駅〜西穂山荘〜西穂独標（往復）', '4時間45分', '6.0km', 674, 674,
                  '西穂高口駅 → 西穂山荘 → 西穂丸山 → 西穂独標', '新穂高ロープウェイ西穂高口駅', '6696'),
            route('上高地〜西穂山荘〜西穂独標〜西穂高岳（往復）', '10時間5分', '9.8km', 1519, 1519,
                  '上高地西穂高岳登山口 → 西穂山荘 → 西穂丸山 → 西穂独標 → … → チャンピオンピーク → 西穂高岳', '上高地（西穂高岳登山口）', '20145')],
    description=('穂高連峰の南西にそびえる岩峰の山。新穂高ロープウェイの西穂高口駅や上高地から登る人でにぎわう。'
                 '西穂独標までは穂高の入門のコースだが、独標から山頂までは岩峰が連なる熟達者向きの道になる。花の百名山にも選ばれている。'),
    recommendReason='ロープウェイから登れる穂高の岩稜。独標までは入門、山頂までは熟達者向き',
    metaManual='西穂高岳（にしほたかだけ・2,909m）は新穂高ロープウェイから登れる穂高連峰の岩峰。西穂独標・山頂へのコース・アクセスを解説。',
    nearby=['hotaka', 'yakedake'], vibes=['view', 'rock', 'ridge', 'alpine'], types=['adventure', 'challenge'],
    vibePoints=[{'who': '岩稜歩きに挑戦したい人', 'why': '西穂独標から山頂まで、大小の岩峰を越えて進む'},
                {'who': '北アルプスの絶景を見たい人', 'why': '独標から笠ヶ岳・焼岳・乗鞍岳、眼下に上高地を望む'},
                {'who': 'ロープウェイで高いところから登りたい人', 'why': '西穂高口駅（標高2,156m）から歩き始められる'}],
    features=[{'tag': 'view', 'label': '独標からの360度の展望', 'text': 'ピラミッドピークから奥穂高岳への岩稜、笠ヶ岳・焼岳・乗鞍岳を望み、眼下に上高地が広がる'},
              {'tag': 'rock', 'label': '連なる岩峰', 'text': '西穂山荘から山頂まで大小の岩峰が連なる。独標の山頂直下には鎖場がある'},
              {'tag': 'easy', 'label': 'ロープウェイで上がれる', 'text': '新穂高ロープウェイの西穂高口駅から歩き始められる'},
              {'tag': 'flower', 'label': '花の百名山', 'text': '花の百名山に選ばれている'}],
    featureSources=['https://yamap.com/mountains/1409', 'https://yamap.com/mountains/256', 'https://shinhotaka-ropeway.jp/price/'],
    dl=['<li class="minus">西穂独標から山頂までは岩峰が連なる熟達者向きのコースで、滑落や落石に注意が要る</li>',
        '<li class="minus">独標の山頂直下には鎖場がある</li>',
        '<li class="minus">信州 山のグレーディングでは上高地からのコースが体力度5・技術的難易度D</li>',
        '<li>ロープウェイで標高2,156mの西穂高口駅まで上がれ、途中に西穂山荘がある</li>'],
    dlSources=['https://yamap.com/mountains/1409', 'https://yamap.com/mountains/256', 'https://www.pref.nagano.lg.jp/kankoki/sangyo/kanko/documents/2026_grading_list.pdf'],
    faq1=('西穂高岳の山頂までは岩峰が連なる熟達者向きの道で、初心者には向きません。初めての人は西穂独標（2,701m）までを目標にし、'
          '岩場の経験を積んでから山頂を目指します。'),
    faq3=('バスタ新宿から高速バス（新宿〜新穂高温泉線・全席指定）で新穂高温泉へ行き、新穂高ロープウェイ（第1・第2の通し・約22分）で西穂高口駅へ上がります。'
          '新宿から約6時間7分、大宮からは新宿でバスに乗り約6時間37分、横浜からは約6時間41分が目安で、'
          '運賃はロープウェイ片道を含めて新宿から10,400円、大宮から10,930円、横浜から11,020円です。'),
    faq4=('西穂高岳の登山シーズンは7月〜10月が目安です。11月〜6月は雪や凍結で冬山装備が要る時期で、岩稜では特に経験が要ります。'
          '残雪や天気は年によって変わるので、直前の最新情報も確認してください。'),
)

# ---------------- 妙義山 ----------------
legs = {
    'shinjuku': [leg('新宿駅', 'train', 'JR湘南新宿ライン', 30), leg('大宮駅', 'train', '上越・北陸新幹線', 44), leg('高崎駅', 'train', 'JR信越本線', 36)],
    'omiya': [leg('大宮駅', 'train', '上越・北陸新幹線', 23), leg('高崎駅', 'train', 'JR信越本線', 39)],
    'yokohama': [leg('横浜駅', 'train', 'JR上野東京ライン・宇都宮線', 58), leg('大宮駅', 'train', '上越・北陸新幹線', 43), leg('高崎駅', 'train', 'JR信越本線', 39)],
}
for dep in legs:
    legs[dep] += [leg('松井田駅', 'taxi', 'タクシー', 10), leg('妙義神社')]
M['myogisan'] = dict(
    name='妙義山', kana='みょうぎさん', elevation=1104, area='群馬県', category='二百名山', difficulty='上級', daytrip=True,
    lat=36.29864, lng=138.74885, yamapUrl='https://yamap.com/mountains/470', yamapName='妙義山（相馬岳）',
    map=(36.300461, 138.762557, '妙義神社'), trailhead='妙義神社', parking='道の駅みょうぎ・妙義山市営駐車場', address='群馬県富岡市妙義町妙義',
    drive=[111, 100, 132, 141, 112],
    legs=legs, fares={'shinjuku': 4290, 'omiya': 3660, 'yokohama': 4620},
    transfers={'shinjuku': 3, 'omiya': 2, 'yokohama': 3},
    badge={'type': 'year', 'style': None, 'icon': 'check', 'label': '年中運行'},
    lineName='上越・北陸新幹線・JR信越本線・タクシー',
    note=('💡 松井田駅から妙義神社までバスは無く、タクシーで約10分（運賃は別）。表示の運賃は大宮〜高崎の新幹線の自由席を使った場合'),
    links=[{'type': 'yahoo', 'label': '乗換案内で検索', 'url': 'https://transit.yahoo.co.jp/search/result?from=新宿&to=松井田(群馬県)&type=1'}],
    annual=None,
    gear=[L, L, L, N, N, N, N, N, N, N, N, L],
    season='3月〜12月', seasonOk=['spring', 'fall'],
    routes=[route('妙義神社〜大の字〜大のぞき〜相馬岳〜タルワキ沢（周回）', '6時間25分', '4.9km', 898, 898,
                  '妙義神社 → 白雲山登山口 → 大の字 → 見晴 → 大のぞき → … → 相馬岳 → タルワキ沢のコル', '妙義神社', '1225'),
            route('妙義神社〜中間道〜タルワキ沢〜相馬岳（往復）', '5時間38分', '4.9km', 812, 812,
                  '妙義神社 → 第二見晴 → タルワキ沢分岐 → … → タルワキ沢のコル → 相馬岳', '妙義神社', '12924'),
            route('妙義神社〜相馬岳〜鷹戻し〜中之岳〜中之嶽神社（縦走）', '7時間22分', '5.4km', 1195, 903,
                  '妙義神社 → 大の字 → 大のぞき → 相馬岳 → … → 鷹戻し → 東岳 → 中之岳 → 中之嶽神社', '妙義神社', '20367')],
    description=('日本三大奇景のひとつとされる群馬の岩山。白雲山・金洞山・相馬岳などの総称で、最高峰は表妙義の稜線にある相馬岳（1,103.8m）。'
                 '中腹には妙義神社があり、中之嶽の石門や奇岩群は日本屈指の山岳美とされる。'),
    recommendReason='日本三大奇景の岩山。鎖場の続く表妙義は上級者向き、中間道は比較的歩きやすい',
    metaManual='妙義山（みょうぎさん・相馬岳1,104m）は日本三大奇景の岩山。妙義神社からの鎖場のコース・中間道・アクセスを解説。',
    nearby=['arafune', 'akagi'], vibes=['rock', 'historic'], types=['challenge', 'adventure'],
    vibePoints=[{'who': '鎖場・岩場の経験がある人', 'why': '白雲山・金洞山へは険しい岩場が続く'},
                {'who': '奇岩の景色を見たい人', 'why': '石門や大砲岩など名前の付いた岩が並ぶ'},
                {'who': '神社と山をあわせて歩きたい人', 'why': '登山口に妙義神社があり、中之嶽神社へも下れる'}],
    features=[{'tag': 'rock', 'label': '日本三大奇景', 'text': '第1〜第4石門、ロウソク岩・大砲岩・筆頭岩など、名前の付いた岩が並ぶ'},
              {'tag': 'historic', 'label': '妙義神社', 'text': '白雲山を御神体とする妙義神社が東の中腹に立ち、登山口になっている'},
              {'tag': 'collector', 'label': '上毛三山', 'text': '赤城山・榛名山とあわせて上毛三山のひとつ。二百名山'},
              {'tag': 'easy', 'label': '中間道', 'text': '山腹をめぐる中間道は比較的アップダウンが少なく、所要時間は約3時間45分'}],
    featureSources=['https://yamap.com/mountains/470', 'https://www.pref.gunma.jp/01/e2310245.html'],
    dl=['<li class="minus">中間道から上の白雲山・金洞山へのコースは険しい岩場が多く大変危険で、初心者は登らないよう呼びかけられている</li>',
        '<li class="minus">鎖場が続き、表妙義の縦走は鷹戻しなどの難所を通る</li>',
        '<li class="minus">登山道でクマの目撃が多く、熊よけの鈴の携行が呼びかけられている</li>',
        '<li>山腹をめぐる中間道は比較的アップダウンが少ない（約3時間45分）</li>'],
    dlSources=['https://www.pref.gunma.jp/01/e2310245.html', 'https://www.pref.gunma.jp/uploaded/attachment/55263.pdf', 'https://yamap.com/mountains/470'],
    faq1=('妙義山の白雲山・金洞山・相馬岳へのコースは険しい岩場と鎖場が続き、群馬県も初心者は決して登らないよう呼びかけています。'
          '初めての人は、山腹をめぐる中間道（約3時間45分）を歩くのがよいでしょう。'),
    faq3=('大宮で上越・北陸新幹線に乗り、高崎で信越本線に乗り換えて松井田駅へ行き、タクシーで妙義神社まで約10分です。'
          '新宿から約2時間、大宮から約1時間12分、横浜から約2時間30分が目安で、運賃（タクシー代は別）は新宿から4,290円、大宮から3,660円、横浜から4,620円です。'
          '松井田駅から妙義神社へのバスはありません。'),
    faq4=('妙義山は標高が低く、春と秋が登りやすい時期です。冬は鎖場や岩が凍ることがあり、滑り止めの装備と経験が要ります。'
          '2025年に山火事で通行止めになっていた中間道と白雲山・金洞山の登山道は、2025年12月27日に解除されています。'),
)

# ---------------- 仙ノ倉山 ----------------
TAI = BY['tairappyo']
M['sennokurayama'] = dict(
    name='仙ノ倉山', kana='せんのくらやま', elevation=2026, area='群馬県・新潟県', category='二百名山', difficulty='中級', daytrip=True,
    lat=36.81747, lng=138.83952, yamapUrl='https://yamap.com/mountains/22', yamapName='仙ノ倉山',
    map=None, trailhead=TAI['trailhead'], parking=TAI['parking'], address=TAI['address'],
    drive=None, legs=copy.deepcopy(TAI['trainRoutes']['routes']),
    fares={'shinjuku': TAI['fareShinjuku'], 'omiya': TAI['fareOmiya'], 'yokohama': TAI['fareYokohama']},
    transfers={'shinjuku': TAI.get('transfersShinjuku'), 'omiya': TAI.get('transfersOmiya'), 'yokohama': TAI.get('transfersYokohama')},
    badge=copy.deepcopy(TAI['trainRoutes'].get('badge')), lineName=TAI['trainRoutes'].get('lineName'),
    note=TAI['trainRoutes'].get('note'), links=copy.deepcopy(TAI['trainRoutes'].get('links')),
    annual=copy.deepcopy(TAI.get('annualItems')),
    gear=copy.deepcopy(TAI['gearCalendar']),
    season='6月〜10月', seasonOk=['summer', 'fall'],
    routes=[route('平標登山口〜松手山〜平標山〜仙ノ倉山（往復）', '8時間36分', '11.9km', 1366, 1366,
                  '平標登山口 → 松手山 → 平標山 → 前仙ノ倉山 → 仙ノ倉山', '平標登山口', '12351'),
            route('天神平〜谷川岳〜万太郎山〜仙ノ倉山〜平標山〜平標登山口（縦走）', '14時間33分', '19.1km', 2197, 2537,
                  '天神尾根 → 谷川岳（トマノ耳） → オジカ沢ノ頭 → 万太郎山 → … → 仙ノ倉山 → 平標山 → 松手山 → 平標登山口', '谷川岳ロープウェイ天神平駅', '80851')],
    description=('谷川連峰の最高峰で二百名山。西の平標山とつながるたおやかな稜線には、見渡す限りのお花畑と笹原が広がり、6月上旬〜7月上旬に高山植物が咲く。'
                 '広場のような山頂からの雄大な展望も魅力。平標登山口を早朝に出れば日帰りもできる。'),
    recommendReason='谷川連峰の最高峰。平標山からお花畑と笹原の稜線を歩く',
    metaManual='仙ノ倉山（せんのくらやま・2,026m）は谷川連峰の最高峰。平標登山口から平標山を経て登るコース・アクセス・装備を解説。',
    nearby=['tairappyo', 'tanigawa'], vibes=['view', 'ridge', 'flower'], types=['adventure', 'collector'],
    vibePoints=[{'who': '稜線歩きを楽しみたい人', 'why': '平標山から仙ノ倉山へ、たおやかな稜線が続く'},
                {'who': '高山植物を見たい人', 'why': '6月上旬〜7月上旬に稜線のお花畑が咲く'},
                {'who': '谷川連峰を縦走したい人', 'why': '谷川岳から万太郎山を経て仙ノ倉山へ縦走できる（上級者向き）'}],
    features=[{'tag': 'flower', 'label': '稜線のお花畑', 'text': '平標山との稜線に、6月上旬〜7月上旬に高山植物が咲く。谷に残る雪渓も見える'},
              {'tag': 'ridge', 'label': 'たおやかな稜線', 'text': '平標山から仙ノ倉山へ、お花畑と笹原の広い稜線が続く'},
              {'tag': 'view', 'label': '広い山頂の展望', 'text': '広場のような山頂から雄大な展望が広がる'},
              {'tag': 'collector', 'label': '谷川連峰の最高峰', 'text': '標高2,026m。二百名山'}],
    featureSources=['https://yamap.com/mountains/22'],
    dl=['<li class="minus">平標登山口からの往復は8時間半以上かかり、早朝の出発が要る</li>',
        '<li class="minus">東の谷川岳方面への縦走は岩場を通るので上級者向き</li>',
        '<li>平標山との稜線は広くたおやかで、平標山乃家に泊まってゆっくり歩くこともできる</li>'],
    dlSources=['https://yamap.com/mountains/22'],
    faq1=('仙ノ倉山は平標山の先にある山で、平標登山口からの往復は8時間半以上かかります。道は広い稜線ですが、体力に自信がなければ平標山乃家に泊まる計画が安心です。'),
    faq3=next(q for q in TAI['faq'] if 'アクセス' in q['question'])['answer'],
    faq4=('仙ノ倉山の登山シーズンは6月〜10月が目安で、稜線のお花畑は6月上旬〜7月上旬が見ごろです。残雪や天気は年によって変わるので、直前の最新情報も確認してください。'),
)

GM = {'tengudake': None, 'kitayokodake': None, 'nyukasayama': None, 'myogisan': None}

added = []
for mid in NEW:
    c = M[mid]
    m = {'id': mid}
    m.update({k: c[k] for k in ('name', 'kana', 'elevation', 'area', 'category', 'difficulty', 'daytrip', 'lat', 'lng', 'yamapUrl', 'yamapName',
                                'trailhead', 'parking', 'address', 'nearby', 'vibes', 'types', 'season', 'seasonOk', 'description', 'recommendReason')})
    m['coordSource'] = 'YAMAP（山頂の座標）・国土地理院／OpenStreetMap で照合'
    m['metaDescriptionManual'] = c['metaManual']
    m['metaAuto'] = True
    if c.get('driveTarget'):
        m['driveTarget'] = c['driveTarget']
    # 地図と車
    if c['map']:
        lat, lng, q = c['map']
        m['gmapUrl'], m['amapUrl'], m['mapBtnsHtml'] = gmap(lat, lng, q)
        for (a, b), v in zip(FIELDS, c['drive']):
            r5 = int(5 * round(v / 5.0))
            m[a] = r5
            m[b] = r5
        m['driveCheckedAt'] = TODAY
    else:
        src = KASA if mid == 'nishihotaka' else TAI
        for k in ('gmapUrl', 'amapUrl', 'mapBtnsHtml', 'driveDistance', 'driveCheckedAt'):
            if k in src:
                m[k] = copy.deepcopy(src[k])
        for a, b in FIELDS:
            m[a] = src[a]
            m[b] = src[b]
    # 電車・バス
    R = c['legs']
    routes = {dep: {'legs': (R[dep]['legs'] if isinstance(R[dep], dict) else R[dep])} for dep in ('shinjuku', 'omiya', 'yokohama')}
    m['trainRoutes'] = {'badge': c['badge'], 'lineName': c['lineName'], 'routes': routes, 'note': c['note'], 'summaryNote': None, 'links': c['links']}
    for dep, key in (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama')):
        legs_ = routes[dep]['legs']
        m['trainTime' + key] = sum(x.get('durationMin') or 0 for x in legs_)
        m['fare' + key] = c['fares'][dep]
        m['transfers' + key] = c['transfers'][dep]
    if mid == 'sennokurayama':
        for k in ('trainAccess', 'trainAccessOmiya', 'trainAccessYokohama', 'trainTimeShinjuku', 'trainTimeOmiya', 'trainTimeYokohama', 'busLinks', 'busScheduleLinks', 'lines'):
            if k in TAI:
                m[k] = copy.deepcopy(TAI[k])
    else:
        m['trainAccess'] = arrow(routes['shinjuku']['legs'])
        m['trainAccessOmiya'] = arrow(routes['omiya']['legs'])
        m['trainAccessYokohama'] = arrow(routes['yokohama']['legs'])
        m['busLinks'], m['busScheduleLinks'], m['lines'] = [], [], []
    m['fareCheckedAt'] = TODAY
    if c.get('annual'):
        m['annualItems'] = c['annual']
    m['status'] = None
    m['warnBanner'] = None
    # 装備
    m['gearCalendar'] = c['gear']
    sc = [CLS[e['before']] if isinstance(e, dict) else CLS[e] for e in c['gear']]
    m['seasonCalendar'] = sc
    m['calLegend'] = [x for x, k in (('アイゼン不要', 's-ok'), ('軽アイゼン等', 's-gear'), ('冬山装備', 's-hard')) if k in sc]
    m['seasonNoGear'] = ranges([i + 1 for i in range(12) if sc[i] == 's-ok'])
    m['season6Crampons'] = ranges([i + 1 for i in range(12) if sc[i] == 's-gear'])
    # コース
    m['routes'] = c['routes']
    # 文章
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
    m['relatedLinksHtml'] = TPL['relatedLinksHtml'].replace('燕岳', c['name'])
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
       'data': {mid: M[mid]['drive'] for mid in NEW if M[mid]['drive']},
       'targets': {mid: M[mid]['map'][:2] for mid in NEW if M[mid]['map']}}
json.dump(rec, open(os.path.join(ROOT, 'scripts', 'migrations', 'drive_times_six_2026_10.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('追加しました：', added, '（%d山）' % len(D))
