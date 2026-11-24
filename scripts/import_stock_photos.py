#!/usr/bin/env python3
"""写真AC・ぱくたその写真を山の写真に取り込む（2026-11-24〜。運営者の指示「古賀志山の写真 13・6・11番」）。

写真AC は会員がブラウザで手でダウンロードする決まり（無料会員は1日の回数に上限がある）。
ダウンロードのフォルダ（~/Downloads）に置かれたファイルを、写真の番号で探して取り込む。

  python3 scripts/import_stock_photos.py <山ID> A22565906 A34613604 ...   # 写真AC（A＋番号）。並べた順に photos の後ろへ足す
  python3 scripts/import_stock_photos.py <山ID> P<ファイル名の一部> ...     # ぱくたそ
  --front を付けると、足した写真を photos の先頭に置く（山ページの1枚目）

やること：長辺1600pxの WebP（品質80）にして images/mountains/<山ID>/ に置き、mountains.json の photos と
image-credits.json（作者・ライセンス・元のページ。source は photoac / pakutaso）に足す。何度流しても同じ写真を二重には足さない。
そのあと gen_mountain_pages.py --id <山ID> と check_pages.py。山の写真を使う記事（冬でも登れる山7選など）は作り直す。
"""
import glob
import html
import json
import os
import re
import sys
import urllib.request

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOADS = os.path.expanduser('~/Downloads')
SRC = {
    'A': {'source': 'photoac', 'sourceName': '写真AC', 'author': '写真AC', 'license': '写真AC 利用規約',
          'licenseUrl': 'https://www.photo-ac.com/main/terms', 'page': 'https://www.photo-ac.com/main/detail/%s', 'prefix': 'photoac'},
    'P': {'source': 'pakutaso', 'sourceName': 'ぱくたそ', 'author': 'ぱくたそ', 'license': 'ぱくたそ 利用規約',
          'licenseUrl': 'https://www.pakutaso.com/userpolicy.html', 'page': 'https://www.pakutaso.com/', 'prefix': 'pakutaso'},
}


def author_of(kind, page):
    """写真のページに出ている作者（写真AC は「作者:」のリンク、ぱくたそは構造化データの creator）。読めなければ None"""
    try:
        s = urllib.request.urlopen(urllib.request.Request(page, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode('utf-8', 'replace')
    except Exception:
        return None
    if kind == 'A':
        m = re.search(r'作者:\s*</span>\s*<a[^>]*href="([^"]+)"[^>]*>\s*(.*?)\s*</a>', s, re.S)
        return (re.sub(r'<[^>]+>', '', html.unescape(m.group(2))).strip(), 'https://www.photo-ac.com' + m.group(1)) if m else None
    m = re.search(r'"creator"\s*:\s*\{[^}]*?"name"\s*:\s*"([^"]+)"\s*,\s*"url"\s*:\s*"([^"]+)"', s)
    return (m.group(1), m.group(2)) if m else None


def find_file(key):
    hits = [p for p in glob.glob(os.path.join(DOWNLOADS, '*')) if key in os.path.basename(p)
            and os.path.splitext(p)[1].lower() in ('.jpg', '.jpeg', '.png', '.webp')]
    if not hits:
        raise SystemExit('ダウンロードのフォルダに「%s」を含む写真が無い' % key)
    return max(hits, key=os.path.getmtime)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) < 2:
        raise SystemExit(__doc__)
    mid, keys = args[0], args[1:]
    mp = os.path.join(ROOT, 'data', 'mountains.json')
    cp = os.path.join(ROOT, 'data', 'image-credits.json')
    ms = json.load(open(mp, encoding='utf-8'))
    credits = json.load(open(cp, encoding='utf-8'))
    m = next((x for x in ms if x['id'] == mid), None)
    if not m:
        raise SystemExit('山が無い：' + mid)
    added = []
    for k in keys:
        s = SRC[k[0]]
        key = k[1:]
        rel = '/images/mountains/%s/%s-%s.webp' % (mid, s['prefix'], key)
        if rel in (m.get('photos') or []):
            print('もうある', rel)
            continue
        src = find_file(key)
        im = Image.open(src).convert('RGB')
        im.thumbnail((1600, 1600), Image.LANCZOS)
        os.makedirs(os.path.join(ROOT, 'images', 'mountains', mid), exist_ok=True)
        im.save(os.path.join(ROOT, rel.lstrip('/')), 'WEBP', quality=80, method=4)
        page = s['page'] % key if '%s' in s['page'] else s['page']
        who = author_of(k[0], page) if '%s' in s['page'] else None
        credits.setdefault(mid, []).append({
            'fileName': os.path.basename(src), 'localPath': rel, 'author': who[0] if who else s['author'], 'authorUrl': who[1] if who else None, 'license': s['license'],
            'licenseUrl': s['licenseUrl'], 'commonsPageUrl': None,
            'sourcePageUrl': s['page'] % key if '%s' in s['page'] else s['page'],
            'source': s['source'], 'sourceName': s['sourceName'], 'sourceId': '%s:%s' % (s['source'], key),
            'modifications': '長辺1600pxのWebPに変換'})
        added.append(rel)
        print('取り込んだ', src, '→', rel, im.size)
    if added:
        photos = m.get('photos') or []
        m['photos'] = (added + photos) if '--front' in sys.argv else (photos + added)
        json.dump(ms, open(mp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        json.dump(credits, open(cp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('photos:', m.get('photos'))


if __name__ == '__main__':
    main()
