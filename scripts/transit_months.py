"""電車・バスで行ける山のうち、季節運行の乗り物が走っていない月を除くと、各月に何山残るかを数える（2026-11-11。運営者の指示）

季節運行の判定と運行期間は build_access_tier.py の seasons()（annualItems の transport・accesses.json の operation）を使う。
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
from build_access_tier import seasons  # noqa: E402


def runs(periods, mon, full=False):
    y = 2026
    s = datetime.date(y, mon, 1)
    e = datetime.date(y, mon, calendar.monthrange(y, mon)[1])
    for a, b, _, _ in periods:
        A = datetime.date.fromisoformat(a).replace(year=y)
        B = datetime.date.fromisoformat(b).replace(year=y)
        if full and not (A <= s and B >= e):
            return False
        if not full and (B < s or A > e):
            return False
    return True


def main():
    M = json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))
    A = json.load(open(os.path.join(ROOT, 'data', 'accesses.json'), encoding='utf-8'))
    train = [m for m in M if m.get('trainAccess')]
    dated, undated = [], []
    for m in train:
        ps = seasons(m, A)
        if not ps:
            continue
        if all(p[0] and p[1] for p in ps):
            dated.append((m, ps))
        else:
            undated.append((m, [p for p in ps if not (p[0] and p[1])]))
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
