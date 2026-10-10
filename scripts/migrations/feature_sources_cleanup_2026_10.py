#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""featureSources の点検（2026-10-10）。ページを取得して確かめたところ、別の山・無関係の記事を指していた出典URLを外す。
featurePoints の本文は該当の山の内容であることを確認済み（変更しない）。
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
DROP = {
    'nantaisan': 'https://www.gltjp.com/ja/directory/item/12645/',      # 筑波山のページ
    'otake': 'https://www.nap-camp.com/mag/111504',                     # 鳥取の大山の記事
    'sengenrei': 'https://yamahack.com/2133',                           # 浅間山の記事
    'hafuzan_chichibu': 'https://yamahack.com/2103',                    # 奥秩父の破風山（別の山）
    'kannokura': 'https://yamahack.com/4492',                           # 無関係の記事
    'kayagatake': 'https://yamahack.com/7768',                          # ツアー募集の告知
    'bukosan': 'https://yamahack.com/7547',                             # 山頂トイレの話題で、特徴の出典ではない
}
n = 0
for mid, url in DROP.items():
    s = N[mid]['featureSources']
    assert url in s, (mid, url)
    s.remove(url); n += 1
    assert s, mid
assert n == len(DROP)
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('外した出典:', n)
