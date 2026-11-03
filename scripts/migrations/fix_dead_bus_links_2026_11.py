#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""開けなくなっていた時刻表などのリンクを差し替える（2026-11-03。運営者「筑波山でバス時刻表を開くと見つかりません」から全山を確認）。

ブラウザで開いて、ページが消えていた（404・400・「アクセス権限がありません」）ものだけ。差し替え先はブラウザで開けることを確認した。
PDF は改正ごとに名前が変わるので、時刻表の並ぶページへリンクする。
中央アルプス観光（木曽駒ヶ岳）はブラウザでも 403 だが、公式のページなので変えていない。
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section

KOBOTOKE = 'https://transfer.navitime.biz/bus-navi/pc/transfer/DepArrTimeList?snode=00020348&gnode=00020514'
FIX = {
    # 山ID: [(前のURL, 新しいURL, 新しい表示名)]
    'amagi': [('https://www.navitime.co.jp/bus/diagram/timelist?departure=00307097&arrival=00307402&line=00055624',
               'https://www.tokaibus.jp/rosen/timetable.html', 'バス時刻表（東海バス「伊豆天城リゾート」）')],
    'ryokami': [('https://www.town.ogano.lg.jp/kurashi-tetsuzuki/bus-taxi/',
                 'https://kanko-ogano.jp/2025/04/20210326/', '小鹿野町営バス 時刻表（小鹿野町観光協会）')],
    'nantaisan': [('https://www.tobu-bus.com/pc/area/nikko.html',
                   'https://www.tobu-bus.com/pc/area/nikko/', 'バス時刻表（東武バス 日光エリア）')],
    'terkari': [('https://tohyamago.com/archives/19377',
                 'https://tohyamago.com/archives/3681', None)],
    'hakusan': [('https://www.hokutetsu.co.jp/news/news-11388/',
                 'https://www.hokutetsu.co.jp/tourism-bus/', None)],
    'kagenobusan': [('https://www.keio-bus.com/rosen/timetable/', KOBOTOKE, 'バス時刻表（高尾駅北口→小仏）')],
    'kobotokeshiroyama': [('https://transfer.navitime.biz/keio-bus/pc/diagram/BusDiagram?stationCd=00003793&updown=0', KOBOTOKE, 'バス時刻表（高尾駅北口→小仏）')],
    'iyogatake': [('https://www.city.minamiboso.chiba.jp/0000001487.html',
                   'https://www.city.minamiboso.chiba.jp/0000000796.html', 'トミー号 時刻表（南房総市）')],
    'bonori': [('https://transfer.navitime.biz/kokusaikogyo/pc/diagram/BusDiagram?stationCd=00021504&updown=0',
                'https://www.navitime.co.jp/bus/diagram/timelist?departure=00124293&arrival=00124340&line=00029154', 'バス時刻表（飯能駅→河又名栗湖入口）')],
}


def main():
    P = os.path.join(ROOT, 'data', 'mountains.json')
    s = open(P, encoding='utf-8').read()
    D = json.loads(s)
    n = 0
    for m in D:
        for old, new, label in FIX.get(m['id'], []):
            hit = [l for l in m['trainRoutes']['links'] if l['url'] == old]
            assert len(hit) == 1, (m['id'], old)
            hit[0]['url'] = new
            if label:
                hit[0]['label'] = label
            lk = m['trainRoutes']['links']
            m['busLinks'] = [l['url'] for l in lk if l.get('type') == 'yahoo'] or None
            m['busScheduleLinks'] = [l['url'] for l in lk if l.get('type') == 'bus'] or None
            m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
            m['mountainUpdated'] = '2026-11-03'
            n += 1
    assert n == sum(len(v) for v in FIX.values())
    open(P, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=2) + ('\n' if s.endswith('\n') else ''))
    print('差し替え', n)


if __name__ == '__main__':
    main()
