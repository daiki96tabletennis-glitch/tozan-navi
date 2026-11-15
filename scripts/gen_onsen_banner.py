#!/usr/bin/env python3
"""記事「登山のあとの温泉・サウナ」の記事一覧のバナーと共有の画像（articles/images/hero_onsen_sauna.jpg。2026-11-15）
写真は使わず、色・山の形・湯けむり・文字だけで描く（冬の特集のバナー gen_winter_banners.py と同じ部品）。運営者の絵に差し替えるときは同じ名前で置き換える
2026-11-15 に運営者の絵（1200×632）に差し替えた。このスクリプトを流すと運営者の絵を上書きするので流さない（作った絵の控えは .claude/backup/onsen_banner_generated/）"""
import sys as _s
if __name__ == '__main__' and '--force' not in _s.argv:
    raise SystemExit('運営者の絵に差し替え済み。上書きするときだけ --force')
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import gen_winter_banners as B  # noqa: E402


def banner():
    W, H = B.W, B.H
    im = B.grad(B.hexc('#f3c9a0'), B.hexc('#7b8f6a'))
    B.sun(im, (820, 150), 34, (255, 236, 200), (255, 210, 160, 170))
    B.ridges(im, [((122, 138, 104), [(540, 300), (660, 210), (760, 260), (870, 190), (960, 230)]),
                  ((86, 104, 72), [(520, 380), (640, 310), (760, 350), (880, 300), (960, 320)])])
    d = ImageDraw.Draw(im)
    # 湯船（岩で囲んだ露天風呂）
    d.ellipse([600, 400, 940, 500], fill=(120, 110, 96))
    d.ellipse([620, 410, 920, 488], fill=(150, 196, 206))
    for x, y, r in [(610, 440, 22), (650, 470, 20), (900, 445, 24), (930, 470, 18), (700, 488, 16), (860, 488, 18)]:
        d.ellipse([x - r, y - r * 0.7, x + r, y + r * 0.7], fill=(104, 96, 84))
    # 湯けむり
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    for cx in (700, 770, 840):
        for k in range(6):
            y = 400 - k * 28
            x = cx + (14 if k % 2 else -14)
            gd.ellipse([x - 22, y - 16, x + 22, y + 16], fill=(255, 255, 255, 110 - k * 14))
    g = g.filter(ImageFilter.GaussianBlur(8))
    im.paste(g, (0, 0), g)
    B.text_block(im, '下山後の楽しみ', '登山のあとの', '温泉・サウナ',
                 ['関東発の日帰り登山12山と、', '下山後に寄れる温泉・サウナ。', '料金・最終受付・行き方つき'], '#2a2520', '#a0522d', (255, 252, 246, 228))
    return im


if __name__ == '__main__':
    p = os.path.join(ROOT, 'articles', 'images', 'hero_onsen_sauna.jpg')
    banner().save(p, 'JPEG', quality=88)
    print('書きました', p)
