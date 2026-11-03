#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""古いリンクの項目（busScheduleLinks・busLinks）を、電車・バス欄のリンク（trainRoutes.links）と同じにする（2026-11-03）。

山ページの mountain-engine.js が、ページを開いたあとにこの古い項目でリンクを上書きしていて、
33山で時刻表・乗換案内のリンクが古い・消えたページに変わっていた（筑波山は両方とも関東鉄道の404のページ）。
上書きの処理はやめたので表示には効かないが、管理画面が表示に使うので値をそろえておく。
新しい形の山は build_derived.py が同じ形で作る。
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')


def main():
    s = open(P, encoding='utf-8').read()
    D = json.loads(s)
    n = 0
    for m in D:
        if m.get('dataModel') == 'ssot-v1':
            continue
        lk = (m.get('trainRoutes') or {}).get('links') or []
        if not lk and not (m.get('busLinks') or m.get('busScheduleLinks')):
            continue
        bl = [l['url'] for l in lk if l.get('type') == 'yahoo'] or None
        bs = [l['url'] for l in lk if l.get('type') == 'bus'] or None
        if m.get('busLinks') != bl or m.get('busScheduleLinks') != bs:
            m['busLinks'], m['busScheduleLinks'] = bl, bs
            n += 1
    open(P, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=2) + ('\n' if s.endswith('\n') else ''))
    print('そろえた山', n)


if __name__ == '__main__':
    main()
