#!/usr/bin/env python3
"""冬の特集記事の記事一覧のバナーと共有の画像を作る（2026-11-12）

写真は使わず、色・山の形・太陽・文字だけで描く（出典の表示が要らない）。運営者の絵に差し替えるときは、同じ名前の画像を置き換える。
- articles/images/hero_hatsuhinode.jpg  初日の出登山
- articles/images/hero_diamond_fuji.jpg ダイヤモンド富士
- articles/images/hero_winter_views.jpg 冬にしか見られない絶景
大きさは今のバナー（hero_winter.jpg）と同じ 960×505。字体は Zen Kaku Gothic New（.claude/fonts/。gen_type_ogp.py と同じ）
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from gen_type_ogp import zen  # noqa: E402

W, H = 960, 505


def grad(top, bottom):
    im = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return im


def hexc(s):
    s = s.lstrip('#')
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def ridges(im, layers):
    d = ImageDraw.Draw(im)
    for color, pts in layers:
        d.polygon([(0, H)] + pts + [(W, H)], fill=color)


def sun(im, xy, r, color, glow):
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    x, y = xy
    gd.ellipse([x - r * 3, y - r * 3, x + r * 3, y + r * 3], fill=glow)
    g = g.filter(ImageFilter.GaussianBlur(r))
    im.paste(g, (0, 0), g)
    ImageDraw.Draw(im).ellipse([x - r, y - r, x + r, y + r], fill=color)


def text_block(im, label, title1, title2, sub, ink, accent, panel):
    p = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(p)
    pd.rounded_rectangle([28, 34, 600, 470], radius=36, fill=panel)
    im.paste(p, (0, 0), p)
    d = ImageDraw.Draw(im)
    f_label = zen('Bold', 24)
    lw = d.textlength(label, font=f_label)
    d.rounded_rectangle([58, 62, 58 + lw + 40, 106], radius=22, fill=accent)
    d.text((78, 69), label, font=f_label, fill='#ffffff')
    f1 = zen('Black', 46)
    f2 = zen('Black', 60)
    d.text((58, 136), title1, font=f1, fill=ink)
    d.text((58, 200), title2, font=f2, fill=accent)
    assert 58 + d.textlength(title1, font=f1) <= 590, title1
    assert 58 + d.textlength(title2, font=f2) <= 590, title2
    d.line([(60, 292), (570, 292)], fill=accent, width=3)
    fs = zen('Medium', 23)
    y = 312
    for line in sub:
        assert 58 + d.textlength(line, font=fs) <= 590, line
        d.text((58, y), line, font=fs, fill=ink)
        y += 38


def hatsuhinode():
    im = grad(hexc('#2d3b6b'), hexc('#f2b07a'))
    sun(im, (790, 300), 46, (255, 214, 130), (255, 170, 90, 170))
    ridges(im, [((84, 70, 96), [(560, 330), (700, 270), (820, 320), (960, 250)]),
                ((52, 46, 70), [(520, 400), (640, 340), (760, 380), (900, 320), (960, 340)])])
    text_block(im, '冬の特集', '元日の山頂で', '初日の出登山',
               ['山頂の日の出の時刻と、', '元日の始発で間に合うかを7山で。', '初詣ができる神社・寺も'], '#2a2520', '#c0563a', (255, 252, 246, 225))
    return im


def diamond():
    im = grad(hexc('#f6c58b'), hexc('#5a6e9a'))
    d = ImageDraw.Draw(im)
    # 富士山（頂上が平らな円錐）と、その頂に重なる太陽
    sun(im, (790, 205), 30, (255, 240, 200), (255, 230, 170, 200))
    d.polygon([(560, 505), (745, 222), (835, 222), (960, 420), (960, 505)], fill=(70, 88, 128))
    d.polygon([(745, 222), (835, 222), (812, 250), (790, 238), (770, 252)], fill=(240, 244, 250))
    ridges(im, [((48, 60, 90), [(470, 470), (600, 420), (720, 455), (840, 430), (960, 460)])])
    text_block(im, '冬の特集', 'ダイヤモンド富士が', '見える山と日付',
               ['関東の8山を厳選し、山頂から', '太陽が富士山頂に重なる日と', '時刻を計算しました'], '#2a2520', '#3e5a8a', (255, 252, 246, 225))
    return im


def views():
    im = grad(hexc('#bcd6ec'), hexc('#f4f8fb'))
    d = ImageDraw.Draw(im)
    ridges(im, [((206, 220, 234), [(560, 300), (690, 210), (780, 260), (880, 190), (960, 240)]),
                ((236, 242, 248), [(520, 390), (660, 300), (790, 360), (900, 300), (960, 330)])])
    # 樹氷（雪をかぶった木）
    for x, y, s in [(640, 420, 1.0), (700, 440, 0.8), (760, 415, 1.2), (830, 445, 0.9), (890, 420, 1.1)]:
        d.polygon([(x, y - 90 * s), (x - 32 * s, y), (x + 32 * s, y)], fill=(255, 255, 255))
        d.polygon([(x, y - 90 * s), (x - 32 * s, y), (x + 32 * s, y)], outline=(170, 196, 220), width=2)
    text_block(im, '冬の特集', '冬にしか見られない', '絶景の山',
               ['樹氷・霧氷・銀世界の湿原・氷の世界。', '冬の装備と行き方つきで', '6山を紹介します'], '#2a2520', '#3a6a8e', (255, 255, 255, 215))
    return im


def main():
    # ダイヤモンド富士・冬の絶景は運営者の絵に差し替えた（2026-11-15。1200×630）。作り直すと上書きするので、この2枚は作らない
    out = {'hero_hatsuhinode.jpg': hatsuhinode()}
    for name, im in out.items():
        p = os.path.join(ROOT, 'articles', 'images', name)
        im.convert('RGB').save(p, quality=88)
        print('書きました', os.path.relpath(p, ROOT))


if __name__ == '__main__':
    main()
