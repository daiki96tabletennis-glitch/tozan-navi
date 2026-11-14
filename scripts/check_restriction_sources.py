#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""規制・閉鎖の出典ページを毎日見張る（2026-11-15〜。運営者の指示）

弘法山公園の閉鎖の解除（2026-11-03）に、毎月1日の見張り（check_annual_updates.py）では気づけなかった
（10/30 に登録した直後の 11/1 の回が初めての取得で、比べる前の内容が無かった）。規制・閉鎖は数日で変わるので、
その出典だけを毎日見る。**サイトのデータは書き換えない**（人が出典を読んで確かめてから直す）。

見張る出典（同じ URL は1つにまとめる）
- 規制中の山（status.level が restricted）の status.sourceUrl
- 注意のバナー（warnBanner）の url
- 新しい形の山の注意（alerts[].sourceUrl）
- 期間の無い閉鎖・通行止め（annualItems の kind が closure で validTo が無いもの）の sourceUrl

知らせること
- 前の日から、ページの中の「日付と規制・閉鎖に関わる行」が変わった（check_annual_updates.py の fetch_keylines と同じ取り出し方）
- 「解除」「再開」「解放」「開通」などの行に、今日の前後30日の日付がある（初めて読んだ日でも知らせる。弘法山のように、登録した直後に解除されることがあるため）
見つけたものは 14 日間、報告に出し続ける（マイページ・管理画面のお知らせで見落とさないため）。

  python3 scripts/check_restriction_sources.py --state restrict_state.json --out restrict_report.md [--new-out restrict_new.txt]
終了コード：知らせるものがあれば 1、無ければ 0。--new-out には、今日新しく見つけた件数を書く（Issue を作るかどうかに使う）
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from check_annual_updates import fetch_keylines  # noqa: E402

KEEP_DAYS = 14
LIFT_RE = re.compile(r'解除|再開|解放|開通|通行可能|通行できます|運行を再開|入山できます')
# 出典ではないリンク（地図・乗換案内）は見張らない（注意のバナーのリンクに混ざっている）
NOT_SOURCE = re.compile(r'google\.[a-z.]+/maps|maps\.google|transit\.yahoo|navitime\.co\.jp|jorudan')
NEAR_DAYS = 30   # 初日の「解除」の知らせは、今日の前後30日の日付がある行だけ（昔の解除の記載を知らせないため）


def dates_in(line, today):
    """行の中の日付（令和N年M月D日・YYYY年M月D日・M月D日・M/D）。年の無いものは今日に近い年にする"""
    out = []
    for m in re.finditer(r'(?:令和\s*(\d+)年|(20\d\d)年)?\s*(\d{1,2})月\s*(\d{1,2})日|(?<![\d/])(\d{1,2})/(\d{1,2})(?![\d/])', line):
        if m.group(3):
            y = 2018 + int(m.group(1)) if m.group(1) else (int(m.group(2)) if m.group(2) else None)
            mo, d = int(m.group(3)), int(m.group(4))
        else:
            y, mo, d = None, int(m.group(5)), int(m.group(6))
        cands = [y] if y else [today.year - 1, today.year, today.year + 1]
        for yy in cands:
            try:
                out.append(datetime.date(yy, mo, d))
            except ValueError:
                pass
    return out


def near(line, today):
    return any(abs((d - today).days) <= NEAR_DAYS for d in dates_in(line, today))


def collect():
    M = json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))
    by_url = {}

    def add(url, name, label):
        if url and url.startswith('http') and not NOT_SOURCE.search(url):
            by_url.setdefault(url, {'mountains': set(), 'labels': set()})
            by_url[url]['mountains'].add(name)
            if label:
                by_url[url]['labels'].add(label)

    for m in M:
        st = m.get('status') or {}
        if st.get('level') == 'restricted':
            add(st.get('sourceUrl'), m['name'], '規制中')
        wb = m.get('warnBanner') or {}
        add(wb.get('url'), m['name'], wb.get('title'))
        for al in m.get('alerts') or []:
            add(al.get('sourceUrl'), m['name'], al.get('title'))
        for it in m.get('annualItems') or []:
            if it.get('kind') == 'closure' and not it.get('validTo'):
                add(it.get('sourceUrl'), m['name'], it.get('label'))
    return by_url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--state', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--new-out')
    ap.add_argument('--today')
    a = ap.parse_args()
    today = datetime.date.fromisoformat(a.today) if a.today else (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date()
    state = json.load(open(a.state, encoding='utf-8')) if os.path.exists(a.state) else {}
    hashes = state.get('hash', {})
    found = state.get('found', {})      # url → {date, why, lines}
    targets = collect()
    new, failed, first = 0, [], 0
    for url, t in sorted(targets.items()):
        try:
            keys = fetch_keylines(url)
        except Exception as e:
            failed.append((url, t, str(e)[:80]))
            continue
        h = hashlib.sha256(keys.encode('utf-8')).hexdigest()
        lift_all = [l for l in keys.split('\n') if LIFT_RE.search(l)]
        lift = lift_all[:2]
        why = None
        if url in hashes and hashes[url] != h:
            why = '出典ページの規制・閉鎖に関わる行が変わった'
        elif url not in hashes:
            first += 1
            recent = [l for l in lift_all if near(l, today)][:2]
            if recent:
                why = '出典ページに、最近の日付の「解除」「再開」などの記載がある（見張りの初日）'
                lift = recent
        hashes[url] = h
        if why:
            found[url] = {'date': today.isoformat(), 'why': why, 'lines': lift}
            new += 1
    # 14日を過ぎたもの・見張りから外れたもの（データを直して規制が外れた）は消す
    for url in list(found):
        old = datetime.date.fromisoformat(found[url]['date'])
        if url not in targets or (today - old).days > KEEP_DAYS:
            del found[url]
    json.dump({'hash': hashes, 'found': found}, open(a.state, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    def names(t):
        return '・'.join(sorted(t['mountains']))
    out = ['# 規制・閉鎖の出典の見張り（%s）' % today.isoformat(), '',
           '見張っている出典：%d件／知らせるもの：%d件（今日見つけた：%d件）／取得できず：%d件' % (len(targets), len(found), new, len(failed)), '',
           '## 出典ページが変わった・解除の記載がある（出典を読んで、解除・変更ならサイトを直す）', '']
    rows = []
    for url, f in sorted(found.items(), key=lambda kv: kv[1]['date'], reverse=True):
        t = targets[url]
        rows.append('- %s：%s（%s 見つけた）— %s%s' % (names(t), '／'.join(sorted(t['labels'])) or '注意', f['date'], url,
                                                    ('　記載：' + ' ／ '.join(f['lines'])) if f['lines'] else ''))
    out += rows or ['- なし']
    out += ['', '## 出典ページを取得できなかった（URLの変更・リンク切れの可能性）', '']
    out += ['- %s：%s（%s）' % (names(t), url, err) for url, t, err in failed] or ['- なし']
    out += ['']
    if first:
        out += ['※ 今回が初回の取得だった出典：%d件（次回から変更を検知します）' % first, '']
    open(a.out, 'w', encoding='utf-8').write('\n'.join(out))
    if a.new_out:
        open(a.new_out, 'w').write(str(new))
    print('\n'.join(out))
    sys.exit(1 if (found or failed) else 0)


if __name__ == '__main__':
    main()
