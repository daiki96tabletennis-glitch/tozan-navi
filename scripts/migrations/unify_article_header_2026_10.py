#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事（/articles/<記事>/）とまとめ（/search/<まとめ>/）のヘッダーを1つにそろえる（2026-10-31。運営者の指示）。

- 形は記事のヘッダー（色 #3a4f28・三角3つのロゴ・Georgia の「Yamatch」）
- ボタンは左から「山を検索する」（/）「記事一覧へ」（/articles/）の2つ。運営者のボタンは廃止
- ページごとの CSS に左右されないよう、見た目はすべて style 属性に書く
- 生成スクリプト（gen_train_daytrip.py・gen_gourmet_article.py）は、いまのページのヘッダーを引き継ぐので、そのまま残る

  python3 scripts/migrations/unify_article_header_2026_10.py
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LOGO = ('<svg width="24" height="24" viewBox="0 0 36 36" style="flex-shrink:0" aria-hidden="true">'
        '<polygon points="18,4 34,30 2,30" fill="#405830"/><polygon points="18,10 30,30 6,30" fill="#789858"/>'
        '<polygon points="10,30 17,17 24,30" fill="#2c4020"/></svg>')
BTN = ('background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.3);color:#fff;border-radius:8px;'
       'padding:6px 10px;font-size:12px;font-weight:600;line-height:1.2;text-decoration:none;white-space:nowrap')
HEADER = (
    '<header class="ym-site-header" style="background:#3a4f28;padding:12px 16px;margin:0">'
    '<div style="max-width:760px;margin:0 auto;display:flex;align-items:center;gap:8px">'
    '<a href="/" style="display:flex;align-items:center;gap:6px;text-decoration:none;min-width:0;margin-right:auto">' + LOGO
    + '<span style="color:#fff;font-size:20px;font-weight:700;font-family:Georgia,serif;line-height:1">Yamatch</span></a>'
    '<a href="/" style="' + BTN + '">山を検索する</a>'
    '<a href="/articles/" style="' + BTN + '">記事一覧へ</a>'
    '</div></header>'
)


def main():
    files = sorted(glob.glob(os.path.join(ROOT, 'articles', '*', 'index.html'))
                   + glob.glob(os.path.join(ROOT, 'search', '*', 'index.html')))
    done = 0
    for f in files:
        s = open(f, encoding='utf-8').read()
        new, n = re.subn(r'(?s)<header\b[^>]*>.*?</header>', lambda _: HEADER, s, count=1)
        if n != 1:
            sys.exit('ヘッダーが見つからない：' + f)
        if new != s:
            open(f, 'w', encoding='utf-8').write(new)
            done += 1
    print('ページ', len(files), '書き換え', done)


if __name__ == '__main__':
    main()
