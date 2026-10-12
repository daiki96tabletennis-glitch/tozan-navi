#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""電車・バスの終点と、紹介しているコースの出発点が食い違っていた山を直す（2026-10-12）。

- 大岳山：コースは御岳山（ケーブルカーの上）から歩くのに、経路はケーブル下（御岳登山口）で終わり、バス20分・ケーブルカーなしだった。
          注記も「バスは30〜40分間隔」と「10〜20分間隔」が並んでいた。
          → 同じ区間を使う御岳山（mitakesan。2026-10-07 に運賃・時間を検算済み）の経路・運賃にそろえる（御岳山駅まで）。
            確認できていないバスの本数・「約290円」は注記から外す。
- 美ヶ原：直行バスの終点（美ヶ原自然保護センター）から歩くコースが無かった。
          → 「美ヶ原自然保護センター〜王ヶ頭（往復）」を追加。片道 徒歩30分（旅行メディア tabi-mag「美ヶ原」https://tabi-mag.jp/nn085 ）。
            距離・累積標高差は確認できていないので入れない（コース定数も付けない）。
- 聖岳：聖沢登山口のコースに時間・距離が無かった。
          → YAMA HACK「聖岳」（2026/03/10 更新 https://yamahack.com/2309 ）の聖沢登山口往復（聖平小屋泊）15時間45分・23.4km を入れる。
            1日目 聖沢登山口→聖平小屋は6時間10分。同記事の累積標高（上り 4,925m）は大きすぎて確かめられないので入れない（コース定数も付けない）。
"""
import copy, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from render_transit_routes import render_ts_section
from build_derived import legs_text
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-12'
DEPS = (('shinjuku', 'Shinjuku'), ('omiya', 'Omiya'), ('yokohama', 'Yokohama'))

# ── 大岳山 ──
m, s = N['otake'], N['mitakesan']
assert m['trainRoutes']['routes']['shinjuku']['legs'][-1]['station'] == '御岳登山口', '適用済み？'
assert s['trainRoutes']['routes']['shinjuku']['legs'][-1]['station'] == '御岳山'
m['trainRoutes']['routes'] = copy.deepcopy(s['trainRoutes']['routes'])
for dep, K in DEPS:
    m['fare' + K] = s['fare' + K]
    m['trainTime' + K] = sum(l.get('durationMin') or 0 for l in m['trainRoutes']['routes'][dep]['legs'])
    assert m['trainTime' + K] == s['trainTime' + K], dep
m['trainRoutes']['lineName'] = s['trainRoutes'].get('lineName') or m['trainRoutes'].get('lineName')
m['trainRoutes']['summaryNote'] = '※運賃はJR＋西東京バス＋御岳登山鉄道（ケーブルカー片道）の合計。バスとケーブルカーの時刻は季節で変わるので、出発前に確認する'
m['trainRoutes']['note'] = ('💡 御嶽駅から西東京バスでケーブル下へ行き、御岳登山鉄道のケーブルカー（約6分）で御岳山駅へ上がる。'
                            '大岳山へは御岳山駅から歩く（往復のコースタイムは下の「コース」を参照）。'
                            'ケーブルカーの最終に間に合うように下山する')
def hm(x):
    h, mi = divmod(int(x), 60)
    return '約%d時間%d分' % (h, mi) if h and mi else ('約%d時間' % h if h else '約%d分' % mi)


hit = [q for q in m['faq'] if 'アクセス方法' in q['question']]
assert len(hit) == 1
hit[0]['answer'] = ('新宿駅からは電車・バス・ケーブルカーを乗り継いで御岳山駅まで%s（運賃%s円、ケーブルカー含む）。大宮からは%s（運賃%s円）、横浜からは%s（運賃%s円）が目安です。'
                    '車の場合はケーブルカー滝本駅の駐車場を使います。' % (
                        hm(m['trainTimeShinjuku']), format(m['fareShinjuku'], ','), hm(m['trainTimeOmiya']), format(m['fareOmiya'], ','),
                        hm(m['trainTimeYokohama']), format(m['fareYokohama'], ',')))
m['trainAccess'] = legs_text(m['trainRoutes']['routes']['shinjuku']['legs'])
m['trainAccessOmiya'] = legs_text(m['trainRoutes']['routes']['omiya']['legs'])
m['trainAccessYokohama'] = legs_text(m['trainRoutes']['routes']['yokohama']['legs'])
m['trainAccessHtml'] = render_ts_section(m['trainRoutes'], m)
m['mountainUpdated'] = V
m['fareCheckedAt'] = s['fareCheckedAt']
print('otake', m['fareShinjuku'], m['fareOmiya'], m['fareYokohama'], m['trainTimeShinjuku'], '|', m['trainAccess'])

# ── 美ヶ原 ──
m = N['utsukushigahara']
assert not any('自然保護センター' in r['name'] for r in m['routes']), '適用済み？'
m['routes'].append({
    'name': '美ヶ原自然保護センター〜王ヶ頭（往復）', 'time': '1時間', 'waypoints': '美ヶ原自然保護センター → 王ヶ頭',
    'trailheadName': '美ヶ原自然保護センター',
    'accessNote': '松本駅からの「信州美ヶ原高原直行バス」の終点。下の「電車・バスでのアクセス」と同じ経路。車は自然保護センターの駐車場を使う',
    'accessNeedsVerification': False, 'accessSource': '旅行メディア tabi-mag「美ヶ原」（自然保護センター〜王ヶ頭は徒歩30分）', 'accessSourceUrl': 'https://tabi-mag.jp/nn085',
    'accessLastChecked': V, 'needsVerification': True})
m['mountainUpdated'] = V
print('utsukushigahara routes', [r['name'] for r in m['routes']])

# ── 聖岳 ──
m = N['hijiridade']
r = [x for x in m['routes'] if x['name'].startswith('聖沢登山口')]
assert len(r) == 1 and not r[0].get('time'), '適用済み？'
r[0]['time'] = '15時間45分'
r[0]['distance'] = '23.4km'
r[0]['timeNote'] = '1泊2日（聖平小屋泊）。1日目の聖沢登山口→聖平小屋は6時間10分'
r[0]['timeSource'] = 'YAMA HACK「聖岳」（2026/03/10 更新）'
r[0]['timeSourceUrl'] = 'https://yamahack.com/2309'
m['mountainUpdated'] = V
print('hijiridade', r[0]['time'], r[0]['distance'])

json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
