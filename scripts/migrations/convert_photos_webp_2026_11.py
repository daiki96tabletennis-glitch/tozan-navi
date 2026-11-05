"""山の写真（images/mountains/）を、長辺1600pxの WebP（品質80）にそろえる（2026-11-05。運営者の指示「既存の写真も変換」）

管理画面の「山画像を管理」が新しい写真を同じ形で保存するようになったので、前からある JPEG も合わせる。
- 写真ごとに、同じ名前の .webp を作る（元の .jpg は消さない＝検索の画像・共有ずみのリンクのため）
- 書き換える：data/mountains.json の photos、data/image-credits.json の localPath・fileName・contentHash・modifications、
  手で作った記事の img（articles/coeff-*）
- このあと gen_mountain_pages.py --all（共有の画像は JPEG の写しを作る）・gen_train_daytrip.py・grade_photos.py を流す
何度流しても同じ結果（作ってある .webp は作り直さない）。
"""
import glob
import hashlib
import json
import os
import re

from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EDGE = 1600
QUALITY = 80
NOTE = '長辺1600pxのWebPに変換'
PAT = re.compile(r'(/images/mountains/[A-Za-z0-9_\-]+/[A-Za-z0-9_\-.]+)\.(jpe?g|png)')


def webp_of(path):
    return re.sub(r'\.(jpe?g|png)$', '.webp', path, flags=re.I)


def convert(rel):
    src = os.path.join(ROOT, rel.lstrip('/'))
    dst = webp_of(src)
    if not os.path.exists(dst):
        im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
        im.thumbnail((EDGE, EDGE), Image.LANCZOS)
        im.save(dst, 'WEBP', quality=QUALITY, method=6)
    return os.path.getsize(src), os.path.getsize(dst)


def sha256(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def main():
    mp = os.path.join(ROOT, 'data', 'mountains.json')
    cp = os.path.join(ROOT, 'data', 'image-credits.json')
    M = json.load(open(mp, encoding='utf-8'))
    C = json.load(open(cp, encoding='utf-8'))

    # 1) ファイルを変換（photos に載っている写真だけ。どこにも使っていない古い JPEG は変換しない）
    files = set(p for m in M for p in (m.get('photos') or []) if isinstance(p, str) and PAT.fullmatch(p))
    before = after = 0
    for rel in sorted(files):
        a, b = convert(rel)
        before += a
        after += b
    print('写真 %d 枚：%.1fMB → %.1fMB' % (len(files), before / 1e6, after / 1e6))

    # 2) データの書き換え
    n_photo = 0
    for m in M:
        ph = m.get('photos')
        if not ph:
            continue
        new = [webp_of(p) if isinstance(p, str) and PAT.fullmatch(p) else p for p in ph]
        n_photo += sum(1 for x, y in zip(ph, new) if x != y)
        m['photos'] = new
    n_cred = 0
    for mid, lst in C.items():
        for c in lst:
            lp = c.get('localPath')
            if isinstance(lp, str) and PAT.fullmatch(lp) and lp in files:
                c['localPath'] = webp_of(lp)
                if c.get('fileName'):
                    c['fileName'] = webp_of(c['fileName']) if c.get('source') == 'own' else c['fileName']
                c['contentHash'] = sha256(os.path.join(ROOT, c['localPath'].lstrip('/')))
                mod = c.get('modifications') or ''
                if NOTE not in mod:
                    c['modifications'] = (mod + '／' if mod else '') + NOTE
                n_cred += 1
    json.dump(M, open(mp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    json.dump(C, open(cp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('photos の書き換え：%d　クレジットの書き換え：%d' % (n_photo, n_cred))

    # 3) 手で作った記事の img
    for f in sorted(glob.glob(os.path.join(ROOT, 'articles', 'coeff-*', 'index.html'))):
        s = open(f, encoding='utf-8').read()
        t, k = PAT.subn(lambda mm: mm.group(1) + '.webp', s)
        if k:
            open(f, 'w', encoding='utf-8').write(t)
            print('記事：', os.path.relpath(f, ROOT), k)

    # 4) 確かめ：photos とクレジットの写真がすべてあること
    missing = [p for m in M for p in (m.get('photos') or []) if isinstance(p, str) and p.startswith('/') and not os.path.exists(os.path.join(ROOT, p.lstrip('/')))]
    missing += [c['localPath'] for lst in C.values() for c in lst if c.get('localPath') and not os.path.exists(os.path.join(ROOT, c['localPath'].lstrip('/')))]
    if missing:
        raise SystemExit('見つからない写真：%s' % missing[:10])


if __name__ == '__main__':
    main()
