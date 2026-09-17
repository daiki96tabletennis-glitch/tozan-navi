#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAMATCH 山ページ 共通CSS/JS同期スクリプト（Phase1）

assets/css/mountain.css・assets/js/mountain.js に定義されている「全山共通の
CSSルール／JSブロック」を正本として、指定した山ページのインラインCSS/JSから
該当箇所を取り除き、相対パス（../../assets/...）の<link>/<script src>参照に
置き換える。

新しい山ページを追加したときや、既存ページのCSS/JSが編集されて共通部分が
インラインに戻ってしまったときに実行する。

使い方:
  python3 scripts/sync_mountain_assets.py <山id> [<山id> ...]
  python3 scripts/sync_mountain_assets.py --all       # mountains.json全件が対象
"""
import argparse
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)


def split_css_rules(css):
    """CSSを波括弧の深さを見てトップレベルルール単位に分割する（@media等も1ルールとして扱う）。"""
    rules, depth, start = [], 0, 0
    for i, c in enumerate(css):
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                rules.append(css[start:i + 1].strip())
                start = i + 1
    tail = css[start:].strip()
    if tail:
        rules.append(tail)
    return [r for r in rules if r]


def load_common_rules():
    css = open(os.path.join(ROOT, 'assets/css/mountain.css'), encoding='utf-8').read()
    return set(split_css_rules(css))


def load_common_scripts():
    js = open(os.path.join(ROOT, 'assets/js/mountain.js'), encoding='utf-8').read()
    # mountain.js は空行区切りでブロックを連結して生成されているため、
    # 元の各<script>ブロックの内容と厳密一致させるには生成時と同じ単位に戻す必要がある。
    # ここでは「連続する2つ以上の改行」で区切られたブロックを1単位とみなす。
    blocks = re.split(r'\n{2,}', js.strip())
    return set(b.strip() for b in blocks if b.strip())


def sync_one(mid, common_rules, common_scripts):
    path = os.path.join(ROOT, 'mountains', mid, 'index.html')
    if not os.path.isfile(path):
        raise RuntimeError(f'{path} が存在しない')
    html = open(path, encoding='utf-8').read()

    if 'mountain.css' in html and 'mountain.js' in html:
        return {'skipped': True, 'reason': '既に共通アセット参照済み'}

    style_blocks = list(re.finditer(r'<style([^>]*)>(.*?)</style>', html, re.S))
    if not style_blocks:
        raise RuntimeError(f'{mid}: <style>タグが見つからない')
    main_style_match = max(style_blocks, key=lambda m: len(m.group(2)))
    rules = split_css_rules(main_style_match.group(2))
    remaining_rules = [r for r in rules if r not in common_rules]
    removed_css = len(rules) - len(remaining_rules)
    new_style_tag = f'<style{main_style_match.group(1)}>' + '\n'.join(remaining_rules) + '\n</style>'
    html = html[:main_style_match.start()] + new_style_tag + html[main_style_match.end():]
    link_tag = '<link rel="stylesheet" href="../../assets/css/mountain.css">\n'
    insert_pos = html.find(new_style_tag)
    html = html[:insert_pos] + link_tag + html[insert_pos:]

    blocks = list(re.finditer(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', html, re.S))
    removed_js = 0
    for m in reversed(blocks):
        if m.group(1).strip() in common_scripts:
            html = html[:m.start()] + html[m.end():]
            removed_js += 1
    if removed_js > 0:
        body_close = html.rfind('</body>')
        if body_close == -1:
            raise RuntimeError(f'{mid}: </body>が見つからない')
        html = (html[:body_close] +
                '<script src="../../assets/js/mountain.js"></script>\n' +
                html[body_close:])

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    return {'skipped': False, 'removed_css': removed_css, 'total_css': len(rules), 'removed_js': removed_js}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ids', nargs='*', help='対象の山id')
    ap.add_argument('--all', action='store_true', help='mountains.json全件を対象にする')
    args = ap.parse_args()

    mountains = json.load(open(os.path.join(ROOT, 'data/mountains.json'), encoding='utf-8'))
    targets = [m['id'] for m in mountains] if args.all else args.ids
    if not targets:
        ap.error('対象の山idを指定するか --all を付けてください')

    common_rules = load_common_rules()
    common_scripts = load_common_scripts()

    ok, skipped, failed = 0, 0, 0
    for mid in targets:
        try:
            result = sync_one(mid, common_rules, common_scripts)
            if result['skipped']:
                print(f'{mid}: スキップ（{result["reason"]}）')
                skipped += 1
            else:
                print(f'{mid}: CSS {result["removed_css"]}/{result["total_css"]}ルール除去, '
                      f'JS {result["removed_js"]}ブロック除去')
                ok += 1
        except Exception as e:
            print(f'{mid}: 失敗 - {e}')
            failed += 1

    print(f'\n完了: {ok}件 / スキップ: {skipped}件 / 失敗: {failed}件')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
