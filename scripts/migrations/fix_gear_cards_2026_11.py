#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""装備カード（data/gear-data.json）の食い違いを直す（2026-11-02。運営者の指示「直して」）。

1. 登山靴・ポールの文の数字（距離・標高差）を、いまの代表コースの値にする
   （2026-10-24〜25 にコースを YAMAP の値に替えたとき、装備の文は前のコースの数字のままだった）
   ・距離は0.1km、標高差は50m単位。累積の文（「累積標高差+◯mと大きめ」）は900m以上の山だけ、それ未満は「標高差◯m。」の文にする
2. アイゼンのカードを gearCalendar に合わせる（大天井岳の6月：表は冬山装備、カードは軽アイゼン）
3. 来月分のアイゼン（crampon_next）を gearCalendar に合わせる
   ・来月の区分が厳しくなる月は、その区分の「来月分」を出す
   ・冬山装備→軽アイゼン等に下がる月の「軽アイゼン（来月分）」は前からの出し方なので残す
   ・それ以外（来月も同じ区分・入山不可・アイゼン不要になる月）の「来月分」は外す
入山不可の月はページでカードを出さないので触らない。
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GP = os.path.join(ROOT, 'data', 'gear-data.json')
MP = os.path.join(ROOT, 'data', 'mountains.json')
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'migrations'))
import add_gear_new_mountains_2026_11 as A

RANK = {'no_crampons': 0, 'light_crampons': 1, 'winter_gear': 2}


def b(x):
    return x if isinstance(x, str) else x['before']


def rep_route(m):
    rs = m.get('routes') or []
    rid = m.get('representativeRouteId')
    for r in rs:
        if r.get('id') == rid:
            return r
    return rs[0] if rs else {}


def num(s):
    x = re.search(r'[\d.]+', str(s or '').replace(',', ''))
    return float(x.group(0)) if x else None


def fix_text(c, km, gain):
    r = c['r']
    if c['c'] == 'shoe':
        if km is not None:
            r = re.sub(r'距離[\d.]+km', '距離%.1fkm' % km, r)
        if gain:
            r = re.sub(r'標高差\d+m', '標高差%dm' % gain, r)
    elif c['c'] == 'pole' and gain:
        tail = 'ポールがあるとひざへの負担がかなり変わります。'
        assert r.endswith(tail), r
        r = ('累積標高差+%dmと大きめ。' % gain if gain >= 900 else '標高差%dm。' % gain) + tail
    return r


def main():
    write = '--write' in sys.argv
    GD = json.load(open(GP, encoding='utf-8'))
    MS = {m['id']: m for m in json.load(open(MP, encoding='utf-8'))}
    changed = {}
    for mid, mm in GD.items():
        m = MS[mid]
        r = rep_route(m)
        km = num(r.get('distance'))
        g = num(r.get('elevation'))
        gain = int(round(g / 50.0) * 50) if g else None
        cal = m['gearCalendar']
        axe = any(c['c'] == 'axe' for cs in mm.values() for c in cs)
        for mo in range(1, 13):
            key = str(mo)
            cards = mm[key]
            before = json.dumps(cards, ensure_ascii=False)
            cur = b(cal[mo - 1])
            nxt = cal[mo - 1]['after'] if not isinstance(cal[mo - 1], str) else b(cal[mo % 12])
            for c in cards:
                c['r'] = fix_text(c, km, gain)
            if cur != 'closed':
                # 今月のアイゼン
                has = [c for c in cards if c['c'] == 'crampon']
                kind = None if not has else ('winter_gear' if 'G12' in has[0]['p'] else 'light_crampons')
                want = None if cur == 'no_crampons' else cur
                if kind != want:
                    assert mid == 'otenshoudake' and mo == 6, (mid, mo, kind, want)
                    rest = [c for c in cards if c['c'] not in ('shoe', 'crampon', 'crampon_next', 'axe')]
                    cards[:] = [dict(A.W_SHOE2 if axe else A.W_SHOE), [c for c in rest if c['c'] == 'rain'][0], dict(A.WINTER)] \
                        + ([dict(A.AXE)] if axe else []) + [c for c in rest if c['c'] not in ('rain', 'pole')]
                # 来月分
                nx = [c for c in cards if c['c'] == 'crampon_next']
                got = None if not nx else ('winter_gear' if 'G12' in nx[0]['p'] else 'light_crampons')
                if nxt in RANK and RANK[nxt] > RANK[cur]:
                    want_n = nxt
                elif cur == 'winter_gear' and nxt == 'light_crampons' and got == 'light_crampons':
                    want_n = got
                else:
                    want_n = None
                if got != want_n:
                    cards[:] = [c for c in cards if c['c'] != 'crampon_next']
                    if want_n:
                        idx = max(i for i, c in enumerate(cards) if c['c'] in ('shoe', 'rain', 'crampon')) + 1
                        cards.insert(idx, dict(A.WINTER_NEXT if want_n == 'winter_gear' else A.LIGHT_NEXT))
            if json.dumps(cards, ensure_ascii=False) != before:
                changed.setdefault(mid, []).append(mo)
    for mid, mos in changed.items():
        print(mid, MS[mid]['name'], mos)
    print('変わった山', len(changed))
    if write:
        with open(GP, 'w', encoding='utf-8') as f:
            json.dump(GD, f, ensure_ascii=False, indent=2)
        json.dump(sorted(changed), open(os.path.join(ROOT, '.claude', 'gear_fix_ids.json'), 'w'))
        print('書き込みました')


if __name__ == '__main__':
    main()
