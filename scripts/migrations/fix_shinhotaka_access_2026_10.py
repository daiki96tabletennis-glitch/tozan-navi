#!/usr/bin/env python3
"""笠ヶ岳・西穂高岳の電車・バスの経路を直す（2026-10-27。運営者の指示）。

前のデータは「バスタ新宿→新穂高温泉 直通・約5時間45分・8,000円」だったが誤り。
京王バス・濃飛バスの高速バスは「新宿〜飛騨高山線」で、新穂高温泉には止まらない（途中の停留所は平湯温泉・丹生川など。
5時間45分は高山までの時間）。平湯温泉で濃飛バスの路線バス「平湯・新穂高線」に乗り換える。

出典（2026-10-27 に確認）
- 濃飛バス 高山・平湯温泉〜新宿線 https://www.nouhibus.co.jp/highwaybus/shinjuku/
  バスタ新宿 7:05→平湯温泉 11:45 などで約4時間40分。運賃はバスタ新宿〜平湯温泉（高山まで同じ）昼行8,000円。全席指定・予約制（1か月前から）
- 濃飛バス 平湯・新穂高線 https://www.nouhibus.co.jp/route_bus/shinhotaka-line/
  時刻表（2026/4/1）：平湯温泉発→新穂高温泉 32分、→新穂高ロープウェイ 36分（例：12:40発→13:12・13:16）。ほぼ1時間に1本
  運賃表（fare_hirayu_shinhotaka.pdf）：平湯温泉〜新穂高温泉・新穂高ロープウェイ 910円
- 大宮→新宿 530円・横浜→新宿 620円（Yahoo!路線情報・きっぷ）は前のデータのまま
- 新穂高ロープウェイ（第1・第2の通し）片道2,400円・約22分（西穂高岳。追加のときに確認済み）

Yahoo!乗換案内は平湯温泉・新穂高のバス停で検索できないので、リンクは濃飛バスの公式ページにする。

  python3 scripts/migrations/fix_shinhotaka_access_2026_10.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section  # noqa: E402

PATH = os.path.join(ROOT, 'data', 'mountains.json')
TODAY = '2026-10-27'
D = json.load(open(PATH, encoding='utf-8'))
BY = {m['id']: m for m in D}

HB = '京王バス・濃飛バス「新宿〜飛騨高山線」'
LOCAL = '濃飛バス「平湯・新穂高線」'
HB_MIN, HB_FARE = 280, 8000
LOCAL_FARE = 910
TO_SHINJUKU = {'omiya': ('大宮駅', 'JR埼京線', 30, 530), 'yokohama': ('横浜駅', 'JR湘南新宿ライン', 34, 620)}
LINKS = [{'type': 'bus', 'label': '京王バス・濃飛バス 新宿〜飛騨高山線（時刻表・予約）', 'url': 'https://www.nouhibus.co.jp/highwaybus/shinjuku/'},
         {'type': 'bus', 'label': '濃飛バス 平湯・新穂高線（時刻表・運賃）', 'url': 'https://www.nouhibus.co.jp/route_bus/shinhotaka-line/'}]
NOTE = ('💡 バスタ新宿〜平湯温泉は京王バス・濃飛バスの高速バス「新宿〜飛騨高山線」で約4時間40分・8,000円（昼行）。全席指定・予約制で、乗車1か月前から予約できる。'
        '平湯温泉で濃飛バス「平湯・新穂高線」に乗り換える（新穂高温泉まで約32分・910円。ほぼ1時間に1本）。'
        '新宿から新穂高温泉まで乗り換えなしで行くバスは無い')


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


def build(tail, extra_fare):
    """tail: 平湯温泉から先の区間（平湯温泉の leg を含む）"""
    routes, fares = {}, {}
    routes['shinjuku'] = {'legs': [leg('バスタ新宿', 'bus', HB, HB_MIN)] + tail}
    fares['shinjuku'] = HB_FARE + LOCAL_FARE + extra_fare
    for dep, (st, line, mins, yen) in TO_SHINJUKU.items():
        routes[dep] = {'legs': [leg(st, 'train', line, mins), leg('バスタ新宿', 'bus', HB, HB_MIN)] + tail}
        fares[dep] = yen + HB_FARE + LOCAL_FARE + extra_fare
    return routes, fares


def apply(m, routes, fares, transfers, line_name, note, links, faq3):
    tr = m['trainRoutes']
    tr['routes'] = routes
    tr['lineName'] = line_name
    tr['note'] = note
    tr['links'] = links
    tr['badge'] = {'type': 'year', 'style': None, 'icon': 'check', 'label': '年中運行'}
    for dep, key in (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama')):
        legs = routes[dep]['legs']
        m['trainTime' + key] = sum(x.get('durationMin') or 0 for x in legs)
        m['fare' + key] = fares[dep]
        m['transfers' + key] = transfers[dep]
    m['trainAccess'] = arrow(routes['shinjuku']['legs'])
    m['trainAccessOmiya'] = arrow(routes['omiya']['legs'])
    m['trainAccessYokohama'] = arrow(routes['yokohama']['legs'])
    m['busLinks'] = []
    m['busScheduleLinks'] = [x['url'] for x in links if x['type'] == 'bus']
    for q in m['faq']:
        if 'アクセス' in q['question']:
            q['answer'] = faq3
    m['fareCheckedAt'] = TODAY
    m['mountainUpdated'] = TODAY
    m['trainAccessHtml'] = render_ts_section(tr, m)


# ---- 笠ヶ岳（新穂高温泉） ----
k = BY['kasagatake']
routes, fares = build([leg('平湯温泉', 'bus', LOCAL, 32), leg('新穂高温泉')], 0)
apply(k, routes, fares, {'shinjuku': 1, 'omiya': 2, 'yokohama': 2},
      '京王バス・濃飛バス「新宿〜飛騨高山線」・濃飛バス「平湯・新穂高線」', NOTE, LINKS,
      ('笠ヶ岳の登山口の新穂高温泉へは、バスタ新宿から京王バス・濃飛バスの高速バス（新宿〜飛騨高山線）で平湯温泉へ行き、濃飛バスの路線バス（平湯・新穂高線）に乗り換えます。'
       '新宿から約5時間12分、大宮からは新宿でバスに乗り約5時間42分、横浜からは約5時間46分が目安で（乗り換えの待ち時間は別）、'
       '運賃は新宿から8,910円、大宮から9,440円、横浜から9,530円です。高速バスは全席指定・予約制（乗車1か月前から）なので、早めに予約してください。'))

# ---- 西穂高岳（新穂高ロープウェイ） ----
n = BY['nishihotaka']
routes, fares = build([leg('平湯温泉', 'bus', LOCAL, 36),
                       leg('新穂高ロープウェイ（新穂高温泉駅）', 'ropeway', '新穂高ロープウェイ（第1・第2）', 22), leg('西穂高口駅')], 2400)
apply(n, routes, fares, {'shinjuku': 2, 'omiya': 3, 'yokohama': 3},
      '京王バス・濃飛バス「新宿〜飛騨高山線」・濃飛バス「平湯・新穂高線」・新穂高ロープウェイ',
      NOTE.replace('（新穂高温泉まで約32分・910円。ほぼ1時間に1本）', '（新穂高ロープウェイまで約36分・910円。ほぼ1時間に1本）')
      + '。新穂高ロープウェイは第1・第2の通しで片道2,400円・通年営業。第1は毎時00分・30分、第2は毎時15分・45分発。天候不良や定期点検で運休することがある',
      LINKS + [{'type': 'bus', 'label': '新穂高ロープウェイ 料金・時刻', 'url': 'https://shinhotaka-ropeway.jp/price/'}],
      ('バスタ新宿から京王バス・濃飛バスの高速バス（新宿〜飛騨高山線）で平湯温泉へ行き、濃飛バスの路線バス（平湯・新穂高線）で新穂高ロープウェイへ、'
       'ロープウェイ（第1・第2の通し・約22分）で西穂高口駅へ上がります。新宿から約5時間38分、大宮からは新宿でバスに乗り約6時間8分、'
       '横浜からは約6時間12分が目安で（乗り換えの待ち時間は別）、運賃はロープウェイ片道を含めて新宿から11,310円、大宮から11,840円、横浜から11,930円です。'))

json.dump(D, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for mid in ('kasagatake', 'nishihotaka'):
    m = BY[mid]
    print(mid, m['trainTimeShinjuku'], m['trainTimeOmiya'], m['trainTimeYokohama'], m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'])
