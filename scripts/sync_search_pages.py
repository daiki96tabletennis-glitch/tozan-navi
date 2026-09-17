#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAMATCH 検索ページ スタッツ同期スクリプト（Phase4/Task3）

search/配下の各ページに掲載されている山カードのスタッツ（地域・標高・カテゴリ・
難易度・コース定数）と、本文中（FAQPage JSON-LD等）の「山名（コース定数X〜Y…）」
言及を、data/mountains.json を正本として同期する。

掲載する山・並び順・intro文・FAQ・カード内の紹介文といった編集的な内容は対象外
（このスクリプトは変更しない）。mountains.jsonの該当山データを更新した後に実行する。

ページ構造は2種類を自動判定する:
  - curated: <div class="mountain-card" ...>の山カード形式（大半のページ）
  - hub:     全件一覧型（ofuna/omiya/yokohama/shinjuku、<a href="/mountains/ID/" ...onmouseover>形式）

使い方:
  python3 scripts/sync_search_pages.py <slug> [<slug> ...]
  python3 scripts/sync_search_pages.py --all         # search/配下全ページが対象
"""
import argparse
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)


# --- div境界抽出（ネスト対応） ---------------------------------------------

def extract_balanced_div(html, start_idx):
    m = re.match(r'<div[^>]*>', html[start_idx:])
    if not m:
        return None
    depth = 1
    pos = start_idx + m.end()
    tag_re = re.compile(r'<div[^>]*>|</div>')
    for tm in tag_re.finditer(html, pos):
        depth += -1 if tm.group().startswith('</div') else 1
        if depth == 0:
            return html[start_idx:tm.end()]
    return None


def find_all_mountain_cards(html):
    cards = []
    for m in re.finditer(r'<div class="mountain-card"[^>]*>', html):
        block = extract_balanced_div(html, m.start())
        if block:
            cards.append((m.start(), m.start() + len(block), block))
    return cards


# --- curated型（山カード形式）の同期 ----------------------------------------

MC_AREA_RE = re.compile(r'(<div class="mc-area">)([^<]*?)\s*\u30fb\s*([\d,]+)m(</div>)')
MC_CAT_RE = re.compile(r'(<span class="sb sb-cat">)([^<]*)(</span>)')
MC_DIFF_RE = re.compile(r'(<span class="mc-label">難易度</span><span class="mc-val">)([^<]*)(</span>)')
MC_CCR_RE = re.compile(r'(<span class="mc-label">コース定数</span><span class="mc-val">)([^<]*)(</span>)')
CARD_ID_RE = re.compile(r'href="/mountains/([a-z0-9_]+)/"')


def fmt_elev(v):
    return '{:,}'.format(v)


def fix_ccr_mentions_in_text(html, by_id, mountain_ids):
    """本文中（FAQPage JSON-LD等）の「山名（コース定数X〜Y…）」言及を補正する。
    括弧内にコース定数以外の付随テキスト（例:「・高尾駅からバス」）が同居している
    ケースがあるため、括弧全体ではなく数値/範囲部分だけを置換し残りは保持する。"""
    changes = []
    for mid in mountain_ids:
        mt = by_id.get(mid)
        if not mt or not mt.get('name') or not mt.get('courseCoefficientRange'):
            continue
        name = re.escape(mt['name'])
        correct = mt['courseCoefficientRange']
        pattern = re.compile(name + r'（コース定数(\d+(?:\u301c\d+)?)')

        def repl(m, correct=correct, mid=mid, name_text=mt['name']):
            if m.group(1) != correct:
                changes.append((mid, f'本文言及のコース定数: "{m.group(1)}" -> "{correct}"'))
            return name_text + '（コース定数' + correct
        html = pattern.sub(repl, html)
    return html, changes


def sync_curated(path, by_id):
    html = open(path, encoding='utf-8').read()
    cards = find_all_mountain_cards(html)
    if not cards:
        return None  # curated型ではない
    changes = []
    mountain_list = []

    for start, end, block in reversed(cards):
        id_m = CARD_ID_RE.search(block)
        if not id_m:
            continue
        mid = id_m.group(1)
        mt = by_id.get(mid)
        if not mt:
            mountain_list.append(mid)
            continue
        new_block = block

        def sub_area(m, mt=mt, mid=mid):
            new_area = mt.get('area') or m.group(2)
            new_elev = mt.get('elevation')
            new_elev_str = fmt_elev(new_elev) if new_elev is not None else m.group(3)
            if m.group(2) != new_area or m.group(3) != new_elev_str:
                changes.append((mid, f'area/elevation: "{m.group(2)}・{m.group(3)}m" -> "{new_area}・{new_elev_str}m"'))
            return m.group(1) + new_area + ' \u30fb ' + new_elev_str + 'm' + m.group(4)
        new_block = MC_AREA_RE.sub(sub_area, new_block, count=1)

        def sub_cat(m, mt=mt, mid=mid):
            new_cat = mt.get('category') or m.group(2)
            if m.group(2) != new_cat:
                changes.append((mid, f'category: "{m.group(2)}" -> "{new_cat}"'))
            return m.group(1) + new_cat + m.group(3)
        new_block = MC_CAT_RE.sub(sub_cat, new_block, count=1)

        def sub_diff(m, mt=mt, mid=mid):
            new_diff = mt.get('difficulty') or m.group(2)
            if m.group(2) != new_diff:
                changes.append((mid, f'difficulty: "{m.group(2)}" -> "{new_diff}"'))
            return m.group(1) + new_diff + m.group(3)
        new_block = MC_DIFF_RE.sub(sub_diff, new_block, count=1)

        def sub_ccr(m, mt=mt, mid=mid):
            new_ccr = mt.get('courseCoefficientRange') or m.group(2)
            if m.group(2) != new_ccr:
                changes.append((mid, f'courseCoefficientRange: "{m.group(2)}" -> "{new_ccr}"'))
            return m.group(1) + new_ccr + m.group(3)
        new_block = MC_CCR_RE.sub(sub_ccr, new_block, count=1)

        html = html[:start] + new_block + html[end:]
        mountain_list.append(mid)

    mountain_list.reverse()
    html, mention_changes = fix_ccr_mentions_in_text(html, by_id, mountain_list)
    changes.extend(mention_changes)

    if changes:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
    return changes


# --- hub型（全件一覧型）の同期 ----------------------------------------------

HUB_CCR_RE = re.compile(r'(コース定数 <strong[^>]*>)([^<]*)(</strong>)')
HUB_ELEV_RE = re.compile(r'(<div style="font-size:12px;color:#a09888">)([\d,]+)(m</div>)')
HUB_DIFF_BADGE_RE = re.compile(
    r'(<span style="background:#e8f8e8;color:#3a6a3a;font-size:11px;font-weight:bold;padding:2px 8px;border-radius:10px">)([^<]*)(</span>)'
)


def sync_hub(path, by_id):
    html = open(path, encoding='utf-8').read()
    anchors = list(re.finditer(r'<a href="/mountains/([a-z0-9_]+)/"[^>]*onmouseover', html))
    if not anchors:
        return None  # hub型ではない
    changes = []

    for m in reversed(anchors):
        mid = m.group(1)
        mt = by_id.get(mid)
        if not mt:
            continue
        block_start = m.start()
        next_m = re.search(r'<a href="/mountains/[a-z0-9_]+/"[^>]*onmouseover', html[m.end():])
        block_end = m.end() + next_m.start() if next_m else len(html)
        block = html[block_start:block_end]
        new_block = block

        def sub_ccr(mm, mt=mt, mid=mid):
            new_val = mt.get('courseCoefficientRange') or mm.group(2)
            if mm.group(2) != new_val:
                changes.append((mid, f'courseCoefficientRange: "{mm.group(2)}" -> "{new_val}"'))
            return mm.group(1) + new_val + mm.group(3)
        new_block = HUB_CCR_RE.sub(sub_ccr, new_block, count=1)

        def sub_elev(mm, mt=mt, mid=mid):
            new_val = str(mt.get('elevation')) if mt.get('elevation') is not None else mm.group(2)
            if mm.group(2) != new_val:
                changes.append((mid, f'elevation: "{mm.group(2)}" -> "{new_val}"'))
            return mm.group(1) + new_val + mm.group(3)
        new_block = HUB_ELEV_RE.sub(sub_elev, new_block, count=1)

        def sub_diff(mm, mt=mt, mid=mid):
            new_val = mt.get('difficulty') or mm.group(2)
            if mm.group(2) != new_val:
                changes.append((mid, f'difficulty: "{mm.group(2)}" -> "{new_val}"'))
            return mm.group(1) + new_val + mm.group(3)
        new_block = HUB_DIFF_BADGE_RE.sub(sub_diff, new_block, count=1)

        html = html[:block_start] + new_block + html[block_end:]

    if changes:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
    return changes


def sync_one(slug, by_id):
    path = os.path.join(ROOT, 'search', slug, 'index.html')
    if not os.path.isfile(path):
        raise RuntimeError(f'{path} が存在しない')
    changes = sync_curated(path, by_id)
    if changes is None:
        changes = sync_hub(path, by_id)
    if changes is None:
        raise RuntimeError('curated型・hub型のどちらの構造にも一致しない（未知のページ形式）')
    return changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slugs', nargs='*')
    ap.add_argument('--all', action='store_true')
    args = ap.parse_args()

    mountains = json.load(open(os.path.join(ROOT, 'data/mountains.json'), encoding='utf-8'))
    by_id = {m['id']: m for m in mountains}

    if args.all:
        targets = sorted(d for d in os.listdir(os.path.join(ROOT, 'search'))
                          if os.path.isdir(os.path.join(ROOT, 'search', d)))
    else:
        targets = args.slugs
    if not targets:
        ap.error('対象のページslugを指定するか --all を付けてください')

    ok = skipped = failed = 0
    for slug in targets:
        try:
            changes = sync_one(slug, by_id)
            if changes:
                print(f'{slug}: {len(changes)}件修正')
                for c in changes:
                    print('   ', c)
                ok += 1
            else:
                print(f'{slug}: スキップ（既に最新）')
                skipped += 1
        except Exception as e:
            print(f'{slug}: 失敗 - {e}')
            failed += 1

    print(f'\n完了: {ok}件 / スキップ: {skipped}件 / 失敗: {failed}件')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
