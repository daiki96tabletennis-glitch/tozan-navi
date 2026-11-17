"""電車・バスで行ける山のうち、季節運行の乗り物が走っていない月を除くと、各月に何山残るかを数える（2026-11-11。運営者の指示）

季節運行の判定と運行期間は build_access_tier.py の season_groups()（annualItems の transport・accesses.json の operation。季節ダイヤ transitSeasons の山は夏・冬のどれかが走れば行ける）を使う。
期間はいま入っている年の期間を、毎年同じとみなす（1〜3月は次の年も同じ期間で走るとみなす）。
季節運行の乗り物を2つ使う山は、両方が走る月だけ数える。
期間が入っていない季節運行（要確認）は別に一覧にする（数には「走る」として入れる）。

  python3 scripts/transit_months.py          # 月ごとの山の数と、季節運行の山の一覧
  python3 scripts/transit_months.py --check  # 期間が入っていない季節運行があれば終了コード1（要確認の印のものは除く）
"""
import calendar
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from build_access_tier import season_groups, _md_in  # noqa: E402


def runs(groups, mon, full=False):
    """季節運行のまとまり（season_groups）がすべて走る日がその月にあるか（full なら月の全日）"""
    y = 2026
    days = [datetime.date(y, mon, d).strftime('%m-%d') for d in range(1, calendar.monthrange(y, mon)[1] + 1)]

    def ok(md):
        for per, _label, _nv in groups:
            if not any(a and b and _md_in(a, b, md) for a, b in per):
                return False
        return True
    hits = [ok(md) for md in days]
    return all(hits) if full else any(hits)


def main():
    M = json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))
    A = json.load(open(os.path.join(ROOT, 'data', 'accesses.json'), encoding='utf-8'))
    train = [m for m in M if m.get('trainAccess')]
    dated, undated = [], []
    for m in train:
        gs = season_groups(m, A)
        if not gs:
            continue
        if all(f and t for per, _l, _n in gs for f, t in per):
            dated.append((m, gs))
        else:
            undated.append((m, [(None, None, label, nv) for per, label, nv in gs if not all(f and t for f, t in per)]))
    if '--check' in sys.argv:
        bad = [(m, ps) for m, ps in undated if not all(p[3] for p in ps)]
        for m, ps in bad:
            print('期間が入っていない季節運行：%s %s' % (m['name'], ' / '.join(p[2] for p in ps)))
        sys.exit(1 if bad else 0)
    print('電車で行ける山 %d（季節運行の期間あり %d・期間なし %d）' % (len(train), len(dated), len(undated)))
    print('月  1日でも走る月は出す  月の全日走る月だけ出す')
    for mon in range(1, 13):
        a = len(train) - sum(1 for m, ps in dated if not runs(ps, mon))
        b = len(train) - sum(1 for m, ps in dated if not runs(ps, mon, True))
        print('%2d月  %3d  %3d' % (mon, a, b))
    for m, ps in undated:
        print('期間なし：%s %s%s' % (m['name'], ' / '.join(p[2] for p in ps), '（要確認）' if all(p[3] for p in ps) else ''))


if __name__ == '__main__':
    main()
