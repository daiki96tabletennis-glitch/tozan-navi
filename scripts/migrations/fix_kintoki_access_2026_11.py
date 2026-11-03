#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""金時山の電車・バスを「小田原駅から箱根登山バス」の経路にする（2026-11-03。運営者の指示）。

確かめたこと（2026-11-03）
- 箱根ナビ（箱根登山バス公式）の経路検索 小田原駅→金時神社入口（2026-11-07 土曜 7:00 以降）：
  小田原駅 7:10 発 箱根登山バス［T］桃源台線（桃源台行）→ 仙石 7:49 着（39分・1,260円）→ 徒歩 → 金時神社入口 8:06 着（17分）
- Yahoo!路線情報（2026-11-07 6時台・現金）：
  新宿→小田原 小田急小田原線急行 1時間30分・910円／大宮→小田原 JR湘南新宿ライン快速 1時間55分・2,090円／横浜→小田原 JR東海道本線 58分・1,040円
- 小田急ハイウェイバス「新宿－御殿場・箱根線」公式の運賃表：新宿～金時登山口 2,400円、新宿～乙女峠 2,340円
  （前のデータの 1,940円は誤り。時刻表のページに金時登山口の所要時間は無いので、時間は書かない）
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section

P = os.path.join(ROOT, 'data', 'mountains.json')
LP = os.path.join(ROOT, 'data', 'line_articles.json')
DAY = '2026-11-03'
NAVI = 'https://www.hakonenavi.jp/transportation/ticket_info/search/route/?departure=%E5%B0%8F%E7%94%B0%E5%8E%9F%E9%A7%85&destination=%E9%87%91%E6%99%82%E7%A5%9E%E7%A4%BE%E5%85%A5%E5%8F%A3&type=1'

BUS = [
    {'station': '小田原駅', 'method': {'icon': 'bus', 'line': '箱根登山バス［T］桃源台線（桃源台行）'}, 'durationMin': 39, 'fareYen': None},
    {'station': '仙石', 'method': {'icon': 'walk', 'line': '徒歩'}, 'durationMin': 17, 'fareYen': None},
    {'station': '金時神社入口'},
]
FIRST = {
    'shinjuku': ('新宿駅', 'train', '小田急小田原線（急行）', 90, 910),
    'omiya': ('大宮駅', 'train', 'JR湘南新宿ライン（快速）', 115, 2090),
    'yokohama': ('横浜駅', 'train', 'JR東海道線', 58, 1040),
}
BUS_FARE = 1260


def hm(mi):
    h, m = divmod(mi, 60)
    return ('%d時間%d分' % (h, m)) if h and m else (('%d時間' % h) if h else ('%d分' % m))


def plain(dep):
    st, _, line, mi, _ = FIRST[dep]
    return '%s→%s約%s→小田原駅→箱根登山バス［T］桃源台線約39分→仙石→徒歩約17分→金時神社入口' % (st, line, hm(mi))


def main():
    s = open(P, encoding='utf-8').read()
    D = json.loads(s)
    m = next(x for x in D if x['id'] == 'kintoki')
    tr = m['trainRoutes']
    tr['lineName'] = '小田急線・箱根登山バス'
    for dep, (st, icon, line, mi, fare) in FIRST.items():
        tr['routes'][dep] = {'legs': [{'station': st, 'method': {'icon': icon, 'line': line}, 'durationMin': mi, 'fareYen': None}] + [dict(l) for l in BUS]}
    tr['note'] = ('💡 小田原駅の4番のりばから箱根登山バス［T］桃源台線（桃源台行き）に乗り、仙石で降りて金時神社入口まで歩く（約17分）。'
                  'バスは予約なしで乗れる。'
                  'バスタ新宿からは小田急ハイウェイバス「新宿－御殿場・箱根線」で金時登山口・乙女峠まで乗り換えなしで行ける（金時登山口まで2,400円）。'
                  '高速バスは本数が少ないので、時刻と予約（発車オーライネット）を事前に確認する。'
                  '小田急ロマンスカーで箱根湯本駅へ出て、箱根登山バス［L］で金時登山口まで行く方法もある')
    tr['summaryNote'] = '※運賃は小田原駅までの電車（新宿910円・大宮2,090円・横浜1,040円）と、箱根登山バスの小田原駅〜仙石1,260円の合計。'
    tr['links'] = [
        {'type': 'yahoo', 'label': '乗換案内で検索', 'url': 'https://transit.yahoo.co.jp/search/result?from=新宿&to=小田原&type=1'},
        {'type': 'bus', 'label': '箱根ナビ 経路検索（小田原駅〜金時神社入口）', 'url': NAVI},
        {'type': 'bus', 'label': '高速バスの時刻表（小田急ハイウェイバス）', 'url': 'https://odakyu-highway.jp/hakone/'},
    ]
    for dep, key in (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama')):
        legs = tr['routes'][dep]['legs']
        m['trainTime' + key] = sum(l.get('durationMin') or 0 for l in legs)
        m['fare' + key] = FIRST[dep][4] + BUS_FARE
    m['trainAccess'] = plain('shinjuku')
    m['trainAccessOmiya'] = plain('omiya')
    m['trainAccessYokohama'] = plain('yokohama')
    m['trainInfo'] = '新宿→小田原駅（小田急線急行約90分）→箱根登山バス約39分→仙石から徒歩約17分'
    m['trainAccessHtml'] = render_ts_section(tr, m)
    hit = [q for q in m['faq'] if 'アクセス' in q['question']]
    assert len(hit) == 1
    hit[0]['answer'] = ('電車なら小田原駅から箱根登山バス［T］桃源台線に乗り、仙石で降りて金時神社入口まで歩きます（約17分）。'
                        '新宿からは約%s（運賃%s円）、大宮からは約%s（運賃%s円）、横浜からは約%s（運賃%s円）が目安です。'
                        'バスタ新宿からは小田急ハイウェイバスで金時登山口まで乗り換えなしで行けます。'
                        '車の場合は都心から約1時間5分が目安です。') % (
        hm(m['trainTimeShinjuku']), format(m['fareShinjuku'], ','),
        hm(m['trainTimeOmiya']), format(m['fareOmiya'], ','),
        hm(m['trainTimeYokohama']), format(m['fareYokohama'], ','))
    vn = m.get('verifyNotes') or []
    vn = [v for v in vn if '高速バスの運賃' not in v]
    m['verifyNotes'] = vn
    m['mountainUpdated'] = '2026-11-03'
    out = json.dumps(D, ensure_ascii=False, indent=2) + ('\n' if s.endswith('\n') else '')
    open(P, 'w', encoding='utf-8').write(out)
    print(m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'], m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'])

    # 路線別の記事：本線が小田原駅からのバスになったので、別の行き方（altAccess）を外し、文を合わせる
    ls = open(LP, encoding='utf-8').read()
    L = json.loads(ls)
    od = L['odakyu-hiking']
    n = 0
    for sec in od['sections']:
        for it in sec['items']:
            if it['id'] == 'kintoki':
                it.pop('altAccess', None)
                sec['title'] = '箱根の金時山へ（小田原駅からバス）'
                sec['lead'] = '小田原駅から箱根登山バスで仙石へ行き、金時神社入口まで歩きます。バスタ新宿から小田急の高速バスで登山口まで行くこともできます。'
                n += 1
    assert n == 1
    t = json.dumps(od, ensure_ascii=False)
    t2, k = re.subn('箱根の金時山は、バスタ新宿から小田急の高速バスで登山口まで行けるほか、小田原駅から箱根登山バスでも行けます。',
                    '箱根の金時山は、小田原駅から箱根登山バスで行けます（バスタ新宿からの高速バスもあります）。', t)
    assert k == 1, k
    L['odakyu-hiking'] = json.loads(t2)
    open(LP, 'w', encoding='utf-8').write(json.dumps(L, ensure_ascii=False, indent=2) + ('\n' if ls.endswith('\n') else ''))
    print('記事を直しました')


if __name__ == '__main__':
    main()
