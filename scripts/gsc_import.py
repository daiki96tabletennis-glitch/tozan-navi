#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Search Console の「検索パフォーマンス」の書き出し（zip）を読み、山ごとの検索のされ方を data/seo_intents.json にまとめる。
使い方：python3 scripts/gsc_import.py <書き出した zip のパス>
        そのあと python3 scripts/build_meta.py --write → gen_mountain_pages.py --all

まとめる内容（山ごと）：
  - ページの表示回数・クリック数・クリック率・掲載順位と、その順位ならふつう得られるクリック率との差（取りこぼし）
  - その山の名前を含む検索語を、知りたいこと別に分けた割合（表示回数で重みづけ）
      難易度（難易度・レベル）／初心者／日帰り／時間（コースタイム・所要時間）／アクセス（行き方・駐車場・登山口）／標高差／名前だけ
build_meta.py は、いちばん多い「知りたいこと」に答える形で、その山の見出しと説明文を作る。
検索語の書き出しは上位1,000件までなので、表示の少ない山は検索語が無いことがある（その山は全体でいちばん多い型を使う）。
"""
import csv, io, json, os, re, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTENTS = [('難易度', r'難易度|レベル|難し|きつ|危険|上級|中級'), ('初心者', r'初心者|初級|子供|子連れ|はじめて|初めて'), ('日帰り', r'日帰り'),
           ('時間', r'コースタイム|時間|所要'), ('アクセス', r'アクセス|行き方|電車|バス|駐車場|登山口|ロープウェイ|ケーブル'), ('標高差', r'標高差|標高|高さ'),
           ('コース', r'ルート|コース|登山道')]
CURVE = [(1, 28), (2, 15), (3, 10), (4, 7), (5, 5), (6, 4), (7, 3), (8, 2.5), (9, 2), (10, 1.7), (15, 1), (20, 0.6), (50, 0.2)]


def expected_ctr(pos):
    """掲載順位ごとの、おおよそのクリック率（一般的な目安。山ごとの優先順位を付けるためだけに使う）"""
    for (p1, c1), (p2, c2) in zip(CURVE, CURVE[1:]):
        if pos <= p2:
            return c1 + (c2 - c1) * (max(pos, p1) - p1) / (p2 - p1)
    return 0.1


def num(x):
    return float(str(x).replace('%', '').replace(',', '') or 0)


def main():
    z = zipfile.ZipFile(sys.argv[1])
    tables = {}
    for info in z.infolist():
        rows = list(csv.reader(io.StringIO(z.read(info).decode('utf-8-sig'))))
        if rows and rows[0]:
            tables[rows[0][0]] = rows[1:]
    pages, queries = tables.get('上位のページ') or [], tables.get('上位のクエリ') or []
    assert pages and queries, 'ページ・クエリの表が見つからない'
    ms = json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))
    out = {}
    for r in pages:
        m = re.match(r'https://tozan-navi\.com/mountains/([a-z0-9_]+)/$', r[0])
        if m:
            c, i, ctr, pos = num(r[1]), num(r[2]), num(r[3]), num(r[4])
            e = expected_ctr(pos)
            out[m.group(1)] = {'clicks': int(c), 'impressions': int(i), 'ctr': ctr, 'position': pos, 'expectedCtr': round(e, 1), 'lost': int(round(i * (e - ctr) / 100)), 'intents': {}, 'queries': []}
    names = sorted(((re.sub(r'[（(].*?[）)]', '', m['name']), m['id']) for m in ms), key=lambda x: -len(x[0]))
    total = {}
    for r in queries:
        q, i = r[0], num(r[2])
        hit = next((mid for n, mid in names if n in q), None)
        if not hit:
            continue
        kind = next((k for k, rx in INTENTS if re.search(rx, q)), '名前だけ')
        d = out.setdefault(hit, {'clicks': 0, 'impressions': 0, 'ctr': 0, 'position': 0, 'expectedCtr': 0, 'lost': 0, 'intents': {}, 'queries': []})
        d['intents'][kind] = d['intents'].get(kind, 0) + int(i)
        d['queries'].append([q, int(num(r[1])), int(i), num(r[3]), num(r[4])])
        total[kind] = total.get(kind, 0) + int(i)
    for d in out.values():
        d['queries'] = sorted(d['queries'], key=lambda x: -x[2])[:8]
        named = {k: v for k, v in d['intents'].items() if k != '名前だけ'}
        d['top'] = max(named, key=named.get) if named else None
    period = next((r[1] for r in (tables.get('フィルタ') or []) if r and r[0] == '日付'), '')
    json.dump({'note': 'Search Console の書き出しから scripts/gsc_import.py が作る。build_meta.py が見出し・説明文の型を選ぶのに使う',
               'period': period, 'importedFrom': os.path.basename(sys.argv[1]), 'overall': total, 'mountains': out},
              open(os.path.join(ROOT, 'data', 'seo_intents.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
    print('山ページ %d／知りたいこと別の表示回数（全体）：%s' % (len(out), sorted(total.items(), key=lambda x: -x[1])))
    import collections
    print('山ごとのいちばん多い型：', collections.Counter(d['top'] for d in out.values()))


if __name__ == '__main__':
    main()
