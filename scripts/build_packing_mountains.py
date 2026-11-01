#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""持ち物チェックリストのページ（/packing/）が使う、山の軽い一覧を作る（2026-11-01）。

mountains.json は 5MB あり、スマホで山を選ぶだけのために読むには重い。
山ID・山名・都道府県（area）・標高・装備カレンダー（gearCalendar）だけを data/packing_mountains.json に書き出す。
山を足したり、装備カレンダーを直したりしたら実行する（食い違いは check_pages.py のセクション19で見つかる）。

  python3 scripts/build_packing_mountains.py          # 書き出す
  python3 scripts/build_packing_mountains.py --check  # 食い違いがあれば終了コード1
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'data', 'mountains.json')
OUT = os.path.join(ROOT, 'data', 'packing_mountains.json')


def build():
    rows = []
    for m in json.load(open(SRC, encoding='utf-8')):
        rows.append({
            'id': m['id'],
            'name': m['name'],
            'area': m.get('area') or '',
            'elev': int(m['elevation']) if m.get('elevation') else 0,
            'gear': m.get('gearCalendar') or [],
        })
    rows.sort(key=lambda r: r['name'])
    return rows


def text(rows):
    return json.dumps(rows, ensure_ascii=False, separators=(',', ':')) + '\n'


def main():
    new = text(build())
    if '--check' in sys.argv:
        old = open(OUT, encoding='utf-8').read() if os.path.exists(OUT) else ''
        if old != new:
            print('data/packing_mountains.json が mountains.json と食い違っています（build_packing_mountains.py を実行）')
            sys.exit(1)
        print('ok')
        return
    open(OUT, 'w', encoding='utf-8').write(new)
    print('書きました：%d山 → data/packing_mountains.json（%d KB）' % (len(json.loads(new)), len(new.encode('utf-8')) // 1024))


if __name__ == '__main__':
    main()
