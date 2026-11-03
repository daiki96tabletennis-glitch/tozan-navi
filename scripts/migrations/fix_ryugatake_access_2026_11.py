#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""竜ヶ岳の電車・バスを、高速バスから電車（特急「富士回遊」）の経路にする（2026-11-03。運営者の指示）。

確かめたこと（Yahoo!路線情報・現金・2026-11-07 土曜。河口湖駅 9:35 発の周遊バスに乗り継げる便）
- 新宿 7:30 → 河口湖 9:28 特急「富士回遊3号」（乗り換えなし）1時間58分・4,200円（乗車券2,580円＋指定席1,620円）
- 大宮 6:43 → 新宿 7:15 JR湘南新宿ライン → 富士回遊3号 → 河口湖 9:28。4,390円（乗車券2,770円＋指定席1,620円）
- 横浜 6:48 → 新宿 7:21 JR湘南新宿ライン → 富士回遊3号 → 河口湖 9:28。4,390円
- 普通列車（大月乗り換え）なら新宿〜河口湖 2,580円・2時間25分（河口湖 9:45 着で、次の周遊バスは 10:35）
河口湖駅〜本栖湖の周遊バス（57分・1,470円）は前のまま（運賃は乗換案内の値。公式の区間運賃は未確認）。
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section

P = os.path.join(ROOT, 'data', 'mountains.json')
BUSLINE = '富士急バス「鳴沢・精進湖・本栖湖周遊バス（ブルーライン）」'
FUJI = 'JR中央線・富士急行線直通特急「富士回遊」'
BUS_FARE = 1470


def hm(mi):
    h, m = divmod(mi, 60)
    return ('%d時間%d分' % (h, m)) if h and m else (('%d時間' % h) if h else ('%d分' % m))


def leg(st, icon, line, mi):
    return {'station': st, 'method': {'icon': icon, 'line': line}, 'durationMin': mi, 'fareYen': None}


def main():
    s = open(P, encoding='utf-8').read()
    D = json.loads(s)
    m = next(x for x in D if x['id'] == 'ryugatake')
    tr = m['trainRoutes']
    last = [leg('河口湖駅', 'bus', BUSLINE, 57), {'station': '本栖湖'}]
    tr['routes'] = {
        'shinjuku': {'legs': [leg('新宿駅', 'train', FUJI, 118)] + [dict(x) for x in last]},
        'omiya': {'legs': [leg('大宮駅', 'train', 'JR湘南新宿ライン', 32), leg('新宿駅', 'train', FUJI, 118)] + [dict(x) for x in last]},
        'yokohama': {'legs': [leg('横浜駅', 'train', 'JR湘南新宿ライン', 33), leg('新宿駅', 'train', FUJI, 118)] + [dict(x) for x in last]},
    }
    tr['lineName'] = '特急「富士回遊」・' + BUSLINE
    fares = {'shinjuku': 4200, 'omiya': 4390, 'yokohama': 4390}
    for dep, key in (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama')):
        m['trainTime' + key] = sum(l.get('durationMin') or 0 for l in tr['routes'][dep]['legs'])
        m['fare' + key] = fares[dep] + BUS_FARE
    tr['note'] = ('💡 河口湖駅から富士急バス「鳴沢・精進湖・本栖湖周遊バス（ブルーライン）」で本栖湖まで約57分・1,470円。'
                  '本栖湖バス停は県営本栖湖駐車場の前。'
                  '河口湖駅発の午前の便は9時35分・10時35分・11時35分。'
                  '新宿7時30分発の特急「富士回遊3号」（河口湖9時28分着）なら9時35分の便に乗り継げる。'
                  '特急は全席指定で、運賃に指定席の料金を含む。'
                  '普通列車（大月乗り換え）なら新宿〜河口湖が2,580円・約2時間25分。'
                  'バスタ新宿・横浜駅からは河口湖駅への高速バスもある')
    tr['summaryNote'] = '※運賃は河口湖駅までの電車（特急「富士回遊」の指定席の料金を含む。新宿4,200円・大宮4,390円・横浜4,390円）と、周遊バスの河口湖駅〜本栖湖1,470円の合計。'
    for l in tr.get('links') or []:
        if l.get('type') == 'yahoo':
            l['url'] = 'https://transit.yahoo.co.jp/search/result?from=新宿&to=河口湖&type=1'
    def plain(dep):
        legs = tr['routes'][dep]['legs']
        out = legs[0]['station']
        for i in range(len(legs) - 1):
            out += '→%s約%s→%s' % (legs[i]['method']['line'], hm(legs[i]['durationMin']), legs[i + 1]['station'])
        return out
    m['trainAccess'] = plain('shinjuku')
    m['trainAccessOmiya'] = plain('omiya')
    m['trainAccessYokohama'] = plain('yokohama')
    if 'trainInfo' in m:
        m['trainInfo'] = '新宿→河口湖駅（特急「富士回遊」約1時間58分）→周遊バス約57分→本栖湖'
    m['trainAccessHtml'] = render_ts_section(tr, m)
    hit = [q for q in m['faq'] if 'アクセス' in q['question']]
    assert len(hit) == 1
    hit[0]['answer'] = ('河口湖駅から富士急バスの周遊バス（ブルーライン）で本栖湖まで約57分です。'
                        '河口湖駅へは新宿から特急「富士回遊」で乗り換えなしで行けます。'
                        '新宿からは約%s、大宮からは約%s、横浜からは約%s（どちらも新宿で富士回遊に乗る）が目安で、'
                        '運賃は新宿から%s円、大宮から%s円、横浜から%s円です（乗り換えの待ち時間は別）。') % (
        hm(m['trainTimeShinjuku']), hm(m['trainTimeOmiya']), hm(m['trainTimeYokohama']),
        format(m['fareShinjuku'], ','), format(m['fareOmiya'], ','), format(m['fareYokohama'], ','))
    m['mountainUpdated'] = '2026-11-03'
    open(P, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=2) + ('\n' if s.endswith('\n') else ''))
    print(m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'], m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'])
    print(hit[0]['answer'])


if __name__ == '__main__':
    main()
