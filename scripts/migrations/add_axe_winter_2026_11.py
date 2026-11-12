"""冬山装備の月の装備カードに、ピッケルのカードをそろえる（2026-11-11。運営者の指示「ピッケルが必要な山は追加して」）

サイトの決まりでは、冬山装備（winter_gear）＝12本爪アイゼン・ピッケル等（装備カレンダー・持ち物リストの冬山装備の欄）。
ところが gear-data.json のピッケルのカード（axe）は26山の一部の月にしか無く、冬山装備の月がある57山（燕岳・八ヶ岳・白馬岳・立山など）には1枚も無かった。
北岳などの26山でも6月の冬山装備の月に無かった。

- 冬山装備の月（gearCalendar がその月 winter_gear、または月の途中で変わる月で前半が winter_gear）に、ピッケルのカードが無ければ足す
  （カードの中身は前からある山と同じ。場所はアイゼン（来月分があればその後ろ）の次）
- 月の途中で冬山装備に変わる月（後半が winter_gear）は、切り替わる日から翌月のカードが出る（fix_split_month_gear_2026_11.py）ので足さない
- 冬山装備でない月のピッケルのカードは変えない
- 手で作った記事・まとめの装備カードの写し（data-gear-variants）も作り直す
何度流しても同じ結果。このあと gen_mountain_pages.py --all → gen_recommend_gear.py → gen_line_articles.py（路線別の記事）→ check_pages.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GP = os.path.join(ROOT, 'data', 'gear-data.json')
MP = os.path.join(ROOT, 'data', 'mountains.json')
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'migrations'))
from fix_split_month_gear_2026_11 import variants_attr  # noqa: E402

AXE = {'c': 'axe', 'i': '推奨', 'p': 'ブラックダイヤモンド レイブンウィズグリップ',
       'r': '急な雪面・凍結した斜面ではピッケルによる滑落停止技術が必要です。冬季登山に不慣れな場合は経験者との同行をおすすめします。事前に最新の積雪・凍結情報を確認してください。'}


# 出典でピッケルが要らないと確かめた山（review_axe_cards_2026_11.py）
SKIP = ['kitayokodake', 'zaosan', 'azuma', 'adatara', 'nantaisan', 'shirane_gunma', 'kenashiyama', 'kazahariyama', 'enasan', 'keizandake']


def winter(v):
    return v == 'winter_gear' or (isinstance(v, dict) and v.get('before') == 'winter_gear')


def main():
    G = json.load(open(GP, encoding='utf-8'))
    MS = {m['id']: m for m in json.load(open(MP, encoding='utf-8'))}
    changed = {}
    for mid, mm in G.items():
        if mid in SKIP:
            continue
        cal = MS[mid].get('gearCalendar') or []
        for i, v in enumerate(cal):
            if not winter(v):
                continue
            cards = mm[str(i + 1)]
            if any(c['c'] == 'axe' for c in cards):
                continue
            idx = max(j for j, c in enumerate(cards) if c['c'] in ('crampon', 'crampon_next')) + 1
            cards.insert(idx, dict(AXE))
            changed.setdefault(mid, []).append(i + 1)
    with open(GP, 'w', encoding='utf-8') as f:
        json.dump(G, f, ensure_ascii=False, indent=2)
        f.write('\n')
    for mid, mos in changed.items():
        print(MS[mid]['name'], mos)
    print('足した山', len(changed), '月', sum(len(v) for v in changed.values()))
    pages = glob.glob(os.path.join(ROOT, 'articles/*/index.html')) + glob.glob(os.path.join(ROOT, 'search/*/index.html'))
    for p in sorted(pages):
        s = open(p, encoding='utf-8').read()
        if '<!-- generated: scripts/gen_line_articles' in s:
            continue
        hit = []
        for mid in sorted(set(re.findall(r'data-gear-mid="([a-z0-9_-]+)"', s))):
            if mid not in G:
                continue
            pat = re.compile(r'(data-gear-mid="' + mid + r'"[^>]*?data-gear-variants=")([^"]*)(")')
            new = pat.sub(lambda m: m.group(1) + variants_attr(G[mid]) + m.group(3), s)
            if new != s:
                hit.append(mid)
                s = new
        if hit:
            open(p, 'w', encoding='utf-8').write(s)
            print('記事の写し', os.path.relpath(p, ROOT), ' '.join(hit))


if __name__ == '__main__':
    main()
