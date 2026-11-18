#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「日帰り可」（daytrip）の決まりを見直す（2026-11-18。運営者の指示）

運営者の指示「電車・車では分けないけど、電車と車両方で移動時間の往復と登山時間（代表コースの一番短いコースで）の合計が14時間以内の山を日帰り可能とする」。
決まり：
- 登山時間＝泊を含まないコース（コース名に「泊」「◯日」が無い）のうち、いちばん短いコースの歩く時間（休憩を含まないコースタイム）
- 移動時間＝新宿からの片道を2倍（電車・バス＝trainTimeShinjuku、車＝driveTimeShinjuku）
- 電車・バスの往復＋登山時間、車の往復＋登山時間の両方が14時間（840分）以内なら日帰り可。電車・バスで行けない山は車だけで見る
- 泊を含まないコースが無い山は日帰り不可
前の決まり（泊を含まない9時間未満のコースがある）から、2026-11-18 の計算で26山が日帰り不可になった（日帰り可になる山は0）。

やること（何度流しても同じ結果）：
1. mountains.json の daytrip を決まりどおりにする（変えた山は mountainUpdated を今日に）
2. 手で作ったまとめ（search/*/）の山のカードの「日帰り可／宿泊推奨」のバッジを daytrip に合わせる
このあと sync_route_text.py <変えた山> → build_meta.py --write → gen_mountain_pages.py → sync_search_pages.py --all
→ sync_search_hubs.py --write → build_winter_find.py → gen_find_winter.py → check_pages.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
DAY = '2026-11-18'
LIMIT = 14 * 60


def mins(t):
    h = re.search(r'(\d+)時間', t or '')
    mi = re.search(r'(\d+)分', t or '')
    if not h and not mi:
        return None
    return (int(h.group(1)) if h else 0) * 60 + (int(mi.group(1)) if mi else 0)


def day_routes(m):
    return [r for r in m.get('routes') or [] if mins(r.get('time')) and not re.search(r'泊|\d日', r.get('name') or '')
            and (r.get('status') or {}).get('state') != 'closed']


def calc(m):
    """(日帰り可か, いちばん短いコースの分, 電車・バスの往復＋登山, 車の往復＋登山)"""
    rs = day_routes(m)
    if not rs:
        return False, None, None, None
    w = min(mins(r['time']) for r in rs)
    tt = m.get('trainTimeShinjuku') if m.get('trainAccess') else None
    dt = m.get('driveTimeShinjuku')
    tot_t = 2 * tt + w if isinstance(tt, (int, float)) else None
    tot_c = 2 * dt + w if isinstance(dt, (int, float)) else None
    tots = [x for x in (tot_t, tot_c) if x is not None]
    return (bool(tots) and max(tots) <= LIMIT), w, tot_t, tot_c


def main():
    raw = open(P, encoding='utf-8').read()
    D = json.loads(raw)
    changed = []
    for m in D:
        ok = calc(m)[0]
        if bool(m.get('daytrip')) != ok:
            m['daytrip'] = ok
            m['mountainUpdated'] = DAY
            changed.append(m['id'])
    s = json.dumps(D, ensure_ascii=False, indent=2) + ('\n' if raw.endswith('\n') else '')
    open(P, 'w', encoding='utf-8').write(s)
    M = {m['id']: m for m in D}

    # 手で作ったまとめのバッジ
    nb = 0
    for p in sorted(glob.glob(os.path.join(ROOT, 'search', '*', 'index.html'))):
        t = open(p, encoding='utf-8').read()
        if '<!-- generated:' in t or 'sb sb-day' not in t:
            continue

        def fix(mm):
            c = mm.group(0)
            mid = re.search(r'href="/mountains/([a-z0-9_]+)/"', c)
            if not mid or mid.group(1) not in M:
                return c
            badge = '日帰り可' if M[mid.group(1)].get('daytrip') else '宿泊推奨'
            return re.sub(r'<span class="sb sb-day">[^<]*</span>', '<span class="sb sb-day">%s</span>' % badge, c)
        t2 = re.sub(r'<div class="mountain-card">(?:(?!<div class="mountain-card">).)*?class="mc-link"[^>]*>', fix, t, flags=re.S)
        if t2 != t:
            nb += 1
            open(p, 'w', encoding='utf-8').write(t2)
            print('バッジ', os.path.relpath(p, ROOT))
    print('日帰りの区分を変えた山', len(changed), ' '.join(changed))
    print('バッジを直したまとめ', nb)


if __name__ == '__main__':
    main()
