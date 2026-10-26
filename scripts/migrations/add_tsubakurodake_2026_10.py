#!/usr/bin/env python3
"""燕岳（tsubakurodake）を data/mountains.json に足す（2026-10-26。運営者の指示）。

- 電車・バス・車の時間・運賃・中房線の規制・バスの運行期間は、同じ中房温泉登山口の大天井岳（otenshoudake）の確認済みの値を使う
  （同じ登山口の山は同じ値にする決まり）。終点の表記だけ「中房温泉（夏季運行）」にする。
- コース：YAMAP の燕岳のページ（mountains/150）のモデルコース 181（中房温泉からの往復）と、北燕岳のページの 100354
  （燕岳・北燕岳〜大天井岳の往復・1泊2日）。表銀座・パノラマ銀座の縦走は槍ヶ岳・大天井岳で使っているので入れない（2本）。
- 難易度：信州 山のグレーディング 2026 の「燕岳（中房温泉）」体力度4・技術的難易度B。サイトで同じ 4B の蝶ヶ岳・針ノ木岳に合わせて中級。
- 装備の時期・特徴・難易度の理由：燕山荘の公式サイト（燕岳・燕山荘の魅力／初めて燕岳へ登る方へ）と YAMAP の紹介文（山と溪谷社）。
  夏山は7月上旬〜10月上旬、10月〜6月は雪の積もる冬山（燕山荘）→ 6月は冬山装備、10月は11日から冬山装備（それまでは軽アイゼン等）。
- 山頂の座標：国土地理院 地名検索「燕岳」（安曇野市）。

  python3 scripts/migrations/add_tsubakurodake_2026_10.py
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section  # noqa: E402

PATH = os.path.join(ROOT, 'data', 'mountains.json')
TODAY = '2026-10-26'
D = json.load(open(PATH, encoding='utf-8'))
if any(m['id'] == 'tsubakurodake' for m in D):
    sys.exit('tsubakurodake はすでにあります')
src = next(m for m in D if m['id'] == 'otenshoudake')

# ---- 大天井岳から写す（同じ中房温泉登山口） ----
SAME = ['area', 'driveOfuna', 'driveShinjuku', 'driveYokohama', 'driveOmiya', 'driveTachikawa', 'driveDistance',
        'driveTime', 'driveTimeShinjuku', 'driveTimeYokohama', 'driveTimeOmiya', 'driveTimeTachikawa', 'driveCheckedAt',
        'warnBanner', 'status', 'trailhead', 'parking', 'address', 'trailheadAddress', 'gmapUrl', 'amapUrl', 'mapBtnsHtml',
        'gmapUrlLegacy', 'amapUrlLegacy', 'gearLinks', 'calLegend', 'fareShinjuku', 'fareYokohama', 'fareOmiya', 'fareCheckedAt',
        'transfersShinjuku', 'transfersYokohama', 'transfersOmiya', 'trainTimeShinjuku', 'trainTimeYokohama', 'trainTimeOmiya',
        'annualItems', 'climbedBtnStyle', 'busLinks', 'busScheduleLinks', 'lines']
m = {k: copy.deepcopy(src[k]) for k in SAME if k in src}

END_OLD = '中房温泉（燕岳経由で大天井岳へ縦走・夏季運行）'
END_NEW = '中房温泉（夏季運行）'
tr = copy.deepcopy(src['trainRoutes'])
for r in tr['routes'].values():
    for leg in r['legs']:
        if leg.get('station') == END_OLD:
            leg['station'] = END_NEW
tr['note'] = ('💡 穂高駅〜中房温泉の南安タクシー「中房温泉行き定期バス」は約55分・1,500円で、運行は4月下旬〜11月上旬の所定日のみ・1日5便程度。'
              '中房温泉へ向かう県道（中房線）は通行できる時間に規制があるので、安曇野市の最新情報を確認する。'
              '登山口は中房温泉の燕岳登山口。'
              '直通の特急あずさ（白馬行き）は1日1本だけ。ほかの列車は松本で大糸線に乗り換える')
m['trainRoutes'] = tr
for k in ('trainAccess', 'trainAccessYokohama', 'trainAccessOmiya'):
    m[k] = src[k].replace(END_OLD, END_NEW)

m.update({
    'id': 'tsubakurodake',
    'name': '燕岳',
    'kana': 'つばくろだけ',
    'elevation': 2763,
    'category': '二百名山',
    'difficulty': '中級',
    'daytrip': True,
    'lat': 36.40674,
    'lng': 137.71275,
    'coordSource': '国土地理院 地名検索',
    'yamapUrl': 'https://yamap.com/mountains/150',
    'yamapName': '燕岳',
    'description': ('常念山脈の北部、安曇野市と大町市の境にそびえる二百名山。白い花崗岩とハイマツ、イルカ岩などの岩峯群から「アルプスの女王」と呼ばれる。'
                    '中房温泉から北アルプス三大急登の合戦尾根を登り、燕山荘を経て山頂へ。表銀座縦走の出発点でもある。'),
    'recommendReason': '白い花崗岩の「アルプスの女王」。整備された合戦尾根で北アルプス入門に人気',
    'metaDescriptionManual': ('燕岳（つばくろだけ・2,763m）は白い花崗岩と岩峯群から「アルプスの女王」と呼ばれる二百名山。'
                              '中房温泉から合戦尾根を登るコース・アクセス・装備を解説。'),
    'metaAuto': True,
    'nearby': ['otenshoudake', 'jonengatake'],
    'vibes': ['view', 'alpine', 'ridge', 'flower'],
    'types': ['adventure', 'easy'],
    'seasonOk': ['summer', 'fall'],
    'season': '7月〜10月上旬',
    'seasonNoGear': '7月〜9月',
    'season6Crampons': '10月〜6月',
    # 燕山荘：夏山は7月上旬〜10月上旬、10月〜6月は雪の積もる冬山
    'gearCalendar': ['winter_gear', 'winter_gear', 'winter_gear', 'winter_gear', 'winter_gear', 'winter_gear',
                     'no_crampons', 'no_crampons', 'no_crampons',
                     {'split': True, 'before': 'light_crampons', 'after': 'winter_gear', 'changeDate': 11},
                     'winter_gear', 'winter_gear'],
    'seasonCalendar': ['s-hard', 's-hard', 's-hard', 's-hard', 's-hard', 's-hard', 's-ok', 's-ok', 's-ok', 's-gear', 's-hard', 's-hard'],
    'routes': [
        {'name': '中房温泉〜合戦尾根〜燕山荘〜燕岳（往復）', 'time': '8時間55分', 'distance': '9.4km', 'elevation': '+1425m', 'descent': '-1425m',
         'waypoints': '燕岳登山口 → 第1ベンチ → 第2ベンチ → 第3ベンチ → … → 合戦小屋 → 燕山荘 → 燕岳',
         'trailheadName': '中房温泉（燕岳登山口）', 'source': 'YAMAPモデルコース（model-courses/181）',
         'sourceUrl': 'https://yamap.com/model-courses/181', 'lastVerified': TODAY},
        {'name': '中房温泉〜燕岳〜北燕岳〜燕山荘〜大天井岳（往復・1泊2日）', 'time': '16時間40分', 'distance': '19.9km', 'elevation': '+2327m', 'descent': '-2327m',
         'waypoints': '燕岳登山口 → 第1ベンチ → 第2ベンチ → 第3ベンチ → … → 北燕岳 → 燕山荘 → 大天井岳',
         'trailheadName': '中房温泉（燕岳登山口）', 'source': 'YAMAPモデルコース（model-courses/100354）',
         'sourceUrl': 'https://yamap.com/model-courses/100354', 'lastVerified': TODAY},
    ],
    'vibePoints': [
        {'who': '北アルプスに初めて登る人', 'why': '急登でも登山道は整備され、合戦小屋までにベンチが4つある'},
        {'who': '山小屋泊を楽しみたい人', 'why': '燕山荘から山頂まで約40分。喫茶室でケーキを味わえる'},
        {'who': '白い岩と高山植物を見たい人', 'why': '花崗岩の岩峯群と、7月ごろから咲くコマクサ'},
    ],
    'featurePoints': [
        {'tag': 'view', 'label': '360度の大展望', 'text': '槍・穂高連峰や白馬連峰など北アルプスのほとんどが見渡せ、遠くに富士山・南アルプス・八ヶ岳も見える'},
        {'tag': 'collector', 'label': 'アルプスの女王', 'text': '白い花崗岩と緑のハイマツの山。イルカ岩など山頂近くの岩峯群が見どころ'},
        {'tag': 'flower', 'label': 'コマクサ', 'text': '7月ごろから、北燕岳や蛙岩の周りで「高山植物の女王」コマクサが咲き始める'},
        {'tag': 'alpine', 'label': 'ライチョウ', 'text': '北燕岳から表銀座の稜線や、燕山荘の周りで見かけることがある'},
        {'tag': 'hut', 'label': '燕山荘', 'text': '大正10年創業の山小屋。喫茶室ではコーヒーやケーキを味わえ、山頂までは約40分'},
    ],
    'featureSources': ['https://www.enzanso.co.jp/enzanso/attraction', 'https://www.enzanso.co.jp/beginners', 'https://yamap.com/mountains/150'],
    'featureCheckedAt': TODAY,
    'dlReasonsHtml': ('<ul class="dl-reasons">\n'
                      '    <li class="minus">登山口から合戦小屋までは急登が続き、燕山荘まで標高差約1,260m・約5時間の登り</li>\n'
                      '    <li class="minus">日帰りもできるが、標高差約1,300mの急斜面の登り下りで十分な体力が要る</li>\n'
                      '    <li class="minus">下りでの転倒による捻挫・骨折の事故が起きている</li>\n'
                      '    <li>登山道は整備され、合戦小屋までにベンチが4つ（40〜50分ごと）あってペースを作りやすい</li>\n'
                      '    <li>信州 山のグレーディングでは中房温泉からの往復が体力度4・技術的難易度B</li>\n'
                      '    <li>燕山荘から山頂まで約40分。山小屋に泊まって2日に分けて登ることもできる</li>\n'
                      '  </ul>'),
    'dlReasonsSources': ['https://www.enzanso.co.jp/beginners',
                         'https://www.pref.nagano.lg.jp/kankoki/sangyo/kanko/documents/2026_grading_list.pdf'],
    'dlReasonsCheckedAt': TODAY,
    'faq': [
        {'question': '燕岳は初心者でも登れますか？難易度とコース定数を解説',
         'answer': ('燕岳の難易度は中級、コース定数0です。北アルプスの入門の山として人気がありますが、合戦小屋までは急登が続き、標高差は約1,300mあります。'
                    '代表的な中房温泉〜合戦尾根〜燕山荘〜燕岳（往復）は0・0・標高差0が目安。'
                    '日帰りもできますが、体力に自信がなければ燕山荘に泊まる計画が安心です。登山靴・レインウェア・防寒具は必携です。')},
        {'question': '燕岳の所要時間は？日帰りできますか？', 'answer': ''},
        {'question': '燕岳へのアクセス方法は？新宿・横浜からの行き方',
         'answer': ('特急あずさで穂高駅へ行き、中房温泉行きの定期バスで約55分、燕岳登山口のある中房温泉に着きます。'
                    '新宿から約3時間54分、大宮からは新宿で特急に乗り約4時間25分、横浜からは八王子で特急に乗り約4時間21分が目安で、'
                    '運賃はいずれも8,670円です（乗り換えの待ち時間は別）。バスは2026年は4月24日〜11月3日の所定日だけの運行です。')},
        {'question': '燕岳の登山シーズンはいつですか？おすすめの時期',
         'answer': ('燕岳の夏山シーズンは7月上旬〜10月上旬の約3か月です。10月〜6月は雪の積もる冬山で、アイゼンなどの冬山装備と経験が要ります。'
                    'コマクサは7月ごろから咲き始めます。残雪や天気は年によって変わるので、直前の最新情報も確認してください。')},
    ],
    'introHtml': ('<div class="card"><h2><svg width="16" height="16" viewBox="0 0 24 24" style="vertical-align:-3px;margin-right:4px" fill="none" '
                  'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3h10l4 4v14H5z"/>'
                  '<path d="M15 3v4h4"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="13" y2="16"/></svg>山の紹介</h2>'
                  '<p class="intro-text">常念山脈の北部、安曇野市と大町市の境にそびえる二百名山。白い花崗岩とハイマツ、イルカ岩などの岩峯群から「アルプスの女王」と呼ばれる。'
                  '中房温泉から北アルプス三大急登の合戦尾根を登り、燕山荘を経て山頂へ。表銀座縦走の出発点でもある。'
                  '中級レベルでコース定数0、日帰りでの登山が可能。代表コース（x）は所要x/x/標高差x。</p></div>'),
    'hasWeatherWidget': False,
    'hasHeroPhotoScript': False,
    'photos': [],
    'ogUpdatedTime': None,
    'mountainUpdated': TODAY,
})

CHECK = ('<svg class="rec-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
         'stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>')
head = src['vibesHtml'].split('<div class="rec-list">')[0]
items = ''.join('      <div class="rec-item">%s<span><strong>%s</strong>——%s</span></div>\n' % (CHECK, v['who'], v['why']) for v in m['vibePoints'])
m['vibesHtml'] = head + '<div class="rec-list">\n' + items + '    </div>\n  </div>'
m['relatedLinksHtml'] = src['relatedLinksHtml'].replace('大天井岳', '燕岳')
m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)

# 大天井岳の次に入れる
i = next(i for i, x in enumerate(D) if x['id'] == 'otenshoudake')
D.insert(i + 1, m)
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('追加しました：tsubakurodake（%d山）' % len(D))
