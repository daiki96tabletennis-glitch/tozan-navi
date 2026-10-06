#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""光岳（前回修正の誤りを戻す）・聖岳・鋸岳の通行状況、明神ヶ岳のルート作り直し（2026-10-06）。

出典
- 遠山郷観光協会「登山口や山小屋などの情報一覧」「易老渡登山口までのタクシー送迎について」（どちらも2026-07-09更新）
- 伊那市公式「戸台河原駐車場に関するお知らせ」（2025-04-21更新）
- YAMAPモデルコース 15215（宮城野営業所前バス停〜明神ヶ岳 往復 4時間0分・7.2km・+724m・定数17）
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
PATH = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(PATH, encoding='utf-8'))
N = {m['id']: m for m in D}
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))
TOHYAMA = 'https://tohyamago.com/archives/18'
SHIBAZAWA_P = '芝沢ゲート駐車場（約50台・利用協力金 約1,000円）'

def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')

def sync(m):
    R = m['trainRoutes']['routes']
    for dep, K in DEPS:
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)

# ── 光岳：予約制タクシーは易老渡駐車場まで入れる（特定車両）。前回「芝沢ゲートまで45分＋徒歩」としたのは誤り ──
m = N['terkari']
m['trailhead'] = '易老渡'
m['parking'] = SHIBAZAWA_P + '。一般車はここまでで、易老渡へは歩いて約1時間30分'
for dep, _ in DEPS:
    legs = m['trainRoutes']['routes'][dep]['legs']
    assert legs[-2]['station'] == '芝沢ゲート' and legs[-3]['method']['icon'] == 'taxi', dep
    legs[-3]['durationMin'] = 80
    legs[-3]['method']['line'] = '予約制タクシー（易老渡まで入れる特定車両）'
    del legs[-2]
    assert legs[-1]['station'] == '易老渡'
m['trainRoutes']['note'] = (
    '💡 道の駅遠山郷から易老渡駐車場まで、予約制のタクシー送迎がある（2026年は7月1日〜11月8日）。'
    '行きは道の駅遠山郷を4時30分発、帰りは易老渡を13時発で、約1時間20分。'
    '料金は1台15,000〜20,000円（メーター制または時間制）。事前にタクシー会社へ直接予約する。'
    '芝沢ゲートでの乗り降りはできない。'
    '始発のバスでは間に合わないので、遠山郷か飯田市内に前泊する。'
    '飯田駅前〜かぐらの湯は信南交通「遠山郷線」で約1時間23分、1日数本。'
    '表示の運賃は高速バス・路線バス・タクシーを合わせた概算で、正式な額は未確認')
m['trainAccessLabel'] = '易老渡（予約制タクシー）'
sync(m)
hit = [q for q in m['faq'] if 'アクセス方法' in q['question']][0]
hit['answer'] = (f'光岳へは新宿から高速バスで飯田駅まで約4時間10分、信南交通の遠山郷線でかぐらの湯（道の駅遠山郷）まで約1時間23分、そこから予約制タクシーで易老渡まで約1時間20分です。'
                 f'新宿から{hm(m["trainTimeShinjuku"])}・運賃約24,800円が目安（大宮・横浜は新宿経由でほぼ同程度）。'
                 'タクシーは早朝4時30分発の事前予約制（2026年は7月1日〜11月8日）のため前泊が必要です。マイカーは芝沢ゲートまでで、易老渡へは歩いて約1時間30分かかります。')
m['verifyNotes'] = ['運賃にタクシー代の概算が含まれている（タクシーは1台15,000〜20,000円）', '高速バス（新宿〜飯田）は日によって運賃が変わる。遠山郷線の運賃は未確認']

# ── 聖岳：便ヶ島〜西沢渡は災害復旧工事で当分の間通行不可（2026-07-09時点） ──
m = N['hijiridade']
m['parking'] = SHIBAZAWA_P
m['routes'][0]['status'] = {'state': 'closed', 'label': '通行止め（便ヶ島〜西沢渡）'}
m['warnBanner'] = {
    'type': 'yellow', 'title': '便ヶ島からのルートは通行止め',
    'text': ('便ヶ島〜西沢渡の区間は災害復旧工事のため、当分の間通れません（遠山郷観光協会・2026年7月9日更新）。'
             '長野県側の便ヶ島から聖岳へは登れないので、静岡県側の聖沢登山口などを使ってください。'
             '一般車が入れるのは芝沢ゲートまでです。'
             '出発前に最新の状況を確認してください。'),
    'url': TOHYAMA, 'linkText': '遠山郷観光協会の登山情報'}
m['verifyNotes'] = ['便ヶ島〜西沢渡の通行止めの解除時期', '聖沢登山口ルートの時間・距離は未登録（代表ルートが通行止めのため、登録が必要）']

# ── 鋸岳：戸台河原駐車場は流出して利用不可（伊那市公式） ──
m = N['nokogiriyama']
m['warnBanner'] = {
    'type': 'yellow', 'title': '戸台河原駐車場は使えません',
    'text': ('戸台河原駐車場は大雨で流出し、利用できません（復旧時期は未定）。'
             '伊那市は南アルプス林道バスの駐車場（戸台パーク）を使い、路上駐車をしないよう呼びかけています。'
             '戸台河原から先は川を何度も渡ります。'
             'コースの時間・距離は戸台河原を起点にした値なので、戸台パークからの歩きが加わります。'),
    'url': 'https://www.inacity.jp/kankojoho/sangaku_alps/minamialps/minamialps_tozan/tozanshanominasamahe/2021todaigawara.html',
    'linkText': '伊那市のお知らせ'}
m['verifyNotes'] = ['戸台パーク駐車場の台数・料金（約700台・1,000円との情報）', '戸台パーク〜戸台河原の徒歩時間', '鋸岳の稜線（第一高点〜第二高点）に崩落箇所があるとの市の情報（2022年）の現況']

# ── 明神ヶ岳：出典不明の「矢倉沢登山口 往復」を、宮城野からの往復に置き換える ──
m = N['myojingatake']
old = m['routes'][0]
assert old['name'] == '矢倉沢登山口 往復'
m.setdefault('removedRoutes', []).append(dict(old, removedReason='明神ヶ岳の登山口として確認できない（矢倉岳の内容が混入した疑い）', removedAt='2026-10-06'))
m['routes'][0] = {
    'name': '宮城野〜明神ヶ岳（往復）', 'time': '4時間', 'distance': '7.2km', 'elevation': '+724m', 'coeff': 17,
    'waypoints': '宮城野 → 明神ヶ岳登山口 → 鞍部 → 明神ヶ岳', 'trailheadName': '宮城野',
    'source': 'YAMAPモデルコース（model-courses/15215）'}
a = '代表コースの矢倉沢登山口 往復は4時間30分・9.0km・標高差+850m'
assert a in m['dlNoteHtml']
m['dlNoteHtml'] = m['dlNoteHtml'].replace(a, '代表コースの宮城野〜明神ヶ岳（往復）は4時間・7.2km・標高差+724m')
a = '宮城野からの往復コースで約4時間30分、標高差約850m'
assert a in m['faq'][0]['answer']
m['faq'][0]['answer'] = m['faq'][0]['answer'].replace(a, '宮城野からの往復コースで約4時間、標高差約724m')
m['verifyNotes'] = ['宮城野周辺の駐車場', '地図ボタンは座標未確認のため名称検索', '上部のコース定数（25〜29）は旧ルート基準のまま。新ルートは17（コース定数は保留中）']

for mid in ('terkari', 'hijiridade', 'nokogiriyama', 'myojingatake'):
    N[mid]['mountainUpdated'] = '2026-10-06'
json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(N['terkari']['trainTimeShinjuku'], N['terkari']['trainTimeOmiya'], N['terkari']['trainTimeYokohama'])
