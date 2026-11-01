#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事一覧（/articles/）の記事を、直近1週間によく読まれている順に並べるための並び順を作る（2026-11-01。運営者の指示）。

- GA4 の「表示回数」（screenPageViews）を、記事ごとに直近7日間（GA4 は1〜2日遅れるので、7日前〜昨日）で数え、多い順に並べる
- 新しい記事は、記事一覧に初めて載った日から14日間は、表示回数に関係なく上に出す（新しい順）
- 書くのは並び順と、記事が初めて載った日だけ。**表示回数は書かない**（リポジトリもサイトも誰でも読めるため）
- 対象は、記事一覧の上のカード（articles/index.html の class="acard"）。将来まとめ記事も入れるときは TARGETS を足す
- AIは使わない。.github/workflows/article-rank.yml が毎朝実行し、data/article_rank.json をコミットする

  python3 scripts/article_rank.py            # GA4 を読んで data/article_rank.json を書く（鍵は admin_dashboard.py と同じ）
  python3 scripts/article_rank.py --dry-run  # 書かずに並び順を出す
"""
import argparse
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
OUT = os.path.join(ROOT, 'data', 'article_rank.json')
# 並べ替えるカードがあるページ。(ページのファイル, カードを見分ける正規表現)
TARGETS = [('articles/index.html', r'<a href="(/articles/[a-z0-9-]+/)" class="acard">')]
NEW_DAYS = 14


def jst_today():
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date()


def listed_paths():
    out = []
    for f, pat in TARGETS:
        s = open(os.path.join(ROOT, f), encoding='utf-8').read()
        for p in re.findall(pat, s):
            if p not in out:
                out.append(p)
    return out


def views(paths):
    import admin_dashboard as ad
    s = ad.session(['https://www.googleapis.com/auth/analytics.readonly'])
    flt = {'orGroup': {'expressions': [{'filter': {'fieldName': 'pagePath', 'stringFilter': {'matchType': 'BEGINS_WITH', 'value': p}}} for p in paths]}}
    rows, err = ad.ga(s, {'dateRanges': [{'startDate': '7daysAgo', 'endDate': 'yesterday'}],
                          'dimensions': [{'name': 'pagePath'}], 'metrics': [{'name': 'screenPageViews'}],
                          'dimensionFilter': flt, 'limit': 10000})
    if err:
        raise SystemExit('GA4 の読み取りに失敗：' + err)
    count = dict((p, 0) for p in paths)
    for path, v in rows or []:
        base = re.sub(r'[?#].*$', '', path)
        if not base.endswith('/'):
            base += '/'
        if base in count:
            count[base] += int(v)
    return count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    today = jst_today()
    old = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
    added = old.get('added', {})
    paths = listed_paths()
    for p in paths:
        if p not in added:
            added[p] = str(today)          # 記事一覧に初めて載った日
    added = dict((p, added[p]) for p in paths)   # 一覧から消えた記事は外す
    count = views(paths)
    pos = dict((p, i) for i, p in enumerate(paths))   # 同じ表示回数なら、いまのページの順
    new = [p for p in paths if (today - datetime.date.fromisoformat(added[p])).days < NEW_DAYS]
    new.sort(key=lambda p: (added[p], -pos[p]), reverse=True)
    rest = [p for p in paths if p not in new]
    rest.sort(key=lambda p: (-count[p], pos[p]))
    out = {'note': '記事一覧の並び順（直近7日間の表示回数の多い順。記事一覧に載ってから14日間の新しい記事は上）。scripts/article_rank.py が毎朝作る。表示回数は書かない',
           'updated': str(today), 'order': new + rest, 'new': new, 'added': added}
    if args.dry_run:
        for i, p in enumerate(out['order'], 1):
            print(i, p, '（新着）' if p in new else '', count[p])
        return
    if old.get('order') == out['order'] and old.get('added') == out['added'] and old.get('new') == out['new']:
        print('並び順は変わりません')
        return
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('書きました：' + ' / '.join(out['order']))


if __name__ == '__main__':
    main()
