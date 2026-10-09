#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""装備カレンダー：切替日を確認できない月は安全側（厳しいほう）の区分にする（運営者の方針・2026-10-09）。
- 北岳・奥穂高岳・槍ヶ岳：7月上旬〜中旬まで雪渓・残雪があるが、切替日が分からない → 7月全体を軽アイゼン等に
  （山梨県の北岳登山案内「残雪は7月上旬、年により7月下旬まで」、涸沢・槍沢の残雪情報）
- 槍ヶ岳・奥穂高岳：6月は槍沢・涸沢が雪渓で、ピッケル・12本爪アイゼンなどの雪山装備が必要との記録 → 6月を冬山装備に
- 針ノ木岳：8月の針ノ木雪渓は出典が取れていない → 安全側で軽アイゼン等に
- 百蔵山：隣の扇山と同じく 12〜2月を軽アイゼン等に
旧フィールド・FAQ・装備カードも同じ内容に揃える。新構造の山（槍ヶ岳・奥穂高岳）は conditions.gearMonthly を直し、build_derived.py で反映する。
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


def old_light(mid, months, six_text, faq_text=None):
    m = N[mid]
    assert m.get('dataModel') != 'ssot-v1'
    for mo in months:
        assert m['gearCalendar'][mo - 1] == 'no_crampons', (mid, mo)
        m['gearCalendar'][mo - 1] = 'light_crampons'
        m['seasonCalendar'][mo - 1] = 's-gear'
    assert not G.validate(m['gearCalendar'])
    keys = set(m['gearCalendar'])
    m['calLegend'] = [G.LABEL[k] for k in G.KEYS if k in keys]
    m['seasonNoGear'] = ranges([i + 1 for i in range(12) if m['gearCalendar'][i] == 'no_crampons'])
    if six_text:
        m['season6Crampons'] = six_text
    if faq_text:
        hit = [q for q in m['faq'] if 'シーズン' in q['question']]
        assert len(hit) == 1, mid
        hit[0]['answer'] = faq_text
    m['mountainUpdated'] = V
    add_light(mid, months)


# 北岳
old_light('kitadake', [7], None,
          '北岳の登山シーズンは7月〜9月が目安です。7月は上旬（年によっては下旬）まで残雪や雪渓があり、チェーンスパイクや6本爪アイゼンなどの軽アイゼン等が必要になることがあります。'
          '残雪の状況は年によって変わるため、直前の最新情報を確認してください。')
# 針ノ木岳（8月）
old_light('harinokidake', [8], '7月〜8月・10月',
          '針ノ木岳の登山シーズンは7月〜10月が目安です。7月〜8月は針ノ木雪渓に雪が残り、チェーンスパイクや6本爪アイゼンなどの軽アイゼン等が必要です。'
          '6月の雪渓は、12本爪アイゼン・ピッケル等の冬山装備が必要です。残雪の状況は年によって変わるため、直前の最新情報を確認してください。')
# 百蔵山
old_light('momakurasan', [12, 1, 2], '12月〜2月',
          '百蔵山は通年登れます。12月〜2月は積雪や凍結があり、チェーンスパイクや6本爪アイゼンなどの軽アイゼン等が必要になることがあります。積雪・凍結の状況は年によって変わるため、直前の最新情報を確認してください。')
N['momakurasan']['season'] = '通年（冬は積雪・凍結に注意）'

# 槍ヶ岳・奥穂高岳（新構造）
for mid in ('yari', 'hotaka'):
    m = N[mid]
    gm = m['conditions']['gearMonthly']
    assert gm[5] == 'snow_caution' and gm[6] == 'normal', (mid, gm)
    gm[5] = 'winter'
    gm[6] = 'snow_caution'
    m['conditions']['gearSource'] = '6月は雪渓のため冬山装備、7月は切替日が不明のため安全側で軽アイゼン等（2026-10-09）'
    m['mountainUpdated'] = V
    set_winter(mid, [6])
    add_light(mid, [7])

json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump(GD, open(GP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok')
