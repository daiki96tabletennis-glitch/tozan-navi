#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""装備カレンダー：区分の監査で、出典で確認できた3山を直す（2026-10-09）。
- 針ノ木岳：代表ルートは針ノ木雪渓を登る。6月は「アイゼン（軽アイゼン不可）・ピッケル・ヘルメット」が必要（針ノ木岳慎太郎祭の装備案内）、
  7月も雪渓が残りチェーンスパイク・軽アイゼンで登られている → 6月を冬山装備、7月を軽アイゼン等に
- 剱岳：別山尾根でも、雪の多い年は7月下旬〜8月上旬まで登山道に雪が残る。海の日の連休ごろにアイゼンなしで入る人が多いと注意喚起
  （富山県警察 山岳情報「試練と憧れ」）→ 7月を軽アイゼン等に
- 那須岳：冬の茶臼岳は峰の茶屋から上で12本爪アイゼン・ピッケルを使う（登山記録）。同じ標高帯の安達太良山・磐梯山に合わせ、12〜3月を冬山装備に
8月の針ノ木雪渓、北岳・奥穂高岳・槍ヶ岳の7月前半は、切替日を確認できないため変えていない（要確認）。
旧フィールド・FAQ・装備カード（gear-data.json）も同じ内容に揃える。
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import gear_calendar as G
from build_derived import ranges
P = os.path.join(ROOT, 'data', 'mountains.json')
GP = os.path.join(ROOT, 'data', 'gear-data.json')
D = json.load(open(P, encoding='utf-8'))
GD = json.load(open(GP, encoding='utf-8'))
N = {m['id']: m for m in D}
V = '2026-10-09'
LIGHT = {'c': 'crampon', 'i': '推奨', 'p': 'エバニュー 6本爪アイゼン',
         'r': '凍結・残雪が見られる時期です。チェーンスパイクや6本爪アイゼンなどの軽アイゼン等があると滑りにくく安心です。事前に最新の積雪・凍結情報を確認してください。'}
W_SHOE = {'c': 'shoe', 'i': '必須', 'p': 'スカルパ マンタテックGTX', 'r': '本格的な積雪期です。アイゼン対応の冬季ブーツに切り替えましょう。'}
W_CRAMPON = {'c': 'crampon', 'i': '推奨', 'p': 'グリベル G12 ニュークラシック',
             'r': '本格的な積雪期です。12本爪アイゼン・ピッケル等の冬山装備と、雪山の経験が必要です。事前に最新の積雪・凍結情報を確認してください。'}


def set_months(m, key, months):
    for mo in months:
        m['gearCalendar'][mo - 1] = key
        m['seasonCalendar'][mo - 1] = G.CLS[key]


def finish(m):
    assert not G.validate(m['gearCalendar'])
    keys = set(m['gearCalendar'])
    m['calLegend'] = [G.LABEL[k] for k in G.KEYS if k in keys]
    m['seasonNoGear'] = ranges([i + 1 for i in range(12) if m['gearCalendar'][i] == 'no_crampons'])
    m['mountainUpdated'] = V


def add_light(mid, months):
    for mo in months:
        cards = GD[mid][str(mo)]
        cards[:] = [c for c in cards if c['c'] != 'crampon']
        idx = max(i for i, c in enumerate(cards) if c['c'] in ('shoe', 'rain')) + 1
        cards.insert(idx, dict(LIGHT))


def set_winter(mid, months):
    for mo in months:
        cards = [c for c in GD[mid][str(mo)] if c['c'] not in ('shoe', 'crampon', 'crampon_next')]
        GD[mid][str(mo)] = [dict(W_SHOE)] + [c for c in cards if c['c'] == 'rain'] + [dict(W_CRAMPON)] + [c for c in cards if c['c'] != 'rain']


def faq(m):
    hit = [q for q in m['faq'] if 'シーズン' in q['question']]
    assert len(hit) == 1, m['id']
    return hit[0]


# 針ノ木岳
m = N['harinokidake']
assert m['gearCalendar'][5] == 'light_crampons' and m['gearCalendar'][6] == 'no_crampons'
set_months(m, 'winter_gear', [6]); set_months(m, 'light_crampons', [7])
finish(m)
m['season6Crampons'] = '7月・10月'
faq(m)['answer'] = ('針ノ木岳の登山シーズンは7月〜10月が目安です。7月は針ノ木雪渓に雪が残り、チェーンスパイクや6本爪アイゼンなどの軽アイゼン等が必要です。'
                    '6月の雪渓は、12本爪アイゼン・ピッケル等の冬山装備が必要です。残雪の状況は年によって変わるため、直前の最新情報を確認してください。')
set_winter('harinokidake', [6]); add_light('harinokidake', [7])

# 剱岳
m = N['tsurugi']
assert m['gearCalendar'][6] == 'no_crampons'
set_months(m, 'light_crampons', [7])
finish(m)
faq(m)['answer'] = ('剱岳の登山シーズンは7月〜9月が目安です。雪の多い年は7月下旬〜8月上旬まで別山尾根の登山道に雪が残り、アイゼンが必要になることがあります。'
                    '残雪の状況は年によって変わるため、直前に富山県警察の山岳情報や山小屋の情報を確認してください。')
add_light('tsurugi', [7])

# 那須岳
m = N['nasu']
assert all(m['gearCalendar'][i] == 'light_crampons' for i in (0, 1, 2, 11))
set_months(m, 'winter_gear', [12, 1, 2, 3])
finish(m)
m['season6Crampons'] = '4月・11月'
faq(m)['answer'] = ('那須岳の登山シーズンは5月〜10月（活火山・規制確認要）が目安です。12月〜3月は強風と凍結が厳しく、峰の茶屋から上は12本爪アイゼン・ピッケル等の冬山装備が必要です。'
                    '4月と11月は残雪や凍結があり、軽アイゼン等が必要になることがあります。直前の最新情報を確認してください。')
set_winter('nasu', [12, 1, 2, 3])

json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump(GD, open(GP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
A = {'no_crampons': '○', 'light_crampons': '△', 'winter_gear': '■', 'closed': '×'}
for i in ('harinokidake', 'tsurugi', 'nasu'):
    m = N[i]
    print(i, ''.join(A[e] for e in m['gearCalendar']), m['seasonNoGear'], '/', m['season6Crampons'])
