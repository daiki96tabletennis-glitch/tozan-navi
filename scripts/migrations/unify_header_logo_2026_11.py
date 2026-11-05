"""ヘッダーのロゴ（三角3つ）と「Yamatch」の字体を全ページでそろえる（2026-11-04。運営者の指示）

正解は記事・山小屋のページのヘッダーの形：
  三角3つの SVG（24px・#405830／#789858／#2c4020）＋ Georgia・20px・太さ700・白・行の高さ1 の「Yamatch」
見た目は style 属性で書く（ページごとの CSS に左右されない）。
対象は「Yamatch」を出すヘッダーがあるページだけ。ヘッダーにページ名だけを出すページ（山選び診断・ギアのページ）と、
ヘッダーの無いページは対象外。トップ（index.html）はヒーローの大きな見出しで別の形なので対象外。
山ページは gen_mountain_pages.py が作るので、スクリプト側を直す（真ん中の三角の色が #6a8055 だった）。
何度流しても同じ結果になる。
"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SVG = ('<svg width="24" height="24" viewBox="0 0 36 36" style="flex-shrink:0" aria-hidden="true">'
       '<polygon points="18,4 34,30 2,30" fill="#405830"/><polygon points="18,10 30,30 6,30" fill="#789858"/>'
       '<polygon points="10,30 17,17 24,30" fill="#2c4020"/></svg>')
FONT = 'color:#fff;font-size:20px;font-weight:700;font-family:Georgia,serif;line-height:1'
SPAN = '<span style="' + FONT + '">Yamatch</span>'
ANY_SVG = r'<svg width="2[246]" height="2[246]" viewBox="0 0 36 36"[^>]*>\s*<polygon points="18,4 34,30 2,30"[\s\S]*?</svg>'


def fix(rel, s):
    hm = re.search(r'<header[\s\S]*?</header>', s)
    if not hm:
        return s, 0
    h = hm.group(0)
    if SVG in h and FONT in h:
        return s, 0
    n = 0
    if rel.startswith('type/') and rel != 'type/index.html' or rel == 'guide/gear-checklist/index.html':
        # <a class="header-logo"><svg 22px/>Yamatch</a>（字体は CSS まかせで Georgia でなかった）
        h, n = re.subn(ANY_SVG + r'\s*Yamatch\s*', SVG + SPAN, h, count=1)
    elif rel in ('about/index.html', 'privacy/index.html', 'terms/index.html', 'type/index.html', 'summit-map/index.html'):
        h, a = re.subn(ANY_SVG, SVG, h, count=1)
        h, b = re.subn(r'<div class="header-title"( style="[^"]*")?>', '<div class="header-title" style="' + FONT + '">', h, count=1)
        n = a + b if (a and b) else 0
    elif rel == 'listing/index.html':
        h, n = re.subn(r'<a href="/" style="flex:1;text-decoration:none"><span class="header-title">Yamatch</span></a>',
                       '<a href="/" style="flex:1;display:flex;align-items:center;gap:6px;text-decoration:none">' + SVG + SPAN + '</a>', h, count=1)
    elif rel == 'howto/index.html':
        h, n = re.subn(r'<div class="ym-logo">Yamatch</div>',
                       '<a href="/" class="ym-logo" style="display:flex;align-items:center;gap:6px;text-decoration:none">' + SVG + SPAN + '</a>', h, count=1)
    if not n:
        return s, 0
    return s[:hm.start()] + h + s[hm.end():], 1


def main():
    done = []
    for f in sorted(glob.glob(os.path.join(ROOT, '**', 'index.html'), recursive=True)):
        rel = os.path.relpath(f, ROOT)
        if rel.startswith(('admin/', '.claude/')):
            continue
        s = open(f, encoding='utf-8').read()
        t, k = fix(rel, s)
        if k:
            open(f, 'w', encoding='utf-8').write(t)
            done.append(rel)
    print('そろえたページ:', len(done))
    for d in done:
        print('  ', d)


if __name__ == '__main__':
    main()
