"""記事（/articles/<記事>/）とまとめ（/search/<まとめ>/）の全ページに、共有ボタン（assets/js/share-btn.js）の読み込みを入れる（2026-11-16。運営者の指示）
ボタンはヘッダーの右とページの下に、JS が差し込む。生成スクリプト（gen_winter_specials.py・gen_train_daytrip.py）は自分で入れる。
gen_line_articles.py はページの末尾を引き継ぎ、gen_gourmet_article.py は tokyo-daytrip-5 の末尾を写すので、このスクリプトのあとに作り直しても残る。
記事・まとめを足したら流す。何度流しても同じ結果。記事一覧（articles/index.html）は対象外
"""
import glob
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TAG = '<script src="/assets/js/share-btn.js?v=20261116" defer></script>'
n = 0
for p in sorted(glob.glob(os.path.join(ROOT, 'articles', '*', 'index.html')) + glob.glob(os.path.join(ROOT, 'search', '*', 'index.html'))):
    s = open(p, encoding='utf-8').read()
    if 'share-btn.js' in s:
        continue
    if s.count('</body>') != 1:
        raise SystemExit('</body> が1つでない：' + p)
    s = s.replace('</body>', TAG + '\n</body>')
    open(p, 'w', encoding='utf-8').write(s)
    n += 1
print('入れた', n)
