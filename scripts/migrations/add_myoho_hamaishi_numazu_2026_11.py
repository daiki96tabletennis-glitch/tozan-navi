#!/usr/bin/env python3
"""妙法ヶ岳・浜石岳・沼津アルプスを data/mountains.json に足す（2026-11-18。運営者の指示。旧構造。
add_low_six_2026_10.py と同じやり方）。皆野アルプスは、すでに「破風山」（hafuzan_chichibu）として載っていて
皆野アルプスの縦走もそのコースにあるため、ここでは足していない（運営者の判断待ち）。

出典と判断
- コース：YAMAP の山のページのモデルコース（時間・距離・累積標高差・通過点。2026-11-18 に各コースのページで確認）。
  妙法ヶ岳＝YAMAP の妙法ヶ岳（874）、浜石岳＝浜石岳（3025）、沼津アルプス＝鷲頭山（2821）・徳倉山（2820）・香貫山（15504）のページのコース。
  浜石岳の「興津駅〜薩埵峠〜浜石岳〜由比駅」（24071）は YAMAP が「立入禁止の区域を含む可能性」と出すので使っていない。
  沼津アルプスの全山縦走（20638）は YAMAP の地図で破線の道（難路）を通る。
- 山名・標高・座標：YAMAP の山のページ（山頂）。沼津アルプスは最高点の鷲頭山（392m）の値。
  日本百低山の一覧（data/peak_lists.json）の「秩父三峰山」（別名 妙法ヶ岳）・「浜石岳」に siteId をつなぐ。
- 電車：Yahoo!乗換案内（2026-11-21(土)朝発で検索。きっぷの運賃。新幹線・有料特急を使わない経路）。
- バス：
  妙法ヶ岳＝西武バス「三峯神社線」公式（西武秩父駅〜三峯神社 1,100円・時刻表から約80分・土日祝8便／平日6便、
    三峯神社発の最終16:30）。三峯神社〜三峰口駅は800円（帰り方は雲取山の縦走と同じ値）。
  沼津アルプス＝東海バス 沼津駅〜黒瀬 6分・260円、沼津駅〜多比 25分・650円、志下公会堂前〜沼津駅 21分・420円（Yahoo!乗換案内。
    東海バスの公式の区間運賃は確かめていない＝要確認）。
- 車：Googleマップの経路検索（車）。出発を 2026-11-19 3:00 にしたときの車の所要時間（5分単位）。
  この測り方で堂平山（剣ヶ峰駐車場）を測ると、サイトの値（新宿100分・大宮90分）と同じになることを確かめた。
  行き先は 秩父市営三峰駐車場（OpenStreetMap で駐車場）・薩埵峠展望台駐車場（OpenStreetMap で駐車場）・
  沼津アルプス駐車場（香陵台。OpenStreetMap では香陵台無料休憩所＝駐車場の隣）。記録は drive_times_myoho_hamaishi_numazu_2026_11.json。
- 駐車場：三峰＝tabi-mag（第1駐車場240台・第2駐車場42台・有料）、薩埵峠＝BE-PAL（展望台用の駐車場10台ほど・公衆トイレ）、
  浜石岳山頂駐車場＝静岡市の資料（無料・約5台）、香陵台＝koyo.walkerplus（約10台。道幅が狭く市営駐車場をすすめる）。
- 装備の時期：関東の低山は標高1,200mが目安（サイトの決まり）。妙法ヶ岳（1,329m）は同じ秩父の武甲山（1,304m）と同じ区分
  （12〜2月は軽アイゼン等。要確認）。浜石岳・沼津アルプスは通年アイゼン不要。
- 紹介文・特徴：YAMAP の山の紹介文（妙法ヶ岳・浜石岳・鷲頭山・香貫山・徳倉山・大嵐山）、tabi-mag（三峯神社奥宮）、
  静岡市の資料（浜石岳の展望）、静岡新聞 SBS の記事（沼津アルプスの道の様子。2024-06-11）に書かれていることだけ。

  python3 scripts/migrations/add_myoho_hamaishi_numazu_2026_11.py
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
TODAY = '2026-11-18'
D = json.load(open(PATH, encoding='utf-8'))
BY = {m['id']: m for m in D}
NEW = ['myohogatake', 'hamaishidake', 'numazu_alps']
if any(i in BY for i in NEW):
    sys.exit('すでにあります')

W, L, N = 'winter_gear', 'light_crampons', 'no_crampons'
CLS = {W: 's-hard', L: 's-gear', N: 's-ok'}
FIELDS = [('driveTimeShinjuku', 'driveShinjuku'), ('driveTimeOmiya', 'driveOmiya'), ('driveTimeYokohama', 'driveYokohama'),
          ('driveOfuna', 'driveTime'), ('driveTimeTachikawa', 'driveTachikawa')]
CHECK = ('<svg class="rec-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
         'stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>')
TPL = BY['tsubakurodake']
REL = BY['dodairasan']     # 関連するまとめは堂平山の形を使う
ALLN = [N] * 12
DEPS = (('shinjuku', 'Shinjuku', '新宿'), ('omiya', 'Omiya', '大宮'), ('yokohama', 'Yokohama', '横浜'))


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


def access_sentence(c):
    t = {dep: sum(x.get('durationMin') or 0 for x in c['legs'][dep]) for dep, _, _ in DEPS}
    return ('新宿から約%s、大宮から約%s、横浜から約%sが目安で、運賃は新宿から{:,}円、大宮から{:,}円、横浜から{:,}円です（乗り換えの待ち時間は別）。'
            % (fmt(t['shinjuku']), fmt(t['omiya']), fmt(t['yokohama']))).format(c['fares']['shinjuku'], c['fares']['omiya'], c['fares']['yokohama'])


YEAR = {'type': 'year', 'style': None, 'icon': 'check', 'label': '年中運行'}
M = {}

# ---------------- 妙法ヶ岳 ----------------
MITSU = [leg('西武秩父駅', 'bus', '西武バス「三峯神社線」', 80), leg('三峯神社')]
M['myohogatake'] = dict(
    name='妙法ヶ岳', kana='みょうほうがたけ', elevation=1329, area='埼玉県', category='人気の山', difficulty='初級', daytrip=True,
    lat=35.9180192943393, lng=138.947477680008, yamapUrl='https://yamap.com/mountains/874', yamapName='妙法ヶ岳',
    map=(35.92158828585108, 138.933180132799, '秩父市営三峰駐車場'), trailhead='三峯神社（奥宮参道入口）',
    parking='三峯神社の秩父市営三峰駐車場（有料。第1駐車場240台・第2駐車場42台）',
    address='埼玉県秩父市三峰',
    drive=[160, 150, 170, 170, 150],
    legs={'shinjuku': [leg('新宿駅', 'train', 'JR埼京線', 6), leg('池袋駅', 'train', '西武池袋線（飯能乗換）', 99)] + copy.deepcopy(MITSU),
          'omiya': [leg('大宮駅', 'train', 'JR川越線', 24), leg('川越駅', 'train', 'JR川越線・八高線', 30), leg('東飯能駅', 'train', '西武池袋線', 44)] + copy.deepcopy(MITSU),
          'yokohama': [leg('横浜駅', 'train', 'JR湘南新宿ライン', 39), leg('池袋駅', 'train', '西武池袋線（飯能乗換）', 95)] + copy.deepcopy(MITSU)},
    fares={'shinjuku': 2100, 'omiya': 2310, 'yokohama': 2620},
    badge=YEAR, lineName='西武池袋線・西武バス「三峯神社線」',
    note=('三峯神社へのバスは土日祝8便・平日6便で、三峯神社発の最終は16時30分。紅葉の時期・連休は大幅な遅れや特別ダイヤあり'),
    links=[{'type': 'yahoo', 'label': '乗換案内で検索', 'url': yahoo('新宿', '西武秩父')},
           {'type': 'bus', 'label': '三峯神社線 時刻表・運賃（西武バス）', 'url': 'https://www.seibubus.co.jp/rosen/mitsumine/'}],
    gear=[L, L, N, N, N, N, N, N, N, N, N, L], season='通年（冬は凍結に注意）', seasonOk=['spring', 'summer', 'fall'],
    routes=[route('三峯神社〜妙法ヶ岳〜奥宮参道入口（周回）', '2時間42分', '5.2km', 469, 470,
                  '三峯神社バス停（三峰駐車場） → 妙法ヶ岳分岐 → 妙法ヶ岳（三峯神社奥宮） → 妙法ヶ岳分岐 → 奥宮参道入口（雲取山登山口） → 三峯神社 → 三峯神社バス停',
                  '三峯神社（奥宮参道入口）', '102101'),
            route('三峰ビジターセンター〜妙法ヶ岳〜地蔵峠〜霧藻ヶ峰（周回）', '4時間15分', '7.5km', 722, 724,
                  '三峰ビジターセンター → 妙法ヶ岳分岐 → 妙法ヶ岳 → 地蔵峠 → 霧藻ヶ峰 → 地蔵峠 → 妙法ヶ岳分岐 → 三峰ビジターセンター',
                  '三峰ビジターセンター', '17543'),
            route('大輪〜表参道〜妙法ヶ岳〜奥宮参道入口（縦走）', '4時間51分', '7.0km', 1205, 516,
                  '大輪バス停 → 表参道 → 奥宮参道入口（雲取山登山口） → 妙法ヶ岳分岐 → 妙法ヶ岳 → 妙法ヶ岳分岐 → 奥宮参道入口（三峯神社）',
                  '大輪バス停', '11822')],
    description=('奥秩父の山域の一つで、秩父市にある標高1,329mの山。山頂には北西1.8kmほどにある三峯神社の奥宮（奥の院）がまつられ、'
                 '拝殿から歩いて1時間ほどで登拝できる。神仏習合の時代には、妙法ヶ岳・白岩山・雲取山を合わせた三峰山が三峯大権現と呼ばれていた。'
                 '麓の大輪から三峯神社へ上がる表参道を歩いて登ることもできる。'),
    recommendReason='三峯神社の拝殿から1時間ほど。山頂に奥宮がまつられた信仰の山',
    metaManual='妙法ヶ岳（みょうほうがたけ・1,329m）は三峯神社の奥宮がまつられた山。三峯神社からの周回、大輪からの表参道、西武秩父駅からのバス、冬の装備を解説。',
    nearby=['kumotori', 'bukosan', 'nakawarayama'], vibes=['historic', 'accessible'], types=['easy'],
    vibePoints=[{'who': '神社めぐりと山歩きを一緒に楽しみたい人', 'why': '三峯神社の拝殿から歩いて山頂の奥宮へ登拝できる'},
                {'who': 'バスで山の上まで行きたい人', 'why': '西武秩父駅から三峯神社までバスが通い、標高1,000mを超える境内から歩き始められる'},
                {'who': '昔の参道を歩きたい人', 'why': '麓の大輪から三峯神社へ上がる表参道を通って登れる'}],
    features=[{'tag': 'historic', 'label': '三峯神社の奥宮', 'text': '山頂に三峯神社の奥宮（奥の院）がまつられ、拝殿から歩いて1時間ほどで登拝できる'},
              {'tag': 'historic', 'label': '三峰山', 'text': '妙法ヶ岳・白岩山・雲取山を合わせて三峰山と呼び、神仏習合の時代は三峯大権現と呼ばれた'},
              {'tag': 'easy', 'label': 'バスで神社まで', 'text': '西武秩父駅・三峰口駅から三峯神社までバスが通う'},
              {'tag': 'historic', 'label': '大輪からの表参道', 'text': '麓の大輪バス停から三峯神社へ上がる表参道を歩いて登れる'}],
    featureSources=['https://yamap.com/mountains/874', 'https://tabi-mag.jp/sa0231/', 'https://www.seibubus.co.jp/rosen/mitsumine/'],
    dl=['<li>三峯神社から山頂まで標高差は約400mで、周回でも2時間40分ほど</li>',
        '<li class="minus">大輪から表参道を登るコースは、登りの合計が1,200mを超える</li>',
        '<li class="minus">標高が1,300mを超え、冬は道が凍ることがある（軽アイゼン等があると安心）</li>'],
    dlSources=['https://yamap.com/model-courses/102101', 'https://yamap.com/model-courses/11822'],
    faq1=('妙法ヶ岳は三峯神社から山頂まで標高差が約400mで、周回でも2時間40分ほどの山です。麓の大輪から表参道を登ると登りの合計が1,200mを超えるので、'
          '体力に合わせて選びましょう。'),
    faq3pre='西武池袋線で西武秩父駅へ行き、西武バス「三峯神社線」で終点の三峯神社まで約1時間20分です。',
    faq4=('妙法ヶ岳は標高1,329mで、春から秋が登りやすい時期です。12月〜2月は道が凍ることがあるので、軽アイゼン等を用意しましょう。'
          '三峯神社へのバスは紅葉の時期や連休に大幅に遅れることがあるので、時間に余裕を持って計画してください。'),
)

# ---------------- 浜石岳 ----------------
M['hamaishidake'] = dict(
    name='浜石岳', kana='はまいしだけ', elevation=707, area='静岡県', category='人気の山', difficulty='初〜中級', daytrip=True,
    lat=35.12011944, lng=138.5335167, yamapUrl='https://yamap.com/mountains/3025', yamapName='浜石岳',
    map=(35.07163089792591, 138.5412094865056, '薩埵峠展望台駐車場'), trailhead='由比駅',
    parking='薩埵峠展望台の駐車場（約10台・公衆トイレあり）。山頂の近くにも浜石岳山頂駐車場（無料・約5台）がある',
    address='静岡県静岡市清水区由比西倉澤',
    drive=[140, 160, 130, 120, 150],
    legs={'shinjuku': [leg('新宿駅', 'train', '小田急小田原線（新松田乗換）', 93), leg('小田原駅', 'train', 'JR東海道線', 23),
                       leg('熱海駅', 'train', 'JR東海道線', 18), leg('沼津駅', 'train', 'JR東海道線', 34), leg('由比駅')],
          'omiya': [leg('大宮駅', 'train', 'JR上野東京ライン（高崎線直通）', 119), leg('小田原駅', 'train', 'JR東海道線', 23),
                    leg('熱海駅', 'train', 'JR東海道線', 13), leg('三島駅', 'train', 'JR東海道線', 42), leg('由比駅')],
          'yokohama': [leg('横浜駅', 'train', 'JR東海道線', 54), leg('小田原駅', 'train', 'JR東海道線', 50),
                       leg('沼津駅', 'train', 'JR東海道線', 33), leg('由比駅')]},
    fares={'shinjuku': 2270, 'omiya': 3520, 'yokohama': 2380},
    badge=YEAR, lineName='JR東海道線',
    note=None,
    links=[{'type': 'yahoo', 'label': '乗換案内で検索', 'url': yahoo('新宿', '由比')}],
    gear=ALLN, season='通年', seasonOk=['spring', 'fall', 'winter'],
    routes=[route('由比駅〜浜石岳（往復）', '4時間50分', '12.5km', 867, 867,
                  '由比駅 → 浜石岳 → 由比駅', '由比駅', '20666'),
            route('由比駅〜薩埵峠〜浜石岳（周回）', '6時間22分', '15.2km', 1055, 1048,
                  '由比駅 → 薩埵峠 → 浜石岳 → 由比駅', '由比駅', '27689'),
            route('薩埵峠〜浜石岳（往復）', '6時間35分', '13.1km', 1020, 1020,
                  '薩埵峠 → 浜石岳 → 薩埵峠', '薩埵峠（展望台駐車場）', '16358')],
    description=('静岡市清水区の北東部、旧由比町にある標高707mの山で、由比では西山とも呼ばれる。山頂からは富士山・南アルプス・駿河湾が見え、'
                 '360度のパノラマが広がる。南へ延びる稜線は、歌川広重が東海道五十三次に描いた薩埵峠を経て駿河湾に達する。'
                 '山麓はミカンなどの果樹園で、由比駅から歩いて登れる。'),
    recommendReason='山頂から富士山・南アルプス・駿河湾の360度パノラマ。由比駅から歩いて登れる',
    metaManual='浜石岳（はまいしだけ・707m）は静岡市清水区由比の山。山頂から富士山と駿河湾を一望。由比駅からの往復、薩埵峠をめぐる周回、駐車場を解説。',
    nearby=['ryugatake', 'kenashiyama'], vibes=['view', 'historic'], types=['easy'],
    vibePoints=[{'who': '富士山と海を一緒に見たい人', 'why': '山頂から富士山・南アルプス・駿河湾の360度のパノラマが広がる'},
                {'who': '駅から歩いて登りたい人', 'why': 'JR東海道線の由比駅から歩き始めて往復できる'},
                {'who': '旧東海道の歴史にふれたい人', 'why': '周回のコースで、広重の東海道五十三次に描かれた薩埵峠を通る'}],
    features=[{'tag': 'view', 'label': '360度のパノラマ', 'text': '山頂から富士山・南アルプス・駿河湾が見え、360度のパノラマが楽しめる'},
              {'tag': 'historic', 'label': '薩埵峠', 'text': '南の稜線は薩埵峠を経て駿河湾に達する。南北朝時代と戦国時代に薩埵峠の戦いの舞台になった'},
              {'tag': 'easy', 'label': '駅から歩ける', 'text': 'JR東海道線の由比駅から歩いて山頂まで往復できる'},
              {'tag': 'collector', 'label': 'オクシズ100選', 'text': '静岡市のシティプロモーションで「オクシズ100選」の一つに選ばれている'}],
    featureSources=['https://yamap.com/mountains/3025', 'https://www.city.shizuoka.lg.jp/documents/1629/000716008.pdf'],
    dl=['<li>山頂近くまで車道があり、道に迷いにくい</li>',
        '<li class="minus">由比駅からの往復は約12.5km・4時間50分と長め（登りの合計は約870m）</li>',
        '<li class="minus">薩埵峠をめぐる周回は約15km・6時間を超える</li>'],
    dlSources=['https://yamap.com/model-courses/20666', 'https://yamap.com/model-courses/27689'],
    faq1=('浜石岳は標高707mの山ですが、由比駅から歩くと往復約12.5km・登りの合計が約870mあり、歩きごたえがあります。'
          '薩埵峠をめぐる周回は6時間を超えるので、体力に合わせて選びましょう。'),
    faq3pre='JR東海道線の由比駅から歩いて登ります。',
    faq4=('浜石岳は標高707mで、一年を通して登れます。冬は空気が澄み、山頂から富士山や南アルプスが見えやすい時期です。夏は暑いので、朝早い時間がおすすめです。'),
)
# 山頂近くまで車道がある、は YAMAP の紹介文に無い。静岡市の資料（山頂駐車場）に合わせて言い換える
M['hamaishidake']['dl'][0] = '<li>山頂の近くに無料の駐車場（約5台）がある（静岡市の資料）</li>'
M['hamaishidake']['dlSources'].append('https://www.city.shizuoka.lg.jp/documents/1629/000716008.pdf')

# ---------------- 沼津アルプス ----------------
KUROSE = [leg('沼津駅', 'bus', '東海バス（大平車庫行き）', 6), leg('黒瀬')]
M['numazu_alps'] = dict(
    name='沼津アルプス', kana='ぬまづあるぷす', elevation=392, area='静岡県', category='人気の山', difficulty='初〜中級', daytrip=True,
    lat=35.05938889, lng=138.8939722, yamapUrl='https://yamap.com/mountains/2821', yamapName='鷲頭山',
    map=(35.0961884563975, 138.8744631479881, '沼津アルプス駐車場（香陵台）'), trailhead='黒瀬バス停（香貫山登山口）',
    parking='香陵台の駐車場（香貫山の中腹・約10台）。駐車場までの道は狭く、ハイカーも同じ道を歩くので、近くの市営駐車場の利用がすすめられている',
    address='静岡県沼津市上香貫',
    drive=[110, 130, 100, 100, 120],
    legs={'shinjuku': [leg('新宿駅', 'train', '小田急小田原線（新松田乗換）', 93), leg('小田原駅', 'train', 'JR東海道線', 23),
                       leg('熱海駅', 'train', 'JR東海道線', 18)] + copy.deepcopy(KUROSE),
          'omiya': [leg('大宮駅', 'train', 'JR上野東京ライン（高崎線直通）', 119), leg('小田原駅', 'train', 'JR東海道線', 23),
                    leg('熱海駅', 'train', 'JR東海道線', 19)] + copy.deepcopy(KUROSE),
          'yokohama': [leg('横浜駅', 'train', 'JR東海道線', 54), leg('小田原駅', 'train', 'JR東海道線', 50)] + copy.deepcopy(KUROSE)},
    fares={'shinjuku': 1960, 'omiya': 3010, 'yokohama': 2020},
    badge=YEAR, lineName='JR東海道線・東海バス',
    note='南の多比から歩くコースは、沼津駅から東海バスで多比まで約25分・650円',
    links=[{'type': 'yahoo', 'label': '乗換案内で検索', 'url': yahoo('新宿', '沼津')},
           {'type': 'bus', 'label': '路線バス 時刻表（東海バス）', 'url': 'https://www.tokaibus.jp/rosen/timetable.html'}],
    gear=ALLN, season='通年', seasonOk=['spring', 'fall', 'winter'],
    routes=[route('黒瀬バス停〜香貫山〜横山〜徳倉山〜志下山〜志下公会堂前バス停（縦走）', '4時間28分', '7.5km', 714, 714,
                  '黒瀬バス停 → 香貫山登山口 → 香陵台 → 香貫山 → 八重坂峠 → 横山 → 徳倉山 → 志下坂峠 → 志下山 → 馬込峠 → 志下峠 → 志下公会堂前バス停',
                  '黒瀬バス停（香貫山登山口）', '26797'),
            route('多比バス停〜大平山〜鷲頭山〜徳倉山〜香貫山〜黒瀬バス停（縦走）', '6時間42分', '10.3km', 1109, 1108,
                  '多比バス停 → 多比口峠 → 大平山 → 多比峠 → 鷲頭山 → 小鷲頭山 → 志下峠 → 志下山 → 徳倉山 → 横山 → 八重坂峠 → 香貫山 → 黒瀬バス停',
                  '多比バス停', '33789'),
            route('原木駅〜大嵐山〜大平山〜鷲頭山〜徳倉山〜香貫山〜沼津駅（縦走）', '8時間32分', '14.1km', 1300, 1305,
                  '原木駅 → 茶臼山 → 大嵐山（日守山） → 大平山 → 多比峠 → 鷲頭山 → 小鷲頭山 → 志下山 → 徳倉山 → 横山 → 香貫山 → 黒瀬バス停 → 沼津駅',
                  '原木駅（伊豆箱根鉄道）', '20638')],
    description=('沼津市の駿河湾沿いに連なる静浦山地の山並みの通称で、北の香貫山（193m）から横山・徳倉山・志下山・小鷲頭山・鷲頭山・大平山へと続く。'
                 '最高点の鷲頭山（392m）の山頂には鷲頭神社の祠があり、平重衡にまつわる伝説の碑も立つ。標高は200〜400mほどだが、'
                 '鎖を伝う急登やロープを使う下りもあり、峠ごとに登り下りをくり返す。沼津駅から近く、バスで登山口へ行ける。'),
    recommendReason='沼津駅からすぐの低山の縦走路。峠ごとの登り下りで歩きごたえのある駿河湾沿いの山並み',
    metaManual='沼津アルプス（鷲頭山392m）は香貫山から大平山へ続く沼津市の山並み。黒瀬からの縦走、多比からの縦走、全山縦走、沼津駅からのバスを解説。',
    nearby=['kintoki', 'amagi'], vibes=['historic'], types=['easy'],
    vibePoints=[{'who': '短い登り下りをくり返して歩きごたえを求める人', 'why': '香貫山から大平山まで、峠ごとに登り下りが続く縦走路'},
                {'who': '駅から近い山を歩きたい人', 'why': '沼津駅からバスで数分の黒瀬から歩き始められる'},
                {'who': '山頂の祠や伝説の地をたずねたい人', 'why': '鷲頭山の山頂に鷲頭神社の祠と、平重衡にまつわる碑がある'}],
    features=[{'tag': 'ridge', 'label': '静浦山地の縦走', 'text': '香貫山から横山・徳倉山・志下山・小鷲頭山・鷲頭山・大平山へ山並みが続く'},
              {'tag': 'historic', 'label': '鷲頭神社の祠', 'text': '鷲頭山の山頂に鷲頭神社の本殿ともいうべき小さな祠がある。中腹には平重衡が幽閉されたという岩屋の跡の伝説も残る'},
              {'tag': 'challenge', 'label': '鎖とロープの急坂', 'text': '歩きやすい小径から鎖を伝う急登まで変化に富み、徳倉山の下りではロープを使う場面がある'},
              {'tag': 'view', 'label': '香貫山の展望台', 'text': '香貫山には芝住展望台があり、眼下に沼津の市街地が広がる'}],
    featureSources=['https://yamap.com/mountains/2821', 'https://yamap.com/mountains/15504', 'https://www.at-s.com/life/article/ats/1486206.html'],
    dl=['<li>標高は200〜400mほどで、途中の峠から麓へ下りる道が多い</li>',
        '<li class="minus">峠ごとに登り下りをくり返し、鎖を伝う急登やロープを使う下りがある</li>',
        '<li class="minus">原木駅から沼津駅までの全山縦走は約14km・8時間半と長い</li>'],
    dlSources=['https://www.at-s.com/life/article/ats/1486206.html', 'https://yamap.com/model-courses/20638'],
    faq1=('沼津アルプスは標高200〜400mほどの低山の山並みですが、峠ごとに登り下りをくり返し、鎖を伝う急登やロープを使う下りもあります。'
          '黒瀬から志下までの北側の縦走（4時間半ほど）から始めると、自分の体力に合わせて計画しやすいでしょう。'),
    faq3pre='JR東海道線で沼津駅へ行き、東海バス（大平車庫行き）で黒瀬まで約6分です。',
    faq4=('沼津アルプスは標高392mまでの低山で、一年を通して登れます。冬も雪や凍結は少なく、春は香貫山の桜でにぎわいます。夏は暑いので、朝早い時間がおすすめです。'),
)
# 「途中の峠から麓へ下りる道が多い」は登山記録の言い方なので使わない
M['numazu_alps']['dl'][0] = '<li>標高は200〜400mほどで、沼津駅からバスで数分の黒瀬から歩き始められる</li>'

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
    routes = {dep: {'legs': c['legs'][dep]} for dep, _, _ in DEPS}
    m['trainRoutes'] = {'badge': c['badge'], 'lineName': c['lineName'], 'routes': routes, 'note': c['note'], 'summaryNote': None, 'links': c['links']}
    for dep, key, _ in DEPS:
        legs_ = routes[dep]['legs']
        m['trainTime' + key] = sum(x.get('durationMin') or 0 for x in legs_)
        m['fare' + key] = c['fares'][dep]
        m['transfers' + key] = len([x for x in legs_ if x.get('method') and x['method']['icon'] != 'walk']) - 1
    m['trainAccess'] = arrow(routes['shinjuku']['legs'])
    m['trainAccessOmiya'] = arrow(routes['omiya']['legs'])
    m['trainAccessYokohama'] = arrow(routes['yokohama']['legs'])
    m['busLinks'] = [x['url'] for x in c['links'] if x['type'] == 'yahoo']
    m['busScheduleLinks'] = [x['url'] for x in c['links'] if x['type'] == 'bus']
    m['lines'] = []
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
        {'question': '%sへのアクセス方法は？新宿・横浜からの行き方' % c['name'], 'answer': c['faq3pre'] + access_sentence(c)},
        {'question': '%sの登山シーズンはいつですか？おすすめの時期' % c['name'], 'answer': c['faq4']},
    ]
    m['introHtml'] = TPL['introHtml'].split('<p class="intro-text">')[0] + '<p class="intro-text">' + c['description'] + \
        '%sレベルでコース定数0、日帰りでの登山が可能。代表コース（x）は所要x/x/標高差x。</p></div>' % c['difficulty']
    head = TPL['vibesHtml'].split('<div class="rec-list">')[0]
    items = ''.join('      <div class="rec-item">%s<span><strong>%s</strong>——%s</span></div>\n' % (CHECK, v['who'], v['why']) for v in c['vibePoints'])
    m['vibesHtml'] = head + '<div class="rec-list">\n' + items + '    </div>\n  </div>'
    m['relatedLinksHtml'] = REL['relatedLinksHtml'].replace('堂平山', c['name'])
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
rec = {'measuredAt': TODAY, 'source': 'Googleマップの経路検索（車）。出発を 2026-11-19 3:00 にしたときの車の所要時間（分）。出発地の順は 新宿・大宮・横浜・大船・立川',
       'data': {mid: M[mid]['drive'] for mid in NEW}, 'targets': {mid: list(M[mid]['map'][:2]) + [M[mid]['map'][2]] for mid in NEW}}
json.dump(rec, open(os.path.join(ROOT, 'scripts', 'migrations', 'drive_times_myoho_hamaishi_numazu_2026_11.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
# 日本百低山の一覧の山と、サイトの山をつなぐ
PL = os.path.join(ROOT, 'data', 'peak_lists.json')
P = json.load(open(PL, encoding='utf-8'))
LINK = {'秩父三峰山': 'myohogatake', '浜石岳': 'hamaishidake'}
for p in P['peaks']:
    if p['name'] in LINK and p.get('prefs') in (['埼玉県'], ['静岡県']):
        p['siteId'] = LINK[p['name']]
json.dump(P, open(PL, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('追加しました：', added, '（%d山）' % len(D))
