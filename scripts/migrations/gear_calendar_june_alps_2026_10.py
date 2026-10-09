#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""装備カレンダー：北アルプス・南アルプスの標高2,800m以上の山で、6月を「軽アイゼン等」から「冬山装備」にする（安全側・2026-10-09）。
6月の3,000m級は残雪期で、雪渓や稜線の雪にピッケル・12本爪アイゼンが必要になることが多い（槍沢・涸沢・針ノ木雪渓の例）。
山ごとの切替時期は確認できていないため、月全体を厳しいほうの区分にする（運営者の方針）。
対象外：八ヶ岳・木曽駒ヶ岳・白山・飯豊山・平ヶ岳など北ア・南ア以外の山、2,800m未満の山（唐松岳・蝶ヶ岳など）。これらは個別の確認が必要。
旧フィールド・装備カードも揃える。新構造の山は conditions.gearMonthly を直し、build_derived.py で反映する。
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import gear_calendar as G
P = os.path.join(ROOT, 'data', 'mountains.json')
GP = os.path.join(ROOT, 'data', 'gear-data.json')
D = json.load(open(P, encoding='utf-8'))
GD = json.load(open(GP, encoding='utf-8'))
V = '2026-10-09'
NAMES = ['五竜岳', '黒部五郎岳', '常念岳', '鹿島槍ヶ岳', '笠ヶ岳', '大天井岳', '野口五郎岳', '薬師岳', '白馬岳', '剱岳', '立山', '乗鞍岳',
         '甲斐駒ヶ岳', '聖岳', '農鳥岳', '仙丈ヶ岳', '塩見岳', '赤石岳', '荒川岳', '間ノ岳', '北岳']
W_SHOE = {'c': 'shoe', 'i': '必須', 'p': 'スカルパ マンタテックGTX', 'r': '本格的な積雪期です。アイゼン対応の冬季ブーツに切り替えましょう。'}
W_CRAMPON = {'c': 'crampon', 'i': '推奨', 'p': 'グリベル G12 ニュークラシック',
             'r': '本格的な積雪期です。12本爪アイゼン・ピッケル等の冬山装備と、雪山の経験が必要です。事前に最新の積雪・凍結情報を確認してください。'}
done = []
for m in D:
    if m['name'] not in NAMES:
        continue
    assert (m.get('elevation') or 0) >= 2800, m['name']
    cal = m['gearCalendar']
    assert cal[4] == 'winter_gear' and cal[5] == 'light_crampons', (m['name'], cal[4:6])
    if m.get('dataModel') == 'ssot-v1':
        gm = m['conditions']['gearMonthly']
        assert gm[5] == 'snow_caution'
        gm[5] = 'winter'
        m['conditions']['gearSource'] = '6月は残雪期のため、安全側で冬山装備（2026-10-09）'
    else:
        cal[5] = 'winter_gear'
        m['seasonCalendar'][5] = 's-hard'
        keys = set(e for e in cal if isinstance(e, str))
        m['calLegend'] = [G.LABEL[k] for k in G.KEYS if k in keys]
    m['mountainUpdated'] = V
    cards = [c for c in GD[m['id']]['6'] if c['c'] not in ('shoe', 'crampon', 'crampon_next')]
    GD[m['id']]['6'] = [dict(W_SHOE)] + [c for c in cards if c['c'] == 'rain'] + [dict(W_CRAMPON)] + [c for c in cards if c['c'] != 'rain']
    done.append(m['id'])
assert len(done) == len(NAMES), (len(done), len(NAMES))
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump(GD, open(GP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(' '.join(done))
