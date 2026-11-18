#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-11-18 に足した3山（妙法ヶ岳・浜石岳・沼津アルプス）の装備カード（data/gear-data.json）を作る。

作り方は add_gear_new_mountains_2026_11.py の build() と同じ（アイゼン・冬靴は gearCalendar から、
防寒・保温ボトル・ポールを出す月は近くの似た山 REF と同じ）。熊鈴は出典が無いので付けない。
前の13山は作り直さない（ヘルメット・ピッケルなど、あとから足したカードを消さないため）。

  python3 scripts/migrations/add_gear_myoho_hamaishi_numazu_2026_11.py --write
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import add_gear_new_mountains_2026_11 as G  # noqa: E402

NEW = {
    'myohogatake': ('bukosan', 'dist', False),     # 同じ秩父で装備カレンダーが同じ武甲山
    'hamaishidake': ('ohnoyama', 'dist', False),   # 通年アイゼン不要の低山
    'numazu_alps': ('ohnoyama', 'dist', False),
    'minano_alps': ('hafuzan_chichibu', 'dist', False),  # 同じ尾根の破風山（2026-11-18 に足した）
}


def main():
    write = '--write' in sys.argv
    GD = json.load(open(G.GP, encoding='utf-8'))
    MS = {m['id']: m for m in json.load(open(G.MP, encoding='utf-8'))}
    G.NEW.clear()
    G.NEW.update(NEW)
    for mid in NEW:
        GD[mid] = G.build(mid, MS[mid], GD[NEW[mid][0]])
        print(mid, MS[mid]['name'])
        for mo in range(1, 13):
            print('  %2d' % mo, ' '.join('%s(%s)' % (c['c'], c['i']) for c in GD[mid][str(mo)]))
        print('  例:', GD[mid]['7'][0]['r'])
    if write:
        with open(G.GP, 'w', encoding='utf-8') as f:
            json.dump(GD, f, ensure_ascii=False, indent=2)
        print('書き込みました')


if __name__ == '__main__':
    main()
