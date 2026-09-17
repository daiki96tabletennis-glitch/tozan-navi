#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAMATCH 山ページ エンジンJS同期スクリプト（Phase3）

各山ページの個別エンジンJS（shareNative/applyDep等を含む本体）を、共通の
assets/js/mountain-engine.js + 山固有の初期化データ(window.YM_MOUNTAIN_INIT)に
置き換える。

新しい山ページを追加したときに実行する。既に統一済みのページは自動でスキップする。
heroMinMap（車アクセス時間のJSON fetch完了前フォールバック値）はmountains.jsonの
driveOfuna/driveShinjuku/driveYokohama/driveOmiya/driveTachikawaから都度算出するため、
手動でJS側に値を持つ必要はない。nearbyIds（近くて似た山カードの時間更新対象）は、
ページ内の「近くて似た山」カードのid="nearby-time-XXX"から自動抽出する。

使い方:
  python3 scripts/gen_mountain_engine.py <山id> [<山id> ...]
  python3 scripts/gen_mountain_engine.py --all       # mountains.json全件が対象
"""
import argparse
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)

DRIVE_KEYS = [
    ('ofuna', 'driveOfuna'), ('shinjuku', 'driveShinjuku'),
    ('yokohama', 'driveYokohama'), ('omiya', 'driveOmiya'),
    ('tachikawa', 'driveTachikawa'),
]

SCRIPT_TAG_RE = re.compile(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', re.S)


def find_engine_script(html):
    """applyDepを含む<script>タグ（山ごとのエンジン本体）をタグ単位で探す。
    内部のコード順序や、shareNative()の有無（ネイティブ共有ボタンを持たない
    ページもある）が山によって異なっていても検出できる。"""
    candidates = [m for m in SCRIPT_TAG_RE.finditer(html)
                  if 'applyDep' in m.group(1) and 'function applyDep(' in m.group(1)]
    if len(candidates) != 1:
        return None
    return candidates[0]


def build_hero_min_map(m):
    return {key: str(m[field]) for key, field in DRIVE_KEYS if m.get(field) is not None}


def extract_nearby_ids(html):
    return re.findall(r'id="nearby-time-([a-z0-9_]+)"', html)


def build_init_block(m, nearby_ids):
    init = {
        'id': m['id'],
        'name': m['name'],
        'heroMinMap': build_hero_min_map(m),
        'nearbyIds': nearby_ids,
    }
    js_obj = json.dumps(init, ensure_ascii=False, indent=2)
    return (
        '<script>\nvar YM_MOUNTAIN_INIT = ' + js_obj + ';\n</script>\n'
        '<script src="../../assets/js/mountain-engine.js"></script>'
    )


def sync_one(mid, mountains_by_id):
    path = os.path.join(ROOT, 'mountains', mid, 'index.html')
    if not os.path.isfile(path):
        raise RuntimeError(f'{path} が存在しない')
    html = open(path, encoding='utf-8').read()

    if 'mountain-engine.js' in html and 'YM_MOUNTAIN_INIT' in html:
        return {'skipped': True, 'reason': '既に共通エンジン参照済み'}

    m = find_engine_script(html)
    if not m:
        raise RuntimeError('個別エンジンscriptブロックを一意に特定できない（手動確認が必要）')
    if mid not in mountains_by_id:
        raise RuntimeError('mountains.jsonに存在しないid')

    nearby_ids = extract_nearby_ids(html)
    init_block = build_init_block(mountains_by_id[mid], nearby_ids)
    new_html = html[:m.start()] + init_block + html[m.end():]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_html)
    return {'skipped': False, 'nearby_ids': len(nearby_ids)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ids', nargs='*', help='対象の山id')
    ap.add_argument('--all', action='store_true', help='mountains.json全件を対象にする')
    args = ap.parse_args()

    mountains = json.load(open(os.path.join(ROOT, 'data/mountains.json'), encoding='utf-8'))
    by_id = {m['id']: m for m in mountains}
    targets = [m['id'] for m in mountains] if args.all else args.ids
    if not targets:
        ap.error('対象の山idを指定するか --all を付けてください')

    ok = skipped = failed = 0
    for mid in targets:
        try:
            result = sync_one(mid, by_id)
            if result['skipped']:
                print(f'{mid}: スキップ（{result["reason"]}）')
                skipped += 1
            else:
                print(f'{mid}: エンジン置き換え完了（nearbyIds={result["nearby_ids"]}件）')
                ok += 1
        except Exception as e:
            print(f'{mid}: 失敗 - {e}')
            failed += 1

    print(f'\n完了: {ok}件 / スキップ: {skipped}件 / 失敗: {failed}件')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
