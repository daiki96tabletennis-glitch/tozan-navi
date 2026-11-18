#!/usr/bin/env python3
"""皆野アルプスを data/mountains.json に足す（2026-11-18。運営者の指示「別の山として足す。コースが重なってもよい」。旧構造）。

破風山（hafuzan_chichibu）のコース3（秩父華厳前〜大前山〜札立峠〜破風山〜前原山〜皆野駅）と同じ縦走を代表にする。
同じ縦走路を2つの山に入れるので、check_pages.py セクション9の SHARED_ROUTE_ALLOWLIST にこの2山の組み合わせだけを足した。
ほかの2コースは破風山と違う起点・向き（秩父華厳の滝から天狗山・大前山を回る周回、皆野町営駐車場から逆回り）にした。

出典と判断
- 山名：皆野町が「皆野アルプス」と位置付けた尾根（日本山岳会埼玉支部の山行報告 2025-04-27）。
  山頂の値は最高点の大前山（YAMAP 15027。653m・座標）。天狗山は YAMAP で650m。
- コース：YAMAP のモデルコース（20899・26639・30109。2026-11-18 に各コースのページで確認）。
- 電車：Yahoo!乗換案内（2026-11-21(土)朝発・きっぷの運賃）。
- バス：皆野町営バス「日野沢線」皆野駅前〜秩父華厳前 24分・240円（Yahoo!乗換案内。皆野町の日野沢線の時刻表（令和4年10月1日改正）・料金表に
  秩父華厳前・風戸入口のバス停がある）。皆野町は 2027-01-08 から町営バスのルート・ダイヤ・運賃を変える（大人300円の均一。
  「皆野町公共交通ガイド（令和8年8月発行）」。改正後も秩父華厳前・風戸入口に止まる）。annualItems に見張りの項目を入れた。
- 車：Googleマップの経路検索（車）。出発を 2026-11-19 3:00 にしたときの値（add_myoho_hamaishi_numazu_2026_11.py と同じ測り方）。
  行き先は Google マップの「秩父華厳の滝 無料駐車場」（皆野町上日野沢）。
- 装備の時期：低山（653m）なので通年アイゼン不要（破風山と同じ）。
- 紹介文・特徴：日本山岳会埼玉支部の山行報告（2025-04-27）、YAMAP の山とコースのページ、皆野町の町営バスのページに書かれていることだけ。

  python3 scripts/migrations/add_minano_alps_2026_11.py
"""
import copy
import json
import os
import sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section  # noqa: E402
from build_derived import ranges  # noqa: E402

PATH = os.path.join(ROOT, 'data', 'mountains.json')
TODAY = '2026-11-18'
D = json.load(open(PATH, encoding='utf-8'))
BY = {m['id']: m for m in D}
MID = 'minano_alps'
if MID in BY:
    sys.exit('すでにあります')
TPL = BY['tsubakurodake']
REL = BY['dodairasan']
HAFU = BY['hafuzan_chichibu']
CHECK = ('<svg class="rec-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
         'stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>')
FIELDS = [('driveTimeShinjuku', 'driveShinjuku'), ('driveTimeOmiya', 'driveOmiya'), ('driveTimeYokohama', 'driveYokohama'),
          ('driveOfuna', 'driveTime'), ('driveTimeTachikawa', 'driveTachikawa')]
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))
BUS_PAGE = 'https://www.town.minano.saitama.jp/traffic/bus/'


def leg(st, icon=None, line=None, mins=None):
    d = {'station': st}
    if icon:
        d['method'] = {'icon': icon, 'line': line}
        d['durationMin'] = mins
        d['fareYen'] = None
    return d


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


def route(name, time, dist, up, down, wp, th, cid):
    return {'name': name, 'time': time, 'distance': dist, 'elevation': '+%dm' % up, 'descent': '-%dm' % down, 'waypoints': wp,
            'trailheadName': th, 'source': 'YAMAPモデルコース（model-courses/%s）' % cid,
            'sourceUrl': 'https://yamap.com/model-courses/%s' % cid, 'lastVerified': TODAY}


BUS = [leg('皆野駅', 'bus', '皆野町営バス「日野沢線」', 24), leg('秩父華厳前')]
LEGS = {'shinjuku': [leg('新宿駅', 'train', 'JR埼京線', 5), leg('池袋駅', 'train', '東武東上線（和光市・小川町乗換）', 84),
                     leg('寄居駅', 'train', '秩父鉄道', 24)] + copy.deepcopy(BUS),
        'omiya': [leg('大宮駅', 'train', 'JR高崎線', 38), leg('熊谷駅', 'train', '秩父鉄道', 59)] + copy.deepcopy(BUS),
        'yokohama': [leg('横浜駅', 'train', 'JR湘南新宿ライン（高崎線直通）', 102), leg('熊谷駅', 'train', '秩父鉄道', 57)] + copy.deepcopy(BUS)}
FARES = {'shinjuku': 2010, 'omiya': 1760, 'yokohama': 2930}

# 代表コースは破風山のコース3と同じ縦走（名前・時間・距離・登りをそろえる）
r1 = route(HAFU['routes'][2]['name'], '4時間49分', '8km', 688, 823,
           '秩父華厳前バス停 → 秩父華厳の滝 → 華厳の滝登山口 → 天狗山 → 大前山 → 武蔵展望台 → 札立峠 → 破風山 → 東屋 → 三叉ピーク → 前原山 → 皆野駅',
           '秩父華厳前バス停', '20899')
assert (r1['name'], r1['time'], r1['distance'], r1['elevation']) == tuple(HAFU['routes'][2][k] for k in ('name', 'time', 'distance', 'elevation'))
ROUTES = [
    r1,
    route('秩父華厳の滝〜天狗山〜大前山〜札立峠〜破風山〜札所前（周回）', '3時間12分', '5.4km', 565, 565,
          '秩父華厳の滝駐車場 → 華厳の滝登山口 → 天狗山 → 大前山 → 武蔵展望台 → 札立峠 → 破風山 → 札立峠 → 札所前バス停 → 華厳の滝登山口 → 秩父華厳の滝駐車場',
          '秩父華厳の滝（駐車場・秩父華厳前バス停）', '26639'),
    route('皆野町営駐車場〜破風山〜札立峠〜大前山〜天狗山〜秩父華厳の滝（周回）', '4時間12分', '8.6km', 666, 666,
          '皆野町営駐車場 → 破風山登り口 → 東屋 → 破風山 → 札立峠 → 武蔵展望台 → 大前山 → 天狗山 → 華厳の滝登山口 → 秩父華厳の滝 → 札所前バス停 → 風戸入口バス停 → 皆野町営駐車場',
          '皆野町営駐車場（風戸）', '30109'),
]

m = {'id': MID, 'name': '皆野アルプス', 'kana': 'みなのあるぷす', 'elevation': 653, 'area': '埼玉県', 'category': '人気の山',
     'difficulty': '初〜中級', 'daytrip': True, 'lat': 36.0747016, 'lng': 139.04506,
     'yamapUrl': 'https://yamap.com/mountains/15027', 'yamapName': '大前山',
     'trailhead': '秩父華厳前バス停（秩父華厳の滝）',
     'parking': '秩父華厳の滝の無料駐車場（台数は少ない）。破風山側の風戸には皆野町営駐車場（無料）がある',
     'address': '埼玉県秩父郡皆野町上日野沢',
     'nearby': ['hafuzan_chichibu', 'hodosan', 'bukosan'], 'vibes': ['ridge', 'accessible'], 'types': ['easy'],
     'season': '通年', 'seasonOk': ['spring', 'fall', 'winter'],
     'description': ('皆野町の破風山（627m）を中心に、天狗山・大前山・札立峠・破風山・前原山と続く尾根を、皆野町が「皆野アルプス」と位置付けている。'
                     '最高点は大前山（653m）。ふもとの秩父華厳の滝から尾根に上がり、天狗山・大前山を越え、いくつかの鎖場を経て破風山へ。'
                     '前原山を経て、秩父鉄道の皆野駅まで歩いて下りられる。'),
     'recommendReason': '秩父華厳の滝から天狗山・大前山・破風山へ。鎖場もある尾根を皆野駅まで歩き通せる',
     'coordSource': 'YAMAP（大前山の山頂の座標）',
     'metaDescriptionManual': '皆野アルプス（大前山653m・破風山627m）は皆野町の尾根歩き。秩父華厳前から皆野駅への縦走、華厳の滝からの周回、町営バスと駐車場を解説。',
     'metaAuto': True}
g = 'https://www.google.com/maps/search/?api=1&query=36.0833957%2C139.0430706'
a = 'https://maps.apple.com/?ll=36.0833957,139.0430706&q=%s' % quote('秩父華厳の滝 無料駐車場')
m['gmapUrl'], m['amapUrl'] = g, a
m['mapBtnsHtml'] = ('<div class="map-btns"><a href="%s" target="_blank" class="map-btn-link">Googleマップ</a>\n'
                    '<a href="%s" target="_blank" class="map-btn-link">Apple Maps</a>\n</div>' % (g, a))
DRIVE = [110, 90, 130, 140, 110]
for (x, y), v in zip(FIELDS, DRIVE):
    m[x] = m[y] = v
m['driveCheckedAt'] = TODAY
m['trainRoutes'] = {'badge': {'type': 'year', 'style': None, 'icon': 'check', 'label': '年中運行'},
                    'lineName': '秩父鉄道・皆野町営バス「日野沢線」',
                    'routes': {dep: {'legs': LEGS[dep]} for dep, _ in DEPS},
                    'note': '2027年1月8日から町営バスの運賃が300円になり、ダイヤも変わる',
                    'summaryNote': None,
                    'links': [{'type': 'yahoo', 'label': '乗換案内で検索', 'url': 'https://transit.yahoo.co.jp/search/result?from=新宿&to=皆野&type=1'},
                              {'type': 'bus', 'label': '町営バス 時刻表・料金表（皆野町）', 'url': BUS_PAGE}]}
for dep, key in DEPS:
    legs_ = LEGS[dep]
    m['trainTime' + key] = sum(x.get('durationMin') or 0 for x in legs_)
    m['fare' + key] = FARES[dep]
    m['transfers' + key] = len([x for x in legs_ if x.get('method')]) - 1
m['trainAccess'] = arrow(LEGS['shinjuku'])
m['trainAccessOmiya'] = arrow(LEGS['omiya'])
m['trainAccessYokohama'] = arrow(LEGS['yokohama'])
m['busLinks'] = [m['trainRoutes']['links'][0]['url']]
m['busScheduleLinks'] = [BUS_PAGE]
m['lines'] = []
m['fareCheckedAt'] = TODAY
m['annualItems'] = [{'kind': 'info', 'label': '皆野町営バス「日野沢線」のルート・ダイヤ・運賃の改正（2027年1月8日から）', 'validFrom': None, 'validTo': None,
                     'seasonYear': None, 'sourceUrl': BUS_PAGE, 'lastVerified': TODAY,
                     'note': '改正後は大人300円の均一（皆野町公共交通ガイド 令和8年8月発行）。改正の日に運賃・時間を直す'}]
m['status'] = None
m['warnBanner'] = None
m['gearCalendar'] = ['no_crampons'] * 12
m['seasonCalendar'] = ['s-ok'] * 12
m['calLegend'] = ['アイゼン不要']
m['seasonNoGear'] = ranges(list(range(1, 13)))
m['season6Crampons'] = ranges([])
m['routes'] = ROUTES
m['vibePoints'] = [{'who': '尾根をつないで歩きたい人', 'why': '天狗山・大前山・札立峠・破風山・前原山と、尾根をつないで歩ける'},
                   {'who': '駅まで歩いて帰りたい人', 'why': '縦走の終わりは秩父鉄道の皆野駅で、帰りのバスを待たずに済む'},
                   {'who': '滝と山を一緒に楽しみたい人', 'why': '歩き始めのバス停から数分の所に秩父華厳の滝がある'}]
m['featurePoints'] = [{'tag': 'ridge', 'label': '皆野アルプスの尾根', 'text': '天狗山・大前山・札立峠・破風山・前原山と続く尾根を、皆野町が「皆野アルプス」と位置付けている'},
                      {'tag': 'challenge', 'label': '鎖場', 'text': '札立峠から破風山の山頂までの間に、いくつかの鎖場がある'},
                      {'tag': 'river', 'label': '秩父華厳の滝', 'text': '歩き始めの秩父華厳前のバス停から数分の所に、秩父華厳の滝がある'},
                      {'tag': 'easy', 'label': '皆野駅へ下りる', 'text': '前原山を経て大渕登山口に下り、秩父鉄道の皆野駅まで歩ける'}]
m['featureSources'] = ['https://shibu.jac1.or.jp/saitama/wp-content/uploads/2025/05/250427_Minano_Alps.pdf', 'https://yamap.com/mountains/15027']
m['featureCheckedAt'] = TODAY
m['dlReasonsHtml'] = ('<ul class="dl-reasons">\n    <li>標高は600m台で、縦走は秩父華厳前のバス停から皆野駅まで5時間弱</li>\n'
                      '    <li class="minus">札立峠から破風山の間に鎖場がいくつかある</li>\n'
                      '    <li class="minus">天狗山から下る道は急</li>\n  </ul>')
m['dlReasonsSources'] = ['https://shibu.jac1.or.jp/saitama/wp-content/uploads/2025/05/250427_Minano_Alps.pdf', 'https://yamap.com/model-courses/20899']
m['dlReasonsCheckedAt'] = TODAY
t = {dep: m['trainTime' + key] for dep, key in DEPS}
faq3 = ('秩父鉄道の皆野駅前から皆野町営バス「日野沢線」で秩父華厳前まで約24分です。新宿から約%s、大宮から約%s、横浜から約%sが目安で、'
        '運賃は新宿から{:,}円、大宮から{:,}円、横浜から{:,}円です（乗り換えの待ち時間は別）。2027年1月8日から町営バスの運賃とダイヤが変わります。'
        % (fmt(t['shinjuku']), fmt(t['omiya']), fmt(t['yokohama']))).format(FARES['shinjuku'], FARES['omiya'], FARES['yokohama'])
m['faq'] = [
    {'question': '皆野アルプスは初心者でも登れますか？難易度とコース定数を解説',
     'answer': ('皆野アルプスの難易度は初〜中級、コース定数0です。標高は600m台ですが、札立峠から破風山の間にいくつかの鎖場があり、天狗山から下る道は急です。'
                '短く歩くなら秩父華厳の滝からの周回（3時間ほど）も選べます。代表的な%sは0・0・標高差0が目安。' % r1['name'])},
    {'question': '皆野アルプスの所要時間は？日帰りできますか？', 'answer': ''},
    {'question': '皆野アルプスへのアクセス方法は？新宿・横浜からの行き方', 'answer': faq3},
    {'question': '皆野アルプスの登山シーズンはいつですか？おすすめの時期',
     'answer': '皆野アルプスは標高653mまでの低山で、一年を通して登れます。夏は暑いので、春や秋、空気の澄む冬が歩きやすい時期です。鎖場や急な下りは、雨のあとは滑りやすくなります。'},
]
m['introHtml'] = TPL['introHtml'].split('<p class="intro-text">')[0] + '<p class="intro-text">' + m['description'] + \
    '初〜中級レベルでコース定数0、日帰りでの登山が可能。代表コース（x）は所要x/x/標高差x。</p></div>'
head = TPL['vibesHtml'].split('<div class="rec-list">')[0]
items = ''.join('      <div class="rec-item">%s<span><strong>%s</strong>——%s</span></div>\n' % (CHECK, v['who'], v['why']) for v in m['vibePoints'])
m['vibesHtml'] = head + '<div class="rec-list">\n' + items + '    </div>\n  </div>'
m['relatedLinksHtml'] = REL['relatedLinksHtml'].replace('堂平山', m['name'])
m['gearLinks'] = copy.deepcopy(TPL['gearLinks'])
m['climbedBtnStyle'] = TPL.get('climbedBtnStyle')
m['hasWeatherWidget'] = False
m['hasHeroPhotoScript'] = False
m['photos'] = []
m['ogUpdatedTime'] = None
m['mountainUpdated'] = TODAY
m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
D.append(m)
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
rec_path = os.path.join(ROOT, 'scripts', 'migrations', 'drive_times_myoho_hamaishi_numazu_2026_11.json')
rec = json.load(open(rec_path, encoding='utf-8'))
rec['data'][MID] = DRIVE
rec['targets'][MID] = [36.0833957, 139.0430706, '秩父華厳の滝 無料駐車場']
json.dump(rec, open(rec_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('追加しました：', MID, '（%d山）' % len(D))
