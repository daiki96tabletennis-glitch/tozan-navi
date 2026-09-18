#!/usr/bin/env python3
# ============================================================
# [DEPRECATED 2026-09-18] gen_mountain_pages.py への完全移行に伴い廃止。
# このスクリプトが担っていた同期処理は、gen_mountain_pages.py が
# mountains.json 等の正本データから全ページを毎回フル再生成することで
# 完全に代替されています（HTMLへの部分パッチではなく全体生成のため）。
# 通常運用では実行しないでください。参照用に残置しています。
# ============================================================
# -*- coding: utf-8 -*-
"""
YAMATCH 山ページ FAQ同期スクリプト（Phase2）

mountains.json の faq フィールド（[{question, answer}, ...]）を正本として、
対象山ページのFAQPage JSON-LDと可視FAQブロックの両方を再生成する。

mountains.jsonのfaqを編集した後に実行し、HTML側（構造化データ・可視表示）を
最新化する。既にJSON-LD・可視FAQ両方が正本と完全一致しているページは自動でスキップする。

使い方:
  python3 scripts/sync_mountain_faq.py <山id> [<山id> ...]
  python3 scripts/sync_mountain_faq.py --all       # mountains.json全件が対象
"""
import argparse
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)

FAQ_ITEM_BLOCK_RE = re.compile(
    r'(<div class="faq-item">\s*<h2 class="faq-q">.*?</h2>\s*'
    r'<div class="faq-a">\s*<div><p>.*?</p></div>\s*</div>\s*</div>\s*)+',
    re.S
)
JSONLD_RE = re.compile(
    r'<script type="application/ld\+json">\{"@context".*?"FAQPage".*?\}</script>'
)


def build_visible_faq(faq_list):
    items = []
    for qa in faq_list:
        items.append(
            '<div class="faq-item">\n'
            f'    <h2 class="faq-q">{qa["question"]}</h2>\n'
            '    <div class="faq-a">\n'
            f'      <div><p>{qa["answer"]}</p></div>\n'
            '    </div>\n'
            '  </div>\n'
        )
    return '  ' + ''.join(items)


def build_jsonld(faq_list):
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": qa["question"],
             "acceptedAnswer": {"@type": "Answer", "text": qa["answer"]}}
            for qa in faq_list
        ],
    }
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + '</script>'


def sync_one(mid, m):
    path = os.path.join(ROOT, 'mountains', mid, 'index.html')
    if not os.path.isfile(path):
        raise RuntimeError(f'{path} が存在しない')
    html = open(path, encoding='utf-8').read()
    faq_list = m.get('faq')
    if not faq_list:
        return {'skipped': True, 'reason': 'mountains.jsonにfaqが無い'}

    new_jsonld = build_jsonld(faq_list)
    new_visible = build_visible_faq(faq_list)

    jsonld_match = JSONLD_RE.search(html)
    if not jsonld_match:
        raise RuntimeError('FAQPage JSON-LDが見つからない')
    visible_match = FAQ_ITEM_BLOCK_RE.search(html)
    if not visible_match:
        raise RuntimeError('可視FAQブロックが見つからない')

    if jsonld_match.group(0) == new_jsonld and visible_match.group(0).strip() == new_visible.strip():
        return {'skipped': True, 'reason': '既に最新'}

    html = html[:jsonld_match.start()] + new_jsonld + html[jsonld_match.end():]
    # 可視FAQのオフセットはJSON-LD置換で変わらない（JSON-LDより後ろにあるため）
    visible_match2 = FAQ_ITEM_BLOCK_RE.search(html)
    html = html[:visible_match2.start()] + new_visible + html[visible_match2.end():]

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    return {'skipped': False, 'count': len(faq_list)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ids', nargs='*')
    ap.add_argument('--all', action='store_true')
    args = ap.parse_args()

    mountains = json.load(open(os.path.join(ROOT, 'data/mountains.json'), encoding='utf-8'))
    by_id = {m['id']: m for m in mountains}
    targets = [m['id'] for m in mountains] if args.all else args.ids
    if not targets:
        ap.error('対象の山idを指定するか --all を付けてください')

    ok = skipped = failed = 0
    for mid in targets:
        try:
            m = by_id.get(mid)
            if not m:
                raise RuntimeError('mountains.jsonに存在しないid')
            result = sync_one(mid, m)
            if result['skipped']:
                print(f'{mid}: スキップ（{result["reason"]}）')
                skipped += 1
            else:
                print(f'{mid}: FAQ再生成完了（{result["count"]}問）')
                ok += 1
        except Exception as e:
            print(f'{mid}: 失敗 - {e}')
            failed += 1

    print(f'\n完了: {ok}件 / スキップ: {skipped}件 / 失敗: {failed}件')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
