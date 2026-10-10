#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YAMAPへのリンクの誤りを直す（2026-10-10）。
全156山の yamapUrl を取得して確認したところ、ページが無い（404）リンクが16件、別の山を指すリンクが15件、
山のページではなく活動日記の検索を開くリンクが5件あった。YAMAPの山検索（名前・標高・都道府県が一致するもの）で正しいページを特定した。
あわせて、確認中に見つかった地域表示の誤り2件を直す（笠ヶ岳：長野県北部→岐阜県、倉岳山：神奈川県→山梨県）。
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
IDS = {
    'hotaka': 143, 'iide': 155, 'aizu_koma': 159, 'hiuchigatake': 163, 'jonengatake': 144, 'yakedake': 145, 'kashimayari': 174,
    'kasagatake': 175, 'karamatsu': 58, 'shiomidake': 182, 'arakawadake': 183, 'akaisidake': 184, 'hijiridade': 185, 'terkari': 186,
    'yakushidake': 52, 'kurobegorodam': 271, 'hakusan': 99, 'zaosan': 191, 'myojingatake': 19981, 'yaguradake': 15750,
    'kawanoriyama': 30, 'takanosuyama': 3650, 'iwadonoyama': 16033, 'maruyama_okubusuma': 15432, 'ohnoyama': 811,
    'momakurasan': 19994, 'ogiyama': 16203, 'makuyama': 15756, 'taiheizan': 16730, 'kukiyama': 16005, 'hafuzan_chichibu': 16643,
    'ranzan_saitama': 16667,   # 嵐山渓谷の大平山
    'kamakura_alps': 5352,     # 鎌倉アルプスの最高地点・大平山
    'okusuyama': 3659, 'kannokura': 16665,
}
n = 0
for mid, yid in IDS.items():
    new = 'https://yamap.com/mountains/%d' % yid
    assert N[mid].get('yamapUrl') != new, mid
    N[mid]['yamapUrl'] = new
    n += 1
assert n == 35
for mid, old, new in (('kasagatake', '長野県北部', '岐阜県'), ('kuratakeyama', '神奈川県', '山梨県')):
    assert N[mid]['area'] == old, (mid, N[mid]['area'])
    N[mid]['area'] = new
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('リンクを直した山', n)
