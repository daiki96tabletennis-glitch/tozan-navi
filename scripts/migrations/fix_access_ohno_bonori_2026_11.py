"""大野山と棒ノ折山の電車・バスの行き先を、コースの歩き始めに合わせる（2026-11-09。運営者の指示）

どちらも、アクセス欄の行き先から歩き始めるコースが無く、コースに電車のアイコン（routes[].byTrain）が付かなかった。
時間・運賃は Yahoo!乗換案内（2026-11-14 土曜 7時台の出発で検索。運賃はきっぷ）。

大野山：山北駅から歩いて大野山入口 → JR御殿場線の谷峨駅（定番の谷峨駅〜大野山〜山北駅・谷峨駅〜大野山の歩き始め）
  新宿：小田急線快速急行 76分 → 新松田駅 → 徒歩3分 → 松田駅 → JR御殿場線 14分 → 谷峨駅（93分・996円＝小田急796円＋JR200円）
  大宮：JR湘南新宿ライン 30分 → 新宿駅 → 同上（123分・1,524円）
  横浜：JR東海道線 48分 → 国府津駅 → JR御殿場線 30分 → 谷峨駅（78分・1,220円）
棒ノ折山：国際興業バスの河又名栗湖入口のあとに「徒歩11分 → さわらびの湯」を足す（Yahoo!乗換案内の徒歩の時間）。
  さわらびの湯からの2コース（YAMAP 512・22148）の歩き始め。運賃は変わらない。一部のバスは「ノーラ名栗・さわらびの湯」に止まる
  （電車で行ける日帰り登山の最終バスも、このバス停の時刻）

何度流しても同じ結果。このあと mark_train_routes_2026_11.py → build_meta.py --write → gen_mountain_pages.py --id ohnoyama / bonori
→ gen_line_articles.py seibu-hiking → gen_train_daytrip.py → sync_search_pages.py --all → check_pages.py
"""
import json
import os
import sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section  # noqa: E402

PATH = os.path.join(ROOT, 'data', 'mountains.json')
TODAY = '2026-11-09'


def leg(station, icon=None, line=None, minutes=None):
    if icon is None:
        return {'station': station}
    return {'station': station, 'method': {'icon': icon, 'line': line}, 'durationMin': minutes, 'fareYen': None}


def text(legs):
    out = []
    for l in legs:
        out.append(l['station'])
        if l.get('method'):
            mins = l['durationMin']
            t = ('約%d時間%d分' % (mins // 60, mins % 60) if mins >= 60 else '約%d分' % mins).replace('時間0分', '時間')
            out.append(('徒歩' if l['method']['icon'] == 'walk' else l['method']['line']) + t)
    return '→'.join(out)


def hm(mins):
    return ('%d時間%d分' % (mins // 60, mins % 60) if mins % 60 else '%d時間' % (mins // 60)) if mins >= 60 else '%d分' % mins


def total(legs):
    return sum(l.get('durationMin') or 0 for l in legs)


def set_access(m, routes, fares):
    m['trainRoutes']['routes'] = routes
    for dep, key in (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama')):
        m['train' + 'Time' + key] = total(routes[dep]['legs'])
        m['fare' + key] = fares[dep]
    m['trainAccess'] = text(routes['shinjuku']['legs'])
    m['trainAccessOmiya'] = text(routes['omiya']['legs'])
    m['trainAccessYokohama'] = text(routes['yokohama']['legs'])
    m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
    m['mountainUpdated'] = TODAY


def ohnoyama(m):
    odakyu = [leg('新松田駅', 'walk', '徒歩', 3), leg('松田駅', 'train', 'JR御殿場線', 14), leg('谷峨駅')]
    routes = {
        'shinjuku': {'legs': [leg('新宿駅', 'train', '小田急線快速急行', 76)] + odakyu},
        'omiya': {'legs': [leg('大宮駅', 'train', 'JR湘南新宿ライン', 30), leg('新宿駅', 'train', '小田急線快速急行', 76)] + odakyu},
        'yokohama': {'legs': [leg('横浜駅', 'train', 'JR東海道線', 48), leg('国府津駅', 'train', 'JR御殿場線', 30), leg('谷峨駅')]},
    }
    set_access(m, routes, {'shinjuku': 996, 'omiya': 1524, 'yokohama': 1220})
    y = 'https://transit.yahoo.co.jp/search/result?from=%s&to=%s&type=1' % (quote('新宿'), quote('谷峨'))
    m['trainRoutes']['links'] = [{'type': 'yahoo', 'label': '乗換案内で検索', 'url': y}]
    m['busLinks'] = [y]
    m['trailhead'] = '谷峨駅'
    m['nearestStation'] = '谷峨駅'
    m['trainInfo'] = '新宿→新松田・松田→谷峨駅（小田急＋御殿場線 約1時間33分）'
    for f in m.get('faq') or []:
        if f['question'].startswith('大野山へのアクセス方法'):
            f['answer'] = ('新宿駅からは小田急線で新松田駅へ行き、JR御殿場線（松田駅）に乗り換えて谷峨駅へ。駅から歩いて登れ、'
                           '谷峨駅〜大野山〜山北駅の縦走が定番です。新宿から約%s・996円、大宮からは新宿経由で約%s・1,524円、'
                           '横浜からはJR東海道線・御殿場線（国府津乗換）で約%s・1,220円が目安です。'
                           % (hm(m['trainTimeShinjuku']), hm(m['trainTimeOmiya']), hm(m['trainTimeYokohama'])))


def bonori(m):
    routes = m['trainRoutes']['routes']
    for dep in ('shinjuku', 'omiya', 'yokohama'):
        legs = routes[dep]['legs']
        if legs[-1]['station'] == 'さわらびの湯':
            continue
        assert legs[-1]['station'] == '河又名栗湖入口', legs[-1]
        legs[-1] = leg('河又名栗湖入口', 'walk', '徒歩', 11)
        legs.append(leg('さわらびの湯'))
    set_access(m, routes, {'shinjuku': m['fareShinjuku'], 'omiya': m['fareOmiya'], 'yokohama': m['fareYokohama']})
    for f in m.get('faq') or []:
        if f['question'].startswith('棒ノ折山へのアクセス方法'):
            f['answer'] = ('池袋で西武池袋線に乗り換えて飯能駅へ行き、国際興業バスで河又名栗湖入口まで約40分、さわらびの湯まで歩いて約11分です'
                           '（一部のバスは「ノーラ名栗・さわらびの湯」に止まります）。新宿から約%s・1,446円、大宮から約%s・1,687円、'
                           '横浜から約%s・1,962円が目安です。車の場合は都心から約1時間40分が目安です。'
                           % (hm(m['trainTimeShinjuku']), hm(m['trainTimeOmiya']), hm(m['trainTimeYokohama'])))


def main():
    M = json.load(open(PATH, encoding='utf-8'))
    by = {m['id']: m for m in M}
    ohnoyama(by['ohnoyama'])
    bonori(by['bonori'])
    json.dump(M, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    for i in ('ohnoyama', 'bonori'):
        m = by[i]
        print(i, m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'], m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'])
        print('  ', m['trainAccess'])


if __name__ == '__main__':
    main()
