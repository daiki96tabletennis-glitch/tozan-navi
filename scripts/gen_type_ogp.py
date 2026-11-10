"""登山タイプ診断の共有画像（ogp/type-<記号>.png。1200×630）を16タイプ分作る（2026-11-10。運営者の指示）

LINE はリンクの画像を真ん中の正方形に切って小さく出すので、カワウソとタイプ名を真ん中に置く。
背景はオフホワイト、左上にヘッダーと同じロゴ（三角3つ＋Georgia の「Yamatch」）と「登山タイプ診断」、
右上に「◯◯型」と診断者の割合。タイプ名・割合は recommend/index.html の TYPES、絵は MINI_SVGS から読む。
字体は Zen Kaku Gothic New（Google Fonts。.claude/fonts/ に置く。無ければ取ってくる）。Mac の Georgia を使う。
画像を作り直したら、読み込みの版（?v=）を上げる：--ver で指定（type/*/ recommend/*/ recommend/index.html の ogp/type- の版を書き換える）
  python3 scripts/gen_type_ogp.py --ver 20261110
"""
import argparse
import glob
import os
import re
import urllib.request

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, '.claude', 'fonts')
FONT_URL = 'https://github.com/google/fonts/raw/main/ofl/zenkakugothicnew/%s.ttf'
GEORGIA = '/System/Library/Fonts/Supplemental/Georgia Bold.ttf'
W, H = 1200, 630
BG = '#faf8f2'
INK = '#2a2520'


def zen(weight, size):
    name = 'ZenKakuGothicNew-' + weight
    path = os.path.join(FONT_DIR, name + '.ttf')
    if not os.path.exists(path):
        os.makedirs(FONT_DIR, exist_ok=True)
        urllib.request.urlretrieve(FONT_URL % name, path)
    return ImageFont.truetype(path, size)


def load_types():
    s = open(os.path.join(ROOT, 'recommend', 'index.html'), encoding='utf-8').read()
    out = {}
    for m in re.finditer(r"  ([AV][CH][FP][LS]):\{emoji:'[^']*',name:'([^']+)',", s):
        code = m.group(1)
        seg = s[m.end():m.end() + 1500]
        rare = re.search(r"rare:([\d.]+)", seg).group(1)
        img = re.search(r"MINI_SVGS\['%s'\] = '<picture><source srcset=..?/recommend/images/(otter_[a-z]+_v2)\.webp" % code, s).group(1)
        out[code] = {'name': m.group(2), 'rare': rare, 'img': img}
    assert len(out) == 16, len(out)
    return out


def draw_logo(d, x0, y0):
    k = 44 / 36  # ヘッダーの SVG（viewBox 36）を44pxに
    P = lambda pts: [(x0 + a * k, y0 + b * k) for a, b in pts]
    d.polygon(P([(18, 4), (34, 30), (2, 30)]), fill='#405830')
    d.polygon(P([(18, 10), (30, 30), (6, 30)]), fill='#789858')
    d.polygon(P([(10, 30), (17, 17), (24, 30)]), fill='#2c4020')
    d.text((x0 + 48, y0 + 5), 'Yamatch', font=ImageFont.truetype(GEORGIA, 38), fill='#3a4f28')


def make(code, t):
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    ot = Image.open(os.path.join(ROOT, 'recommend', 'images', t['img'] + '.png')).convert('RGBA')
    ot = ot.crop(ot.getbbox())
    s = min(440 / ot.height, 560 / ot.width)
    ot = ot.resize((int(ot.width * s), int(ot.height * s)), Image.LANCZOS)
    im.paste(ot, (600 - ot.width // 2, 36 + (440 - ot.height)), ot)
    # タイプ名：LINE の正方形（幅630）に入るよう、幅600までに収める
    size = 72
    while True:
        fn = zen('Black', size)
        w = d.textlength(t['name'], font=fn)
        if w <= 600 or size <= 40:
            break
        size -= 2
    d.text((600 - w / 2, 486 + (72 - size) // 2), t['name'], font=fn, fill=INK)
    # 左上の文字は LINE の正方形（x 285〜915）にかからないよう x 270 までに収める
    draw_logo(d, 40, 56)
    d.text((40, 118), '登山タイプ診断', font=zen('Bold', 32), fill=INK)
    assert 40 + d.textlength('登山タイプ診断', font=zen('Bold', 32)) <= 270
    assert 40 + 48 + d.textlength('Yamatch', font=ImageFont.truetype(GEORGIA, 38)) <= 270
    for txt, y, f, col in ((code + '型', 60, zen('Black', 42), INK), ('診断者の', 122, zen('Bold', 28), '#6a6058'),
                           (t['rare'] + '%', 158, zen('Black', 50), '#4e6535')):
        w = d.textlength(txt, font=f)
        d.text((W - 48 - w, y), txt, font=f, fill=col)
    out = os.path.join(ROOT, 'ogp', 'type-%s.png' % code.lower())
    im.save(out, optimize=True)
    return out


def bump(ver):
    n = 0
    for f in glob.glob(os.path.join(ROOT, 'type', '*', 'index.html')) + glob.glob(os.path.join(ROOT, 'recommend', '*', 'index.html')) \
            + [os.path.join(ROOT, 'recommend', 'index.html')]:
        s = open(f, encoding='utf-8').read()
        t, k = re.subn(r"(ogp/type-[a-z]{4}\.png|ogp/type-'\+ogpMap\[type\]\+'\.png)\?v=\d+", lambda m: m.group(1) + '?v=' + ver, s)
        if k and t != s:
            open(f, 'w', encoding='utf-8').write(t)
            n += k
    print('版を書き換え：%d か所' % n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ver', help='読み込みの版（例 20261110）')
    a = ap.parse_args()
    for code, t in load_types().items():
        print(make(code, t))
    if a.ver:
        bump(a.ver)


if __name__ == '__main__':
    main()
