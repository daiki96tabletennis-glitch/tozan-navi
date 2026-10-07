#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""近郊4山（弘法山・矢倉岳・大野山・浅間嶺）の運賃を確定する（2026-10-07）。
出典：
- 弘法山：Yahoo!路線情報 横浜→秦野 617円・59分（相鉄本線特急→海老名→小田急線急行）。横浜発も降車駅を秦野駅に揃える
- 矢倉岳：NAVITIME 新松田駅→（関本で乗り換え）→地蔵堂 1,010円・47分、大雄山駅→地蔵堂 580円・28分
        Yahoo!路線情報 横浜→小田原 1,034円、大雄山線 310円。箱根登山バス 地蔵堂の時刻表（2026年10月1日改正）で本数がごく少ないことを確認
- 大野山：Yahoo!路線情報 新宿→山北 986円（小田急796＋御殿場線190）、横浜→山北（国府津経由）1,220円
- 浅間嶺：Yahoo!路線情報 →武蔵五日市 新宿902／大宮1,034／横浜1,221円、NAVITIME 武蔵五日市駅→払沢の滝入口 530円・23分
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-07'
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))


def hm(x):
    h, mi = divmod(int(x), 60)
    return f'約{h}時間{mi}分' if h and mi else (f'約{h}時間' if h else f'約{mi}分')


def yen(n):
    return format(n, ',') + '円'


def leg(station, icon, line, minutes):
    return {'station': station, 'method': {'icon': icon, 'line': line}, 'durationMin': minutes, 'fareYen': None}


def sync(m, fares, drop):
    R = m['trainRoutes']['routes']
    for dep, K in DEPS:
        m['fare' + K] = fares[dep]
        m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in R[dep]['legs'])
    m['trainAccess'] = legs_text(R['shinjuku']['legs'])
    m['trainAccessOmiya'] = legs_text(R['omiya']['legs'])
    m['trainAccessYokohama'] = legs_text(R['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    keep = [n for n in (m.get('verifyNotes') or []) if not any(k in n for k in drop)]
    m['verifyNotes'] = keep
    m['needsVerification'] = bool(keep)
    m['mountainUpdated'] = V
    m['fareCheckedAt'] = V


def set_faq(m, text):
    hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
    # アクセスのFAQが無い山（弘法山・矢倉岳）は何もしない
    assert len(hit) <= 1, m['id']
    if hit:
        hit[0]['answer'] = text


def times(m):
    return tuple(hm(m['trainTime' + K]) for _, K in DEPS)


# 弘法山
m = N['koubousan']
last = m['trainRoutes']['routes']['shinjuku']['legs'][-1]['station']
m['trainRoutes']['routes']['yokohama'] = {'legs': [leg('横浜駅', 'train', '相鉄本線', 26), leg('海老名駅', 'train', '小田急線（乗換待ち含む）', 33),
                                                   leg('秦野駅', 'walk', '徒歩', 25), {'station': last}]}
sync(m, {'shinjuku': 692, 'omiya': 1220, 'yokohama': 617}, ['横浜発だけ降車駅'])
t = times(m)
set_faq(m, '小田急線の秦野駅から徒歩約25分で登山口です。'
        f'新宿からは小田急線で{t[0]}・{yen(m["fareShinjuku"])}、大宮からは新宿経由で{t[1]}・{yen(m["fareOmiya"])}、横浜からは相鉄本線で海老名に出て小田急線に乗り換え{t[2]}・{yen(m["fareYokohama"])}が目安です。')

# 矢倉岳
m = N['yaguradake']
R = m['trainRoutes']['routes']
for dep in ('shinjuku', 'omiya'):
    b = R[dep]['legs'][-2]
    assert b['station'] == '新松田駅'
    b['method']['line'] = '箱根登山バス（関本で乗り換え）'
    b['durationMin'] = 47
b = R['yokohama']['legs'][-2]
assert b['station'] == '大雄山駅'
b['durationMin'] = 28
m['trainRoutes']['summaryNote'] = '※地蔵堂行きのバスは本数がごく少ない（2026年10月1日改正）。新松田駅からは関本（大雄山駅）で乗り換える。出かける前に箱根登山バスの時刻表で確認を'
sync(m, {'shinjuku': 1806, 'omiya': 2334, 'yokohama': 1924}, ['バス運賃'])
t = times(m)
set_faq(m, '新宿からは小田急線で新松田駅へ行き、箱根登山バスを関本（大雄山駅）で乗り継いで地蔵堂バス停へ向かいます。'
        f'新宿から{t[0]}・{yen(m["fareShinjuku"])}、大宮からは新宿経由で{t[1]}・{yen(m["fareOmiya"])}が目安です。'
        f'横浜からはJR東海道線で小田原駅、伊豆箱根鉄道大雄山線で大雄山駅へ行き、バスで地蔵堂へ。{t[2]}・{yen(m["fareYokohama"])}が目安です。'
        '地蔵堂行きのバスは本数がごく少ないため、時刻を確認してから出かけてください。')

m['trainRoutes']['note'] = '💡 新松田駅から地蔵堂へは、関本（大雄山駅）でバスを乗り継ぐ。関本〜地蔵堂は約28分・580円。本数がごく少ないため、行き帰りとも時刻表を確認してから計画を'
m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
m['trainInfo'] = '新宿→新松田（小田急線）→関本でバス乗り継ぎ→地蔵堂'
N['koubousan']['trainInfo'] = '新宿→秦野駅（小田急線約70分）→徒歩25分'

# 大野山
m = N['ohnoyama']
sync(m, {'shinjuku': 986, 'omiya': 1514, 'yokohama': 1220}, ['JR運賃'])
t = times(m)
set_faq(m, '新宿駅からは小田急線で新松田駅へ行き、JR御殿場線（松田駅）に乗り換えて山北駅へ。徒歩約20分で大野山入口（登山口）です。'
        f'新宿から{t[0]}・{yen(m["fareShinjuku"])}、大宮からは新宿経由で{t[1]}・{yen(m["fareOmiya"])}、横浜からはJR東海道線・御殿場線（国府津乗換）で{t[2]}・{yen(m["fareYokohama"])}が目安です。'
        '山北駅から大野山入口バス停まで富士急湘南バスもありますが本数が少ないため、徒歩が確実です。')

# 浅間嶺
m = N['sengenrei']
for dep in m['trainRoutes']['routes']:
    b = m['trainRoutes']['routes'][dep]['legs'][-2]
    assert b['station'] == '武蔵五日市駅'
    b['durationMin'] = 23
sync(m, {'shinjuku': 1432, 'omiya': 1564, 'yokohama': 1751}, ['バス運賃'])
t = times(m)
set_faq(m, 'JR五日市線の武蔵五日市駅から西東京バスで約23分、払沢の滝入口から登ります。'
        f'新宿からは立川乗換で{t[0]}・{yen(m["fareShinjuku"])}、大宮からは武蔵野線経由で{t[1]}・{yen(m["fareOmiya"])}、横浜からは南武線経由で{t[2]}・{yen(m["fareYokohama"])}が目安です。')

json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for i in ['koubousan', 'yaguradake', 'ohnoyama', 'sengenrei']:
    m = N[i]
    print(i, m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'], m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'], m['verifyNotes'])
