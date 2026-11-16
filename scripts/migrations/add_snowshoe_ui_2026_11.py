"""装備カードに「スノーシュー」（c: "snowshoe"）の名前とアイコンを足す（2026-11-17。運営者の指示）
- 山ページ（assets/js/mountain.js）と、装備カードを写している記事・まとめ（GEAR_ICONS / GEAR_LABEL を持つページ）
- 診断（recommend/index.html）の GEAR_CAT_LABEL / GEAR_CAT_ICON / YM_ICON_BODY
アイコンの形は scripts/ym_icons.py の CUSTOM['snowshoe']。何度流しても同じ結果
"""
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import ym_icons  # noqa: E402

BODY = ym_icons.body('snowshoe')
files = [os.path.join(ROOT, 'assets', 'js', 'mountain.js')] + sorted(
    glob.glob(os.path.join(ROOT, 'articles', '*', 'index.html')) + glob.glob(os.path.join(ROOT, 'search', '*', 'index.html')))
n = 0
for p in files:
    s = open(p, encoding='utf-8').read()
    if 'GEAR_ICONS = {' not in s or 'snowshoe:' in s:
        continue
    a = "  helmet:'"
    b = "helmet:'ヘルメット'"
    if s.count(a) != 1 or s.count(b) != 1:
        raise SystemExit('形が違う：' + p)
    s = s.replace(a, "  snowshoe:'" + BODY + "',\n" + a, 1)
    s = s.replace(b, b + ",snowshoe:'スノーシュー'", 1)
    open(p, 'w', encoding='utf-8').write(s)
    n += 1
p = os.path.join(ROOT, 'recommend', 'index.html')
s = open(p, encoding='utf-8').read()
if "snowshoe:'スノーシュー'" not in s:
    for a, b in ((",helmet:'hard-hat'}", ",helmet:'hard-hat',snowshoe:'snowshoe'}"),
                 ("var YM_ICON_BODY={", "var YM_ICON_BODY={'snowshoe':'" + BODY + "',")):
        if s.count(a) != 1:
            raise SystemExit('recommend の形が違う：' + a)
        s = s.replace(a, b, 1)
    import re
    m = re.search(r"var GEAR_CAT_LABEL=\{[^}]*\}", s)
    s = s[:m.end() - 1] + ",snowshoe:'スノーシュー'}" + s[m.end():]
    open(p, 'w', encoding='utf-8').write(s)
    n += 1
print('直した', n)
