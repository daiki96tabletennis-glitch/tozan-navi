#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""出発地別の全件一覧ページ（search/shinjuku・omiya・yokohama・ofuna）を data/mountains.json に合わせる。

そろえる項目：車の所要時間／難易度／「日帰り可」の表示／地域／標高／並び順（所要時間の短い順）／掲載件数の表記
カード形式のページ（日帰り一覧など）は、カードの「◯◯から 車 △時間」だけをそろえる（並び順・掲載する山は編集内容なので変えない）。
掲載する山は変えない（追加・削除は手作業）。コース定数の数字とバーは sync_search_pages.py が担当する。

使い方
  python3 scripts/sync_search_hubs.py            # 食い違いを表示するだけ
  python3 scripts/sync_search_hubs.py --write    # ページを書き換える
check_pages.py のセクション17が、ここの hub_problems() を使って食い違いを検出する。
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ページ → 車の所要時間（分）のフィールド
HUBS = {'shinjuku': 'driveTimeShinjuku', 'omiya': 'driveTimeOmiya', 'yokohama': 'driveTimeYokohama', 'ofuna': 'driveOfuna'}
BADGE = 'font-size:11px;font-weight:bold;padding:2px 8px;border-radius:10px'
DIFF_STYLE = {
    '初級': 'background:#e8f8e8;color:#3a6a3a;' + BADGE,
    '初〜中級': 'background:#e8f0e8;color:#3a6a3a;' + BADGE,
    '中級': 'background:#f8f0e0;color:#7a6020;' + BADGE,
    '中〜上級': 'background:#fde8d8;color:#8a5010;' + BADGE,
    '上級': 'background:#fde8e8;color:#8a2020;' + BADGE,
}
DAY_SPAN = '<span style="background:#e8f0e8;color:#3a6a3a;font-size:10px;padding:1px 6px;border-radius:8px;font-weight:bold">日帰り可</span>'
BLOCK_RE = re.compile(r'<a href="/mountains/([a-z0-9_]+)/" style=.*?</a>\n', re.S)
META_RE = re.compile(r'(<div style="font-size:12px;color:#a09888;margin-top:2px">📍 )(.*?)( &nbsp; <span style=")([^"]*)(">)([^<]*)(</span>)((?: &nbsp; )?(?:<span style="[^"]*">日帰り可</span>)?)(</div>)')
TIME_RE = re.compile(r'(<div style="font-size:20px;font-weight:bold;color:#4a5e4a">)([^<]*)(</div>)')
ELEV_RE = re.compile(r'(<div style="font-size:12px;color:#a09888">)(\d+)m(</div>)')
COUNT_RES = (re.compile(r'(\d+)(件の山が見つかりました)'), re.compile(r'(\d+)(選。)'))


def fmt_min(v):
    h, mi = divmod(v, 60)
    if not h:
        return '%d分' % mi
    return '%d時間%d分' % (h, mi) if mi else '%d時間' % h


def path(slug):
    return os.path.join(ROOT, 'search', slug, 'index.html')


def expected_block(block, m, field):
    """カード1枚を、データに合わせた内容にして返す"""
    def meta(mm):
        return (mm.group(1) + m['area'] + mm.group(3) + DIFF_STYLE[m['difficulty']] + mm.group(5) + m['difficulty'] + mm.group(7)
                + ' &nbsp; ' + (DAY_SPAN if m.get('daytrip') else '') + mm.group(9))
    new, c1 = META_RE.subn(meta, block)
    new, c2 = TIME_RE.subn(lambda mm: mm.group(1) + fmt_min(m[field]) + mm.group(3), new)
    new, c3 = ELEV_RE.subn(lambda mm: mm.group(1) + str(m['elevation']) + 'm' + mm.group(3), new)
    if (c1, c2, c3) != (1, 1, 1):
        raise ValueError('%s: カードの形が想定と違う %s' % (m['id'], (c1, c2, c3)))
    return new


def rebuild(slug, mountains):
    """(今のHTML, あるべきHTML, 食い違いの一覧) を返す"""
    field = HUBS[slug]
    by_id = {m['id']: m for m in mountains}
    html = open(path(slug), encoding='utf-8').read()
    blocks = list(BLOCK_RE.finditer(html))
    probs = []
    if not blocks:
        return html, html, ['カードが見つからない']
    for a, b in zip(blocks, blocks[1:]):
        if html[a.end():b.start()].strip():
            raise ValueError(slug + ': カードのあいだに別の要素がある')
    items = []
    for i, b in enumerate(blocks):
        mid = b.group(1)
        m = by_id.get(mid)
        if m is None:
            probs.append('%s: mountains.json に無い山が載っている' % mid)
            items.append((0, i, b.group(0)))
            continue
        new = expected_block(b.group(0), m, field)
        if new != b.group(0):
            old_t = TIME_RE.search(b.group(0)).group(2)
            what = '所要時間 %s→%s' % (old_t, fmt_min(m[field])) if old_t != fmt_min(m[field]) else '難易度・日帰り・地域・標高の表示'
            probs.append('%s: %s' % (mid, what))
        items.append((m[field], i, new))
    ordered = sorted(items)
    if [x[1] for x in ordered] != list(range(len(items))):
        probs.append('並び順が所要時間の短い順になっていない')
    body = '\n'.join(x[2] for x in ordered)
    new_html = html[:blocks[0].start()] + body + html[blocks[-1].end():]
    n = len(items)
    for cre in COUNT_RES:
        found = cre.findall(new_html)
        if any(int(x[0]) != n for x in found):
            probs.append('掲載件数の表記が実際（%d山）と違う' % n)
        new_html = cre.sub(lambda mm: str(n) + mm.group(2), new_html)
    return html, new_html, probs


# カード形式のページ（日帰り一覧など）にある「◯◯から 車 △時間」の表示
CARD_RE = re.compile(r'<div class="mountain-card">.*?class="mc-link"', re.S)
CARD_TIME_RE = re.compile(r'(<span class="mc-label">)([^<]*から)(</span><span class="mc-val">車 )([^<]*)(</span>)')
CARD_KEY = {'新宿から': 'driveTimeShinjuku', '大宮から': 'driveTimeOmiya', '横浜から': 'driveTimeYokohama',
            '大船・横浜から': 'driveOfuna', '大船から': 'driveOfuna', '立川から': 'driveTimeTachikawa'}


def card_pages():
    base = os.path.join(ROOT, 'search')
    return sorted(d for d in os.listdir(base) if d not in HUBS and os.path.isfile(os.path.join(base, d, 'index.html')))


def rebuild_cards(slug, mountains):
    """カード形式のページ：車の所要時間をデータに合わせる。(今のHTML, あるべきHTML, 食い違い)"""
    by_id = {m['id']: m for m in mountains}
    html = open(path(slug), encoding='utf-8').read()
    probs = []

    def card(cm):
        g = cm.group(0)
        idm = re.search(r'/mountains/([a-z0-9_]+)/', g)
        m = by_id.get(idm.group(1)) if idm else None
        if m is None:
            return g

        def tm(mm):
            f = CARD_KEY.get(mm.group(2))
            if f is None or not isinstance(m.get(f), int):
                return mm.group(0)
            new = fmt_min(m[f])
            if new != mm.group(4):
                probs.append('%s: 車の所要時間 %s→%s' % (m['id'], mm.group(4), new))
            return mm.group(1) + mm.group(2) + mm.group(3) + new + mm.group(5)
        return CARD_TIME_RE.sub(tm, g)
    return html, CARD_RE.sub(card, html), probs


def hub_problems(mountains):
    """check_pages.py 用：[{'id': ページ, 'problem': 内容}]"""
    out = []
    for slug in HUBS:
        try:
            _, _, probs = rebuild(slug, mountains)
        except ValueError as e:
            probs = [str(e)]
        out += [{'id': 'search/' + slug, 'problem': p} for p in probs]
    for slug in card_pages():
        _, _, probs = rebuild_cards(slug, mountains)
        out += [{'id': 'search/' + slug, 'problem': p} for p in probs]
    return out


if __name__ == '__main__':
    M = json.load(open(os.path.join(ROOT, 'data', 'mountains.json'), encoding='utf-8'))
    write = '--write' in sys.argv
    for slug in HUBS:
        old, new, probs = rebuild(slug, M)
        print('%s: 食い違い %d件' % (slug, len(probs)))
        for p in probs[:200]:
            print('  -', p)
        if write and new != old:
            assert new.rstrip().endswith('</html>')
            assert len(re.findall(r'<div\b', new)) - len(re.findall(r'</div>', new)) == len(re.findall(r'<div\b', old)) - len(re.findall(r'</div>', old))
            assert len(BLOCK_RE.findall(new)) == len(BLOCK_RE.findall(old))
            open(path(slug), 'w', encoding='utf-8').write(new)
            print('  → 書き換えました')
    for slug in card_pages():
        old, new, probs = rebuild_cards(slug, M)
        if probs:
            print('%s: 車の所要時間の食い違い %d件' % (slug, len(probs)))
        if write and new != old:
            assert new.rstrip().endswith('</html>') and len(new.split('<div')) == len(old.split('<div'))
            open(path(slug), 'w', encoding='utf-8').write(new)
            print('  → 書き換えました')
