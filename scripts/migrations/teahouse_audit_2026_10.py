#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""山ページの茶屋・山小屋の記述を見直した結果の訂正（2026-10-19。景信茶屋の指摘を受けた点検）。
- 安達太良山：くろがね小屋は建て替え工事のため閉鎖中（宿泊・トイレも使えない）。「通年営業の山小屋」は誤り
  出典：二本松市「安達太良山を登山される方へ」（更新日2024-10-10）https://www.city.nihonmatsu.lg.jp/kankou/kankou_info/page012456.html
        二本松市観光連盟（2026年の山開きの案内に「建て替え工事のため営業を休止中」）https://www.nihonmatsu-kanko.jp/?p=7811
- 塔ノ岳：「大倉尾根には山頂までに5軒の茶屋・山小屋」の軒数は、いまの営業を確かめられないので外す
  （堀山の家が2026年1月に火災にあったという登山者の記録があるが、公式の発表を確かめられていない）"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, 'data', 'mountains.json')
V = '2026-10-19'
D = json.load(open(P, encoding='utf-8'))
N = {m['id']: m for m in D}
a = [f for f in N['adatara']['featurePoints'] if f['label'] == 'くろがね小屋']
assert len(a) == 1 and '通年営業' in a[0]['text']
a[0]['label'] = 'くろがね小屋（休業中）'
a[0]['text'] = '中腹の山小屋。建て替え工事のため閉鎖中で、宿泊・トイレは使えない（小屋の近くに携帯トイレのブースがある）'
N['adatara']['featureSources'] = N['adatara']['featureSources'] + ['https://www.city.nihonmatsu.lg.jp/kankou/kankou_info/page012456.html', 'https://www.nihonmatsu-kanko.jp/?p=7811']
N['adatara']['mountainUpdated'] = V
t = [f for f in N['tonosaki']['featurePoints'] if f['label'] == '茶屋と山小屋']
assert len(t) == 1 and '5軒' in t[0]['text']
t[0]['text'] = '大倉尾根の途中に茶屋・山小屋があり、休みながら登れる（営業日・営業状況は時期によって変わる）'
N['tonosaki']['mountainUpdated'] = V
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok')
