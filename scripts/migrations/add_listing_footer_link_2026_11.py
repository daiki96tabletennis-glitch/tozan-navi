"""全ページのフッターに「お店の掲載」（/listing/）へのリンクを足す（2026-11-04。運営者の指示）

フッターの「プライバシーポリシー」のリンクのすぐ後ろに、同じ見た目（同じ style・同じ区切り）で足す。
- 直前の区切りが <span …>|</span> ならその span を、" | " なら " | " を、区切りが無ければ何も挟まない
- すでに /listing/ へのフッターのリンクがあるページは飛ばす（何度流しても同じ結果）
- トップ（index.html・JSX）と、生成スクリプト（gen_mountain_pages.py の FOOTER_BLOCK・gen_huts_page.py の FOOTER）は別に直す
- 管理画面（admin/）は対象外
"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LABEL = 'お店の掲載'
PRIV = re.compile(r'(<a ([^>]*?)href="/privacy/"([^>]*)>プライバシーポリシー</a>)')


def patch(s):
    if re.search(r'href="/listing/"[^>]*>' + LABEL + '</a>', s):
        return s, 0
    m = None
    for m in PRIV.finditer(s):
        pass  # フッターはページの最後にあるので、最後の1つを使う
    if not m:
        return s, 0
    attrs = (m.group(2) + m.group(3)).strip()
    attrs = (' ' + attrs) if attrs else ''
    before = s[:m.start()]
    sep = ''
    sm = re.search(r'(<span [^>]*>\|</span>)\s*$', before)
    if sm:
        sep = ' ' + sm.group(1) + ' '
    elif re.search(r' \| $', before):
        sep = ' | '
    else:
        sep = ' '
    link = sep + '<a href="/listing/"' + attrs + '>' + LABEL + '</a>'
    return s[:m.end()] + link + s[m.end():], 1


def main():
    files = glob.glob(os.path.join(ROOT, '**', '*.html'), recursive=True)
    n = 0
    for f in sorted(files):
        rel = os.path.relpath(f, ROOT)
        if rel == 'index.html' or rel.startswith(('admin/', '.claude/', 'node_modules/')):
            continue
        s = open(f, encoding='utf-8').read()
        t, k = patch(s)
        if k:
            open(f, 'w', encoding='utf-8').write(t)
            n += 1
    print('フッターに足したページ:', n)


if __name__ == '__main__':
    main()
