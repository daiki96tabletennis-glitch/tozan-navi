"""よく読まれている記事・まとめ（GA4 の直近28日の表示回数の上位10本。2026-11-15）の絵文字を、線画のアイコン（Lucide・オリジナル）にする。
運営者の指示「まとめ記事も合わせてよく読まれている記事上位10記事で iOS アイコン（絵文字）になっている箇所があれば Lucide アイコンかオリジナルアイコンに直して」

- 置き換えの表と処理は scripts/ym_icons.py の EMOJI_ICON・emoji_to_icons（本文は svg、title・meta・属性・JSON-LD は絵文字を消す）
- 生成で作るページは生成スクリプトの側でも同じ処理をする：search/train-daytrip（gen_train_daytrip.py）、
  articles/winter-no-crampons（migrations/update_winter_no_crampons_2026_11.py）
- 上位10本：電車で行ける日帰り登山20選・中央線・小田急線・冬でも登れる関東の山7選・電車で行ける山（train-access-mountains）・西武線・
  奥多摩駅・新宿発の日帰り・関東の日帰り登山（kanto-day-trip-100）・大船・横浜発の日帰り。中央線・小田急線・西武線・奥多摩駅は絵文字なし
何度流しても同じ結果
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import ym_icons  # noqa: E402

PAGES = ['search/train-daytrip', 'search/jr-chuo-hiking', 'search/odakyu-hiking', 'articles/winter-no-crampons',
         'articles/train-access-mountains', 'search/seibu-hiking', 'search/okutama-station-hiking',
         'search/shinjuku-daytrip', 'articles/kanto-day-trip-100', 'search/ofuna-daytrip']
bad = 0
for rel in PAGES:
    p = os.path.join(ROOT, rel, 'index.html')
    s = open(p, encoding='utf-8').read()
    t = ym_icons.emoji_to_icons(s)
    left = ym_icons.leftover_emoji(t)
    if left:
        print('表に無い絵文字：', rel, left)
        bad += 1
    if not t.rstrip().endswith('</html>') or t.count('<div') != t.count('</div>'):
        raise SystemExit('壊れた：' + rel)
    if t != s:
        open(p, 'w', encoding='utf-8').write(t)
    print(rel, '直した' if t != s else '変わらない')
if bad:
    raise SystemExit(1)
