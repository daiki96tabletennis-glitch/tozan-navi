#!/usr/bin/env python3
"""まとめ記事「サウナシュラン受賞サウナに寄れる山」の記事一覧のバナーと共有の画像（articles/images/hero_saunachelin_hiking.jpg。2026-11-16）
写真は使わず、色・山の形・サウナ小屋・文字だけで描く（gen_winter_banners.py の部品）。運営者の絵に差し替えるときは同じ名前で置き換え、このスクリプトは流さない
2026-11-16 に運営者の絵（幅1200px）に差し替えた（作った絵の控えは .claude/backup/sauna_banner_generated/）。--force が無いと動かない"""
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
    im = B.grad(B.hexc('#cfe0ee'), B.hexc('#e9efe2'))
    B.ridges(im, [((150, 172, 132), [(540, 290), (650, 190), (750, 250), (860, 170), (960, 220)]),
                  ((104, 128, 88), [(520, 380), (640, 320), (770, 360), (900, 300), (960, 330)])])
    d = ImageDraw.Draw(im)
    # サウナ小屋（丸太の小屋と煙突）
    d.polygon([(690, 330), (800, 270), (910, 330)], fill=(120, 78, 48))
    d.rectangle([710, 330, 890, 450], fill=(176, 122, 76))
    for y in range(342, 450, 16):
        d.line([(710, y), (890, y)], fill=(150, 100, 60), width=2)
    d.rectangle([780, 370, 830, 450], fill=(90, 58, 36))
    d.rectangle([860, 262, 878, 310], fill=(70, 70, 70))
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    for k in range(5):
        gd.ellipse([862 + k * 6, 236 - k * 26, 892 + k * 6, 262 - k * 26], fill=(255, 255, 255, 150 - k * 25))
    g = g.filter(ImageFilter.GaussianBlur(6))
    im.paste(g, (0, 0), g)
    d.rectangle([0, 450, W, H], fill=(96, 118, 80))
    B.text_block(im, 'サウナシュラン', '受賞サウナに', '寄れる山',
                 ['登山口から車で30分ほど。', '日帰りで使えるサウナと', '近くの山を地図で紹介'], '#2a2520', '#a0522d', (255, 252, 246, 230))
    return im


if __name__ == '__main__':
    p = os.path.join(ROOT, 'articles', 'images', 'hero_saunachelin_hiking.jpg')
    banner().save(p, 'JPEG', quality=88)
    print('書きました', p)
