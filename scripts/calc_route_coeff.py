#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data/mountains.json の各ルート(routes[])に、コース定数 coeff を追加・更新する。

計算式（山と溪谷社「コース定数」の一般式）:
  定数 = 1.8×行動時間(h) + 0.3×水平距離(km) + 10.0×登り累積標高差(km) + 0.6×下り累積標高差(km)
下りの累積標高差は元データに無いため、登りと同じと仮定する（往復・周回ルート前提の近似）。
time / distance / elevation のいずれかが読み取れないルートは coeff を付けない（既存値は削除）。

山全体の coeffMin / coeffMax はこのスクリプトでは変更しない（フィルター・診断用の既存値のまま）。

使い方: python3 scripts/calc_route_coeff.py [--dry-run]
"""
import json, re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'data', 'mountains.json')


def minutes(s):
    m = re.fullmatch(r'\s*(?:(\d+)時間)?(?:(\d+)分)?\s*', s or '')
    if not m or not (m.group(1) or m.group(2)):
        return None
    return int(m.group(1) or 0) * 60 + int(m.group(2) or 0)


def km(s):
    m = re.search(r'([\d.]+)\s*km', s or '')
    return float(m.group(1)) if m else None


def climb_m(s):
    m = re.search(r'\+?\s*([\d,]+)\s*m', s or '')
    return int(m.group(1).replace(',', '')) if m else None


def route_coeff(r):
    t, d, u = minutes(r.get('time')), km(r.get('distance')), climb_m(r.get('elevation'))
    if None in (t, d, u):
        return None
    return round(1.8 * t / 60 + 0.3 * d + 10.0 * u / 1000 + 0.6 * u / 1000)


if __name__ == '__main__':
    data = json.load(open(PATH, encoding='utf-8'))
    set_n = skip_n = 0
    for m in data:
        for r in m.get('routes') or []:
            c = route_coeff(r)
            if c is None:
                r.pop('coeff', None)
                skip_n += 1
            else:
                r['coeff'] = c
                set_n += 1
    print(f'coeff付与 {set_n} ルート / 算出不可 {skip_n} ルート')
    if '--dry-run' not in sys.argv:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
